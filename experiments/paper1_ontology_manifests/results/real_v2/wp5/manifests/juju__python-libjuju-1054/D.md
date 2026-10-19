## Repository context

The following information about juju/python-libjuju was computed from its git history up to the base commit of this task (2024-07-11). Repository-level figures cover 36 complete months ending 2024-06; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 108301 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 79895 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | -0.10 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | 0.383 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | -0.15 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 38 | Commits with author date in the last three window months. |
| Months with at least one commit | 35 | Window months with one or more commits. |
| Share of months with at least one commit | 0.97 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 2.53 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.72 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 3.49 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.24 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.25 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.94 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.94 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | -0.26 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | -9468.67 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 325 | 2 | 2 | 8 | 2 % | 5 |
| examples | 1859 | 3 | 2 | 152 | 8 % | 9 |
| juju/application.py | 786 | 10 | 4 | 173 | 22 % | 1 |
| juju/bundle.py | 944 | 5 | 5 | 222 | 24 % | 3 |
| juju/charmhub.py | 144 | 1 | 1 | 3 | 2 % | 11 |
| juju/client | 63541 | 36 | 7 | 9678 | 15 % | 3 |
| juju/constraints.py | 133 | 1 | 1 | 3 | 2 % | 11 |
| juju/controller.py | 847 | 6 | 5 | 33 | 4 % | 4 |
| juju/delta.py | 89 | 1 | 1 | 3 | 3 % | 11 |
| juju/errors.py | 100 | 7 | 4 | 23 | 23 % | 6 |
| juju/jasyncio.py | 92 | 4 | 2 | 21 | 23 % | 10 |
| juju/machine.py | 250 | 11 | 4 | 129 | 52 % | 4 |
| juju/model.py | 2582 | 33 | 9 | 619 | 24 % | 2 |
| juju/names.py | 54 | 1 | 1 | 3 | 6 % | 11 |
| juju/offerendpoints.py | 144 | 1 | 1 | 3 | 2 % | 11 |
| juju/origin.py | 159 | 1 | 1 | 3 | 2 % | 11 |
| juju/placement.py | 48 | 1 | 1 | 3 | 6 % | 11 |
| juju/provisioner.py | 292 | 1 | 1 | 3 | 1 % | 11 |
| juju/relation.py | 128 | 1 | 1 | 3 | 2 % | 11 |
| juju/secrets.py | 96 | 2 | 1 | 130 | 135 % | 8 |
| juju/status.py | 175 | 1 | 1 | 3 | 2 % | 11 |
| juju/unit.py | 339 | 2 | 2 | 12 | 4 % | 9 |
| juju/url.py | 126 | 2 | 2 | 20 | 16 % | 9 |
| juju/user.py | 140 | 1 | 1 | 3 | 2 % | 11 |
| juju/utils.py | 448 | 14 | 4 | 75 | 17 % | 1 |

Other modules: 12 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2024-06 | 3 | 79895 | 2 | 101 | 20 |
| 2024-05 | 9 | 79895 | 4 | 16 | 3 |
| 2024-04 | 26 | 79885 | 4 | 135 | 39 |
| 2024-03 | 13 | 79799 | 5 | 56 | 22 |
| 2024-02 | 26 | 79752 | 4 | 15 | 51 |
| 2024-01 | 49 | 79724 | 6 | 418 | 368 |
| 2023-12 | 1 | 79738 | 1 | 5 | 2 |
| 2023-11 | 27 | 79738 | 3 | 6360 | 136 |
| 2023-10 | 35 | 74287 | 4 | 372 | 166 |
| 2023-09 | 43 | 74119 | 2 | 3154 | 195 |
| 2023-08 | 36 | 71481 | 4 | 942 | 521 |
| 2023-07 | 45 | 71271 | 3 | 201 | 340 |
| 2023-06 | 40 | 71391 | 4 | 3023 | 548 |
| 2023-05 | 10 | 69648 | 5 | 308 | 1655 |
| 2023-04 | 20 | 70604 | 3 | 2686 | 351 |
| 2023-03 | 8 | 68932 | 4 | 2861 | 138 |
| 2023-02 | 5 | 66950 | 3 | 2748 | 4966 |
| 2023-01 | 20 | 68827 | 3 | 4038 | 8767 |
| 2022-12 | 0 | 73377 | 0 | 0 | 0 |
| 2022-11 | 51 | 73377 | 3 | 471 | 96752 |
| 2022-10 | 62 | 131917 | 5 | 46848 | 108377 |
| 2022-09 | 33 | 185144 | 5 | 463 | 217 |
| 2022-08 | 73 | 185010 | 7 | 23238 | 77991 |
| 2022-07 | 52 | 216517 | 6 | 157109 | 2833 |
| 2022-06 | 15 | 122219 | 4 | 62 | 45 |
| 2022-05 | 7 | 122192 | 3 | 54 | 6 |
| 2022-04 | 17 | 122167 | 7 | 119 | 33 |
| 2022-03 | 27 | 122097 | 5 | 2050 | 540 |
| 2022-02 | 18 | 120694 | 4 | 1496 | 157 |
| 2022-01 | 23 | 119600 | 5 | 128 | 24 |
| 2021-12 | 40 | 119511 | 5 | 422 | 164 |
