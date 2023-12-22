#!/bin/bash


# get clientNum
clientNum=$1
valueSize=$2
writeRatio=$3
if [ -z "$clientNum" ]; then
    echo "clientNum is empty"
    exit 1
fi

tmux send-keys -t client:0.0 "docker exec -ti go-client bash -c 'cd ~/profile/examples_run && go run src/main.go --name=raft_client --requestNum=10000 --clientNum=$clientNum --logPath=log/test1.log --writeRatio=$writeRatio --valueSize=$valueSize' " C-m
