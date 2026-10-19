# WP2b report: do manifest errors get fixed?

Head fetched 2026-10-09 (single run). 1177 claims in 68 manifests (65 contradicted in 29, 1112 supported). All values are in `report.json`; this file only restates them.

## Outcomes

| verdict at S | U | G | R | P-C | P-S | P-O |
|---|---|---|---|---|---|---|
| contradicted | 0 | 0 | 10 | 52 | 3 | 0 |
| supported | 0 | 42 | 64 | 9 | 997 | 0 |

## A1 persistence of errors

52/65 contradicted claims persist (P-C): 0.800, Wilson 95% CI [0.69, 0.88], cluster-bootstrap CI [0.65, 0.93]. Wording: "most persist".

## A2 noticing (within manifest)

29 manifests have both kinds; removed: contradicted 10/65, supported 15/557. MH RR 3.5869200884268695 CI [1.59, 11.32]; MH RD 0.10248189587867962 CI [0.02, 0.20]. Wording: "contradicted claims are removed more often than other claims".

## Robustness (decision unchanged)

- Pooled RR: {'rr': 1.613933236574746, 'ci': [0.30844314460302136, 4.030103035771457], 'wording': 'no detectable difference; the study cannot exclude an RR of 0.31 or 4.03'}
- Regressions: {'n_obs': 1177, 'n_manifests': 68, 'conditional_logit_by_manifest': {'converged': True, 'log_odds': 2.2131789404273396, 'odds_ratio': 9.14474082142811, 'or_ci': [2.962591669655988, 28.689171184387614], 'p': 0.0239880059970015, 'n_boot_ok': 2000}, 'gee_exchangeable': {'converged': True, 'log_odds': 0.8600845867570157, 'odds_ratio': 2.3633605942595333, 'or_ci': [1.1302960259572665, 4.941602173438009], 'fallback_used': None, 'n_clusters': 68}}
- (c) edited manifests: A1 0.7105263157894737 [0.48, 0.91]; A2 RR 3.586920088426868 [1.62, 10.52]
- (d) excl. archived/non-ancestor: A1 0.7936507936507936; A2 RR 3.5869200884268686 [1.58, 10.92]
- (e) reasoner/re-check agree: A1 0.796875; A2 RR 3.5869200884268695 [1.59, 11.32]
- (f) removed = quote gone: RR 2.457694794434614 [1.20, 3.93]

## Exploratory (labelled as such in report.json)

- Forward drift: {'n_retained_supported': 1006, 'n_now_contradicted': 9, 'share': 0.008946322067594433, 'wilson_ci': [0.004713736433890305, 0.016914865392579432], 'claim_years': 460.28039223515094, 'per_claim_year': 0.019553298710586878}
- Removal: {'n_R': 74, 'n_removal_commit_found': 74, 'median_days_S_to_removal': 131.67652777777778, 'range': [1.715439814814815, 311.95016203703705], 'hunk_shape': {'replacement': 70, 'pure_deletion': 4}, 'agent_signal': {'None': 66, 'generic_agent': 3, 'claude_code': 5}, 'method': {'pickaxe': 70, 'scan': 4}, 'by_verdict': {'contradicted': 10, 'supported': 64}}
- Re-check agreement at H: {'n': 1061, 'agree': 1061, 'kappa': 1.0, 'n_disagree_contradicted': 0}
