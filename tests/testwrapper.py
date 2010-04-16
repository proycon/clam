#!/usr/bin/env python
#-*- coding:utf-8 -*-

import getopt
import sys

try:
    opts, args = getopt.getopt(sys.argv[1:], "bi:f:s:t:c:")
except getopt.GetoptError, err:
    print "help information and exit:"
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-b":
        print "Boolean parameter activated"
    elif o == "-i":
        print "Integer parameter: ", a
    elif o == "-f":
        print "Float parameter: ", a
    elif o == "-s":
        print "String parameter: ", a
    elif o == "-c":
        print "Choice parameter: ", a
    elif o == "-t":
        print "Text parameter: ", a
    else:
        assert False, "No such option '%s'" % o

print "done."
