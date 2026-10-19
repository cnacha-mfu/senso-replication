## Repository context

The following information about zopefoundation/Zope was computed from its git history up to the base commit of this task (2023-11-06). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.97, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 34 of 36 months active (ratio 0.94 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.50 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.86 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.97, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.13 < 0.9 x first half 0.22. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.00 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| src/App/ApplicationManager.py | stable | changed in 1 of the last 12 months; lines changed = 9 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/Cache.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/CopySupport.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/DTMLMethod.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/ObjectManager.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/PropertyManager.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/PropertySheets.py | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/SimpleItem.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/interfaces.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/Products/Five | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/Products/PageTemplates | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/Shared/DC | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/Testing/ZopeTestCase | stable | changed in 1 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/ZPublisher/BaseRequest.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/ZPublisher/HTTPResponse.py | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/Zope2/App | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/Zope2/Startup | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/Zope2/utilities | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/webdav/NullResource.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/webdav/Resource.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/webdav/davcmds.py | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/OFS/Application.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/OFS/Image.py | active | 16 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/ZPublisher/HTTPRequest.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/ZPublisher/WSGIPublisher.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 78 stable, 5 active, 1 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured); module stability for 1 module(s) without non-blank lines.
- N3 (stage rules): LOC grows significantly (τ = 0.97, p < 0.001) but by only 0.01 of median size per year, below 0.05; the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: src/ZPublisher/HTTPRequest.py (919 lines changed); src/OFS/Image.py (162 lines changed); src/OFS/Application.py (151 lines changed); src/ZPublisher/pastefilter.py (123 lines changed); src/App/ZODBConnectionDebugger.py (90 lines changed).
