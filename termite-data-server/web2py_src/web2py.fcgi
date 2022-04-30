#!/home/chuangca/bin/python

import cgitb
cgitb.enable()

import os
WEB2PY_PATH = os.path.dirname( os.path.abspath( __file__ ) )  # /u/jcchuang/.../TermiteDataServer/web2py
ENVIRON = { 'web2py_path' : WEB2PY_PATH }

import web2py.gluon.main
import web2py.gluon.contrib.gateways.fcgi as fcgi
server = fcgi.WSGIServer( gluon.main.wsgibase, environ = ENVIRON )
server.run()
