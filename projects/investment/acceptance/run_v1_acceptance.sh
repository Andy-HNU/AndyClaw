#!/usr/bin/env bash
set -euo pipefail

cd /root/.openclaw/workspace/projects/investment

export PYTHONPATH=src

run_step() {
  local name="$1"
  shift
  printf '\n[%s] %s\n' "RUN" "$name"
  "$@"
  printf '[%s] %s\n' "OK" "$name"
}

run_step "init-db" python3 -m investment_agent.main init-db
run_step "portfolio-summary" python3 -m investment_agent.main portfolio-summary
run_step "rebalance-check" python3 -m investment_agent.main rebalance-check
run_step "refresh-prices" python3 -m investment_agent.main refresh-prices
run_step "provider-capabilities" python3 -m investment_agent.main provider-capabilities
run_step "persist-analysis" python3 -m investment_agent.main persist-analysis
run_step "persist-rebalance" python3 -m investment_agent.main persist-rebalance
run_step "monthly-plan" python3 -m investment_agent.main monthly-plan
run_step "signal-review" python3 -m investment_agent.main signal-review
run_step "daily-review" python3 -m investment_agent.main daily-review
run_step "weekly-review" python3 -m investment_agent.main weekly-review
run_step "monthly-review" python3 -m investment_agent.main monthly-review
run_step "test-suite" python3 -m unittest discover -s tests_python

printf '\n[%s] %s\n' "DONE" "V1 acceptance replay completed"
