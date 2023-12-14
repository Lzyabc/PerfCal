# PerfCal
## Overview
  PerfCal is  a specification language designed to generate efficient distributed systems while maintaining simplicity and correctness.  Developers first write a PerfCal specification suitable for model checking. The specification will be converted to TLA+ code to verify the correctness of the specification. The specification can then be transferred to a relaxed specification suited for implementatio by relaxing the atomicity of relaxable steps. The specification will be converted to Go code to implement the specification. 

  Due to time constraints, the format of this project still needs to be further optimized, we will continue to improve the PerfCal compiler, including: 1. Add more English comments; 2. Delete redundant logic; 3. Uniform code format, etc.; 4. Optimize the code structure to make it easier to read and maintain.


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

## Source Code
 The source code of the PerfCal compiler is documented in [src](./src/). The folder lists the source code of the PerfCal compiler. 
 including:
 - The `go` folder contains the source code of the PerfCal compiler for converting the PerfCal to Go code.
 - The `tla` folder contains the source code of the PerfCal compiler for converting the PerfCal to TLA+ code.
 - The `perfcal.lark` file is the grammar file of the PerfCal. It is used by the PerfCal tool to parse the PerfCal. The grammar file is written in [Lark](https://github.com/lark-parser/lark）, a parsing library in Python.


## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

For a copy of the Apache License 2.0, see [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0).
