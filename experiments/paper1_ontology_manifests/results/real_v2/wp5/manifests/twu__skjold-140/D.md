## Repository context

The following information about twu/skjold was computed from its git history up to the base commit of this task (2022-09-30). Repository-level figures cover 32 complete months ending 2022-08; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 32 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 32 | Month ends at which the lines of code were counted. |
| LOC in the first month | 1267 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 2564 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.81 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.27 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 31 | Commits with author date in the last three window months. |
| Months with at least one commit | 22 | Window months with one or more commits. |
| Share of months with at least one commit | 0.69 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 2.30 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.12 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 2.57 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.25 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.13 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.00 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.47 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.42 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 1.02 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 1297.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| src/skjold/__init__.py | 0 | 0 | 0 | 0 | - | 32 |
| src/skjold/cli.py | 216 | 4 | 1 | 22 | 10 % | 2 |
| src/skjold/core.py | 131 | 2 | 1 | 175 | 134 % | 2 |
| src/skjold/cvss.py | 144 | 1 | 1 | 4 | 3 % | 2 |
| src/skjold/formats.py | 87 | 4 | 1 | 51 | 59 % | 2 |
| src/skjold/ignore.py | 62 | 2 | 1 | 11 | 18 % | 2 |
| src/skjold/sources | 609 | 4 | 2 | 231 | 38 % | 2 |
| src/skjold/tasks.py | 216 | 3 | 1 | 36 | 17 % | 2 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2022-08 | 4 | 2564 | 2 | 1 | 1 |
