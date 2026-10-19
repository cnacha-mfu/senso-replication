## Repository context

The following information about zopefoundation/Zope was computed from its git history up to the base commit of this task (2023-11-06). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 47261 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 49566 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.97 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.01 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 51 | Commits with author date in the last three window months. |
| Months with at least one commit | 34 | Window months with one or more commits. |
| Share of months with at least one commit | 0.94 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.50 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.86 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.48 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.22 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.13 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.00 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.81 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.05 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 2305.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| src/App/ApplicationManager.py | 328 | 1 | 1 | 31 | 9 % | 1 |
| src/OFS/Application.py | 457 | 5 | 3 | 151 | 33 % | 1 |
| src/OFS/Cache.py | 479 | 0 | 0 | 0 | 0 % | 46 |
| src/OFS/CopySupport.py | 571 | 0 | 0 | 0 | 0 % | 40 |
| src/OFS/DTMLMethod.py | 409 | 0 | 0 | 0 | 0 % | 28 |
| src/OFS/Image.py | 995 | 5 | 2 | 162 | 16 % | 1 |
| src/OFS/ObjectManager.py | 756 | 0 | 0 | 0 | 0 % | 33 |
| src/OFS/PropertyManager.py | 335 | 1 | 1 | 2 | 1 % | 3 |
| src/OFS/PropertySheets.py | 484 | 1 | 1 | 2 | < 1 % | 3 |
| src/OFS/SimpleItem.py | 330 | 0 | 0 | 0 | 0 % | 37 |
| src/OFS/interfaces.py | 757 | 0 | 0 | 0 | 0 % | 46 |
| src/Products/Five | 1833 | 0 | 0 | 0 | 0 % | 33 |
| src/Products/PageTemplates | 1934 | 1 | 1 | 24 | 1 % | 5 |
| src/Shared/DC | 458 | 0 | 0 | 0 | 0 % | 18 |
| src/Testing/ZopeTestCase | 3556 | 1 | 1 | 133 | 4 % | 10 |
| src/ZPublisher/BaseRequest.py | 655 | 0 | 0 | 0 | 0 % | 40 |
| src/ZPublisher/HTTPRequest.py | 1491 | 12 | 6 | 919 | 62 % | 1 |
| src/ZPublisher/HTTPResponse.py | 1007 | 1 | 1 | 34 | 3 % | 11 |
| src/ZPublisher/WSGIPublisher.py | 351 | 3 | 3 | 35 | 10 % | 2 |
| src/Zope2/App | 327 | 0 | 0 | 0 | 0 % | 37 |
| src/Zope2/Startup | 738 | 1 | 1 | 8 | 1 % | 4 |
| src/Zope2/utilities | 549 | 1 | 1 | 15 | 3 % | 8 |
| src/webdav/NullResource.py | 445 | 0 | 0 | 0 | 0 % | 22 |
| src/webdav/Resource.py | 601 | 0 | 0 | 0 | 0 % | 32 |
| src/webdav/davcmds.py | 511 | 1 | 1 | 2 | < 1 % | 9 |
| docs | 239 | 14 | 8 | 42 | 18 % | 1 |
| src/App/CacheManager.py | 76 | 0 | 0 | 0 | 0 % | 37 |

Other modules: 82 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2023-10 | 17 | 49566 | 4 | 535 | 178 |
| 2023-09 | 32 | 49262 | 9 | 364 | 23 |
| 2023-08 | 2 | 48957 | 1 | 3 | 3 |
| 2023-07 | 3 | 48957 | 2 | 100 | 8 |
| 2023-06 | 8 | 48879 | 4 | 130 | 22 |
| 2023-05 | 6 | 48794 | 3 | 171 | 44 |
| 2023-04 | 5 | 48680 | 5 | 2 | 4 |
| 2023-03 | 11 | 48682 | 5 | 126 | 75 |
| 2023-02 | 2 | 48639 | 2 | 1 | 1 |
| 2023-01 | 12 | 48639 | 5 | 563 | 489 |
| 2022-12 | 19 | 48591 | 4 | 136 | 59 |
| 2022-11 | 9 | 48534 | 2 | 6 | 5 |
| 2022-10 | 5 | 48533 | 3 | 101 | 38 |
| 2022-09 | 6 | 48482 | 1 | 7 | 5 |
| 2022-08 | 4 | 48480 | 2 | 16 | 7 |
| 2022-07 | 2 | 48472 | 2 | 35 | 21 |
| 2022-06 | 8 | 48459 | 2 | 4 | 4 |
| 2022-05 | 5 | 48459 | 5 | 20 | 7 |
| 2022-04 | 12 | 48447 | 4 | 74 | 23 |
| 2022-03 | 7 | 48402 | 3 | 17 | 17 |
| 2022-02 | 3 | 48402 | 3 | 785 | 108 |
| 2022-01 | 9 | 47874 | 3 | 193 | 57 |
| 2021-12 | 3 | 47757 | 2 | 185 | 6 |
| 2021-11 | 3 | 47609 | 1 | 2 | 1 |
| 2021-10 | 2 | 47608 | 2 | 0 | 0 |
| 2021-09 | 0 | 47608 | 0 | 0 | 0 |
| 2021-08 | 0 | 47608 | 0 | 0 | 0 |
| 2021-07 | 14 | 47608 | 2 | 200 | 121 |
| 2021-06 | 13 | 47527 | 5 | 116 | 26 |
| 2021-05 | 12 | 47451 | 3 | 183 | 32 |
| 2021-04 | 3 | 47335 | 2 | 1 | 7 |
| 2021-03 | 6 | 47340 | 2 | 73 | 62 |
| 2021-02 | 17 | 47332 | 4 | 135 | 59 |
| 2021-01 | 1 | 47261 | 1 | 0 | 0 |
| 2020-12 | 2 | 47261 | 1 | 0 | 0 |
| 2020-11 | 17 | 47261 | 5 | 30 | 12 |
