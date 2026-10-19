## Repository context

The following contributor guidance is taken from the repository at the task's base commit.

### CONTRIBUTING.md

# Contributing to pyQuil

Welcome to pyQuil, and thanks for wanting to be a contributor! 🎉

This guide is to help walk you through how to open issues and pull requests for the pyQuil
project, as well as share some general how-tos for development, testing, and maintenance.

If all you want to do is ask a question, you should do so in our
[Rigetti Forest Slack Workspace][slack-invite] rather than opening an issue. Otherwise,
read on to learn more!

This project and everyone participating in it are governed by pyQuil's
[Code of Conduct](.github/CODE_OF_CONDUCT.md). In contributing, you are expected
to uphold this code. Please report unacceptable behavior by contacting support@rigetti.com.

## Table of Contents

[Ways to Contribute](#ways-to-contribute)

- [Reporting a Bug](#reporting-a-bug)

- [Requesting an Enhancement](#requesting-an-enhancement)

- [Choosing an Issue to Address](#choosing-an-issue-to-address)

- [Making a Pull Request](#making-a-pull-request)

- [Adding a Tutorial Notebook](#adding-a-tutorial-notebook)

[Developer How-Tos](#developer-how-tos)

- [Install Dependencies](#install-dependencies)

- [Style Guidelines](#style-guidelines)

- [Running the Tests](#running-the-tests)

- [Building the Docs](#building-the-docs)

- [Working with the Parser](#working-with-the-parser)

- [Using the Docker Image](#using-the-docker-image)

[Tips for Maintainers](#tips-for-maintainers)

- [Merging a Pull Request](#merging-a-pull-request)

- [Managing the CI Pipelines](#managing-the-ci-pipelines)

- [Release Process](#release-process)

- [Issue and PR Labels](#issue-and-pr-labels)

## Ways to Contribute

### Reporting a Bug

If you've encountered an error or unexpected behavior when using pyQuil, please file a
[bug report](https://github.com/rigetti/pyquil/issues/new?assignees=&labels=bug+%3Abug%3A&template=BUG_REPORT.md&title=).
Make sure to fill out the sections that allow us to reproduce the issue and understand
the context of your development environment. We welcome the opportunity to improve pyQuil,
so don't be shy if you think you've found a problem!

### Requesting an Enhancement

If you have an idea for a new addition to pyQuil, please let us know by creating a
[feature request](https://github.com/rigetti/pyquil/issues/new?assignees=&labels=enhancement+%3Asparkles%3A&template=FEATURE_REQUEST.md&title=).
The more information you can provide, the easier it will be for the pyQuil developers
to implement! A clear description of the problem being addressed, a potential solution,
and any alternatives you've considered are all great things to include.

### Choosing an Issue to Address

Rather than opening an issue, if you'd like to work on one that currently exists, we
have some issue labels that make it easy to figure out where to start. The
[good first issue][good-first-issue-label] label references issues that we think a
newcomer wouldn't have too much trouble taking on. In addition, the
[help wanted][help-wanted-label] label is for issues that the team would like to
see completed, but that we don't currently have the bandwidth for.

### Making a Pull Request

Once you've selected an issue to tackle, [forked the repository](https://github.com/rigetti/pyquil/fork), and made your changes, the next step is to [open a pull request](https://github.com/rigetti/pyquil/compare)! We've made opening one easy by providing a [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) that includes a checklist of things to complete before asking for code review. Additionally, all CI checks must pass before the PR will be merged. We look forward to reviewing your work! 🙂

### Adding a Tutorial Notebook

You may have noticed that the `examples` directory has been removed from pyQuil, and a
"launch binder" badge was added to the README. We decided to move all the example notebooks
into a separate repository, [rigetti/forest-tutorials][forest-tutorials], so that they could
be run on [Binder][mybinder], which provides a web-based setup-free execution environment
for [Jupyter][jupyter] notebooks. We're always looking for new tutorials to help people
learn about quantum programming, so if you'd like to contribute one, make a pull request
to that repository directly!

## Developer How-Tos

### Install Dependencies

Before running any of the below commands, you'll need to install [Poetry][poetry] and run the
following from the top-level directory of this repo:

```bash
poetry install
```

[poetry]: https://python-poetry.org

### Style Guidelines

We use [Black](https://black.readthedocs.io/en/stable/index.html) and `flake8` to automatically
lint the code and enforce style requirements as part of the CI pipeline. You can run these style
tests yourself locally by running `make check-style` (to check for violations of the `flake8` rules)
and `make check-format` (to see if `black` would reformat the code) in the top-level directory of
the repository. If you aren't presented with any errors, then that means your code is good enough
for the linter (`flake8`) and formatter (`black`). If `make check-format` fails, it will present
you with a diff, which you can resolve by running `make format`. Black is very opinionated, but
saves a lot of time by removing the need for style nitpicks in PR review. We only deviate from its
default behavior in one category: we choose to use a line length of 100 rather than the Black
default of 88 (this is configured in the [`pyproject.toml`](pyproject.toml) file). As for `flake8`,
we ignore a couple of its rules (all for good reasons), and the specific configuration can be
found in the [`.flake8`](.flake8) file.

In addition to linting and formatting, we use type hints for all parameters and return values,
following the [PEP 484 syntax][pep-484]. This is enforced as part of the CI via the command
`make check-types`, which uses the popular static typechecker [mypy](http://mypy-lang.org/).
For more information on the specific configuration of `mypy` that we use for typechecking, please
refer to the [`mypy.ini`](mypy.ini) file. Also, because we use the `typing` module, types (e.g.
`type` and `rtype` entries) should be omitted when writing (useful) [Sphinx-style][sphinx]
docstrings for classes, methods, and functions.

All of these style-related tests can be performed locally with a single command, by running the
following:

```bash
make check-all
```

### Running the Tests

We use `pytest` to run the pyQuil unit tests. These are run automatically on Python 3.7 and
3.8 as part of the CI pipeline, but you can run them yourself locally as well. Many of the
tests depend on having running QVM and quilc servers. To start them, run each of the following
in a separate terminal window:

```bash
docker run --rm -it -p 5555:5555 rigetti/quilc -R -P
```

```bash
docker run --rm -it -p 5000:5000 rigetti/qvm -S
```

> **Note:** The above commands require [Docker][docker], but you can also download the QVM and
> quilc as part of the [Forest SDK][forest], and run them directly with `qvm -S` and
> `quilc -R -P`, respectively.

Once the QVM and quilc servers are running, you can run all the unit/integration tests with:

```bash
make test
```

To skip [slow tests](#slow-tests), you may run:

```bash
make test-fast
```

You can run end-to-end tests with:

```bash
make e2e TEST_QUANTUM_PROCESSOR=<quantum processor ID>
```

Or you may run all tests (unit/integration/e2e) with:

```bash
make test-all TEST_QUANTUM_PROCESSOR=<quantum processor ID>
```

> **Note:** for `TEST_QUANTUM_PROCESSOR`, supply a value similar to what you would supply to
> `get_qc()`. End-to-end tests are most useful against a real QPU, but they can also be run
> against a QVM (e.g. `make e2e TEST_QUANTUM_PROCESSOR=2q-qvm`).

#### Slow Tests

Some tests (particularly those related to operator estimation and readout symmetrization)
[truncated]