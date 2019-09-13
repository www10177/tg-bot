#!/usr/bin/python
import sys
import logging
import os 
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(stream = sys.stdout)
from app import app as application
