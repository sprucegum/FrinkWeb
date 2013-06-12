#!/bin/bash
python2 manage.py flush
mv ../Parsed/* ../Logs/
python2 logparser.py
