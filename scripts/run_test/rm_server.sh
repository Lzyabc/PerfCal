#!/bin/bash


for i in {1..3}
do
    REMOVE_DOCKER_SERVER="docker stop go-container$i && docker rm go-container$i"
    echo "tmux send-keys -t server$i:0.0 '$REMOVE_DOCKER_SERVER' C-m"
    tmux send-keys -t server$i:0.0 '$REMOVE_DOCKER_SERVER' C-m
done
