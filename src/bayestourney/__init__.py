#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

from flask import Flask
from pathlib import Path

def create_app():
    instance_path = Path(__file__).parent.parent.parent / 'instance'
    static_folder = Path(__file__).parent.parent.parent / 'www' / 'static'
    app = Flask(__name__,
                instance_path=f'{instance_path}',
                instance_relative_config=True,
                template_folder='views',
                static_folder=f'{static_folder}',
                static_url_path='/static/'

    )
    instance_path.mkdir(parents=True, exist_ok=True)
    app.config.from_pyfile('config.py')

    from . import database as db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    
    from . import app as bayestourney_app
    app.register_blueprint(bayestourney_app.bp)
    app.add_url_rule('/', endpoint='index')

    return app
