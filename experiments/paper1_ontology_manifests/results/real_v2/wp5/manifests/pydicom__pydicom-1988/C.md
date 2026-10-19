## Repository context

The following information about pydicom/pydicom was computed from its git history up to the base commit of this task (2024-01-07). Repository-level figures cover 36 complete months ending 2023-12; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.95, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 35 of 36 months active (ratio 0.97 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 4.84 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.88 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.95, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.30 >= 0.9 x first half 0.32. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.06 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| benchmarks | active | 17 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| examples | active | 119 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/_dicom_dict.py | active | 100 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/_private_dict.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/_uid_dict.py | active | 100 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/charset.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/cli | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/config.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/data | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/datadict.py | active | 142 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/dataelem.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/dataset.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/encaps.py | active | 203 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/encoders | active | 153 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/filereader.py | active | 179 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/fileset.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/fileutil.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/filewriter.py | active | 193 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/pixel_data_handlers | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/sr | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/uid.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/util | active | 150 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/valuerep.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pydicom/values.py | active | 166 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| util | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 16 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.95, p < 0.001) but by only 0.02 of median size per year, below 0.05; the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: src/pydicom/sr (80814 lines changed); src/pydicom/_private_dict.py (18587 lines changed); src/pydicom/_dicom_dict.py (5174 lines changed); src/pydicom/dataset.py (4677 lines changed); src/pydicom/pixel_data_handlers (4473 lines changed).
