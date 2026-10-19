# WP2 design: documentation-history consistency checking (RQ2)

Scope: design only. I modified no files. Everything below comes from reading the repo at `c9c800d`, plus read-only `python3 -c` surveys over the cached manifest texts. I did not need GitHub or NIM calls, because the manifest texts are already cached.

---

## 0. Summary of decisions

1. **The corpus already holds the manifest texts.** `experiments/jcsse2026/results/expanded_corpus.json` has 80 entries with `claude_md_content` (612,526 characters in total, median 5,190, max 43,676).
   - 57 entries carry `manifest_path`: 23 `CLAUDE.md`, 21 `AGENTS.md`, 12 `.github/copilot-instructions.md`, 1 `.clinerules`.
   - The 23 entries without it are the JSS-era Paper 1 `phase1_repos.json` repos (all 23 are in the corpus). These are CLAUDE.md files.
   - **No commit SHA was recorded.** The texts were fetched through the Contents API at default-branch HEAD. So WP2 must recover the snapshot commit S by matching the text against history (Section 7).
2. **Seven claim types, each checked mechanically.** T1 path existence, T2 path status (legacy/deprecated/frozen) against churn, T3 tool used, T4 dependency (optionally with a major version), T5 command/script exists, T6 runtime/project version, T7 import constraint (stretch). T8, a project-stage claim checked against WP1's inferred stage, is deferred because WP1 mining has no `--until` date.
3. **Measurement/inference boundary, same as WP1 §3.1.**
   - Python may do lookups, parsing and counting against the git snapshot. That includes "is this string a tracked path" and "is this name declared in package.json". It may also compute differences of two measured values (the WP1 `complexityChange` precedent).
   - Python never compares against a constant and never asserts a verdict class.
   - Every verdict class, threshold and consensus rule lives in a new SWRL-free module, `seo-claims.owl`.
   - **HermiT** decides the verdicts (SWRL-free; WP1 found Pellet 2.3.1 unstable on datatype-heavy TBoxes). **Pellet's `explain` CLI** (`ontology/reasoning/explain.py`) produces justifications.
4. **Verdicts are a disjoint set of named classes:** `SupportedClaim`, `ContradictedClaim`, `UnverifiableClaim` (a reason is stated), `IndeterminateClaim` (the T2 gap band), `ConflictedClaim` (T6, when sources disagree with each other).
   - Claims that get no measurement fall into none of these and are reported as "unmeasured", never as contradicted. This is the WP1 open-world rule: missing data gives "undetermined".
   - Chained classes show inference beyond per-claim checks: `ManifestWithContradiction ≡ ManifestDocument ⊓ ∃makesClaim.ContradictedClaim`, and `DriftedClaim` (false at S, true when the claim text was introduced).
5. **Extraction uses nemotron-3-super, gpt-oss-20b and diffusiongemma.** Each claim is reduced to a canonical key, so matching across models is exact. Consensus is ≥2 of 3 and is itself a TBox threshold (`wp2_consensus_min_votes`), so the 1/3 and 3/3 sensitivity runs are TBox rebuilds.
   - Mechanical validation: verbatim span grounding, a subject-in-quote check, type-specific shape filters, and a regex recall check for T1/T5.
6. **Validation needs no humans:**
   - (a) A deterministic re-check: an independent Python implementation that shares no code with the measurement module, compared verdict by verdict against the reasoner.
   - (b) Second-instrument triangulation: GitHub API at ref S, CI-workflow invocation, `git grep`.
   - (c) Drift origin: each contradicted claim is re-checked at the commit that introduced its text.
7. **Budget:** 152 chunks × 3 models ≈ 456 NIM calls, about 500 with retries (≈2.6M input and 0.6M output tokens), roughly 30 to 60 minutes wall time. Under 1,000 GitHub REST calls. HermiT about 3 s per manifest.

---

## 1. Grounding: what the corpus actually contains

A regex survey over the 80 cached texts (number of repos containing each pattern, and total hits):

| Pattern | Repos | Hits | Implication |
|---|---|---|---|
| Backticked path containing `/` | 62 | 778 | T1 dominates |
| `npm/pnpm/yarn/bun [run] X` | 24 | 308 | T5 |
| `make X` | 17 | 78 | T5 |
| `uv/poetry/pipenv/pip install` | 14 | 90 | T3 |
| pytest / jest / vitest / cargo / go test / dotnet / gradle-mvn | 11 / 3 / 5 / 5 / 4 / 3 / 3 | | T3 |
| Runtime version (Python/Node/Go/…) | 21 | 50 | T6 |
| "do not/never modify/edit/change" | 12 | 27 | Mostly *generated* files, so the churn check is not applicable |
| deprecated / legacy | 14 | 36 | T2 |
| "must not import / depend" | 0 strict, about 5 loose | | T7 is rare, so it is a stretch type |

Examples from the eight manifests I read in full:
- **nats-io/nats.go:** a plain-indented tree with `js.go # Legacy JetStream API (deprecated, see jetstream/)` (T1+T2), "Matrix of Go 1.24 and 1.25" (T6 vs `go.mod`), and `go_test.mod` (T1).
- **a16z/halmos:** `uv run pytest` (T3 uv, T3 pytest), "Use Python ≥ 3.11 … the oldest supported target" (T6 min).
- **chef/chef-vault:** a `├──` tree including `coverage/`, `tmp/`, `vendor/`. These are likely gitignored, so they must come out Unverifiable, not Contradicted.
- **lerna/lerna:** "uses npm (version 10.8.0)" (T3 + T6-style `packageManager` field), `npm run format:check/lint/test/integration` (T5), "legacy-core/: Legacy core functionality maintained for backwards compatibility" (T2, with the caveat that it is legacy but maintained).
- **HassanZahirnia/laravel-package-ocean:** "laravel/framework (LARAVEL) - v12", "tailwindcss - v4", "php - 8.4.13" (T4 versioned, T6 exact), `composer run dev` (T5, composer scripts).
- **JunDamin/hwpapi:** "Version: 0.0.2.2" (T6 project_self, likely stale), notebook-to-module mapping paths (T1), and "NEVER edit .py files in hwpapi/ … auto-generated" (protected, existence only).
- **kubernetes-sigs/cloud-provider-azure:** a tree with globs `azure_vmss*.go` (T1 glob), and "azclient/ … don't call Azure SDK directly" (T7 candidate; it fails grounding because the SDK module path is not written).
- **openai/openai-agents-js:** `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `vitest*.ts` (T1/T3), `pnpm docs:dev` (T5 without `run`).

Out of scope, because they are not mechanically checkable: style rules, workflow advice, agent directives, design rationale, and claims about external systems (CI providers, Jira).

---

## 2. Boundary and verdict semantics

**Python (measurement) may:**
- list the tree at S;
- test membership of a normalized string in that tree or in a parsed manifest;
- parse version constraints into numeric bounds;
- count commits and lines in fixed windows;
- compute a difference of two measured values;
- assert the claim's *extracted* type and content (what the manifest says is input data, not a verdict);
- assert structural closure axioms (`hasEvidence only {…}`), as WP1 does for months.

**Python may not:**
- compare a count with a constant;
- choose a verdict;
- emit booleans (`AboxWriter.literal` already raises on `bool`). Presence facts are integer counts (0/1/n).

**Rejected alternative (record it in the paper):** asserting the whole tree as path individuals and letting SWRL `startsWith`/`equal` do the matching. Trees reach about 10^5 files, and WP1 measured Pellet as superlinear (5k individuals took 106 s). Lookup is measurement; deciding what a lookup result *means* is inference.

**Verdict lattice (all named classes, Horn-union style per `_Rules.union`):**
- `AllDisjoint(SupportedClaim, ContradictedClaim, UnverifiableClaim, IndeterminateClaim, ConflictedClaim)`. An encoding bug that puts a claim in two of these classes makes the manifest's ABox inconsistent. That is caught by `explain_inconsistent` and by the self-test.
- `CheckedClaim ≡ ManifestClaim ⊓ extractionVotes some integer[>= wp2_consensus_min_votes]`. Every leaf verdict class conjoins `CheckedClaim`, so the ABox can hold all claims extracted by at least one model, and the consensus rule is a TBox parameter.
- `ManifestWithContradiction ≡ ManifestDocument ⊓ ∃makesClaim.ContradictedClaim`.
- `DriftedClaim ≡ ContradictedClaim ⊓ ∃introducedAs.SupportedClaim`, and `BornWrongClaim ≡ ContradictedClaim ⊓ ∃introducedAs.ContradictedClaim` (Section 5.3).

---

## 3. Claim taxonomy: schema, measurement and encoding per type

Notation follows WP1 §3.3:
- `p[op k]` means `p some integer[op k]` (or decimal);
- `p[=0]` is `_Rules.between(p, ">=", 0, "<=", 0)`;
- every operand is named, and each leaf class conjoins `CheckedClaim ⊓ <TypeClass>`.

**Common extraction fields:** `type`, `quote` (verbatim, ≤ 200 characters), `line` (global), `subject` (verbatim), `mode` ∈ {`asserts_existing`, `to_be_created`, `example`, `negated`}.

Only `asserts_existing` is checked. An instruction that presupposes the referent ("run `npm run lint`", "tests go in `tests/`") counts as `asserts_existing`. `negated` claims ("instead of pnpm") are counted and dropped in v1.

**Common ABox data properties on the claim:**
- `claimQuote`, `claimSubject` (normalized), `claimKey`, `claimLine`, `extractionVotes` (int 1-3);
- `snapshotCommit` on the `ManifestDocument`.

### T1. PathExistenceClaim: "path/module X exists"

- **Extraction:** `{type:"path_exists", subject, path_components?:[...], kind_hint: file|dir|glob|unknown}`.
  - `path_components` is used only for tree diagrams (`├──` or indentation). Each component must appear verbatim in the chunk.
- **Normalization (mechanical):**
  - strip backticks, quotes and `**`; strip a leading `./`;
  - a leading `/` means the repo root unless the path starts with `/usr /etc /tmp /var /opt /home /dev /proc`, in which case it is dropped;
  - a trailing `/` sets `dir`; collapse `//`;
  - glob if the path contains `* ? [`.
  - **Reject:** URLs (`://`), `~`, `$`, `<`, `{`, `..`, `path/to`, `your-`, `example`, `foo/`, `xxx`, bare file extensions, and the manifest's own path (trivially true).
- **Measures at S** (`git ls-tree -r --full-tree S`, blobless clone):

| Property (int) | Definition |
|---|---|
| `pathExactMatchCount` | Tracked files equal to the path, under the directory, or matching the glob (`pathspec` gitwildmatch, installed 1.1.1) |
| `pathSuffixMatchCount` | Tracked paths with `"/"+path` as suffix (monorepo-relative mentions) |
| `pathIgnoredCount` | 1 if the root or an ancestor `.gitignore` at S (read via `git show`, parsed with `pathspec`) matches the path, else 0 |
| `pathSubmoduleCount` | 1 if a gitlink (mode 160000) is a prefix of the path |
| `pathEverTrackedCount` | Commits ≤ S touching the path (`git log S --format=%H -- path`) |
| `daysSincePathLastTracked` | S date minus the date of the deleting commit (context, for the template) |

- **Classes:**

| Leaf class | Definition | Verdict |
|---|---|---|
| `PathFoundExact` | `exact[>=1]` | Supported |
| `PathFoundBySuffix` | `exact[<=0] ⊓ suffix[>=1]` | Supported (reported separately as "relocated") |
| `PathUntrackedByDesign` | `exact[<=0] ⊓ suffix[<=0] ⊓ ignored[>=1]` | Unverifiable |
| `PathInSubmodule` | `exact[<=0] ⊓ suffix[<=0] ⊓ submodule[>=1]` | Unverifiable |
| `PathRemoved` | `exact0 ⊓ suffix0 ⊓ ignored0 ⊓ submodule0 ⊓ everTracked[>=1]` | Contradicted |
| `PathNeverExisted` | `… ⊓ everTracked[<=0]` | Contradicted |

- `exact0` and the other zero atoms are named classes (`A_pathExactMatchCount_le_0`).
- Template for `PathRemoved`: "`{claimSubject}` is not tracked at the snapshot and not git-ignored; {pathEverTrackedCount} earlier commits touched it."

### T2. PathStatusClaim: "X is legacy / deprecated / frozen / stable"

- **Extraction:** `{type:"path_status", subject, status: legacy|deprecated|frozen|stable|generated|do_not_edit}`.
  - Python maps `legacy|deprecated|frozen|stable` to the asserted subtype `InactiveStatusClaim`.
  - `generated|do_not_edit` maps to `ProtectedStatusClaim`. These are routed to T1 existence only and excluded from contradiction rates, because generated files churn by design and a directive is not a factual claim.
  - Non-path subjects ("Stable public APIs") fail the shape filter.
- **Measures:**
  - The path is resolved by T1 logic. If it is unresolved or the suffix match is ambiguous (more than one), no churn is measured.
  - For W ∈ {90, 180, 365} days before S, using non-merge first-parent history, `git log --numstat S --since=… -- path`:
    - `pathCommitsIn{W}d` (int)
    - `pathLinesChangedIn{W}d` (int, added + deleted inside the path)
  - Context: `repoCommitsIn180d` and `daysSincePathLastChange`.
- **Classes** (the builder picks the property name from `wp2_status_window_days` and validates that it is in {90, 180, 365}):

| Leaf class | Definition | Verdict |
|---|---|---|
| `StatusPathUnresolved` | `InactiveStatusClaim ⊓ exact[<=0] ⊓ suffix[<=0]`, plus a named `SuffixAmbiguous` (`exact[<=0] ⊓ suffix[>=2]`) | Unverifiable |
| `InactivePathQuiet` | `pathCommitsInWd[<= wp2_inactive_support_max_commits]` | Supported |
| `InactivePathActive` | `pathCommitsInWd[>= wp2_inactive_contradict_min_commits] ⊓ pathLinesChangedInWd[>= wp2_inactive_contradict_min_lines]` | Contradicted |
| `InactivePathModerate` | Named positive complement of both of the above (gap band) | Indeterminate |

- **A priori thresholds** (add to `thresholds.yaml` as `group: wp2`, `status: UNJUSTIFIED` with the rationale written down, and commit before extraction runs):

| id | value | sensitivity | rationale |
|---|---|---|---|
| `wp2_status_window_days` | 180 | 90, 365 | About two release cycles. Dormancy definitions in OSS studies use 6 to 12 months. Candidate citations (e.g. Coelho & Valente 2017; Avelino et al. 2019) **must be verified before citing**. |
| `wp2_inactive_contradict_min_commits` | 5 | 3, 10 | Close to monthly activity over the window |
| `wp2_inactive_contradict_min_lines` | 100 | 50, 500 | Excludes one-line fixes and typo sweeps |
| `wp2_inactive_support_max_commits` | 1 | 0, 2 | A single maintenance touch is still "quiet" |

- **Construct caveat for the paper:** "legacy but maintained for backwards compatibility" (lerna) legitimately churns. A T2 contradiction means "contrary to the status label, the path saw active development", not "the manifest lies". Report the subtype split and the sensitivity grid.

### T3. ToolUsageClaim: test framework, package manager, build tool, linter

- **Extraction:** `{type:"tool_used", subject, tool_category: test_framework|package_manager|build_tool|linter_formatter}`.
- **Closed vocabulary**, kept in `configs/wp2_tool_signatures.yaml` and given in the prompt. Tools outside it are dropped mechanically:
  - npm, pnpm, yarn, bun, uv, poetry, pipenv, bundler, composer, maven, gradle;
  - pytest, jest, vitest, mocha, playwright, cypress, rspec, phpunit, pest, junit, xunit, nunit;
  - make, cmake, bazel, nx, turbo, vite, webpack, rollup, esbuild, tsup;
  - eslint, prettier, ruff, black, flake8, mypy, biome, rubocop, golangci-lint.
  - Builtins such as `go test` and `cargo test` are not claims.
- **Each signature has three parts:**
  - `files`: globs such as `pnpm-lock.yaml`, `jest.config.*`, `pytest.ini`, `conftest.py`;
  - `manifest_keys`: e.g. `package.json:packageManager` starts with `pnpm@`, `package.json:jest`, `pyproject:[tool.pytest.ini_options]`, `pyproject:[tool.poetry]`;
  - `deps`: dependency names looked up in the T4 census.
  - Plus `ecosystem_anchors` (package.json for JS tools; pyproject/setup.py/setup.cfg/requirements*.txt for Python tools) and `competitors` (other lockfiles in the same ecosystem).
- **Measures:** `toolSignatureHitCount`, `toolEcosystemAnchorCount`, `competingToolSignatureCount`.
- **Classes:**

| Leaf class | Definition | Verdict |
|---|---|---|
| `ToolSignatureFound` | `hits[>=1]` | Supported |
| `ToolAbsentCompetitorPresent` | `PackageManagerClaim ⊓ hits[<=0] ⊓ competing[>=1]` | Contradicted (strong form) |
| `ToolAbsentInEcosystem` | `hits[<=0] ⊓ anchors[>=1]`, plus the named complement of the strong form | Contradicted |
| `ToolEcosystemAbsent` | `hits[<=0] ⊓ anchors[<=0]` | Unverifiable (conservative) |

- `PackageManagerClaim` is an asserted subtype taken from the extracted `tool_category`.

### T4. DependencyClaim: "uses library Z [vN]"

- **Extraction:** `{type:"dependency", subject, ecosystem_hint?: npm|pypi|composer|go|cargo|maven|nuget|gem, version?: as written}`.
- **Shape filter:** the subject must be identifier-shaped. Allowed: npm `^(@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*$` after lowercasing, composer `vendor/name`, maven `group:artifact`, Go module path. "TanStack Query" is dropped and counted as a "non-identifier mention". This is the main defence against false contradictions from name aliasing.
- **Census** (`wp2/depparse.py`), covering every tracked manifest at S:
  - package.json (dependencies, devDependencies, peerDependencies, optionalDependencies);
  - pyproject (PEP 621 dependencies, optional-dependencies, `[dependency-groups]`, tool.poetry.*);
  - requirements*.txt, setup.cfg, Pipfile;
  - go.mod require, Cargo.toml (`[*dependencies]`, `[workspace.dependencies]`);
  - composer.json require / require-dev;
  - Gemfile and *.csproj PackageReference (regex);
  - pom.xml and build.gradle(.kts) (regex);
  - setup.py with best-effort regex, otherwise counted as unparsed.
  - Names are normalized per ecosystem (PEP 503 for PyPI, lowercase for npm and composer).
- **Measures:**
  - `dependencyExactMatchCount`, `dependencySuffixMatchCount` (match after the last `/`), `dependencyManifestParsedCount`.
  - For versioned claims: `claimedMajor` and `declaredLowerMajorDelta` = declaredLowerMajor − claimedMajor.
  - `declaredUpperMajorDelta` = declaredUpperMajor − claimedMajor, asserted only if the constraint is bounded. Otherwise `declaredUpperUnboundedCount` = 1.
  - Bounds come from `packaging.specifiers` for PyPI and a small caret/tilde/range parser for npm and composer (`^12` gives [12, 12]; `>=3,<5` gives [3, 4]). If several declarations exist, take the minimum lower bound and the maximum upper bound.
- **Classes:** `UnversionedDependencyClaim` and `VersionedDependencyClaim` are asserted subtypes.

| Leaf class | Definition | Verdict |
|---|---|---|
| `DependencyDeclared` | `exact[>=1]` (or `suffix[>=1]`, reported separately) | |
| Supported (unversioned) | `UnversionedDependencyClaim ⊓ DependencyDeclared` | Supported |
| `DependencyUndeclared` | `exact[<=0] ⊓ suffix[<=0] ⊓ parsed[>=1]` | Contradicted |
| `DependencyNoManifest` | `parsed[<=0]` | Unverifiable |
| `DependencyMajorTooOld` | `VersionedDependencyClaim ⊓ DependencyDeclared ⊓ declaredLowerMajorDelta[>0]` | Contradicted |
| `DependencyMajorTooNew` | `… ⊓ declaredUpperMajorDelta[<0]` | Contradicted |
| `DependencyMajorInRange` | `lowerDelta[<=0] ⊓ (UpperOK ⊔ Unbounded)`, both named | Supported |

### T5. CommandClaim: script or target exists

- **Extraction:** `{type:"command", subject: target, runner: npm|pnpm|yarn|bun|make|composer}`.
- **Normalization:**
  - `npm run build:prod -- --x` gives `build:prod`; `pnpm docs:dev` gives `docs:dev`.
  - Builtins per runner are excluded mechanically (install, i, ci, add, remove, exec, dlx, x, create, init, publish, version, audit, update, outdated, link, pack, why, ls, list, config).
  - `test`, `start`, `stop` and `restart` are checked as scripts. `npm start` is also supported if `server.js` exists (npm's default).
- **Measures:**
  - `scriptDefinedRootCount` and `scriptDefinedAnyCount`: across all tracked package.json / composer.json files, or across all Makefile / GNUmakefile / makefile / *.mk files. Make targets are parsed with `^([^\s:#=][^:=]*?)\s*::?(?!=)`, splitting multi-target lines.
  - `scriptHostFileCount` and `dynamicTargetRuleCount` (make pattern rules with `%` or targets containing `$(`).
  - `ciInvocationCount` is context, used only for triangulation.
- **Classes:**

| Leaf class | Definition | Verdict |
|---|---|---|
| `ScriptDefinedRoot` | `root[>=1]` | Supported |
| `ScriptDefinedNested` | `root[<=0] ⊓ any[>=1]` | Supported |
| `ScriptUndefined` | `any[<=0] ⊓ hosts[>=1] ⊓ dynamic[<=0]` | Contradicted |
| `ScriptHostMissing` | `any[<=0] ⊓ hosts[<=0]` | Contradicted (separate subtype; typical of copied template manifests) |
| `ScriptPossiblyDynamic` | `any[<=0] ⊓ dynamic[>=1]` | Unverifiable |

### T6. VersionClaim: runtime or project version

- **Extraction:** `{type:"version", subject: python|node|go|java|dotnet|rust|php|ruby|project_self, version: as written, qualifier: min|exact}`.
  - "3.11+", "≥3.11" and "oldest supported 3.11" are `min`; "Node 20" and "php 8.4.13" are `exact`. `max` and `range` are rare and dropped in v1.
- **Sources** (curated in `configs/wp2_version_sources.yaml`):

| Subject | Sources |
|---|---|
| python | pyproject `requires-python`, poetry `python`, setup.py/setup.cfg `python_requires`, `.python-version`, Pipfile `python_version` |
| node | `engines.node`, `.nvmrc`, `.node-version`, `volta.node`, `.tool-versions` |
| go | `go.mod` `go`/`toolchain` |
| java | pom `maven.compiler.release/source`, `java.version`, gradle toolchain / `VERSION_n` |
| dotnet | csproj `TargetFramework(s)`, `global.json` |
| rust | `rust-toolchain(.toml)`, Cargo `rust-version` |
| php | composer `require.php`, `config.platform.php` |
| ruby | `.ruby-version`, Gemfile `ruby`, gemspec |
| project_self | root package.json / pyproject / setup.cfg / nbdev `settings.ini` / Cargo / composer / `VERSION` file / csproj; if none exist, the latest tag ≤ S |

- **Measures:**
  - Version code = M·10^9 + m·10^6 + p·10^3 + b (xsd:integer).
  - Both sides are truncated to the claim's precision (the number of components written). This is a precision rule, not a threshold.
  - One **evidence individual per source** (`VersionEvidence`) carries `versionLowerDelta` (declaredLower − claimed), `versionUpperDelta` (asserted only if bounded), `versionUpperUnboundedCount`, and the context strings `versionSourcePath`/`versionSourceRaw`.
  - The claim has `evidenceFor` links, a closure `hasEvidence only {e1…en}`, and `versionSourceCount`.
- **Evidence classes:**
  - Min claims: `AgreeingVersionEvidence ⊒ (∃evidenceFor.MinVersionClaim ⊓ lowerDelta[=0])`.
  - Exact claims: `AgreeingVersionEvidence ⊒ (∃evidenceFor.ExactVersionClaim ⊓ lowerDelta[<=0] ⊓ (UpperOK ⊔ Unbounded))`.
  - `DisagreeingVersionEvidence` uses the named positive complements. Both have a Horn subclass into `NonDisagreeing` / `NonAgreeing`.
  - project_self sources are pinned, so lower = upper.
- **Claim classes:**

| Leaf class | Definition | Verdict |
|---|---|---|
| `VersionConfirmed` | `∃hasEvidence.Agreeing ⊓ ∀hasEvidence.NonDisagreeing` | Supported |
| `VersionContradicted` | `∃hasEvidence.Disagreeing ⊓ ∀hasEvidence.NonAgreeing` | Contradicted |
| `VersionSourcesConflict` | `∃Agreeing ⊓ ∃Disagreeing` | Conflicted |
| `NoVersionSource` | `versionSourceCount[<=0]` | Unverifiable |

  Use a count rather than an empty `OneOf`.

### T7 (stretch). ImportConstraintClaim: "S must not import T"

- **Extraction:** `{type:"import_rule", subject: forbidden target (verbatim module/prefix or the literal token "relative"), scope?: path}`.
  - Grounding drops "Azure SDK"-style prose, so only literal targets survive (e.g. simstudio "never from subpaths of `@/components/emcn`", "never relative imports"; snowplow "not /src").
- **Measures:**
  - Regex import extraction for JS/TS (`import … from`, `require(`, `import(`) and `ast` for Python, over tracked source files inside the scope.
  - Properties: `importFilesScanned` and `forbiddenImportEdgeCount`.
- **Classes:**

| Leaf class | Definition | Verdict |
|---|---|---|
| `ImportRuleViolated` | `forbiddenImportEdgeCount[>= wp2_import_violation_min_edges]` (1; sensitivity 3, 5) | Contradicted |
| `ImportRuleHeld` | `forbidden[<=0] ⊓ scanned[>=1]` | Supported |
| Gap band | between the two | Indeterminate |

- Expected n is below 10. Report T7 as case studies, not as prevalence.

### T8 (deferred). ProjectStageClaim

"Maintenance mode" or "no longer maintained" would be contradicted by WP1's `GrowthStage`, and "actively developed" by `DeclineStage`. The rule is `∃claimAboutProject.GrowthStage` and similar. This is the best showcase of chaining with WP1, but `populate.py` mines from `now()` (`:158`) with no end date, and the WP1 worktree is active. Add it only if WP1 gains `--until`.

---

## 4. Ontology module `seo-claims.owl`

**Build hook.** Keep WP2 code out of the WP1 hot spots: there is a locked WP1 worktree, `agent-aac9f99228e6ed8ae`.
- New file `ontology/modules/claims_module.py`, exposing `CLAIM_PROPERTIES` and `build_claims_module(entities_onto, rules)`.
- It reuses `_Rules` (via `rules.fork()`, with `kinds` extended by `CLAIM_PROPERTIES`), `_onto`, `_ns` and `_save`.
- `build_all` gets a three-line call to it, `"seo-claims"` is appended to `MODULE_NAMES`, and `lint_ontology` covers it automatically. The lint already enforces named operands and no `xsd:pattern`.
- The module imports `seo-entities` only. It must not import `seo-inference`, so the WP1 labels and their timings are unchanged.

**TBox content:**
- Classes: `ManifestDocument`, `ManifestClaim`, and asserted claim-type subclasses (T1 to T7 plus the subtypes named in Section 3). Also `ClaimEvidence`/`VersionEvidence`, `CheckedClaim`, the leaf classes, the five verdict classes plus `AllDisjoint`, `ManifestWithContradiction`, `DriftedClaim` and `BornWrongClaim`.
- Object properties: `makesClaim`, `hasEvidence`/`evidenceFor` (inverse), `introducedAs`.
- Data properties: integer for counts and deltas, decimal for ratios, string for context. All are Functional except context strings. Domain codes `CL` (claim), `E` (evidence) and `D` (document) are added in `CLAIM_PROPERTIES`.
- Every leaf class gets `explanationTemplate` and `thresholdId`/`thresholdSource` through `_Rules._annotate`.

**ABox writer.** Extend `ontology/reasoning/abox.py` with `manifest()`, `claim()`, `evidence()` and `close_evidence()`, reusing the `_close` pattern. `property_kinds()` must merge `CLAIM_PROPERTIES`. IRIs:
- `data/manifest/{repo}`
- `data/claim/{repo}/{sha1(claimKey)[:12]}`
- `…/intro` for the introduction-commit copy.

**Reasoner:**
- Add `CLAIMS_MODULES = ["seo-entities", "seo-claims"]` and `"seo-claims"` to `LABEL_MODULES` in `ontology/reasoning/reasoner.py`. This is harmless for WP1 ABoxes.
- Verdicts come from `HermitReasoner(modules=CLAIMS_MODULES).infer(abox)`, one ABox per manifest (about 20 to 150 claims), roughly 2 to 3 s each including the JVM.
- As a cross-check, also run Pellet realization once over all manifests and report verdict agreement with HermiT, as in WP1.
- Explanations: run `explain.explain_instance` (Pellet CLI, `--max 1`) for every `ContradictedClaim`, `ConflictedClaim` and `IndeterminateClaim`, plus 30 random Supported claims. Use `merged_rdfxml` over the claims modules only (small TBox, which avoids the Pellet instability WP1 hit). At about 1.8 s per call and an expected few hundred calls, this takes about 10 minutes.

**WP1 pitfalls checklist:**
- (a) Integer facets on count/delta properties, decimal facets on ratios. `fmt_decimal`/`literal` already handle typing.
- (b) Every union and complement operand is named. The verdict unions are Horn subclasses.
- (c) No `xsd:pattern`, and no SWRL at all in `seo-claims`.
- (d) Per-manifest ABoxes; HermiT for labels.
- (e) Single `seo#` namespace.

**Self-test.** `wp2_consistency.py selftest` builds one synthetic claim per leaf class, including exact boundary values (e.g. commits = 1, 4, 5 under the default thresholds). It asserts the expected verdict and that the ABox is consistent. A second check loads the TBox *without* `seo-claims` and asserts that zero verdict triples appear (the WP1 "done" test).

---

## 5. Claim extraction (LLM step, validated mechanically)

### 5.1 Models

Use **nvidia/nemotron-3-super-120b-a12b** (NVIDIA, key 2), **openai/gpt-oss-20b** (OpenAI open-weight, key 5) and **google/diffusiongemma-26b-a4b-it** (Google, key 4). Reasons:
- three vendors and three architectures (MoE, dense open-weight, diffusion), so errors are less correlated;
- the three fastest models in the 2026-10-06 probe (median about 5, 6 and 1.6 s against 98 to 217 s for Llama-3.2-90B and about 137 s for GLM-5.3);
- each has its own API key, so rate limits do not interact (Meta and Z.ai share `NVIDIA_API_KEY`);
- all passed the JSON probe.

Known quirks to handle in the parser:
- diffusiongemma fences JSON in ```` ```json ```` and returns empty text on trivial prompts;
- nemotron may emit `<think>` blocks;
- gpt-oss-20b is small, so the recall risk is measured by the regex check in 5.4.

**Pre-declared substitution:** if a model has more than 10% unparseable responses after retries on the first 20 chunks, replace it with `meta/llama-3.2-11b-vision-instruct` and report the swap.

**Optional robustness run:** run the two slow panel models on 20 random chunks (40 calls) and report whether consensus membership changes.

### 5.2 Prompt and output schema

- **Input:** the manifest is split at `#`/`##`/`###` headings into chunks of ≤ 6,000 characters (152 chunks over 80 manifests). Each line is prefixed with its global line number, `0123| `.
- **System prompt** (`configs/wp2_extraction_prompt.md`):
  - the seven type definitions with **synthetic** examples only (not corpus text, so no test items leak into the prompt);
  - the closed tool and runtime vocabularies;
  - the four modes;
  - "only statements a script could check against repository files or git history";
  - "copy `quote` and `subject` verbatim; never paraphrase; never compose a path except from a tree diagram, in which case list `path_components`";
  - "return `{"claims": []}` if none".
- **Settings:** temperature 0, `max_tokens` 6000 (tree-heavy chunks can hold 40+ paths).
- **Output** (validated with pydantic):

```json
{"claims": [{"type": "path_exists|path_status|tool_used|dependency|command|version|import_rule",
  "quote": "verbatim ≤200 chars", "line": 123, "subject": "verbatim",
  "path_components": ["features/", "support/"],
  "mode": "asserts_existing|to_be_created|example|negated",
  "status": "legacy|deprecated|frozen|stable|generated|do_not_edit",
  "tool_category": "test_framework|package_manager|build_tool|linter_formatter",
  "runner": "npm|pnpm|yarn|bun|make|composer",
  "ecosystem_hint": "npm|pypi|composer|go|cargo|maven|nuget|gem",
  "version": "as written", "qualifier": "min|exact", "scope": "path"}]}
```

### 5.3 Mechanical validation (applied per model, before consensus)

1. **Parse:** strip fences and `<think>…</think>`, take the outermost `{…}`, and validate the schema. Failures are retried twice with a "return only JSON" repair suffix, then logged as a parse failure.
2. **Span grounding:**
   - strip `^\d{4}\| ` prefixes from the quote;
   - normalize both quote and chunk (NFKC, smart quotes to ASCII, collapse whitespace, remove `` ` `` `*` `_`);
   - the quote must be a substring of the chunk, otherwise the claim is rejected as `ungrounded` (this is the per-model hallucination rate);
   - the subject must be a substring of the quote (case-sensitive for paths and scripts, case-insensitive for vocabulary items);
   - for tree diagrams, each `path_components` element must occur in the chunk;
   - `line` is corrected to the actual line if it is off by more than 3.
3. **Normalization and shape filters** per type (Section 3). Rejections are counted by reason.
4. **Canonical key:**

| Type | Key |
|---|---|
| T1 | `(T1, norm_path)` |
| T2 | `(T2, norm_path, inactive|protected)` |
| T3 | `(T3, category, canonical_tool)` |
| T4 | `(T4, norm_name, major or ∅)` |
| T5 | `(T5, script|make|composer, target)` |
| T6 | `(T6, subject, version_code@precision)` |
| T7 | `(T7, target, scope)` |

   - Occurrences are deduplicated per manifest; the unit of analysis is a unique (manifest, key).
   - **Merge rule:** within a manifest, T1/T2 keys whose paths are "/"-suffix-related and grounded on the same line are merged into the form with the most model votes (tie goes to the longest).
   - Non-key attributes (mode, status, qualifier) take the majority among the extracting models. A tie goes to the more conservative value: `example` beats `asserts_existing`.

### 5.4 Agreement and consensus

- **Pairwise F1** for each model pair: `2|A∩B|/(|A|+|B|)`, micro-averaged over manifests, per type and overall. This metric does not depend on how units are constructed.
- **Krippendorff's α** (nominal, `krippendorff` package installed): units are the union of keys per manifest, and each model codes presence 1/0. Also compute α for `mode`, `status` and `qualifier` over units extracted by all three. Use a manifest-level bootstrap CI (1,000 resamples).
  - State the caveat: union-based presence coding approximates unitizing α_u and is deflated by singletons. That is why F1 is reported alongside it.
- **Consensus:** `extractionVotes` is asserted (1 to 3). `CheckedClaim` requires `wp2_consensus_min_votes` = 2 (sensitivity 1 and 3, by TBox rebuild).
  - Headline robustness check: contradiction rates under 1/3, 2/3 and 3/3, and under "all three agree on mode".
- **Regex recall check (mechanical recall bound):** a deterministic extractor finds T5 candidates (`(npm|pnpm|yarn|bun) (run )?X`, `make X`, `composer run X` in code spans) and T1 candidates (backticked tokens containing `/` or a known extension). Report the share of regex candidates captured by consensus. Misses that the LLM tagged `example` or `to_be_created` are reported separately.
- **Cue-word check on mode:** the share of Contradicted T1 claims whose quote contains `create|add a new|will|should be|e.g.|example`. This is a mechanical upper bound on mode errors.

---

## 6. Re-check, triangulation, drift, and metrics

### 6.1 Deterministic re-check (precision of the reasoner verdicts)

- `wp2/recheck.py` is an independent re-implementation. It must **not import** `wp2/measure.py` or `wp2/depparse.py` (enforce this with a test that inspects imports). It derives a verdict with plain `if` logic from the threshold register:
  - T1 uses `git cat-file -e S:path`, `git ls-tree S -- path` and `git log --diff-filter=D`;
  - T5 uses `json.loads(git show S:package.json)` and its own make-target parser;
  - T4 and T6 use `packaging` (PyPI) and a separately written semver range check;
  - T2 uses `git rev-list --count --since --until S -- path` and `git diff --shortstat`.
- **Output:** a 5×5 verdict confusion matrix (reasoner against re-check), per-type agreement, Cohen's κ, the **precision of `ContradictedClaim`** (share that the re-check also calls Contradicted), and a list of every disagreement with a cause (encoding bug, measurement bug, or boundary rounding).
- **Paper wording:** this measures *encoding fidelity* (the reasoner decides exactly what the rules state). It is not construct validity, which is what 6.2 addresses.

### 6.2 Second-instrument triangulation (mechanical, no humans)

| Type | Instrument | Check |
|---|---|---|
| T1 | GitHub Contents API `GET /repos/{o}/{r}/contents/{path}?ref=S` | All Contradicted T1 plus 50 random Supported T1. Report 200/404 agreement |
| T2 | GitHub `commits?path=&since=&until=S` | Contradicted plus Indeterminate T2: compare counts |
| T5 | `.github/workflows/*.yml` and other CI configs at S | A CI file invoking the missing script flags a possible false contradiction (or broken CI) |
| T3/T4 | `git grep -w -c name S -- ':!*.md'` | Zero hits corroborate the contradiction; non-zero hits flag a signature gap. Report the share as an upper bound on false contradictions |
| T6 | Re-parse with an alternative parser | `packaging` vs the custom parser |

### 6.3 Drift origin ("does history contradict, or was it never true?")

- For each Contradicted or Supported claim of T1, T3, T4, T5 and T6, find the introduction commit I: `git log -S "<quote line>" --reverse -- manifest_path`, the first-parent commit where the quote's line appears.
- Re-measure the claim at I, assert it as `claim/…/intro`, link it with `introducedAs`, and reason.
- `DriftedClaim` gives "true when written, false at S". For drifted claims, also record the commit that made it false: the first commit between I and S where the measurement flips (deleting commit, script removal).
- Report the shares of drifted and born-wrong claims per type, and the median days from becoming false to S (an "unnoticed staleness" duration).
- **Cost:** about one extra measurement per claim. If I cannot be found (quote reformatted), record `intro_unresolved`.

### 6.4 Metrics (all in `report.json`, with manifest-level bootstrap CIs, 10,000 resamples)

- **Flow table:** 80 manifests → cloneable → snapshot resolved → with ≥1 checked claim. Claims: extracted per model → grounded → shape-valid → consensus → `asserts_existing` → checked → measured.
- **Prevalence:** checked claims per manifest by type (median and IQR); percent of manifests with ≥1 claim of each type.
- **Verdict distribution per type**, with subtypes (PathRemoved vs PathNeverExisted, ScriptUndefined vs ScriptHostMissing, …).
- **Contradiction rate per manifest:** Contradicted / (Supported + Contradicted + Conflicted), as a distribution; percent of manifests that are `ManifestWithContradiction`.
  - Breakdowns by manifest type (CLAUDE.md / AGENTS.md / copilot / cline), language, and manifest age at S.
  - Exploratory Spearman between days since the manifest was last modified and contradiction rate.
  - Optional covariate: the JCSSE section category of the containing section, from the existing `*_classification.json` headings.
- **Reasoner vs re-check:** confusion matrix, precision of Contradicted, κ. HermiT vs Pellet verdict agreement.
- **Triangulation:** corroboration rates. Drift shares.
- **Extraction agreement** (5.4): per-model parse and grounding failure rates, pairwise F1, α, consensus counts, regex recall.
- **Threshold sensitivity:** T2 verdict counts over the grid (window × min_commits × min_lines × support_max), and the consensus 1/2/3 sweep. Both are TBox rebuilds that re-reason unchanged ABoxes (`build_all(thresholds_path=…, out_dir=…)`).
- **Timings:** extraction wall time, measurement, HermiT per manifest, explanation calls.

---

## 7. Corpus, snapshot and inclusion

**Corpus:** all 80 JCSSE 2026 repositories, with the same cached manifest texts.

**Overlap statement (for the paper):**
- JCSSE 2026 used these 80 manifests for *section-level topic classification* (6 categories, 3-LLM vote; 73.8% lack evolution context).
- 23 of the 80 are the JSS-era Paper 1 repos. There is no overlap with the WP3 120-repo ground truth (checked).
- **New in WP2:**
  - statement-level verifiable claims;
  - snapshot commits;
  - repository measurements at S and over history;
  - reasoner verdicts with justifications;
  - re-check, triangulation and drift.
- The JCSSE NIM models are retired, and the extraction panel is new.
- Keep clear of the IST plan's RQ4 (manifest category trajectories over history). WP2 uses manifest history only to date when each claim was introduced.

**Snapshot resolution (`wp2/snapshot.py`):**
- Clone with `git clone --filter=blob:none --no-checkout --single-branch -b <default_branch>` into `data/raw/repos/wp2/{owner__name}` (already gitignored). Never use `populate.clone_repo`, which runs `pull`.
- Upper bound T_upper is the date the corpus JSON was committed: **2026-03-18T13:34:47+07:00** for the 23 phase1 repos (`8951fe8`) and **2026-03-19T18:42:00+07:00** for the 57 new ones (`5ab006f`).
- **Manifest path:** use `manifest_path` if present. Otherwise try `CLAUDE.md`, `.claude/CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`.
- **Rule:** S = the newest first-parent commit c ≤ T_upper such that `git show c:path`, with CRLF normalized and stripped, equals the cached text stripped.
  - Implementation: walk `git rev-list --first-parent --before=T_upper HEAD -- path` (manifest-changing commits) to find the newest matching version V. Then S = the newest first-parent commit ≤ T_upper that comes before the next manifest change after V.
  - Record `snapshot_status`: `exact_at_T_upper`, `version_match` (the manifest changed again before T_upper), or `no_match`.
- **The manifest and the repo are checked at the same commit S.** History windows end at S. The current HEAD (2026-10) is not used in the primary analysis.
  - Optional exploratory extension: re-check claims that are still present at HEAD, to measure decay over six months.

**Inclusion rules:**
- Repo level:
  - I1: the repo can be cloned on the run date (record deleted or private repos).
  - I2: `snapshot_status ≠ no_match`.
  - I3: the manifest is at a fixed repo path.
  - Template-like manifests (e.g. cypress's generic "Workflow Orchestration" file) are kept and counted as manifests with zero checkable claims.
- Claim level:
  - consensus;
  - grounded;
  - shape-valid;
  - mode `asserts_existing`;
  - not the manifest's own path;
  - T2 protected claims and all T7 claims excluded from headline rates.
- Report every exclusion by reason. Chinese and other non-English manifests (e.g. VCnoC, huangwb8) are kept; grounding is language-agnostic. Report the language of each manifest.

---

## 8. Files, outputs, budget, checkpointing, day plan

**Code (worktree; minimal edits to shared files):**

| File | Change |
|---|---|
| `ontology/modules/claims_module.py` (new) | `CLAIM_PROPERTIES`, `build_claims_module` |
| `ontology/modules/build_ontology.py` | Three-line hook in `build_all`; `"seo-claims"` added to `MODULE_NAMES` |
| `ontology/modules/thresholds.yaml` | `wp2_*` entries (Section 3), `group: wp2` |
| `ontology/reasoning/abox.py` | `manifest`, `claim`, `evidence`, `close_evidence`; merged `property_kinds` |
| `ontology/reasoning/reasoner.py` | `CLAIMS_MODULES`; `"seo-claims"` in `LABEL_MODULES` |
| `experiments/paper1_ontology_manifests/wp2_consistency.py` (new) | CLI subcommands: `selftest`, `snapshot`, `extract`, `consensus`, `measure`, `reason`, `explain`, `recheck`, `triangulate`, `drift`, `report`, `all` |
| `experiments/paper1_ontology_manifests/wp2/` (new) | `snapshot.py`, `extract.py` (NIM via `shared/llm_judge/nim_registry.load_panel/make_client`), `normalize.py`, `consensus.py`, `measure.py`, `depparse.py`, `recheck.py` (no imports from measure/depparse), `report.py` |
| `experiments/paper1_ontology_manifests/configs/` | `wp2_consistency.yaml` (paths, T_upper values, models, chunk size, concurrency, seeds), `wp2_tool_signatures.yaml`, `wp2_version_sources.yaml`, `wp2_extraction_prompt.md` |

**Outputs** go to `experiments/paper1_ontology_manifests/results/real_v2/wp2/`:
- `snapshots/{repo}.json`
- `extraction/raw/{repo}/{chunk:03d}.{model_slug}.json`, holding the raw text, `usage`, latency, `prompt_sha256` and model id
- `extraction/validated.jsonl`
- `claims/consensus.jsonl`
- `agreement.json`
- `measurements/{repo}.json`
- `abox/{repo}.nt`
- `verdicts/{repo}.json` (HermiT labels plus tbox sha256)
- `explanations/{repo}.json`
- `recheck.json`, `triangulation.json`, `drift.json`, `sensitivity.json`, `timings.json`, `report.json`

Commit these with force-add, per CLAUDE.md. Fuseki is optional (`--fuseki` puts `urn:senso:claims:{repo}` graphs); the local files are the source of truth.

**Checkpointing.** Each unit is skipped if its output exists with matching input hashes: prompt sha for extraction, snapshot sha plus claims sha for measurement, tbox sha plus abox sha for verdicts. The NIM loop runs as a background Bash job: 2 concurrent requests per model (separate keys), exponential backoff on 429/5xx, 120 s timeout, 3 attempts.

**Budget:**

| Item | Estimate |
|---|---|
| NIM extraction | 152 × 3 = 456 calls, about 500 with retries and repairs; ≈2.6M input and 0.6M output tokens; 30 to 60 min wall time |
| Optional slow-model check | +40 calls, about 1.5 h |
| GitHub REST | < 1,000 calls (triangulation only), well within 5,000/h |
| Disk | Blobless clones, a few GB; check `df` first (cypress, dotnet/macios, apache/skywalking and getsentry/sentry-docs are large) |
| HermiT | About 80 × 3 s, plus the drift pass |
| Pellet explain | A few hundred × 1.8 s |
| Sensitivity sweep | 3 × 3 × 3 × 3 T2 grid + 3 consensus levels = 84 TBox builds × 80 manifests × about 3 s ≈ 5.5 h. **Run in the background, or shrink the grid** to one-at-a-time variation (3 + 2 × 4 = 11 builds, about 45 min). Recommended: one-at-a-time for the paper, full grid optional |

**Day plan (one Sonnet agent):**
1. **h0 to h1:**
   - commit the thresholds, taxonomy configs and prompt (timestamped, before any extraction);
   - start snapshot resolution and cloning in the background;
   - write `claims_module.py` and the self-test.
2. **h1 to h2:** `extract.py` with parsing and grounding; dry run on 3 manifests; then launch the full extraction in the background.
3. **h2 to h4:** `measure.py` and `depparse.py`, with T1, T5, T3, T4, T6 and T2 in that priority order. ABox writer and HermiT verdicts on the manifests that have finished.
4. **h4 to h5:** `consensus.py` (keys, merge rule, F1, α, regex recall); `recheck.py`.
5. **h5 to h6:** triangulation, drift and explanations.
6. **h6 to h7:** `report.py`, one-at-a-time sensitivity, README notes. T7 only if time remains.

**Done when:**
- the self-test passes for every leaf class, and removing `seo-claims` makes every verdict disappear;
- `recheck.py` imports nothing from `measure.py`/`depparse.py`;
- every Contradicted claim has a Pellet justification, or a logged explanation error;
- `report.json` reproduces every number in the flow table.

---

## 9. Risks and open decisions

- **T2 construct validity** ("legacy" is not "frozen"). Mitigated by the gap band, the sensitivity grid and subtype reporting. If T2 n is small (about 14 repos mention legacy or deprecated), present it descriptively.
- **Signature or alias gaps produce false contradictions in T3/T4.** Mitigated by the closed vocabulary, the identifier-shape filter, the conservative `Unverifiable` when no ecosystem anchor exists, and the `git grep` bound.
- **Mode errors** (an example path taken as an assertion). Bounded by mode α, the cue-word check and the "all three agree on mode" sensitivity.
- **Snapshot `no_match`** if repos force-pushed or deleted the file. Report the count. Do not substitute HEAD.
- **Shared-file edits** (`build_ontology.py`, `abox.py`, `reasoner.py`) can conflict with the active WP1 worktree. Keep the hooks to a few lines and merge after WP1.
- **Decision needed:** whether to keep "ScriptHostMissing" and "PathNeverExisted" in the headline contradiction rate (they are typical of template manifests copied from another repo), or to report them as a separate "foreign manifest" category.
- **How this answers R2 (D3):**
  - the only LLM step proposes text spans;
  - every surviving claim is verbatim in the manifest and has support from models of at least two vendors;
  - every verdict is an OWL entailment over measured repository facts, with a machine justification;
  - verdict fidelity is measured against an independent deterministic re-check, and construct validity is bounded by a second instrument.

  No human or LLM judges truth at any point.

### Critical Files for Implementation
- /home/adtgrade/research/senso-framework/ontology/modules/build_ontology.py (the `_Rules` DSL, `build_all`, `lint_ontology`, `MEASURED_PROPERTIES` pattern)
- /home/adtgrade/research/senso-framework/ontology/reasoning/reasoner.py (`HermitReasoner`, `LABEL_MODULES`, `infer`)
- /home/adtgrade/research/senso-framework/ontology/reasoning/abox.py (`AboxWriter`, `property_kinds`, the `_close` closure pattern)
- /home/adtgrade/research/senso-framework/ontology/reasoning/explain.py (`explain_instance`, `merged_rdfxml`)
- /home/adtgrade/research/senso-framework/experiments/jcsse2026/results/expanded_corpus.json (manifest texts, `manifest_path`, `default_branch`)
- /home/adtgrade/research/senso-framework/shared/llm_judge/nim_registry.py and /home/adtgrade/research/senso-framework/shared/llm_judge/nim_models_v2.yaml (panel and keys)
- /home/adtgrade/research/senso-framework/ontology/modules/thresholds.yaml (add the `wp2_*` register)

## 10. Main-session decisions (2026-10-06)

- ScriptHostMissing and PathNeverExisted stay in the headline contradiction rate (an agent following the claim fails either way); they are also reported as a separate "foreign manifest" breakdown, with a sensitivity rate excluding them.
- Sensitivity: one-at-a-time variation is primary (11 TBox builds); the full grid is optional.
- T8 (project-stage claims) is in scope only if the v2 population pipeline (snapshot-anchored) is merged in time; otherwise deferred.
