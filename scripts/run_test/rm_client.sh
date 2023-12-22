#!/bin/bash

source config/server3.sh

CREATE_SESSION_CMD="tmux new-session -d -s $SESSION_NAME"

REMOVE_DOCKER_SERVER="docker stop go-client && docker rm go-client"
echo "tmux send-keys -t client:0.0 '$REMOVE_DOCKER_SERVER' C-m"
ssh $SERVER "tmux send-keys -t client:0.0 '$REMOVE_DOCKER_SERVER' C-m"
