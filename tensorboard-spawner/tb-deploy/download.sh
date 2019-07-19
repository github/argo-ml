#!/bin/bash

set -e
set -x

mkdir -p /downloaded

for log in "$@"
do
    mc cp "dumpster/github-virga/$log" "/downloaded/$log"
    dirname=`echo $log | cut -d/ -f2`
    mkdir -p "/logs/$dirname"
    tar -xvzf "/downloaded/$log" -C "/logs/$dirname"
done