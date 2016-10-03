# -*- coding: utf-8 -*-

import collections
import itertools


class LineNumbering(object):
    """A class responsible for managing line numbers."""

    Step = collections.namedtuple('Increment', 'bytecode_step, line_step')

    def __init__(self, code_object):
        """
        Initializes the LineNumbering manager.

        Args:
            code_object (code): The code object whose line numbering to manage.
        """

        # The line numbers are stored as
        # (line number step, byte code step) pairs.
        # For example [1, 2, 3, 4] would indicate that, starting with both the
        # line number and bytecode address being zero, the disasssembled output
        # should thefn be formatted as: (1, 2), (4, 6), the format being
        # (line number, bytecode address).
        # So we simply step through the list in steps of two,
        # starting at different offsets.
        steps = list(bytearray(code_object.co_lnotab))
        steps = zip(steps[::2], steps[1::2])
        self._iterator = itertools.starmap(LineNumbering.Step, steps)

        # The first pair of steps
        self._steps = next(self._iterator)

        # The current (absolute) line number
        self.line_number = code_object.co_firstlineno
        self.line_number += self._steps.line_step

        # The next instruction offset (to know when to call step())
        # Set to None initially for the special starting condition
        self.next_address = self._steps.bytecode_step

        # Whether or not we've exhausted the iterator
        self.is_exhausted = False

    def step(self):
        """
        Increments the line numbering iterator by one step.

        Raises:
            StopIteration if an attempt to step an exhausted iterator is made.
        """
        if self.is_exhausted:
            raise StopIteration('Line numbering exhausted')

        # Add the two increments
        self.line_number += self._steps.line_step

        # Try to get a look at where the next instruction starts
        # so we know when to increment the iterator next
        self._try_step()

    def at_new_line(self, program_counter):
        """
        Tests if a  given program counter is at the next line address.

        Args:
          program_counter (int): The current program counter of the
                                 disassembler.

        Returns:
          True if the program counter has reached the next line, else false.
        """
        if self.is_exhausted:
            return False
        return program_counter >= self.next_address

    def _try_step(self):
        """
        Attempts to increment the iterator to fetch the next address.

        This method is necessary to get a look at the next increment value, so
        that we know when the program counter has reached a new line in the
        original code.
        """
        try:
            self._steps = next(self._iterator)
            self.next_address += self._steps.bytecode_step
        except StopIteration:
            # This just means there's no lines left to disassemble
            self.is_exhausted = True
