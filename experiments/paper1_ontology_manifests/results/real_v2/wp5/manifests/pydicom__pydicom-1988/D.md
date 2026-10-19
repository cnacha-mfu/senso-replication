## Repository context

The following information about pydicom/pydicom was computed from its git history up to the base commit of this task (2024-01-07). Repository-level figures cover 36 complete months ending 2023-12; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 96596 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 108778 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.95 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.02 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 60 | Commits with author date in the last three window months. |
| Months with at least one commit | 35 | Window months with one or more commits. |
| Share of months with at least one commit | 0.97 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 4.84 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.88 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 4.66 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.32 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.30 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.06 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.78 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.30 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.13 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 12182.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| benchmarks | 551 | 2 | 2 | 96 | 17 % | 6 |
| examples | 701 | 14 | 7 | 835 | 119 % | 1 |
| src/pydicom/_dicom_dict.py | 5162 | 4 | 3 | 5174 | 100 % | 2 |
| src/pydicom/_private_dict.py | 11409 | 4 | 4 | 18587 | 163 % | 2 |
| src/pydicom/_uid_dict.py | 485 | 3 | 2 | 487 | 100 % | 2 |
| src/pydicom/charset.py | 716 | 5 | 3 | 1201 | 168 % | 1 |
| src/pydicom/cli | 335 | 8 | 4 | 529 | 158 % | 2 |
| src/pydicom/config.py | 421 | 6 | 4 | 674 | 160 % | 1 |
| src/pydicom/data | 636 | 9 | 5 | 947 | 149 % | 1 |
| src/pydicom/datadict.py | 526 | 8 | 5 | 748 | 142 % | 1 |
| src/pydicom/dataelem.py | 730 | 13 | 5 | 1167 | 160 % | 1 |
| src/pydicom/dataset.py | 2726 | 21 | 6 | 4677 | 172 % | 1 |
| src/pydicom/encaps.py | 1087 | 9 | 5 | 2208 | 203 % | 1 |
| src/pydicom/encoders | 1131 | 8 | 5 | 1730 | 153 % | 2 |
| src/pydicom/filereader.py | 1037 | 13 | 6 | 1858 | 179 % | 1 |
| src/pydicom/fileset.py | 2353 | 11 | 5 | 3431 | 146 % | 1 |
| src/pydicom/fileutil.py | 389 | 5 | 4 | 535 | 138 % | 1 |
| src/pydicom/filewriter.py | 1203 | 12 | 5 | 2320 | 193 % | 1 |
| src/pydicom/pixel_data_handlers | 2680 | 20 | 6 | 4473 | 167 % | 1 |
| src/pydicom/sr | 39193 | 5 | 4 | 80814 | 206 % | 0 |
| src/pydicom/uid.py | 917 | 13 | 6 | 1627 | 177 % | 1 |
| src/pydicom/util | 825 | 8 | 6 | 1234 | 150 % | 1 |
| src/pydicom/valuerep.py | 1742 | 9 | 6 | 3017 | 173 % | 1 |
| src/pydicom/values.py | 735 | 8 | 4 | 1223 | 166 % | 1 |
| util | 1019 | 8 | 6 | 1843 | 181 % | 2 |

Other modules: 16 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2023-12 | 23 | 108778 | 6 | 6112 | 2728 |
| 2023-11 | 19 | 105829 | 4 | 1589 | 989 |
| 2023-10 | 18 | 105343 | 6 | 413 | 320 |
| 2023-09 | 7 | 105261 | 3 | 4897 | 3802 |
| 2023-08 | 15 | 104163 | 4 | 153 | 869 |
| 2023-07 | 19 | 104747 | 5 | 9473 | 8778 |
| 2023-06 | 10 | 104264 | 3 | 152434 | 152508 |
| 2023-05 | 3 | 104339 | 2 | 9 | 7 |
| 2023-04 | 3 | 104337 | 3 | 2 | 1 |
| 2023-03 | 3 | 104336 | 2 | 18 | 7 |
| 2023-02 | 2 | 104326 | 1 | 0 | 0 |
| 2023-01 | 3 | 104326 | 3 | 243 | 90 |
| 2022-12 | 2 | 104173 | 2 | 883 | 659 |
| 2022-11 | 3 | 103986 | 2 | 215 | 134 |
| 2022-10 | 6 | 103914 | 1 | 66 | 16 |
| 2022-09 | 1 | 103866 | 1 | 19 | 3 |
| 2022-08 | 2 | 103854 | 2 | 111 | 26 |
| 2022-07 | 1 | 103783 | 1 | 4 | 2 |
| 2022-06 | 1 | 103781 | 1 | 12 | 0 |
| 2022-05 | 0 | 103771 | 0 | 0 | 0 |
| 2022-04 | 6 | 103771 | 2 | 473 | 57 |
| 2022-03 | 8 | 103404 | 7 | 174 | 89 |
| 2022-02 | 6 | 103335 | 2 | 573 | 488 |
