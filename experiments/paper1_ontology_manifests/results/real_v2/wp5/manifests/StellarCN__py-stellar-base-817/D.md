## Repository context

The following information about StellarCN/py-stellar-base was computed from its git history up to the base commit of this task (2023-11-13). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 36334 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 69860 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.90 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.12 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 63 | Commits with author date in the last three window months. |
| Months with at least one commit | 34 | Window months with one or more commits. |
| Share of months with at least one commit | 0.94 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.51 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.70 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.33 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.06 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.09 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.69 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.78 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.46 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.92 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 429.82 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 180 | 4 | 1 | 218 | 121 % | 3 |
| examples | 2068 | 26 | 11 | 2282 | 110 % | 0 |
| stellar_sdk/asset.py | 190 | 3 | 2 | 6 | 3 % | 3 |
| stellar_sdk/base_server.py | 307 | 2 | 2 | 4 | 1 % | 3 |
| stellar_sdk/call_builder | 1823 | 6 | 4 | 256 | 14 % | 2 |
| stellar_sdk/client | 623 | 9 | 5 | 201 | 32 % | 0 |
| stellar_sdk/exceptions.py | 142 | 5 | 2 | 51 | 36 % | 3 |
| stellar_sdk/keypair.py | 246 | 5 | 4 | 10 | 4 % | 2 |
| stellar_sdk/memo.py | 197 | 3 | 3 | 28 | 14 % | 2 |
| stellar_sdk/operation | 2943 | 15 | 9 | 693 | 24 % | 1 |
| stellar_sdk/preconditions.py | 198 | 3 | 3 | 18 | 9 % | 2 |
| stellar_sdk/scval.py | 504 | 3 | 1 | 708 | 140 % | 3 |
| stellar_sdk/sep | 3061 | 9 | 5 | 333 | 11 % | 2 |
| stellar_sdk/server.py | 317 | 2 | 2 | 4 | 1 % | 3 |
| stellar_sdk/server_async.py | 320 | 0 | 0 | 0 | 0 % | 16 |
| stellar_sdk/signer_key.py | 222 | 4 | 3 | 12 | 5 % | 2 |
| stellar_sdk/soroban_rpc.py | 216 | 6 | 3 | 444 | 206 % | 1 |
| stellar_sdk/soroban_server.py | 295 | 7 | 3 | 530 | 180 % | 1 |
| stellar_sdk/soroban_server_async.py | 295 | 2 | 2 | 346 | 117 % | 1 |
| stellar_sdk/strkey.py | 299 | 6 | 5 | 51 | 17 % | 3 |
| stellar_sdk/transaction.py | 273 | 10 | 7 | 102 | 37 % | 1 |
| stellar_sdk/transaction_builder.py | 1289 | 24 | 10 | 981 | 76 % | 1 |
| stellar_sdk/transaction_envelope.py | 144 | 7 | 6 | 39 | 27 % | 2 |
| stellar_sdk/utils.py | 139 | 7 | 4 | 29 | 21 % | 3 |
| stellar_sdk/xdr | 35567 | 14 | 10 | 32588 | 92 % | 1 |

Other modules: 20 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2023-10 | 11 | 69860 | 2 | 1171 | 1271 |
| 2023-09 | 21 | 69955 | 2 | 4364 | 1959 |
| 2023-08 | 31 | 50294 | 1 | 7202 | 6601 |
| 2023-07 | 14 | 50294 | 2 | 7390 | 5285 |
| 2023-06 | 17 | 50294 | 4 | 2611 | 1342 |
| 2023-05 | 16 | 50268 | 2 | 423 | 427 |
| 2023-04 | 12 | 50268 | 2 | 2141 | 841 |
| 2023-03 | 15 | 50268 | 2 | 339 | 8 |
| 2023-02 | 46 | 50055 | 2 | 4446 | 2502 |
| 2023-01 | 0 | 50054 | 0 | 0 | 0 |
| 2022-12 | 12 | 50054 | 2 | 1721 | 377 |
| 2022-11 | 13 | 50058 | 1 | 3114 | 102 |
| 2022-10 | 34 | 50058 | 2 | 983 | 310 |
| 2022-09 | 9 | 50058 | 2 | 2518 | 210 |
| 2022-08 | 11 | 50058 | 2 | 6645 | 103 |
| 2022-07 | 11 | 50058 | 2 | 6 | 6 |
| 2022-06 | 7 | 50058 | 2 | 465 | 352 |
| 2022-05 | 5 | 49963 | 1 | 154 | 57 |
| 2022-04 | 25 | 49873 | 1 | 3661 | 1513 |
| 2022-03 | 0 | 47959 | 0 | 0 | 0 |
| 2022-02 | 2 | 47959 | 2 | 4 | 1 |
| 2022-01 | 4 | 47957 | 1 | 134 | 130 |
| 2021-12 | 1 | 47945 | 1 | 70 | 27 |
| 2021-11 | 29 | 47903 | 3 | 1266 | 1039 |
| 2021-10 | 56 | 47717 | 3 | 14891 | 11612 |
