#!/bin/bash

echo "prepare to start"
./buildew
mkdir externals
mkdir tools
bin/setup_stm.sh
bin/setup_stmt.sh
bin/setup_mallet.sh
bin/setup_corenlp.sh

echo "python3 web2py/web2py.py -p 8075"
.venv/bin/python3 web2py/web2py.py -p 8075
