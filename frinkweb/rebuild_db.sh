#!/bin/bash
python2 manage.py flush
python2 ./manage.py sql stats
python2 ./manage.py syncdb
mv ../Parsed/* ../Logs/
python2 multiparse.py
