#!/bin/bash
# Note: This script is used only for test because the servers are running in local machine.
source config/server3.sh


SESSION_NAME="test"
CMD1='ls'
ssh $SERVER "tmux send-keys -t $SESSION_NAME:0.0 '$CMD1' C-m"

CREATE_SESSION_CMD="tmux new-session -d -s $SESSION_NAME"

# 
for i in {1..3}
do
    CREATE_DOCKER_SERVER="docker run --network host -it -d --name go-container$i lucaszy/profile:latest /bin/bash"
    tmux send-keys -t server$i:0.0 '$CREATE_DOCKER_SERVER' C-m
done

for i in {1..3}
do
    tmux send-keys -t server$i:0.0 'docker exec -ti go-container$i bash -c "cd ~/profile/examples_run && go run src/main.go --name=raft --id=$i"' C-m
done
