## Repository context

The following information about Fatal1ty/mashumaro was computed from its git history up to the base commit of this task (2023-12-22). Repository-level figures cover 36 complete months ending 2023-11; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 2203 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 18689 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.98 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.53 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 114 | Commits with author date in the last three window months. |
| Months with at least one commit | 31 | Window months with one or more commits. |
| Share of months with at least one commit | 0.86 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.18 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.82 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.05 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.34 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.29 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.64 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.33 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 7.48 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 16486.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| benchmark | 1237 | 6 | 3 | 2313 | 187 % | 1 |
| mashumaro/__init__.py | 9 | 3 | 2 | 4 | 44 % | 6 |
| mashumaro/codecs | 723 | 17 | 3 | 1272 | 176 % | 0 |
| mashumaro/config.py | 59 | 16 | 8 | 74 | 125 % | 0 |
| mashumaro/core | 4173 | 110 | 11 | 3874 | 93 % | 0 |
| mashumaro/dialect.py | 53 | 7 | 3 | 75 | 142 % | 1 |
| mashumaro/exceptions.py | 159 | 3 | 2 | 57 | 36 % | 6 |
| mashumaro/helper.py | 42 | 2 | 2 | 14 | 33 % | 8 |
| mashumaro/jsonschema | 1108 | 49 | 9 | 2099 | 189 % | 0 |
| mashumaro/mixins | 269 | 5 | 3 | 42 | 16 % | 3 |
| mashumaro/types.py | 82 | 10 | 5 | 72 | 88 % | 4 |

Other modules: 0 not listed.
