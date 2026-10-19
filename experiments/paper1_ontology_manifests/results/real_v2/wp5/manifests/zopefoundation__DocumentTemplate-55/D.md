## Repository context

The following information about zopefoundation/DocumentTemplate was computed from its git history up to the base commit of this task (2020-05-28). Repository-level figures cover 36 complete months ending 2020-04; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 6345 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 7468 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.90 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.06 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 2 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 17 | Commits with author date in the last three window months. |
| Months with at least one commit | 20 | Window months with one or more commits. |
| Share of months with at least one commit | 0.56 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 2.31 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.60 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 2.42 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.21 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.13 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.22 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.31 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.18 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 1123.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| bootstrap.py | 155 | 0 | 0 | 0 | 0 % | 65 |
| src/DocumentTemplate/DT_HTML.py | 287 | 3 | 1 | 89 | 31 % | 3 |
| src/DocumentTemplate/DT_If.py | 120 | 2 | 1 | 12 | 10 % | 3 |
| src/DocumentTemplate/DT_In.py | 783 | 4 | 1 | 54 | 7 % | 3 |
| src/DocumentTemplate/DT_InSV.py | 379 | 2 | 1 | 14 | 4 % | 3 |
| src/DocumentTemplate/DT_Let.py | 99 | 4 | 1 | 14 | 14 % | 3 |
| src/DocumentTemplate/DT_Raise.py | 61 | 3 | 1 | 15 | 25 % | 3 |
| src/DocumentTemplate/DT_Return.py | 33 | 1 | 1 | 3 | 9 % | 3 |
| src/DocumentTemplate/DT_String.py | 496 | 3 | 1 | 136 | 27 % | 3 |
| src/DocumentTemplate/DT_Try.py | 174 | 3 | 1 | 21 | 12 % | 3 |
| src/DocumentTemplate/DT_UI.py | 82 | 3 | 1 | 19 | 23 % | 3 |
| src/DocumentTemplate/DT_Util.py | 371 | 4 | 1 | 60 | 16 % | 3 |
| src/DocumentTemplate/DT_Var.py | 495 | 10 | 2 | 120 | 24 % | 3 |
| src/DocumentTemplate/DT_With.py | 76 | 4 | 1 | 21 | 28 % | 3 |
| src/DocumentTemplate/_DocumentTemplate.py | 349 | 2 | 1 | 19 | 5 % | 3 |
| src/DocumentTemplate/__init__.py | 28 | 1 | 1 | 17 | 61 % | 3 |
| src/DocumentTemplate/cDocumentTemplate.py | 24 | 3 | 1 | 61 | 254 % | 3 |
| src/DocumentTemplate/html_quote.py | 13 | 1 | 1 | 3 | 23 % | 3 |
| src/DocumentTemplate/pDocumentTemplate.py | 26 | 2 | 1 | 41 | 158 % | 3 |
| src/DocumentTemplate/security.py | 105 | 3 | 1 | 23 | 22 % | 3 |
| src/DocumentTemplate/sequence | 56 | 5 | 1 | 110 | 196 % | 3 |
| src/DocumentTemplate/ustr.py | 57 | 1 | 1 | 3 | 5 % | 3 |
| src/TreeDisplay/TreeTag.py | 633 | 4 | 2 | 56 | 9 % | 0 |
| src/TreeDisplay/__init__.py | 13 | 0 | 0 | 0 | 0 % | 40 |
| src/TreeDisplay/tests.py | 55 | 1 | 1 | 53 | 96 % | 0 |

Other modules: 1 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2020-04 | 0 | 7468 | 0 | 0 | 0 |
| 2020-03 | 0 | 7468 | 0 | 0 | 0 |
| 2020-02 | 17 | 7468 | 1 | 492 | 423 |
| 2020-01 | 9 | 7441 | 2 | 164 | 37 |
| 2019-12 | 0 | 7340 | 0 | 0 | 0 |
| 2019-11 | 0 | 7340 | 0 | 0 | 0 |
| 2019-10 | 1 | 7340 | 1 | 0 | 0 |
| 2019-09 | 0 | 7340 | 0 | 0 | 0 |
| 2019-08 | 0 | 7340 | 0 | 0 | 0 |
| 2019-07 | 0 | 7340 | 0 | 0 | 0 |
| 2019-06 | 0 | 7340 | 0 | 0 | 0 |
| 2019-05 | 15 | 7340 | 4 | 56 | 21 |
| 2019-04 | 23 | 7310 | 3 | 426 | 131 |
| 2019-03 | 3 | 7046 | 1 | 2 | 2 |
| 2019-02 | 2 | 7037 | 1 | 41 | 27 |
| 2019-01 | 0 | 7037 | 0 | 0 | 0 |
| 2018-12 | 0 | 7037 | 0 | 0 | 0 |
| 2018-11 | 0 | 7037 | 0 | 0 | 0 |
| 2018-10 | 29 | 7037 | 6 | 859 | 187 |
| 2018-09 | 0 | 6412 | 0 | 0 | 0 |
| 2018-08 | 0 | 6412 | 0 | 0 | 0 |
| 2018-07 | 5 | 6412 | 1 | 40 | 6 |
| 2018-06 | 4 | 6389 | 2 | 102 | 63 |
| 2018-05 | 5 | 6387 | 2 | 127 | 126 |
| 2018-04 | 5 | 6387 | 2 | 51 | 13 |
| 2018-03 | 1 | 6356 | 1 | 2 | 4 |
| 2018-02 | 2 | 6358 | 1 | 2 | 1 |
| 2018-01 | 1 | 6357 | 1 | 0 | 0 |
| 2017-12 | 2 | 6357 | 2 | 0 | 0 |
| 2017-11 | 8 | 6355 | 2 | 17 | 9 |
| 2017-10 | 0 | 6351 | 0 | 0 | 0 |
| 2017-09 | 5 | 6351 | 2 | 4 | 4 |
| 2017-08 | 0 | 6351 | 0 | 0 | 0 |
| 2017-07 | 0 | 6351 | 0 | 0 | 0 |
| 2017-06 | 6 | 6351 | 1 | 34 | 24 |
| 2017-05 | 23 | 6345 | 3 | 136 | 98 |
