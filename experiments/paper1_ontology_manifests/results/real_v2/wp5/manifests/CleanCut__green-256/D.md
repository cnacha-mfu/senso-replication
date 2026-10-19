## Repository context

The following information about CleanCut/green was computed from its git history up to the base commit of this task (2022-01-12). Repository-level figures cover 36 complete months ending 2021-12; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 6189 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 7829 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.90 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.08 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 5 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 0 | Commits with author date in the last three window months. |
| Months with at least one commit | 20 | Window months with one or more commits. |
| Share of months with at least one commit | 0.56 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 3.86 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.29 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 3.55 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.33 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.38 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.06 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.25 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.26 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 1640.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| example | 16 | 0 | 0 | 0 | 0 % | 19 |
| green/__init__.py | 3 | 0 | 0 | 0 | 0 % | 56 |
| green/__main__.py | 4 | 0 | 0 | 0 | 0 % | 75 |
| green/cmdline.py | 74 | 0 | 0 | 0 | 0 % | 15 |
| green/command.py | 45 | 0 | 0 | 0 | 0 % | 20 |
| green/config.py | 757 | 1 | 1 | 23 | 3 % | 6 |
| green/djangorunner.py | 114 | 1 | 1 | 1 | 1 % | 0 |
| green/examples.py | 55 | 0 | 0 | 0 | 0 % | 20 |
| green/exceptions.py | 3 | 0 | 0 | 0 | 0 % | 63 |
| green/junit.py | 147 | 0 | 0 | 0 | 0 % | 15 |
| green/loader.py | 431 | 1 | 1 | 1 | < 1 % | 9 |
| green/output.py | 180 | 1 | 1 | 11 | 6 % | 9 |
| green/process.py | 413 | 2 | 1 | 143 | 35 % | 6 |
| green/result.py | 720 | 3 | 2 | 31 | 4 % | 0 |
| green/runner.py | 140 | 1 | 1 | 1 | 1 % | 6 |
| green/suite.py | 228 | 0 | 0 | 0 | 0 % | 16 |
| green/version.py | 17 | 0 | 0 | 0 | 0 % | 20 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2021-12 | 0 | 7829 | 0 | 0 | 0 |
| 2021-11 | 0 | 7829 | 0 | 0 | 0 |
| 2021-10 | 0 | 7829 | 0 | 0 | 0 |
| 2021-09 | 0 | 7829 | 0 | 0 | 0 |
| 2021-08 | 0 | 7829 | 0 | 0 | 0 |
| 2021-07 | 7 | 7829 | 1 | 220 | 69 |
| 2021-06 | 0 | 7688 | 0 | 0 | 0 |
| 2021-05 | 0 | 7688 | 0 | 0 | 0 |
| 2021-04 | 5 | 7688 | 1 | 12 | 10 |
| 2021-03 | 0 | 7686 | 0 | 0 | 0 |
| 2021-02 | 0 | 7686 | 0 | 0 | 0 |
| 2021-01 | 0 | 7686 | 0 | 0 | 0 |
| 2020-12 | 3 | 7686 | 1 | 0 | 0 |
| 2020-11 | 4 | 7686 | 3 | 52 | 26 |
| 2020-10 | 17 | 7664 | 3 | 120 | 109 |
| 2020-09 | 6 | 7648 | 1 | 6 | 7 |
| 2020-08 | 3 | 7648 | 1 | 15 | 16 |
| 2020-07 | 0 | 7648 | 0 | 0 | 0 |
| 2020-06 | 7 | 7648 | 2 | 161 | 24 |
| 2020-05 | 12 | 7535 | 2 | 2322 | 1668 |
| 2020-04 | 10 | 6869 | 1 | 85 | 22 |
| 2020-03 | 2 | 6811 | 2 | 5 | 3 |
