#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import math
import dispy

def foo():
    a = 1
    b = 2
    return math.tanh(a * b)


def main():
    dispy.dis(foo)
    print('=' * 50)
    dispy.dis('a = 1; b = 2;\nc = a + b')


if __name__ == '__main__':
    main()
