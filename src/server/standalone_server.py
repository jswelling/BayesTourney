#!/usr/bin/env python

####################################
# Notes:

####################################

import bottle
import beaker
import reqhandler

rootPath = '/tourney/'

root= bottle.Bottle(catchall=True)
root.mount(rootPath, reqhandler.application)

bottle.debug(True)
reqhandler.logMessage('starting up under standalone server')
bottle.run(app=root, port=9090, reloader=True)

