#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

from flask import Flask
from pathlib import Path

instance_path = Path(__file__).parent.parent.parent / 'instance'
static_folder = Path(__file__).parent.parent.parent / 'www' / 'static'
app = Flask(__name__,
            instance_path=f'{instance_path}',
            instance_relative_config=True,
            template_folder='views',
            static_folder=f'{static_folder}',
            static_url_path='/static/'
            
)
app.config.from_pyfile('config.py')

