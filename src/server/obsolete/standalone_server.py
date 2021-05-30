#!/usr/bin/env python

####################################
# Notes:

####################################

import flask
#import beaker
import reqhandler

rootPath = '/tourney/'

root= flask.Flask(catchall=True)
root.mount(rootPath, reqhandler.application)

flask.debug(True)
reqhandler.logMessage('starting up under standalone server')
flask.run(app=root, port=9090, reloader=True)

