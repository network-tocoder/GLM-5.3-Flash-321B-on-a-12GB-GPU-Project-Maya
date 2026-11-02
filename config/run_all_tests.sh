#!/bin/bash
# Runs the full test set from this repo against a running Maya server on :8080.
set -e
cd "$(dirname "$0")/.."
until curl -s http://127.0.0.1:8080/v1/models >/dev/null; do echo "waiting for Maya on :8080 ..."; sleep 30; done
nohup python3 scripts/monitor.py logs/monitor.csv >/dev/null 2>&1 &
python3 scripts/bench.py --url http://127.0.0.1:8080 --tag maya_glm_s24 | tee -a logs/bench.log
python3 scripts/run_tests.py --url http://127.0.0.1:8080 --phase main  | tee -a logs/run_main.log
python3 scripts/run_tests.py --url http://127.0.0.1:8080 --phase hard2 | tee -a logs/run_hard2.log
