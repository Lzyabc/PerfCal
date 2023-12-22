#!/bin/bash

./start_server.sh
# 
for valueSize in 16 128 1024
do 
    for writeRatio in 0.05
    do
        for clientNum in $(seq 5 10 5)
        do
            sleep 3
            for i in {1..5}
            do
                echo "start client"
                echo "clientNum: $clientNum, valueSize: $valueSize, writeRatio: $writeRatio"
                ./start_client.sh $clientNum $valueSize $writeRatio
                echo "testing"
                sleep 10
                echo "stop client"
                ./stop_client.sh
                sleep 3
            done
        done
    done 
done 
./copy_log.sh