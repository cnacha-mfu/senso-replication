## Repository context

The following information about tkarabela/pysubs2 was computed from its git history up to the base commit of this task (2024-05-04). Repository-level figures cover 36 complete months ending 2024-04; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): phase-out. Evidence: phase-out: no commit for 12 months.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.84, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): not consistent with this regularity. 14 of 36 months active (ratio 0.39 < 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 2.23 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): not consistent with this regularity. Commit-rate CV 1.63 >= 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.84, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.18 < 0.9 x first half 0.24. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.11 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/__main__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/cli.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/common.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/formatbase.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/formats.py | stable | changed in 1 of the last 12 months; lines changed = 9 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/jsonformat.py | stable | changed in 1 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/ssaevent.py | stable | changed in 1 of the last 12 months; lines changed = 6 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/ssafile.py | stable | changed in 1 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/ssastyle.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/substation.py | stable | changed in 1 of the last 12 months; lines changed = 8 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/time.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/webvtt.py | stable | changed in 1 of the last 12 months; lines changed = 5 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/whisper.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pysubs2/__init__.py | active | 13 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pysubs2/exceptions.py | active | 120 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pysubs2/microdvd.py | active | 12 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pysubs2/mpl2.py | active | 56 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pysubs2/subrip.py | active | 19 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pysubs2/tmp.py | active | 31 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.84, p < 0.001), but the last commit was 12 months before the end of the window, at or above the 12-month dormancy limit; the stage rule therefore infers phase-out.
- N4 (stage and modules): Although the repository-level stage is phase-out, these modules changed often in the last 12 months: pysubs2/exceptions.py (59 lines changed); pysubs2/subrip.py (28 lines changed); pysubs2/tmp.py (26 lines changed); pysubs2/mpl2.py (25 lines changed); pysubs2/microdvd.py (11 lines changed).
