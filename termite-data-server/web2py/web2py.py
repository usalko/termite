#!/usr/bin/env .venv/bin/python3
# -*- coding: utf-8 -*-

import os
import sys

if '__file__' in globals():
    path = os.path.dirname(os.path.abspath(__file__))
elif hasattr(sys, 'frozen'):
    path = os.path.dirname(os.path.abspath(sys.executable))  # for py2exe
else:  # should never happen
    path = os.getcwd()
os.chdir(path)

sys.path = [path] + [p for p in sys.path if not p == path]

# import gluon.import_all ##### This should be uncommented for py2exe.py
import gluon.widget

# Start Web2py and Web2py cron service!
if __name__ == '__main__':
    try:
        from multiprocessing import freeze_support
        freeze_support()
    except:
        sys.stderr.write('Sorry, -K only supported for python 2.6-2.7\n')
    if "COVERAGE_PROCESS_START" in os.environ:
        try:
            import coverage
            coverage.process_startup()
        except:
            pass
    gluon.widget.start(cron=True)
