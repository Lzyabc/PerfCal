# PerfCal
## Result
The results of this experiment are documented in [Result](./result/), including:
- The [raw data](./result/raw) from this experiment
- The data analysis results [statistics](./result/statistics) from this experiment

### Raw Data of This Experiment
  - The `raft` folder contains the raw data for the raft-kv stores. To confirm the experimental results of PGo, we repeated the experiment for PGo under some configuration and recorded it in `pgo_repeat.log`.
  - The `mqtt` folder contains the raw data for the message queue systems.
    In each implementation's folder, there are three files:
    - `latency.log`: The 90th percentile tail latency obtained without limiting the publisher's throughput;
    - `throughput.out`: The extreme throughput obtained without limiting the publisher's throughput, except for EMQX. In EMQX, packet loss occurs in broker when the publisher's throughput reaches a certain level, so we limited the publisher's throughput in the EMQX experiment, meaning that the throughput of EMQX may not be the true extreme throughput.
    - `latency_low_load.log`: The 90th percentile tail latency obtained with 500 clients, each sending one message per minute;
  - The `edu` folder contains the raw data for the online homework grading system.
    - `details.log`: Records the tail latency distribution from 10 to 100;
    - `overview.out`: Statistics of throughput and the 90th percentile tail latency.
