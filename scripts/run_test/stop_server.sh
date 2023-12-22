#!/bin/bash

# 
for i in {1..3}
do
    tmux send-keys -t server$i:0.0 C-c
    sleep 0.5
    tmux send-keys -t server$i:0.0 "kill \$(sudo lsof -t -i:800$i)" C-m
done
