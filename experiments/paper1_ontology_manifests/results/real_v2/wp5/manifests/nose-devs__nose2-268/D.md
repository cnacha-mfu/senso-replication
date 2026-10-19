## Repository context

The following information about nose-devs/nose2 was computed from its git history up to the base commit of this task (2016-02-15). Repository-level figures cover 36 complete months ending 2016-01; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 8254 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 10256 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.92 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.08 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 2 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 11 | Commits with author date in the last three window months. |
| Months with at least one commit | 28 | Window months with one or more commits. |
| Share of months with at least one commit | 0.78 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 2.13 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.88 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 2.19 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.29 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.45 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.67 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.64 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.24 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 2002.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 183 | 0 | 0 | 0 | 0 % | 31 |
| nose2/__init__.py | 1 | 0 | 0 | 0 | 0 % | 47 |
| nose2/__main__.py | 8 | 0 | 0 | 0 | 0 % | 32 |
| nose2/backports | 222 | 0 | 0 | 0 | 0 % | 32 |
| nose2/collector.py | 26 | 0 | 0 | 0 | 0 % | 13 |
| nose2/compat.py | 24 | 1 | 1 | 6 | 25 % | 11 |
| nose2/config.py | 61 | 1 | 1 | 4 | 7 % | 11 |
| nose2/events.py | 752 | 2 | 2 | 68 | 9 % | 9 |
| nose2/exceptions.py | 7 | 1 | 1 | 2 | 29 % | 11 |
| nose2/loader.py | 101 | 2 | 2 | 10 | 10 % | 9 |
| nose2/main.py | 252 | 4 | 3 | 34 | 13 % | 3 |
| nose2/plugins | 2955 | 4 | 4 | 118 | 4 % | 3 |
| nose2/result.py | 95 | 1 | 1 | 12 | 13 % | 11 |
| nose2/runner.py | 51 | 1 | 1 | 2 | 4 % | 11 |
| nose2/session.py | 164 | 1 | 1 | 2 | 1 % | 11 |
| nose2/sphinxext.py | 207 | 1 | 1 | 2 | 1 % | 11 |
| nose2/suite.py | 112 | 3 | 2 | 12 | 11 % | 8 |
| nose2/tools | 399 | 1 | 1 | 51 | 13 % | 11 |
| nose2/util.py | 258 | 1 | 1 | 44 | 17 % | 11 |
| unit_workaround.py | 22 | 0 | 0 | 0 | 0 % | 23 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2016-01 | 0 | 10256 | 0 | 0 | 0 |
| 2015-12 | 0 | 10256 | 0 | 0 | 0 |
| 2015-11 | 11 | 10256 | 4 | 12 | 8 |
| 2015-10 | 0 | 10256 | 0 | 0 | 0 |
| 2015-09 | 0 | 10256 | 0 | 0 | 0 |
| 2015-08 | 0 | 10256 | 0 | 0 | 0 |
| 2015-07 | 0 | 10256 | 0 | 0 | 0 |
| 2015-06 | 9 | 10256 | 3 | 18 | 7 |
| 2015-05 | 4 | 10213 | 3 | 49 | 7 |
| 2015-04 | 3 | 10213 | 2 | 0 | 0 |
| 2015-03 | 5 | 10215 | 2 | 153 | 151 |
| 2015-02 | 2 | 10215 | 2 | 0 | 0 |
| 2015-01 | 5 | 10214 | 3 | 64 | 9 |
| 2014-12 | 4 | 10080 | 2 | 117 | 4 |
| 2014-11 | 0 | 10066 | 0 | 0 | 0 |
| 2014-10 | 2 | 10066 | 1 | 0 | 0 |
| 2014-09 | 8 | 9983 | 4 | 104 | 4 |
| 2014-08 | 4 | 9905 | 2 | 44 | 12 |
| 2014-07 | 10 | 9879 | 4 | 1 | 1 |
| 2014-06 | 21 | 9711 | 3 | 672 | 34 |
| 2014-05 | 95 | 9375 | 9 | 1164 | 244 |
| 2014-04 | 8 | 8582 | 4 | 163 | 33 |
| 2014-03 | 4 | 8475 | 1 | 91 | 6 |
| 2014-02 | 20 | 8475 | 4 | 28 | 7 |
| 2014-01 | 3 | 8405 | 1 | 68 | 3 |
| 2013-12 | 3 | 8405 | 3 | 5 | 2 |
