## Repository context

The following information about python-trio/trio was computed from its git history up to the base commit of this task (2024-09-23). Repository-level figures cover 36 complete months ending 2024-08; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 28948 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 39415 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.92 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.12 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 76 | Commits with author date in the last three window months. |
| Months with at least one commit | 36 | Window months with one or more commits. |
| Share of months with at least one commit | 1.00 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 3.31 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.60 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 3.12 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.13 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.15 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 1.00 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 1.00 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.22 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.36 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 10467.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 887 | 21 | 11 | 311 | 35 % | 0 |
| notes-to-self | 1968 | 11 | 7 | 235 | 12 % | 1 |
| src/trio/_abc.py | 517 | 6 | 5 | 738 | 143 % | 1 |
| src/trio/_channel.py | 356 | 4 | 4 | 486 | 137 % | 1 |
| src/trio/_core | 7284 | 41 | 11 | 11047 | 152 % | 0 |
| src/trio/_dtls.py | 1199 | 5 | 4 | 1497 | 125 % | 1 |
| src/trio/_file_io.py | 405 | 4 | 3 | 545 | 135 % | 1 |
| src/trio/_highlevel_open_tcp_listeners.py | 202 | 5 | 5 | 283 | 140 % | 1 |
| src/trio/_highlevel_open_tcp_stream.py | 363 | 3 | 3 | 425 | 117 % | 1 |
| src/trio/_highlevel_socket.py | 355 | 3 | 3 | 436 | 123 % | 1 |
| src/trio/_highlevel_ssl_helpers.py | 145 | 2 | 2 | 186 | 128 % | 1 |
| src/trio/_path.py | 219 | 8 | 7 | 1104 | 504 % | 1 |
| src/trio/_signals.py | 152 | 2 | 2 | 189 | 124 % | 1 |
| src/trio/_socket.py | 1103 | 10 | 5 | 1503 | 136 % | 1 |
| src/trio/_ssl.py | 854 | 3 | 2 | 957 | 112 % | 1 |
| src/trio/_subprocess.py | 980 | 16 | 7 | 1484 | 151 % | 0 |
| src/trio/_subprocess_platform | 235 | 6 | 4 | 329 | 140 % | 1 |
| src/trio/_sync.py | 659 | 6 | 5 | 920 | 140 % | 1 |
| src/trio/_tests | 625 | 13 | 7 | 1232 | 197 % | 1 |
| src/trio/_threads.py | 492 | 13 | 7 | 940 | 191 % | 1 |
| src/trio/_timeouts.py | 144 | 19 | 4 | 813 | 565 % | 0 |
| src/trio/_tools | 438 | 11 | 9 | 578 | 132 % | 0 |
| src/trio/_unix_pipes.py | 173 | 3 | 3 | 216 | 125 % | 1 |
| src/trio/_util.py | 329 | 8 | 6 | 499 | 152 % | 1 |
| src/trio/socket.py | 573 | 8 | 4 | 618 | 108 % | 1 |

Other modules: 14 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2024-08 | 38 | 39415 | 9 | 1256 | 569 |
| 2024-07 | 16 | 38748 | 5 | 48 | 131 |
| 2024-06 | 22 | 38819 | 6 | 581 | 317 |
| 2024-05 | 22 | 38713 | 10 | 837 | 132 |
| 2024-04 | 19 | 38098 | 7 | 77 | 51 |
| 2024-03 | 15 | 38077 | 8 | 497 | 500 |
| 2024-02 | 16 | 38094 | 13 | 494 | 369 |
| 2024-01 | 47 | 37920 | 9 | 1720 | 1294 |
| 2023-12 | 25 | 37272 | 9 | 1144 | 1570 |
| 2023-11 | 68 | 37575 | 14 | 43879 | 42776 |
| 2023-10 | 51 | 36982 | 9 | 2864 | 1910 |
| 2023-09 | 50 | 35939 | 11 | 2264 | 1050 |
| 2023-08 | 42 | 34830 | 7 | 3237 | 1699 |
| 2023-07 | 49 | 33664 | 11 | 3369 | 2001 |
| 2023-06 | 16 | 32604 | 6 | 1194 | 456 |
