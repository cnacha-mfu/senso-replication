## Repository context

The following information about mirumee/ariadne was computed from its git history up to the base commit of this task (2023-11-08). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 8969 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 19259 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.96 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.36 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 10 | Commits with author date in the last three window months. |
| Months with at least one commit | 32 | Window months with one or more commits. |
| Share of months with at least one commit | 0.89 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.69 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.94 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.55 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.18 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.13 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.53 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.81 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 1.15 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 5145.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| ariadne/__init__.py | 80 | 4 | 4 | 14 | 18 % | 5 |
| ariadne/asgi | 1448 | 13 | 6 | 1053 | 73 % | 1 |
| ariadne/contrib | 747 | 8 | 4 | 585 | 78 % | 5 |
| ariadne/enums.py | 285 | 5 | 3 | 148 | 52 % | 5 |
| ariadne/executable_schema.py | 323 | 5 | 3 | 365 | 113 % | 8 |
| ariadne/explorer | 451 | 2 | 2 | 71 | 16 % | 1 |
| ariadne/extensions.py | 78 | 4 | 3 | 77 | 99 % | 9 |
| ariadne/file_uploads.py | 147 | 1 | 1 | 87 | 59 % | 9 |
| ariadne/graphql.py | 523 | 10 | 5 | 380 | 73 % | 7 |
| ariadne/inputs.py | 162 | 1 | 1 | 204 | 126 % | 8 |
| ariadne/interfaces.py | 159 | 1 | 1 | 164 | 103 % | 9 |
| ariadne/objects.py | 222 | 1 | 1 | 228 | 103 % | 9 |
| ariadne/resolvers.py | 97 | 2 | 2 | 76 | 78 % | 9 |
| ariadne/scalars.py | 249 | 1 | 1 | 249 | 100 % | 9 |
| ariadne/schema_names.py | 105 | 2 | 2 | 138 | 131 % | 9 |
| ariadne/schema_visitor.py | 569 | 3 | 2 | 158 | 28 % | 9 |
| ariadne/subscriptions.py | 137 | 1 | 1 | 137 | 100 % | 9 |
| ariadne/types.py | 495 | 14 | 7 | 708 | 143 % | 1 |
| ariadne/unions.py | 138 | 1 | 1 | 152 | 110 % | 9 |
| ariadne/utils.py | 190 | 2 | 1 | 150 | 79 % | 9 |
| ariadne/validation | 351 | 2 | 2 | 14 | 4 % | 7 |
| ariadne/wsgi.py | 514 | 9 | 5 | 444 | 86 % | 7 |
| benchmark | 514 | 2 | 1 | 705 | 137 % | 7 |
| generate_reference.py | 615 | 5 | 3 | 841 | 137 % | 5 |
| tests_mypy | 68 | 4 | 3 | 98 | 144 % | 8 |

Other modules: 5 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2023-10 | 10 | 19259 | 3 | 130 | 19 |
| 2023-09 | 0 | 19175 | 0 | 0 | 0 |
| 2023-08 | 0 | 19175 | 0 | 0 | 0 |
| 2023-07 | 0 | 19175 | 0 | 0 | 0 |
| 2023-06 | 57 | 19175 | 5 | 1479 | 703 |
| 2023-05 | 28 | 18535 | 3 | 0 | 0 |
| 2023-04 | 27 | 18535 | 5 | 1657 | 558 |
| 2023-03 | 13 | 17623 | 4 | 736 | 81 |
| 2023-02 | 16 | 17099 | 3 | 4628 | 191 |
| 2023-01 | 6 | 13898 | 2 | 895 | 58 |
| 2022-12 | 5 | 13241 | 1 | 173 | 18 |
| 2022-11 | 22 | 13112 | 5 | 815 | 235 |
| 2022-10 | 3 | 12631 | 2 | 2168 | 794 |
| 2022-09 | 10 | 11506 | 4 | 80 | 46 |
| 2022-08 | 8 | 11473 | 3 | 24 | 21 |
| 2022-07 | 15 | 11471 | 4 | 2733 | 1065 |
| 2022-06 | 0 | 10033 | 0 | 0 | 0 |
| 2022-05 | 9 | 10033 | 2 | 72 | 7 |
| 2022-04 | 41 | 9977 | 5 | 435 | 151 |
| 2022-03 | 58 | 9712 | 6 | 3425 | 6287 |
| 2022-02 | 73 | 9702 | 4 | 3966 | 1080 |
| 2022-01 | 44 | 9672 | 6 | 87 | 40 |
| 2021-12 | 17 | 9671 | 3 | 377 | 413 |
| 2021-11 | 17 | 9457 | 2 | 94 | 21 |
| 2021-10 | 24 | 9398 | 4 | 45 | 793 |
