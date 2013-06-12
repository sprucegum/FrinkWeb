#!/bin/bash
kill `ps -fC python2 | grep manage | awk '{if($3==1){print $2;}}'`
