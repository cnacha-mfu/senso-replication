# WP2b design and pre-registration: do manifest errors get fixed? (RQ2b)

Status: pre-registration draft, 2026-10-09. To be committed **before** any HEAD fetch; that commit hash is the
registration. Builds on `wp2-design.md` (commit 09860cf) and the frozen RQ2 results in
`experiments/paper1_ontology_manifests/results/real_v2/wp2/`, which are read and never rewritten.
No language model is called: the claims are the frozen RQ2 consensus claims; only measurement at HEAD is new.

## 1. Question

**RQ2b: Are contradicted claims later removed or corrected, or do they persist?** Reported as part of RQ2.
If contradicted claims are removed or corrected more often than supported claims (the base rate of manifest
churn), developers or agents notice the errors. If at the same rate, nobody notices and a mechanical check
adds information that maintainers do not already have.

## 2. Population, unit, follow-up point

- **Unit:** one checked claim of RQ2: consensus ≥ 2 votes, mode `asserts_existing`, headline type, with a
  verdict at S. **Analysed set:** claims that are Supported (n = 1,112) or Contradicted (n = 65, in 29 manifests)
  at S, types T1, T3–T6 (the drift population of `drift.json`; T2's 4 claims and the 39
  Unverifiable/Indeterminate/Conflicted claims are only described). Claims are clustered in 79 manifests.
- **Start:** the snapshot commit S of `snapshots/{slug}.json`. **End:** H, the default-branch head fetched
  once, in a single run. The fetch date and time, the current default branch name (GitHub REST `GET /repos`),
  the `archived` flag, H and whether S is an ancestor of H are all frozen in `head_fetch.json`. No later re-fetch.
- **Known before registration (disclosed):** the local blobless clones (made 2026-10-06) show that
  41/79 manifests had ≥ 1 first-parent commit touching the manifest after S, and that the manifest path is absent at
  the clone head in 4/79. The median S-to-clone-head interval was 198 days (0–474). No claim-level outcome and no
  contradicted-versus-supported split was computed.

## 3. Outcomes (mutually exclusive, assigned in this order)

| Code | Outcome | Computed by |
|---|---|---|
| U | Repository unavailable (fetch fails: deleted, private, or blocked) | `git fetch` exit status + REST 404 |
| G | Manifest gone: no file at the manifest path at H, and no rename found by `git diff -M50% --name-status S H` | new; `gitutil.show_blob` |
| R | Claim removed: the manifest exists at H (renamed path or symlink followed, one level), but no line holds the claim key | new key matcher |
| P-C | Retained and still Contradicted at H | re-measured, HermiT |
| P-S | Retained and now Supported at H (the repository changed to match) | re-measured, HermiT |
| P-O | Retained, other verdict at H (Unverifiable, Indeterminate or Conflicted) | re-measured, HermiT |

- **Key present** means a single line of the H manifest (after `normalize.norm_text`) contains every component
  of the claim's canonical key as whole tokens:
  - T1: the path;
  - T3: the tool name or one of its aliases (`normalize.tool_aliases`);
  - T4: the package name, plus the major version if the claim is versioned;
  - T5: runner and target (the existing co-occurrence rule);
  - T6: subject and version value.
- A changed version value or path therefore counts as R, which covers both deletion and correction by rewording.
- A flag `quote_verbatim` records whether the normalised quote itself survives. It splits retained claims into
  "unchanged" and "edited".
- **Archived** repositories are analysed and flagged (archiving gives the maintainers no further chance to edit).
- **Derived binaries:**
  - *removed* = G ∪ R;
  - *resolved* (contradicted claims only) = G ∪ R ∪ P-S;
  - *persisted* = P-C.
  - U is excluded from the denominators and counted.

## 4. Reused and new code

**Reused unchanged:**
- `snapshot.clone_dir` (the blobless clones under `~/research/data/raw/repos/wp2`);
- `repo.RepoAt(d, H)`, `measure.Ctx`, `step_measure.measure_claim` and `claim_types` (the measurement used at S);
- `ClaimsAboxWriter.claim(..., suffix="/head")`, the same copy mechanism as the `/intro` copies in `step_drift`;
- `HermitReasoner(CLAIMS_MODULES)` on the baseline TBox (`step_reason.ensure_tbox`, sha checked against
  `verdicts/*.json`), with the verdict at H read from the copy's labels;
- `recheck.Git(d, H)` + `recheck.recheck_claim` (the independent re-check);
- `statistics.gee_fit` and `conditional_logit_by_stratum`, and the bootstrap seed from `wp2_consistency.yaml`.

There is **no TBox change**, so the verdict classes and thresholds are identical to RQ2.

**Regression guard:** the original claims stay in each ABox, so HermiT must reproduce `verdicts/{slug}.json`
at S exactly. A mismatch aborts the run.

**New code:**
1. `wp2/step_persist.py` (~250 lines, subcommand `persist` in `wp2_consistency.py`):
   - fetch H into `refs/wp2b/head` (`git fetch --filter=blob:none`, so the clone's own HEAD is untouched;
     3 workers);
   - manifest location (path, rename, symlink);
   - key matcher;
   - measurement and reasoning at H;
   - re-check at H;
   - for R claims, the first commit after S whose manifest diff drops the key (`git log -S` on the subject),
     its date and hunk shape (pure deletion vs replacement).
2. `wp2/step_persist_report.py` (~150 lines): the analyses in Section 5.

**Matcher self-test:** run on the S manifest text, the matcher must find 100% of analysed keys before H is
touched. Any miss is a matcher bug, fixed and logged.

**Output:** `results/real_v2/wp2b/`, a new directory containing `head_fetch.json`, `persistence/{slug}.json`,
`abox_head/`, and `report.json`.

**Runtime:** about 30 minutes wall time.
- fetch: 79 incremental blobless fetches, 5–15 min;
- tree listing, measurement and blob prefetch at H: about 5 min (35 s at S with warm blobs);
- HermiT: 79 × about 6 s over 3 workers, about 3 min;
- re-check: about 5 min;
- removal-commit search: a few minutes.

External calls: 0 NIM calls, about 80 GitHub REST calls and 79 fetches.

## 5. Analysis (confirmatory)

**A1, persistence of errors:** the share of contradicted claims that are P-C, with a Wilson 95% CI. A cluster
bootstrap CI (manifests resampled, B = 10,000) is reported beside it, because 65 claims sit in 29 manifests.

Fixed decision language, applied to the cluster-bootstrap CI:

| CI | Wording |
|---|---|
| Lower bound ≥ 0.75 | "almost all contradicted claims persist" |
| Lower bound > 0.50 | "most persist" |
| Upper bound < 0.50 | "most are resolved" |
| Otherwise | "about half persist; the data cannot say whether most do" |

**A2, noticing (key comparison):** the risk ratio of *removed* for contradicted vs supported claims, **within
manifest**.
- Mantel–Haenszel RR stratified by manifest, over manifests that have both kinds of claim. This removes
  manifest-level churn and dormancy.
- 95% CI from a manifest-level cluster bootstrap (B = 10,000). The MH risk difference is reported alongside.

Fixed decision language:

| CI | Wording |
|---|---|
| Lower bound > 1 | "contradicted claims are removed more often than other claims" (noticed) |
| Upper bound < 1 | "removed less often" |
| Inside [0.5, 2] | "removed at about the same rate as other claims" (not noticed) |
| Otherwise | "no detectable difference; the study cannot exclude an RR of {bound}" |

**Robustness, reported without changing the decision:**
- (a) conditional logit by manifest (`conditional_logit_by_stratum`);
- (b) GEE logistic over all 79 manifests, `removed ~ contradicted + C(type)`, exchangeable, bias-reduced
  sandwich (`gee_fit`);
- (c) A1 and A2 restricted to manifests edited at least once in (S, H], where the maintainers had an
  opportunity to remove the claim;
- (d) excluding archived repositories and repositories where S is not an ancestor of H;
- (e) only the 64 contradicted claims on which the reasoner and the re-check agree;
- (f) *removed* defined by quote disappearance instead of key disappearance.

## 6. Secondary and exploratory analyses (labelled as such)

- **Outcome distribution.** U/G/R/P-C/P-S/P-O by verdict at S, by type, and for drifted vs born-wrong claims
  (`drift.json`).
- **Forward drift.** The share of retained Supported claims that are Contradicted at H, also per claim-year of
  follow-up. This is the rate at which new errors appear.
- **Time.**
  - Days from S to H, per manifest.
  - Days from introduction (the `intro_commit` date in `drift.json`) to H for P-C claims, i.e. the minimum age of
    an uncorrected error.
  - For drifted claims, days from the flip commit to H.
  - Time from S to removal for R claims.
- **How removals happen.** Hunk shape of the removing commit, and whether that commit carries an agent signal
  (`shared/mining/agent_detector.py` trailer and message patterns, commit-local only).
- **Re-check agreement at H.** Cohen's κ between HermiT and `recheck` at H, the same validation as RQ2.

## 7. Threats

- **Short follow-up.** About 6.5 months; dormant repositories (0 commits after S) cannot remove anything.
  Addressed by robustness check (c) and by reporting commits in (S, H].
- **Matcher errors.**
  - Rewording that keeps the key counts as retained.
  - Reformatting a path (for example `./src` → `src/`) could count as R. The canonical key is normalised as at S
    to limit this.
  - The verbatim-quote variant (f) bounds the effect.
- **Removal does not mean correction.** A deleted line may be cleanup unrelated to the error. A2 compares against
  the same-manifest base rate, which does not establish cause.
- **Inherited errors.** RQ2 measurement errors carry over: 1 of the 65 contradicted claims disagrees with the
  re-check. Robustness check (e) addresses this.
- **Selection.** Only claims present at S are followed; errors introduced after S are not counted (only
  forward drift of existing claims is).
- **Small sample.** 65 contradicted claims in 29 manifests, with up to 8 per manifest. A2 is likely to end in
  the "no detectable difference" wording, and the CI bound will be reported as the result.
- **Prior knowledge.** The manifest-level churn figures in Section 2 were known before registration.

## 8. Deviation rule

- Every change after the registration commit goes into `papers/paper1/wp2b-deviations-log.md`, using the
  columns of `wp2-deviations-log.md` (what changed; before or after seeing H outcomes; why and with what
  impact).
- Changes to the matcher or the outcome rules made after outcomes have been seen are reported with the analysis
  run both ways.
- Any analysis not listed in Section 5 is reported as exploratory.
- The results in `results/real_v2/wp2/` and the JSS-era results are never modified.

## 9. Coordinator decisions (frozen 2026-10-09, before any data at H was fetched or analysed)
- Output directory: `experiments/paper1_ontology_manifests/results/real_v2/wp2b/` (new; RQ2 files are read-only inputs).
- Equivalence band for "same rate" wording: risk ratio within [0.5, 2].
- A changed path or version value in the manifest counts as removed (R).
- The primary A2 comparison is within manifest (Mantel-Haenszel with manifest-level bootstrap); the pooled comparison is a robustness check.
