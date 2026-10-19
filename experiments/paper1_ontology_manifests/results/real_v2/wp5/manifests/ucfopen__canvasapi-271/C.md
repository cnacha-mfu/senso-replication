## Repository context

The following information about ucfopen/canvasapi was computed from its git history up to the base commit of this task (2019-06-20). Repository-level figures cover 36 complete months ending 2019-05; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.92, p < 0.001) of 0.54 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.92, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 35 of 36 months active (ratio 0.97 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 2.20 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.69 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.92, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.36 >= 0.9 x first half 0.36. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.89 > 0.3 and multi-author months 0.89 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| canvasapi/communication_channel.py | stable | changed in 2 of the last 12 months; lines changed = 10 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/content_migration.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/discussion_topic.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/external_tool.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/folder.py | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/module.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/outcome.py | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/page.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| docs | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| scripts | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| canvasapi/account.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/assignment.py | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/blueprint.py | active | 166 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/canvas.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/course.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/current_user.py | active | 143 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/group.py | active | 11 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/poll.py | active | 165 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/poll_session.py | active | 167 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/quiz.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/requester.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/section.py | active | 12 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/submission.py | active | 139 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/user.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| canvasapi/util.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 21 stable, 9 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.92, p < 0.001) and by 0.54 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: canvasapi/discussion_topic.py (546 LOC); canvasapi/outcome.py (319 LOC); canvasapi/page.py (227 LOC); docs (219 LOC); canvasapi/content_migration.py (215 LOC).
