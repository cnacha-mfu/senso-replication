## Repository context

The following information about Fatal1ty/mashumaro was computed from its git history up to the base commit of this task (2024-04-28). Repository-level figures cover 36 complete months ending 2024-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 4555 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 19246 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.98 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.62 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 47 | Commits with author date in the last three window months. |
| Months with at least one commit | 31 | Window months with one or more commits. |
| Share of months with at least one commit | 0.86 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.27 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.82 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.14 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.36 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.27 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.61 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.31 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.02 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 3.23 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 14691.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| benchmark | 1237 | 4 | 2 | 2212 | 179 % | 5 |
| mashumaro/__init__.py | 9 | 3 | 2 | 4 | 44 % | 10 |
| mashumaro/codecs | 687 | 19 | 4 | 1380 | 201 % | 3 |
| mashumaro/config.py | 60 | 16 | 7 | 68 | 113 % | 3 |
| mashumaro/core | 4331 | 116 | 11 | 4089 | 94 % | 0 |
| mashumaro/dialect.py | 53 | 7 | 3 | 87 | 164 % | 3 |
| mashumaro/exceptions.py | 172 | 5 | 4 | 78 | 45 % | 1 |
| mashumaro/helper.py | 42 | 0 | 0 | 0 | 0 % | 12 |
| mashumaro/jsonschema | 1124 | 21 | 7 | 419 | 37 % | 3 |
| mashumaro/mixins | 260 | 7 | 4 | 77 | 30 % | 0 |
| mashumaro/types.py | 94 | 10 | 4 | 66 | 70 % | 0 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2024-03 | 22 | 19246 | 3 | 67 | 9 |
