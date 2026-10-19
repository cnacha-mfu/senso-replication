# Third-party content

This package contains material that the authors did not write. It stays under
its original licence and is included only so that readers can verify the
reported numbers.

- **Agent trajectories and patches** (`results/real_v2/*/trajectories/`, `*/patches/`).
  These record what coding agents read and wrote while working on issues from
  public GitHub repositories. They contain source code, issue text and test
  output from those repositories. Each repository's own licence applies to that text.
- **Manifests copied from public repositories** (for example the `CLAUDE.md`,
  `AGENTS.md` and similar files stored under `results/real_v2/`). They are the
  work of the repository authors and keep their original licences.
- **SWE-rebench task data** (task definitions and instance metadata under
  `results/real_v2/wp5/` and `wp6/`). SWE-rebench and the underlying repositories keep
  their own licences and terms.
- **Python and Java dependencies** (listed in `requirements.txt` and
  `experiments/paper1_ontology_manifests/wp5/requirements.txt`) are not included;
  they are installed from their own sources under their own licences.

The MIT licence in `LICENSE` and the CC BY 4.0 licence in `LICENSE-DATA` apply
only to the authors' own content. If you are the owner of included third-party
content and want it removed, please open an issue.
