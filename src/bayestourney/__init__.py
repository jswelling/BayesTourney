#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

from flask import Flask
from pathlib import Path
from pprint import pprint


def create_app(test_config=None):
    static_folder = Path(__file__).parent.parent.parent / 'www' / 'static'
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder='views',
        static_folder=f'{static_folder}',
        static_url_path='/'
    )
    if test_config is None:
        app.config.from_pyfile('config.py')
    else:
        app.config.from_mapping(test_config)
    
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)

    from flask_mail import Mail
    mail = Mail()
    mail.init_app(app)
    app.flask_mail_mail = mail  # for later access

    from . import database as db
    db.init_app(app)

    from flask_migrate import Migrate
    migrate = Migrate()
    migrate.init_app(app, db, render_as_batch=True)

    from . import auth
    app.register_blueprint(auth.bp)
    
    from . import app as bayestourney_app
    app.register_blueprint(bayestourney_app.bp)
    app.add_url_rule('/', endpoint='index')

    return app

