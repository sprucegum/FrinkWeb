#!/bin/bash
python2 manage.py runfcgi host=127.0.0.1 port=8080 maxrequests=1 maxchildren=4
