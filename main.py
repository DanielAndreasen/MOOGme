#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import argparse


if __name__ == '__main__':
    # Here be dragons...

    """
    Try to run with
        python main.py -h

    to see the autogenerated help text! Cool, isn't it?

    Now, try to run something like
        python main.py -i file1.dat -o file2.moog

    to parse in arguments. This is kind of a dictionary and the arguments can
    be accesed by args.input or args.output.

    Caution! Do not create an argument with a -h flag. Not sure how it will
    handle this, but this is already taken for generating the help text, and it
    should ALWAYS be like this. The same is true for bash commands like
        ls --help (-h does not work).
    """

    parser = argparse.ArgumentParser(prog='pymoog',
                                     description='Spectroscopy with MOOG made easy',
                                     epilog='Happy spectroscopying (we know it\
                                             can be tough!) :)')
    parser.add_argument('-i', '--input',
                        help='An input file. This is just an example of how argparse\
                        works')
    parser.add_argument('-o', '--output',
                        help='An output file')

    args = parser.parse_args()
    print args
