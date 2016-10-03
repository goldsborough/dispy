# -*- coding: utf-8 -*-

import dispy.disassembler


def dis(code):
    return dispy.disassembler.disassemble(code)
