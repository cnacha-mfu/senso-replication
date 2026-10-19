## Repository context

The following information about ucfopen/canvasapi was computed from its git history up to the base commit of this task (2019-06-20). Repository-level figures cover 36 complete months ending 2019-05; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 3493 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 18714 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.92 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.54 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 51 | Commits with author date in the last three window months. |
| Months with at least one commit | 35 | Window months with one or more commits. |
| Share of months with at least one commit | 0.97 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 2.20 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.69 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.74 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.36 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.36 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.89 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.89 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 4.36 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 15221.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| canvasapi/account.py | 1266 | 9 | 5 | 231 | 18 % | 0 |
| canvasapi/assignment.py | 319 | 18 | 8 | 277 | 87 % | 0 |
| canvasapi/blueprint.py | 264 | 10 | 2 | 439 | 166 % | 4 |
| canvasapi/canvas.py | 1110 | 16 | 3 | 345 | 31 % | 0 |
| canvasapi/communication_channel.py | 204 | 2 | 2 | 20 | 10 % | 3 |
| canvasapi/content_migration.py | 215 | 0 | 0 | 0 | 0 % | 13 |
| canvasapi/course.py | 1905 | 11 | 4 | 305 | 16 % | 0 |
| canvasapi/current_user.py | 233 | 10 | 1 | 333 | 143 % | 0 |
| canvasapi/discussion_topic.py | 546 | 0 | 0 | 0 | 0 % | 13 |
| canvasapi/external_tool.py | 99 | 0 | 0 | 0 | 0 % | 20 |
| canvasapi/folder.py | 156 | 1 | 1 | 4 | 3 % | 12 |
| canvasapi/group.py | 957 | 4 | 2 | 107 | 11 % | 0 |
| canvasapi/module.py | 195 | 1 | 1 | 4 | 2 % | 10 |
| canvasapi/outcome.py | 319 | 1 | 1 | 1 | < 1 % | 11 |
| canvasapi/page.py | 227 | 0 | 0 | 0 | 0 % | 13 |
| canvasapi/poll.py | 161 | 13 | 1 | 266 | 165 % | 0 |
| canvasapi/poll_session.py | 123 | 7 | 1 | 205 | 167 % | 0 |
| canvasapi/quiz.py | 358 | 6 | 3 | 179 | 50 % | 6 |
| canvasapi/requester.py | 139 | 3 | 3 | 35 | 25 % | 2 |
| canvasapi/section.py | 330 | 4 | 2 | 40 | 12 % | 6 |
| canvasapi/submission.py | 157 | 2 | 1 | 218 | 139 % | 1 |
| canvasapi/user.py | 724 | 7 | 4 | 141 | 19 % | 0 |
| canvasapi/util.py | 135 | 3 | 3 | 33 | 24 % | 2 |
| docs | 219 | 0 | 0 | 0 | 0 % | 27 |
| scripts | 136 | 0 | 0 | 0 | 0 % | 12 |

Other modules: 30 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2019-05 | 21 | 18714 | 5 | 328 | 107 |
| 2019-04 | 15 | 18540 | 3 | 95 | 41 |
| 2019-03 | 15 | 17160 | 7 | 77 | 27 |
| 2019-02 | 21 | 17160 | 3 | 293 | 118 |
| 2019-01 | 10 | 17160 | 2 | 491 | 12 |
| 2018-12 | 13 | 17160 | 5 | 343 | 19 |
| 2018-11 | 19 | 17160 | 4 | 638 | 38 |
| 2018-10 | 1 | 17160 | 1 | 73 | 0 |
| 2018-09 | 15 | 17160 | 4 | 53 | 13 |
| 2018-08 | 10 | 16895 | 4 | 66 | 7 |
| 2018-07 | 11 | 16895 | 2 | 67 | 13 |
| 2018-06 | 34 | 16895 | 8 | 214 | 37 |
| 2018-05 | 37 | 13704 | 6 | 1629 | 924 |
| 2018-04 | 12 | 13704 | 3 | 174 | 9 |
| 2018-03 | 61 | 13704 | 4 | 3984 | 728 |
| 2018-02 | 29 | 13108 | 5 | 1154 | 389 |
| 2018-01 | 58 | 13108 | 6 | 642 | 349 |
| 2017-12 | 18 | 10525 | 5 | 398 | 366 |
| 2017-11 | 51 | 10525 | 6 | 1248 | 262 |
| 2017-10 | 63 | 10525 | 5 | 2888 | 1451 |
| 2017-09 | 34 | 10092 | 7 | 1377 | 453 |
| 2017-08 | 59 | 10092 | 4 | 616 | 357 |
| 2017-07 | 20 | 10006 | 2 | 611 | 293 |
| 2017-06 | 51 | 9812 | 5 | 1074 | 244 |
| 2017-05 | 35 | 7743 | 4 | 1831 | 119 |
| 2017-04 | 12 | 7743 | 3 | 162 | 2 |
| 2017-03 | 16 | 7743 | 1 | 11731 | 11715 |
| 2017-02 | 24 | 5903 | 3 | 1202 | 648 |
| 2017-01 | 64 | 5903 | 3 | 2193 | 373 |
| 2016-12 | 30 | 4192 | 2 | 1248 | 1047 |
