#!/bin/bash
kill `ps -fC python | grep manage | awk '{if($3==1){print $2;}}'`
