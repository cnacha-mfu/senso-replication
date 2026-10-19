## Repository context

The following information about fair-software/howfairis was computed from its git history up to the base commit of this task (2021-03-02). Repository-level figures cover 6 complete months ending 2021-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 6 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 6 | Month ends at which the lines of code were counted. |
| LOC in the first month | 732 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 3153 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.80 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | 0.027 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.43 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 600 | Commits with author date in the last three window months. |
| Months with at least one commit | 4 | Window months with one or more commits. |
| Share of months with at least one commit | 0.67 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.70 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.33 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.69 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.26 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.14 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.67 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.50 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 3.31 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 2421.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 159 | 10 | 1 | 264 | 166 % | 1 |
| howfairis/__init__.py | 18 | 35 | 2 | 195 | 1083 % | 1 |
| howfairis/__version__.py | 1 | 21 | 3 | 39 | 3900 % | 1 |
| howfairis/checker.py | 217 | 41 | 1 | 725 | 334 % | 1 |
| howfairis/cli | 131 | 20 | 2 | 409 | 312 % | 0 |
| howfairis/code_repository_platforms.py | 8 | 2 | 1 | 10 | 125 % | 1 |
| howfairis/compliance.py | 94 | 12 | 1 | 297 | 316 % | 1 |
| howfairis/exceptions | 8 | 10 | 1 | 72 | 900 % | 1 |
| howfairis/get_apikeys_from_env_vars.py | 18 | 1 | 1 | 23 | 128 % | 1 |
| howfairis/mixins | 254 | 53 | 3 | 2094 | 824 % | 1 |
| howfairis/readme.py | 72 | 18 | 1 | 214 | 297 % | 1 |
| howfairis/readme_format.py | 7 | 1 | 1 | 9 | 129 % | 1 |
| howfairis/repo.py | 97 | 24 | 2 | 226 | 233 % | 0 |
| howfairis/requesting | 187 | 11 | 2 | 780 | 417 % | 0 |
| howfairis/schema.py | 12 | 6 | 2 | 57 | 475 % | 1 |
| howfairis/workarounds | 26 | 15 | 2 | 106 | 408 % | 0 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2021-02 | 540 | 3153 | 6 | 12884 | 9708 |
| 2021-01 | 50 | 812 | 6 | 353 | 211 |
| 2020-12 | 10 | 759 | 1 | 31 | 16 |
| 2020-11 | 0 | 732 | 0 | 0 | 0 |
| 2020-10 | 0 | 732 | 0 | 0 | 0 |
