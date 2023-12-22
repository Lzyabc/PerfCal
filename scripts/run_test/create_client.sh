#!/bin/bash


# # create client
CREATE_DOCKER_CLIENT="docker run -it -d --network host --name go-client $PerCalImg:latest /bin/bash"

tmux send-keys -t client:0.0 '$CREATE_DOCKER_CLIENT' C-m
sleep 1
tmux send-keys -t client:0.0 'docker exec -ti go-client bash -c "cd ~/profile/examples_run && go run src/main.go --name=raft_client --requestNum=5000 --clientNum=10 --logPath=log/test.log"' C-m
