#!/bin/bash

# sleep 5
tmux send-keys -t client:0.0 'docker cp go-client:/root/perfcal/examples_run/log/test.log /root/workspace/deploy/perfcal/perfcal/shell/log' C-m

