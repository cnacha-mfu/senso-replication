#!/bin/bash
# Replication reruns after the NIM Ultra outage of 2026-10-16 (WP5 deviation 16). Waits for the phase-1 queue to end, then for
# nemotron-3-ultra to answer on NIM again, then moves infra-failure units aside (selection by terminal state only) and runs what is
# missing: A/C/D on all tasks (the runner skips existing units) and B on its 37 tasks. Repeats up to 4 rounds if the outage returns.
# Writes logs/rep_phase1_complete.done when no infra-failure unit is left.
#   setsid nohup experiments/paper1_ontology_manifests/scripts/rep_rerun_watch.sh > logs/rep_rerun_watch.log 2>&1 &
# Each run goes in its own systemd user scope with the deviation-24 caps (MemoryMax=6G, TasksMax=300, 2 workers).
cd /home/adtgrade/research/senso-framework
PY=/home/adtgrade/research/wp5_feasibility/.venv/bin/python
R=experiments/paper1_ontology_manifests/run_wp6.py
C=experiments/paper1_ontology_manifests/configs
LOG=/home/adtgrade/research/data/wp6/logs
SUP=/home/adtgrade/research/data/wp5_rep_superseded_infra
BIDS="Fatal1ty__mashumaro-220 VirtusLab__git-machete-179 VirtusLab__git-machete-248 VirtusLab__git-machete-330 VirtusLab__git-machete-350 VirtusLab__git-machete-353 VirtusLab__git-machete-463 VirtusLab__git-machete-483 VirtusLab__git-machete-534 agronholm__sqlacodegen-371 boto__botocore-1996 cevoaustralia__aws-google-auth-34 cityofaustin__knackpy-110 cpplint__cpplint-288 fair-software__howfairis-307 getsentry__sentry-python-3247 gitpython-developers__GitPython-1838 juju__python-libjuju-1054 learningequality__ricecooker-394 mirumee__ariadne-1138 nephila__python-taiga-193 networkx__networkx-7336 nhairs__python-json-logger-26 pydicom__pydicom-1988 python-trio__trio-3096 rigetti__pyquil-1564 stravalib__stravalib-446 taverntesting__tavern-851 tkarabela__pysubs2-77 ucfopen__canvasapi-271 uilibs__uiprotect-275 uilibs__uiprotect-283 uilibs__uiprotect-346 uilibs__uiprotect-347 zopefoundation__DateTime-37 zopefoundation__DateTime-42 zopefoundation__Zope-1183"
say() { echo "$(date -u '+%F %T') $*"; }

ultra_ok() {   # 3 short calls in a row, each answered within 30 s
  timeout 150 $PY - <<'EOF'
import os, sys
from dotenv import load_dotenv; load_dotenv('.env')
from openai import OpenAI
c = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY_2"], timeout=30, max_retries=0)
for _ in range(3):
    c.chat.completions.create(model="nvidia/nemotron-3-ultra-550b-a55b", messages=[{"role": "user", "content": "Say OK"}],
                              max_tokens=5, extra_body={"chat_template_kwargs": {"enable_thinking": False}})
EOF
}

move_infra() {   # prints the number of infra-failure units moved aside
  $PY - "$SUP" 2>/dev/null <<'EOF'
import sys, json, glob, shutil, os
sys.path.insert(0, '.')
from experiments.paper1_ontology_manifests.wp5.runner import is_infra
sup = sys.argv[1]; os.makedirs(sup, exist_ok=True); n = 0
base = 'experiments/paper1_ontology_manifests/results/real_v2/wp5_rep/runs'
for f in glob.glob(base + '/units/*ultra*.json'):
    u = json.load(open(f))
    if u['status'] == 'env_failed' or (u['status'] == 'done' and is_infra(u)):
        for p in [f] + glob.glob(f"{base}/trajectories/{u['unit_id']}.*") + glob.glob(f"{base}/patches/{u['unit_id']}.*"):
            dst = os.path.join(sup, os.path.basename(p))
            if os.path.exists(dst):
                dst += '.' + u.get('started', 'x').replace(':', '')
            shutil.move(p, dst)
        n += 1
print(n)
EOF
}

capped() { systemd-run --user --scope -p MemoryMax=6G -p TasksMax=300 --unit="senso-rep-rerun-$1" "${@:2}"; }

say "waiting for senso-rep-queue.scope to end"
while systemctl --user is-active --quiet senso-rep-queue.scope; do sleep 600; done
for round in 1 2 3 4; do
  say "round $round: waiting for Ultra"
  until ultra_ok; do sleep 900; done
  say "Ultra answers; moved $(move_infra | tail -1) infra-failure units to $SUP"
  capped acd-$round $PY $R --config $C/wp5_rep.yaml run --conditions A C D --replicates 2 --workers 2 --models nemotron-3-ultra >> $LOG/rep_wp5_acd.log 2>&1
  capped b-$round $PY $R --config $C/wp5_rep.yaml run --conditions B --replicates 2 --workers 2 --models nemotron-3-ultra --ids $BIDS >> $LOG/rep_wp5_b.log 2>&1
  left=$($PY - 2>/dev/null <<'EOF'
import sys, json, glob
sys.path.insert(0, '.')
from experiments.paper1_ontology_manifests.wp5.runner import is_infra
print(sum(1 for f in glob.glob('experiments/paper1_ontology_manifests/results/real_v2/wp5_rep/runs/units/*ultra*.json')
          for u in [json.load(open(f))] if u['status'] == 'env_failed' or (u['status'] == 'done' and is_infra(u))))
EOF
)
  left=$(echo "$left" | tail -1)   # the wp5 import prints a mini-swe-agent banner on stdout
  say "round $round done; infra-failure units left: $left"
  if [ "$left" = 0 ]; then echo "PHASE1_COMPLETE $(date -u)" > $LOG/rep_phase1_complete.done; exit 0; fi
done
say "infra failures remain after 4 rounds; stopping for the author"
