#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

from flask import Flask
from pathlib import Path

instance_path = Path(__file__).parent.parent.parent / 'instance'
app = Flask(__name__,
            instance_path=f'{instance_path}',
            instance_relative_config=True,
            template_folder='views'
)
app.config.from_pyfile('config.py')

