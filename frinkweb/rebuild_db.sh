#!/bin/bash
echo "DROP DATABASE frinkstats;CREATE DATABASE frinkstats;GRANT ALL PRIVILEGES ON 
DATABASE frinkstats TO frink;" | sudo -u postgres psql
python2 ./manage.py syncdb
python2 ./manage.py sql stats
python2 ./manage.py syncdb
mv ../Parsed/* ../Logs/
python2 multiparse.py
