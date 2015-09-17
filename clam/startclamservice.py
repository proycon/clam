#!/usr/bin/env python
# -*- coding: utf8 -*-


import os.path
import sys

def main():
    PYTHONBIN = 'python'

    try:    
        import clam
    except:
        sys.path.append(sys.path[0] + '/..')
        os.environ['PYTHONPATH'] = sys.path[0] + '/..'
        import clam

    os.chdir(os.path.dirname(clam.__file__))
    return os.system(PYTHONBIN + ' ./clamservice.py ' + ' '.join(sys.argv[1:]))
        
if __name__ == '__main__':
    sys.exit(main())
