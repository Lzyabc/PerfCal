# PerfCal
## Overview
  PerfCal is a specification language, based on TLA+ and PlusCal, designed to generate efficient distributed systems while maintaining simplicity and correctness.  Developers first write a PerfCal specification suitable for model checking. The specification will be converted to TLA+ code to verify the correctness of the specification. The specification can then be transferred to a relaxed specification suited for implementatio by relaxing the atomicity of relaxable steps. The specification will be converted to Go code to implement the specification. 

  PerfCal used the open source libraries from [PGo](https://github.com/DistCompiler/pgo). PGo offers a generation and execution architecture that ensures consistency between the implementation and design. PerfCal follows PGo's approach to maintain consistency between the implementation and design. PerfCal extends the TLA+ and PGo's concepts by introducing new abstractions specifically designed to improve performance and enable the generation of efficient system implementations. PerfCal differs from PGo in three key aspects: 1. We introduce a new Go-like language with a compiler and new abstractions like relaxable atomic steps, specification context, and thread pool; 2. PerfCal creates implementations from a relaxed specification; 3. Unlike MPCal's limitations, PerfCal can specify dynamic multithreaded systems.

  Due to time constraints, the format of this project still needs to be further optimized, we will continue to improve the PerfCal compiler, including: 1. Add more English comments; 2. Delete redundant logic; 3. Uniform code format, etc.; 4. Optimize the code structure to make it easier to read and maintain.

  PerfCal's logo is a hand-drawn cartoon peregrine falcon, a bird known for its speed and agility. 

 <img src="LOGO.svg" alt="alt text" width="300">

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
    - `details.log`: Records the tail latency distribution from 10th percentile tail latency to 100th percentile tail latency;
    - `overview.out`: Statistics of throughput and the 90th percentile tail latency.

## Source Code
 The source code of the PerfCal compiler is documented in [src](./src/). The folder lists the source code of the PerfCal compiler. 
 including:
 - The `go` folder contains the source code for converting the PerfCal to Go code. The core of the PerfCal-Go Compiler is env.py. This module is designed for handling PerfCal objects, focusing on conversion and manipulation tasks. It features a range of utility functions and classes to process and manage profile data effectively. Key components include functions for string manipulation, a Context class for managing code environments, and comprehensive annotation handling capabilities. 

 - The `tla` folder contains the source code for converting the PerfCal to TLA+ code. The env.py in this folder is similar to the env.py in the go folder, serving as the core of the PerfCal-TLA+ Compiler. The main difference is that the env.py in the tla folder is designed for handling TLA+ objects. Currently, some code in tla/env.py may be redundant and can be merged with the code in go/env.py. We will continue to optimize the code in the future.
  
 - The `perfcal.lark` file is the grammar file of the PerfCal. It is used by the PerfCal tool to parse the PerfCal. The grammar file is written in [Lark](https://github.com/lark-parser/lark), a parsing library in Python. Grammer for PerfCal is modified from Python 3 grammar in Lark. Lark is licensed under MIT License (https://opensource.org/license/mit/)

  - The `scripts` folder contains the scripts for data processing and running. The `scripts/run_test` contains part of the shell scripts for running the experiments. The `scripts/analysis` contains the Python scripts for analyzing the experiment results and generating statistics.

## License

This project will be licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

For a copy of the Apache License 2.0, see [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0).
