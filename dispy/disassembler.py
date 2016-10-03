# -*- coding: utf-8 -*-

from __future__ import print_function

import dis
import sys

from dispy.line_numbering import LineNumbering


class Disassembler(object):

    STOP_CODE = 0x0  # dis.opmap['STOP_CODE']
    POP_TOP = 0x1  # dis.opmap['POP_TOP']
    LINE_WIDTH = 8
    FORMAT_WIDTH = max(map(len, dis.opname)) + LINE_WIDTH

    CODE_TYPE = (lambda: None).__code__.__class__

    def __init__(self, code, output_file=sys.stdout):
        """
        Constructs a new disassembler object.

        The disassembler will attempt to access the code object associated with
        the argument passed, or compile the code if required. It will then
        intepret the bytecode of the code object instruction by instruction and
        emulate the behavior of dis.dis by pretty-printing the disassembly of
        each bytecode instruction.

        Args:
          code (any): The code to disassemble.
          output_file (file): the file to print the disassembly to.
        """

        self.output_file = output_file

        # Get the code object, either through
        # compilation or from the __code__ attributes
        self._code_object = Disassembler._compile_to_code_object(code)

        # The actual bytecode byte string
        self._bytecode = list(bytearray(self._code_object.co_code))

        # Get the instructions taking arguments for easier lookup
        instructions = self._join_instructions_that_take_arguments()
        self._instructions_taking_arguments = instructions

        # The program counter for disassembling
        self._program_counter = 0

        # Instantiate a manager class for the line numbering
        self._line_numbering = LineNumbering(self._code_object)

    def __call__(self):
        """See Also: disassemble()"""
        self.disassemble()

    def disassemble(self):
        """Runs the disassembler on the code with which it was constructed."""
        while self._program_counter < len(self._bytecode):
            instruction = self._current_instruction
            # The STOP_CODE instruction (0x0) is used only by the compiler
            # and is not of interest to the intepreter and user. It's always
            # followed by POP_TOP (0x1). Neither take arguments, so just skip
            # two bytes
            if self._at_stop_sequence(instruction):
                self._program_counter += 2
            else:
                self._disassemble_instruction(instruction)

    def _disassemble_instruction(self, instruction):
        """
        Inteprets a single code instruction.

        An instruction can either be a standalone byte of bytecode, or be
        associated with a single 16-bit little-endian argument, stored right
        after the instruction in the bytecode.

        Args:
          instruction (int): The instruction byte (opcode).
        """
        takes_arguments = instruction in self._instructions_taking_arguments

        if takes_arguments:
            constant = self._load_constant(self._program_counter)
            argument = self._load_argument(instruction, constant)
            self._print_instruction(instruction, (constant, argument))
            # Increment two bytes for the argument
            self._program_counter += 2
        else:
            self._print_instruction(instruction)

        # Always increment by one byte for the instruction opcode
        self._program_counter += 1

    def _load_argument(self, instruction, constant):
        """
        Inteprets a constant as an argument for a particular instruction.

        Args:
          instruction (int): The instruction opcode.
          constant (int): The actual argument constant.

        Returns:
            An disassembleation of the constant for the particular kind of
            instruction passed.
        """
        if instruction in dis.hasname:
            # Expects a 16-bit little-endian index into the name table
            return self._code_object.co_names[constant]
        elif instruction in dis.haslocal:
            # Expects a 16-bit little-endian index into the local name table
            return self._code_object.co_varnames[constant]
        elif instruction in dis.hasconst:
            # Expects a 16-bit little-endian index into the constants table
            return self._code_object.co_consts[constant]
        elif instruction in dis.hasnargs:
            # Expects the number positional and keyword arguments
            return self._load_function_call_arguments()
        elif instruction in dis.hasjrel:
            # Expects a constant to be passed in the instruction itself
            return self._program_counter + constant
        elif instruction in dis.hasjabs:
            # Expects a constant to be passed in the instruction itself
            return constant

    @property
    def _current_instruction(self):
        """Utility property to fetch the current instruction opcode."""
        return self._bytecode[self._program_counter]

    def _load_constant(self, offset):
        """
        Loads a constant from bytecode.

        A constant (argument to an instruction) is always 16 bit and
        little-endian. Also, if a instruciton has an argument at all, it only
        has one such argument.

        Args:
          offset (int): The offset of the instruction for which to fetch the
                        constant.

        Returns:
            The constant for the instruction at the given offset.
        """
        # Laod the little-endian 16-bit immediate
        high_byte = self._bytecode[offset + 2] << 8
        low_byte = self._bytecode[offset + 1]

        return high_byte | low_byte

    def _print_instruction(self, instruction, argument=None):
        """
        Prints a disassmbled instruction.

        Args:
          instruction (int): The instruction opcode.
          argument (tuple): If given, a (constant, argument) pair describing
                            the raw and disassembleed argument.
        """
        instruction_name = dis.opname[instruction]
        line = '{0}{1} {2}'.format(
            self._format_line_number(),
            self._program_counter,
            instruction_name
        )

        if argument is not None:
            line = line.ljust(Disassembler.FORMAT_WIDTH)
            line += '{0} ({1})'.format(*argument)

        print(line, file=self.output_file)

    def _load_function_call_arguments(self):
        """
        Load the arguments for function call instructions.

        Function call instructions like CALL_FUNCTION, CALL_FUNCTION_VAR or
        CALL_FUNCTION_KW have a slightly different argument format, in that the
        upper (left) byte of the 16 bit argument specifies the number of
        positional arguments, while the lower (right) bytes specifies the number
        keyword argumens the function takes. This would normally then be used to
        pop the right number of values from the data stack to call a function
        symbol.

        Returns:
            A string suitable for printing as the argument part of a
            disassembled instruction.
        """
        # The lower byte is the number of positional arguments
        number_of_positional = self._bytecode[self._program_counter + 1]
        # The higher byte is the number of keyword arguments
        number_of_keyword = self._bytecode[self._program_counter + 2]

        return '{0} positional, {1} keyword pair'.format(
            number_of_positional,
            number_of_keyword
        )

    def _format_line_number(self):
        """
        Formats the line number according to the current program counter.

        The line number is only printed for new lines in the original code, as
        per the behavior of dis.dis. Furthermore, if the program counter happens
        to be at the bytecode address of the next instruction, the line
        numbering is incremented and the line is added to the returned string.
        Otherwise, for disassembled instructions belonging to previous
        instructions, a strin with a suitable amount of space is returned.

        Returns:
            A string suitable for printing as the left-most part of the
            disassembly of an instruction.
        """
        line_number = ''
        if self._line_numbering.at_new_line(self._program_counter):
            if self._program_counter > 0:
                print(file=self.output_file)
            line_number = self._line_numbering.line_number
            self._line_numbering.step()
        elif self._program_counter == 0:
            # Hack an issue with single-line string code
            line_number = self._line_numbering.line_number

        return str(line_number).ljust(Disassembler.LINE_WIDTH)

    def _at_stop_sequence(self, instruction):
        if instruction != Disassembler.POP_TOP:
            return False
        if self._program_counter + 1 == len(self._bytecode):
            return False
        if self._bytecode[self._program_counter + 1] != Disassembler.STOP_CODE:
            return False
        return True

    @staticmethod
    def _join_instructions_that_take_arguments():
        """Returns a list of the opcodes of instructions taking arguments."""
        result = []
        for name in dir(dis):
            if name.startswith('has'):
                result.extend(getattr(dis, name))

        # Faster lookup in a hashset
        return set(result)

    @staticmethod
    def _compile_to_code_object(code):
        """
        Gets the code object for a piece of code.

        Args:
          code (any): The code to compile (get a code object for).

        Returns:
            For functions and methods with a `__code__` property, returns the
            value of the `__code__` attribute. Else it is the return value of
            calling `compile` on the passed object.
        """
        if hasattr(code, '__code__'):
            return code.__code__
        if isinstance(code, Disassembler.CODE_TYPE):
            return code
        return compile(code, '<string>', 'exec')


def disassemble(code):
    """Runs the disassembler on the given code."""
    Disassembler(code)()
