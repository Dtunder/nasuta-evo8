#!/bin/bash
START_SEED=20 END_SEED=30 NUM_SIMS=5 python src/xai_multiseed.py > run_benchmark.log 2>&1
