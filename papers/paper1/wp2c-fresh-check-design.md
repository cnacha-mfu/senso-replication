# WP2c: fresh check of new repositories with the released tool (Paper 1, JSEP tool framing)

Status: written and committed on 2026-10-19 before any repository of this sample is checked. Exploratory; no
hypothesis test. Changes after this commit go to a "Deviations" list at the end of this file, with dates.

## Purpose

RQ2 evaluated the claim check on 79 manifests collected in March 2026. This study runs the released one-command tool
(`senso_check.py`) on manifests it has never seen, to report what a user would get: how many claims get a result, how
many manifests have a contradicted claim, and how many contradicted results an independent check confirms.

## Tool version

`senso_check.py` with the wildcard fix described below, at the commit that adds this file's "Tool fixed" line (filled
in before the first run). No rule, threshold, prompt, model or TBox differs from RQ2. Runs use `--skip-explain`
(explanations do not change results).

Wildcard fix (decided after the laravel-package-ocean example of 2026-10-18, before this sample): a T1/T2 path claim
is marked as a wildcard (`glob=true`, as RQ2's normaliser does when the subject itself contains `*` or `?`) also when
its quote shows the subject directly preceded by `*/`, `**/` or `*`. Its effect on the committed RQ2 claims is
measured offline and reported; RQ2 results are not re-run or overwritten.

## Sample

- Candidates: GitHub code search (REST, authenticated) for files named `CLAUDE.md` and for files named `AGENTS.md`, at
  the repository root, collected once on the day of the first run; the raw candidate list is saved.
- Keep a repository if: public, not a fork, not archived, at least 20 stars, pushed on or after 2026-07-01, root
  manifest of at least 500 characters, and not one of the 79 RQ2 repositories or the 5 tool test repositories
  (stefanbschneider/mobile-env, jvkersch/tmtools, kantord/headson, HassanZahirnia/laravel-package-ocean,
  and any other repository checked during tool development). If both files exist, check `CLAUDE.md`.
- Order the eligible list by full name, shuffle with seed 20261019, and take repositories in that order until 30 have a
  completed run. A run that fails (clone, snapshot, extraction or reasoner error, or more than 20 minutes) is logged
  with its reason and replaced by the next repository. Repositories larger than 2 GB are skipped as a failure.
- Code search returns at most 1,000 results per query and ranks them, so the sample is not representative of all
  manifests. It is described as a convenience sample of recently active, starred repositories.

## Outcomes (all by deterministic code; no human rater, no LLM judge)

1. Per manifest: claims with a result, counts per check result, any contradicted claim (yes/no), run time per step.
2. Contradicted claims by type (T1-T6) and leaf class.
3. Independent confirmation of each contradicted claim with the RQ2 triangulation instruments (`triangulate` step:
   GitHub Contents API for T1, commits API for T2, CI configs for T5, `git grep` outside docs for T3/T4, re-parse
   for T6). Reported per type as confirmed / not confirmed / not checkable.
4. Quote-context check of each contradicted T1/T2 claim (an extraction check the triangulation cannot make): the
   subject must occur in its quote not preceded by a wildcard, not inside a URL, and not followed by a placeholder
   such as `<name>` or `...`. Reported as passed / failed.
5. Headline: the share of contradicted claims that are confirmed by (3) and pass (4), with a Wilson 95% interval,
   overall and per type; and the share of manifests with at least one such confirmed contradiction.

## Reporting

Main text: a short paragraph in Section 3.6 or RQ2 with the headline numbers and the main kinds of false alarm.
Supplement: a table per type. Numbers go through the results digest. Results go to
`results/real_v2/wp2c/` (code and summaries committed; clones and caches under `/home/adtgrade/research/data/`).

## Tool fixed

Commit 0d546f5c (2026-10-19): wildcard fix in `wp2/normalize.py` (`quote_shows_wildcard`, applied to T1 and T2 path claims; a single `*` or a `*/`, `**/` directly before the subject in the raw quote; markdown bold `**x**` and italics `*x*` do not count). Offline effect on the 1,371 committed T1/T2 RQ2 claims: 0 flip from glob=false to true, so no RQ2 verdict would change (`results/real_v2/wp2c/glob_fix_effect_rq2.json`).

## Deviations

- 2026-10-19: eligibility was applied in one pass per candidate, so the reason counts are for the first failing
  filter (stars < 20: 1,686; pushed before 2026-07-01: 38; manifest < 500 characters: 20; RQ2 or tool-development: 4;
  eligible: 120 of 1,868 candidates). Code search was run with `filename:<name> path:/`.
- 2026-10-19: the `recheck` step (independent re-parse of the rules) was run on each repository in addition to
  `triangulate`, because `triangulate` has no T6 instrument of its own; a contradicted T6 claim counts as confirmed
  if the re-parse also contradicts it.
- 2026-10-19: quote-context check (outcome 4), implementation details found on the first pass: backticks are ignored
  when locating the subject, and for claims expanded from a tree diagram (composed path, quote is the leaf line) the
  leaf name is searched in the quote. Without this 9 of 38 T1 claims failed only because of the composed subject.
  The check does not test slash alternations (`src/a.c/h`), which the check as designed cannot detect.
- 2026-10-19: runs were started under `systemd-run --user --scope -p MemoryMax=6G -p TasksMax=300` (CLAUDE.local.md
  rule), each run in its own process group that is killed when the run ends.
- 2026-10-19 (after the summary): the automatic checks confirmed 40 of the 41 contradicted claims, but they test
  only that the named path or version is absent, so they cannot see a claim that was read wrongly. As in RQ2's first
  pass, the authors read every contradicted claim next to the repository at its snapshot and labelled it a real error or
  a false alarm with its cause (`scripts/wp2c_inspection.py`, which holds each label and its evidence;
  `results/real_v2/wp2c/wp2c_inspection.json`). This is descriptive and is reported next to the pre-planned headline,
  which is reported as an upper bound. No tool change was made after the runs.
