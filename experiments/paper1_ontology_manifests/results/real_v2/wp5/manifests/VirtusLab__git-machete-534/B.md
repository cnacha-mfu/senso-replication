## Repository context

The following contributor guidance is taken from the repository at the task's base commit.

### CONTRIBUTING.md

# Contributing

## PyCharm setup

Make sure the following bundled plugins are enabled:
* Docker
* Markdown
* Ini
* IntelliLang (for language injections, e.g. Markdown/shell scripts in YAML)
* ReStructuredText
* Shell script
* YAML

Optionally, you can also install the following non-bundled plugins from Marketplace:
* [AWK Support](https://plugins.jetbrains.com/plugin/17037-awk-support)
* [.ignore](https://plugins.jetbrains.com/plugin/7495--ignore)
* [NixIDEA](https://plugins.jetbrains.com/plugin/8607-nixidea)


## Run tests locally

To develop that project and run tests locally, it is needed to have Python installed with `tox`.

Use `tox -e venv` to setup virtual environment to work on that project in your favorite IDE.
Use `.tox/venv/bin/python` as a reference `python` interpreter in your IDE.

To run tests, execute `tox`.

It's also possible to execute tests graphically in pycharm (right-clicking on the test file
or clicking the green triangle on the left of the test case name), which can be very useful when debugging a single test case.
To do so, make sure that following libraries are installed (preferably via pip):
* pytest
* pytest-mock
* pytest-xdist

## Generate sandbox repositories

Run `docs/setup-sandbox` script to set up a test repo under `~/machete-sandbox` with a remote in `~/machete-sandbox-remote`.


## Command properties/classification

Deprecated commands are excluded.

| Property                                                          | Commands                                                                                                                                       |
| ----------------------------------------------------------------- | -----------------------------------------------------------------------------------------------------------------------------------------------|
| can accept interactive input on stdin                             | `add`, `advance`, `delete-unmanaged`, `discover`,`github`<sup>[1]</sup>, `go`, `traverse`, `update`                                            |
| can display status (and run `machete-status-branch` hook)         | `discover`, `github`<sup>[1]</sup>, `status`, `traverse`                                                                                       |
| can modify the .git/machete file                                  | `add`, `advance`, `anno`, `discover`, `edit`, `github`, `slide-out`, `traverse`                                                                |
| can modify the git repository (excluding .git/machete)            | `add`, `advance`, `delete-unmanaged`, `github`<sup>[1]</sup>, `go`, `reapply`, `slide-out`, `squash`, `traverse`, `update`                     |
| can run merge                                                     | `advance`<sup>[2]</sup>, `slide-out`, `traverse`, `update`                                                                                     |
| can run rebase (and run `machete-pre-rebase` hook)                | `reapply`<sup>[3]</sup>, `slide-out`, `traverse`, `update`                                                                                     |
| can slide out a branch (and run `machete-post-slide-out` hook)    | `advance`, `slide-out`, `traverse`                                                                                                             |
| expects no ongoing rebase/merge/cherry-pick/revert/am             | `advance`, `go`, `reapply`, `slide-out`, `squash`, `traverse`, `update`                                                                        |
| has stable output format across minor versions (plumbing command) | `file`, `fork-point`<sup>[4]</sup>, `is-managed`, `list`, `show`, `version`                                                                    |

[1]: `github` can only display status, accept interactive mode or modify git repository when `create-pr` or `checkout-prs` subcommand is passed.

[2]: `advance` can only run fast-forward merge (`git merge --ff-only`).

[3]: `reapply` can run rebase but can't run merge since merging a branch with its own fork point is a no-op and generally doesn't make much sense.

[4]: A stable output is only guaranteed for `fork-point` when invoked without any option or only with `--inferred` option.


## Versioning

This tool is [semantically versioned](https://semver.org) with respect to all of the following:

* Python and Git version compatibility
* command-line interface (commands and their options)
* format of its specific files (currently just `machete` file within git directory)
* hooks and their interface
* output format of plumbing commands (see above for the list)
* accepted environment variables

Output format of any non-plumbing command can change in non-backward-compatible manner even between patch-level updates.


## CI Docker setup reference

* [Nifty Docker tricks for your CI (vol. 1)](https://medium.com/virtuslab/nifty-docker-tricks-for-your-ci-vol-1-c4a36d2192ea)
* [Nifty Docker tricks for your CI (vol. 2)](https://medium.com/virtuslab/nifty-docker-tricks-for-your-ci-vol-2-c5191a67f1a4)


## FAQ's about Pull Requests
**What is the proper base for pull request?**

Please set the base of pull request to `develop` branch. Current branch protection rules on GitHub only allow to merge `develop` or `hotfix` branches into `master`.

**Who closes GitHub comments? Author of changes, reviewer or initiator of the conversation?**

It makes sense to close comment:

1) If the comment was trivial and was addressed as suggested by the reviewer, then it is enough for the PR author to simply `Resolve` the thread and that's it
2) If the comment was not trivial and/or for some reason the PR author believes that the comment should not be addressed as suggested by the reviewer, then it is best to leave the thread open after replying; then the reviewer can press `Resolve` once they have decided that the matter is cleared.

**Do you make squash before develop?**

Any technique is okay as long as there are [NO unnecessary merge commits](https://slides.com/plipski/git-machete#/8).
`Squash and merge` from GitHub is okay, fast-forward made from console or via `git machete advance` & `git push` is ok too.

**Is there any commit message convention?**

Nothing special, as long as they look neat in the sense that they are written in imperative form and describe what actually happened on a given commit.

**How do you know that the comment has been approved?**

As in the first point, if the PR author accepts the suggested comment without any additional comments, simply `Resolve` on GitHub will suffice. There is no need to reply things like "Accepted", "Done", etc as it just spams the reviewer's email.

**Can I resolve all comments in a single commit or each comment in an individual commit?**

Review fixes should be pushed on separate commits for easier viewing on GitHub (unlike in e.g. Gerrit's amend-based flow).


## Release TODO list

1. Create release PR from `develop` into `master`.

1. Verify that all checks have passed.

1. Merge develop into master and push to remote repository using console:

         git checkout develop
         git pull origin develop
         git checkout master
         git pull origin master
         git merge --no-ff develop
         git push origin master

1. Verify that the release has been created on [GitHub](https://github.com/VirtusLab/git-machete/releases)
   and that a `git-machete-<VERSION>-1.noarch.rpm` file is present under the Assets.

1. Verify that the latest version is uploaded to [PyPI](https://pypi.org/project/git-machete).

1. Verify that the latest commit in [VirtusLab/homebrew-git-machete](https://github.com/VirtusLab/homebrew-git-machete) tap repo refers to the latest version.

[truncated]