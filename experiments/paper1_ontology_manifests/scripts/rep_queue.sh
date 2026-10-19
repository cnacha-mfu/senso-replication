#!/bin/bash
# Replication queue (WP6 dev 21-23, WP5 dev 15). Phase 1: nemotron-3-ultra on RQ6, RQ4/RQ5 (A C D on 80, B on 37), 30-min wall limit
# as in the original studies. Phase 2: glm-5.3-flash, same runs, 90-min wall limit (configs *_rep_glm.yaml; deviation 23).
# Since deviation 24 (2026-10-14 OOM incident): 2 workers, leftover processes killed after every unit (wp6.runner.kill_strays), and
# the whole queue runs in a systemd user scope with hard caps:
#   setsid nohup systemd-run --user --scope -p MemoryMax=6G -p TasksMax=300 --unit=senso-rep-queue <this script> > logs/rep_queue.log 2>&1 &
cd /home/adtgrade/research/senso-framework
PY=/home/adtgrade/research/wp5_feasibility/.venv/bin/python
R=experiments/paper1_ontology_manifests/run_wp6.py
C=experiments/paper1_ontology_manifests/configs
LOG=/home/adtgrade/research/data/wp6/logs
BIDS="Fatal1ty__mashumaro-220 VirtusLab__git-machete-179 VirtusLab__git-machete-248 VirtusLab__git-machete-330 VirtusLab__git-machete-350 VirtusLab__git-machete-353 VirtusLab__git-machete-463 VirtusLab__git-machete-483 VirtusLab__git-machete-534 agronholm__sqlacodegen-371 boto__botocore-1996 cevoaustralia__aws-google-auth-34 cityofaustin__knackpy-110 cpplint__cpplint-288 fair-software__howfairis-307 getsentry__sentry-python-3247 gitpython-developers__GitPython-1838 juju__python-libjuju-1054 learningequality__ricecooker-394 mirumee__ariadne-1138 nephila__python-taiga-193 networkx__networkx-7336 nhairs__python-json-logger-26 pydicom__pydicom-1988 python-trio__trio-3096 rigetti__pyquil-1564 stravalib__stravalib-446 taverntesting__tavern-851 tkarabela__pysubs2-77 ucfopen__canvasapi-271 uilibs__uiprotect-275 uilibs__uiprotect-283 uilibs__uiprotect-346 uilibs__uiprotect-347 zopefoundation__DateTime-37 zopefoundation__DateTime-42 zopefoundation__Zope-1183"
$PY $R --config $C/wp6_rep.yaml run --replicates 2 --workers 2 --models nemotron-3-ultra >> $LOG/rep_wp6_full.log 2>&1
$PY $R --config $C/wp5_rep.yaml run --conditions A C D --replicates 2 --workers 2 --models nemotron-3-ultra >> $LOG/rep_wp5_acd.log 2>&1
$PY $R --config $C/wp5_rep.yaml run --conditions B --replicates 2 --workers 2 --models nemotron-3-ultra --ids $BIDS >> $LOG/rep_wp5_b.log 2>&1
echo PHASE1_DONE $(date -u) > $LOG/rep_phase1.done
[ "${PHASE2:-0}" = 1 ] || exit 0   # phase 2 (GLM) only when started with PHASE2=1 (author decision 2026-10-14)
$PY $R --config $C/wp6_rep_glm.yaml run --replicates 2 --workers 2 --models glm-5.3-flash >> $LOG/rep_wp6_full.log 2>&1
$PY $R --config $C/wp5_rep_glm.yaml run --conditions A C D --replicates 2 --workers 2 --models glm-5.3-flash >> $LOG/rep_wp5_acd.log 2>&1
$PY $R --config $C/wp5_rep_glm.yaml run --conditions B --replicates 2 --workers 2 --models glm-5.3-flash --ids $BIDS >> $LOG/rep_wp5_b.log 2>&1
echo QUEUE_DONE $(date -u) > $LOG/rep_queue.done
