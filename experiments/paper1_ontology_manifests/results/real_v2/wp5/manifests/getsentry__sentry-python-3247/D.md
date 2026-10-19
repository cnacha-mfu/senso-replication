## Repository context

The following information about getsentry/sentry-python was computed from its git history up to the base commit of this task (2024-07-03). Repository-level figures cover 36 complete months ending 2024-06; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 20495 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 57917 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.99 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.45 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 205 | Commits with author date in the last three window months. |
| Months with at least one commit | 36 | Window months with one or more commits. |
| Share of months with at least one commit | 1.00 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 0.89 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.72 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 0.83 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.26 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.17 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.94 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.94 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.05 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 1.83 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 346.50 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 148 | 58 | 12 | 116 | 78 % | 1 |
| scripts | 488 | 30 | 10 | 789 | 162 % | 1 |
| sentry_sdk/_lru_cache.py | 114 | 1 | 1 | 2 | 2 % | 6 |
| sentry_sdk/_queue.py | 226 | 1 | 1 | 2 | 1 % | 6 |
| sentry_sdk/_types.py | 187 | 16 | 8 | 295 | 158 % | 1 |
| sentry_sdk/api.py | 304 | 15 | 7 | 482 | 159 % | 1 |
| sentry_sdk/client.py | 710 | 40 | 10 | 730 | 103 % | 1 |
| sentry_sdk/consts.py | 455 | 102 | 12 | 447 | 98 % | 1 |
| sentry_sdk/crons | 166 | 11 | 5 | 352 | 212 % | 1 |
| sentry_sdk/db | 117 | 4 | 2 | 172 | 147 % | 6 |
| sentry_sdk/envelope.py | 306 | 9 | 6 | 43 | 14 % | 1 |
| sentry_sdk/hub.py | 613 | 24 | 8 | 1080 | 176 % | 4 |
| sentry_sdk/integrations | 12848 | 202 | 13 | 16158 | 126 % | 0 |
| sentry_sdk/metrics.py | 808 | 31 | 9 | 1505 | 186 % | 1 |
| sentry_sdk/profiler | 1269 | 3 | 1 | 1591 | 125 % | 1 |
| sentry_sdk/scope.py | 1340 | 34 | 10 | 2064 | 154 % | 1 |
| sentry_sdk/scrubber.py | 138 | 9 | 5 | 125 | 91 % | 4 |
| sentry_sdk/serializer.py | 322 | 5 | 2 | 67 | 21 % | 6 |
| sentry_sdk/session.py | 157 | 3 | 2 | 16 | 10 % | 6 |
| sentry_sdk/sessions.py | 188 | 3 | 3 | 60 | 32 % | 5 |
| sentry_sdk/tracing.py | 993 | 41 | 12 | 838 | 84 % | 1 |
| sentry_sdk/tracing_utils.py | 562 | 26 | 11 | 492 | 88 % | 1 |
| sentry_sdk/transport.py | 527 | 17 | 9 | 349 | 66 % | 1 |
| sentry_sdk/utils.py | 1492 | 30 | 11 | 1154 | 77 % | 1 |
| sentry_sdk/worker.py | 119 | 5 | 4 | 20 | 17 % | 5 |

Other modules: 10 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2024-06 | 70 | 57917 | 16 | 6857 | 3072 |
| 2024-05 | 49 | 54893 | 11 | 3825 | 1136 |
| 2024-04 | 86 | 52563 | 18 | 2788 | 731 |
| 2024-03 | 125 | 51014 | 11 | 6182 | 3798 |
| 2024-02 | 86 | 49707 | 12 | 3847 | 1206 |
| 2024-01 | 41 | 47616 | 7 | 4090 | 4077 |
| 2023-12 | 29 | 47762 | 10 | 1288 | 429 |
| 2023-11 | 56 | 47057 | 15 | 3983 | 970 |
| 2023-10 | 43 | 44589 | 11 | 3735 | 652 |
| 2023-09 | 30 | 42092 | 13 | 4402 | 342 |
| 2023-08 | 33 | 38717 | 13 | 1258 | 1863 |
| 2023-07 | 53 | 39259 | 18 | 3336 | 648 |
| 2023-06 | 45 | 37098 | 15 | 3420 | 528 |
| 2023-05 | 47 | 34757 | 13 | 2043 | 359 |
| 2023-04 | 37 | 33374 | 8 | 1773 | 1068 |
| 2023-03 | 27 | 32870 | 11 | 2847 | 632 |
| 2023-02 | 24 | 31138 | 7 | 2693 | 926 |
| 2023-01 | 42 | 29624 | 19 | 2942 | 1281 |
| 2022-12 | 12 | 28349 | 5 | 1342 | 57 |
| 2022-11 | 22 | 27341 | 7 | 1218 | 337 |
| 2022-10 | 41 | 26555 | 10 | 1998 | 565 |
| 2022-09 | 33 | 25330 | 12 | 1843 | 489 |
| 2022-08 | 28 | 24267 | 12 | 552 | 709 |
