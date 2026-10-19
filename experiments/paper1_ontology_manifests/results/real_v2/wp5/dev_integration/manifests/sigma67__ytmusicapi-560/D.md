## Repository context

The following information about sigma67/ytmusicapi was computed from its git history up to the base commit of this task (2024-03-06). Repository-level figures cover 36 complete months ending 2024-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 2716 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 5076 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.95 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.15 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 89 | Commits with author date in the last three window months. |
| Months with at least one commit | 32 | Window months with one or more commits. |
| Share of months with at least one commit | 0.89 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.95 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.98 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.89 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.27 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.40 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.08 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.69 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.87 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 2360.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 40 | 4 | 4 | 48 | 120 % | 1 |
| ytmusicapi/__init__.py | 12 | 3 | 2 | 15 | 125 % | 3 |
| ytmusicapi/auth | 329 | 30 | 7 | 2401 | 730 % | 2 |
| ytmusicapi/constants.py | 26 | 3 | 3 | 50 | 192 % | 3 |
| ytmusicapi/continuations.py | 71 | 1 | 1 | 68 | 96 % | 3 |
| ytmusicapi/helpers.py | 59 | 2 | 2 | 49 | 83 % | 3 |
| ytmusicapi/mixins | 2715 | 60 | 13 | 2803 | 103 % | 0 |
| ytmusicapi/navigation.py | 113 | 15 | 7 | 254 | 225 % | 0 |
| ytmusicapi/parsers | 975 | 45 | 11 | 2020 | 207 % | 0 |
| ytmusicapi/setup.py | 57 | 10 | 5 | 223 | 391 % | 2 |
| ytmusicapi/ytmusic.py | 240 | 20 | 7 | 615 | 256 % | 2 |

Other modules: 0 not listed.
