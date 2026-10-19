## Repository context

The following information about boto/botocore was computed from its git history up to the base commit of this task (2020-03-09). Repository-level figures cover 36 complete months ending 2020-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 38415 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 58230 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.99 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.14 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 211 | Commits with author date in the last three window months. |
| Months with at least one commit | 36 | Window months with one or more commits. |
| Share of months with at least one commit | 1.00 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.08 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.24 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.05 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.05 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.04 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 1.00 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 1.00 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.52 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 19815.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| botocore/args.py | 331 | 4 | 3 | 260 | 79 % | 2 |
| botocore/auth.py | 742 | 1 | 1 | 13 | 2 % | 4 |
| botocore/awsrequest.py | 510 | 3 | 3 | 47 | 9 % | 2 |
| botocore/client.py | 784 | 8 | 5 | 179 | 23 % | 2 |
| botocore/compat.py | 279 | 3 | 3 | 88 | 32 % | 0 |
| botocore/configprovider.py | 455 | 6 | 4 | 188 | 41 % | 2 |
| botocore/credentials.py | 1649 | 7 | 4 | 531 | 32 % | 7 |
| botocore/docs | 2976 | 1 | 1 | 7 | < 1 % | 9 |
| botocore/eventstream.py | 482 | 0 | 0 | 0 | 0 % | 23 |
| botocore/exceptions.py | 398 | 5 | 3 | 49 | 12 % | 2 |
| botocore/handlers.py | 935 | 4 | 4 | 100 | 11 % | 3 |
| botocore/hooks.py | 499 | 0 | 0 | 0 | 0 % | 19 |
| botocore/loaders.py | 366 | 0 | 0 | 0 | 0 % | 40 |
| botocore/model.py | 624 | 2 | 2 | 7 | 1 % | 2 |
| botocore/monitoring.py | 452 | 0 | 0 | 0 | 0 % | 14 |
| botocore/paginate.py | 593 | 1 | 1 | 6 | 1 % | 9 |
| botocore/parsers.py | 832 | 1 | 1 | 2 | < 1 % | 3 |
| botocore/retries | 745 | 2 | 1 | 1024 | 137 % | 2 |
| botocore/retryhandler.py | 290 | 0 | 0 | 0 | 0 % | 19 |
| botocore/serialize.py | 595 | 0 | 0 | 0 | 0 % | 15 |
| botocore/session.py | 875 | 5 | 5 | 65 | 7 % | 3 |
| botocore/signers.py | 584 | 2 | 1 | 21 | 4 % | 4 |
| botocore/stub.py | 324 | 0 | 0 | 0 | 0 % | 17 |
| botocore/utils.py | 1463 | 18 | 8 | 642 | 44 % | 0 |
| botocore/waiter.py | 276 | 0 | 0 | 0 | 0 % | 31 |

Other modules: 13 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2020-02 | 74 | 58230 | 5 | 59 | 48 |
| 2020-01 | 59 | 56023 | 3 | 2722 | 251 |
| 2019-12 | 78 | 56138 | 7 | 152 | 63 |
| 2019-11 | 99 | 54625 | 5 | 2333 | 737 |
| 2019-10 | 98 | 54501 | 7 | 563 | 419 |
| 2019-09 | 76 | 54014 | 4 | 80 | 63 |
| 2019-08 | 83 | 54014 | 5 | 615 | 82 |
| 2019-07 | 92 | 54010 | 7 | 280 | 116 |
| 2019-06 | 97 | 53169 | 7 | 1190 | 255 |
| 2019-05 | 94 | 53060 | 9 | 72 | 46 |
| 2019-04 | 60 | 53085 | 4 | 126 | 165 |
| 2019-03 | 70 | 53055 | 4 | 42 | 43 |
| 2019-02 | 68 | 53056 | 6 | 70 | 44 |
| 2019-01 | 68 | 53055 | 8 | 236 | 94 |
| 2018-12 | 85 | 52804 | 10 | 1203 | 115 |
| 2018-11 | 107 | 50139 | 9 | 398 | 212 |
| 2018-10 | 123 | 48366 | 13 | 3887 | 1715 |
| 2018-09 | 113 | 47898 | 10 | 1833 | 1112 |
| 2018-08 | 150 | 46881 | 9 | 2472 | 641 |
| 2018-07 | 116 | 45857 | 6 | 845 | 533 |
| 2018-06 | 86 | 45769 | 7 | 1229 | 771 |
| 2018-05 | 84 | 45622 | 9 | 1613 | 144 |
| 2018-04 | 66 | 45576 | 7 | 249 | 76 |
| 2018-03 | 88 | 44240 | 7 | 1077 | 170 |
| 2018-02 | 93 | 44052 | 8 | 1373 | 194 |
| 2018-01 | 71 | 43778 | 9 | 250 | 58 |
| 2017-12 | 80 | 43491 | 6 | 433 | 110 |
| 2017-11 | 100 | 43211 | 9 | 848 | 218 |
| 2017-10 | 66 | 40819 | 6 | 165 | 38 |
| 2017-09 | 67 | 40606 | 6 | 180 | 43 |
| 2017-08 | 83 | 40571 | 6 | 3019 | 1791 |
