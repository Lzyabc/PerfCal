#!/bin/bash


for i in {1..3}
do
    # start raft server
    tmux send-keys -t server$i:0.0 "docker exec -i go-container$i bash -c 'cd ~/profile/examples_run && go run src/main.go --name=raft --id=$i'" C-m
    sleep 0.5
done
