## Repository context

The following information about stravalib/stravalib was computed from its git history up to the base commit of this task (2023-11-05). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 4381 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 8094 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.89 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.09 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 92 | Commits with author date in the last three window months. |
| Months with at least one commit | 20 | Window months with one or more commits. |
| Share of months with at least one commit | 0.56 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 3.61 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.84 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 3.42 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.37 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.46 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.31 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.44 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.14 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.85 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 742.60 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 162 | 11 | 6 | 374 | 231 % | 3 |
| examples | 43 | 5 | 4 | 47 | 109 % | 2 |
| src/stravalib/__init__.py | 6 | 1 | 1 | 8 | 133 % | 3 |
| src/stravalib/client.py | 1892 | 1 | 1 | 2297 | 121 % | 3 |
| src/stravalib/exc.py | 137 | 1 | 1 | 191 | 139 % | 3 |
| src/stravalib/field_conversions.py | 57 | 2 | 2 | 91 | 160 % | 2 |
| src/stravalib/model.py | 1031 | 7 | 3 | 1331 | 129 % | 1 |
| src/stravalib/protocol.py | 457 | 1 | 1 | 524 | 115 % | 3 |
| src/stravalib/strava_model.py | 1320 | 1 | 1 | 1449 | 110 % | 3 |
| src/stravalib/unit_registry.py | 3 | 1 | 1 | 4 | 133 % | 3 |
| src/stravalib/unithelper.py | 90 | 1 | 1 | 115 | 128 % | 3 |
| src/stravalib/util | 408 | 1 | 1 | 483 | 118 % | 3 |

Other modules: 0 not listed.
