## Repository context

The following information about Fatal1ty/mashumaro was computed from its git history up to the base commit of this task (2023-11-14). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 1879 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 16094 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.98 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.51 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 1 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 94 | Commits with author date in the last three window months. |
| Months with at least one commit | 31 | Window months with one or more commits. |
| Share of months with at least one commit | 0.86 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.28 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.84 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.13 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.31 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.34 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.61 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.33 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 7.57 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 14215.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| benchmark | 1233 | 11 | 4 | 2718 | 220 % | 3 |
| examples | 72 | 0 | 0 | 0 | 0 % | 35 |
| mashumaro/__init__.py | 9 | 3 | 2 | 4 | 44 % | 5 |
| mashumaro/config.py | 41 | 10 | 6 | 41 | 100 % | 2 |
| mashumaro/core | 3794 | 112 | 10 | 8689 | 229 % | 2 |
| mashumaro/dialect.py | 13 | 4 | 2 | 12 | 92 % | 2 |
| mashumaro/exceptions.py | 159 | 4 | 3 | 122 | 77 % | 5 |
| mashumaro/helper.py | 42 | 3 | 2 | 27 | 64 % | 7 |
| mashumaro/jsonschema | 1093 | 46 | 8 | 2027 | 185 % | 0 |
| mashumaro/mixins | 261 | 5 | 3 | 58 | 22 % | 2 |
| mashumaro/types.py | 82 | 12 | 5 | 113 | 138 % | 3 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2023-10 | 0 | 16094 | 0 | 0 | 0 |
