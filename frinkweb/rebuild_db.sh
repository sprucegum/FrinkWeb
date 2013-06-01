#!/bin/bash
python manage.py flush
mv ../Parsed/* ../Logs/
python logparser.py
