## Repository context

The following contributor guidance is taken from the repository at the task's base commit.

### .github/CONTRIBUTING.md

# Contributing to CanvasAPI

Thanks for your interest in contributing!

Below you'll find guidelines for contributing that will keep our codebase clean and happy.

## Table of Contents

* [How can I contribute?](#how-can-i-contribute)
    * [Bug reports](#bug-reports)
    * [Resolving issues](#resolving-issues)
    * [Making your first contribution](#making-your-first-contribution)
        * [Setting up the environment](#setting-up-the-environment)
        * [Writing tests](#writing-tests)
            * [API Coverage Tests](#api-coverage-tests)
            * [Engine tests](#engine-tests)
        * [Running tests / coverage reports](#running-tests-coverage-reports)
        * [Making a Pull Request](#making-a-pull-request)
* [Code style guidelines](#code-style-guidelines)
    * [Foolish consistency](#foolish-consistency)
    * [Method docstrings](#method-docstrings)
        * [Descriptions](#descriptions)
        * [Links to related API endpoints](#links-to-related-api-endpoints)
        * [Parameters](#parameters)
        * [Returns](#returns)
        * [Docstring examples](#docstring-examples)

## How can I contribute?

### Bug Reports

Bug reports are awesome. Writing quality bug reports helps us identify issues and solve them even faster. You can submit bug reports directly to our [issue tracker](https://github.com/ucfopen/canvasapi/issues).

Here are a few things worth mentioning when making a report:

* What **version** of CanvasAPI are you running? (`pip show canvasapi`)
* What **version** of Python are you using? (`python --version`)
* What steps can be taken to **reproduce the issue**?
* **Detail matters.** Try not to be too be verbose, but generally the more information, the better!

### Resolving issues

We welcome pull requests for bug fixes and new features! Feel free to browse our open, unassigned issues and assign yourself to them. You can also filter by labels:

* [simple](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Asimple) -- easier issues to start working on; great for getting familiar with the codebase.
* [api coverage](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Aapi-coverage) -- covering new endpoints or updating existing ones.
* [enhancement](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Aenhancement) -- updates to the engine to improve performance or add new functionality.
* [major](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Amajor) -- difficult or major changes or additions that require familiarity with the library.
* [bug](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Abug) -- happy little code accidents.
* [fixed-in-develop](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Afixed-in-develop) -- issues that have been resolved but the changes are not in the latest release yet.
* [canvas-bug](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Acanvas-bug) -- confirmed to be an issue with the Canvas LMS rather than the CanvasAPI library.
* [help wanted](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3A"help%20wanted") -- we need *your* help to figure these out!
* [documentation](https://github.com/ucfopen/canvasapi/issues?q=sort%3Aid_desc-desc+is%3Aopen+label%3Adocumentation) -- issues relating to Documentation. Specifically, any of the `.md` files or our [class reference docs](http://canvasapi.readthedocs.io/en/latest/).

Once you've found an issue you're interested in tackling, take a look at our [first contribution tutorial](#making-your-first-contribution) for information on our pull request policy.

### Making your first contribution

#### Setting up the environment

Now that you've selected an issue to work on, you'll need to set up an environment for writing code. We'll assume you already have pip, virtualenv, and git installed and are using a terminal. If not, please set those up before continuing.

1. Clone our repository by executing `git clone git@github.com:ucfopen/canvasapi.git`
2. Checkout (`git checkout develop`) and then pull the latest commit from the develop branch: `git pull origin develop`
3. Create a new branch with the format **issue/[issue_number]-[issue-title]**: `git checkout -b issue/1-test-issue-for-documentation`
4. Set up a new virtual environment ( `virtualenv env` ) and activate it (`source env/bin/activate`)
5. Install the required dependencies with `pip install -r dev_requirements.txt`

From here, you can go about working on your issue you normally would. Please make sure to adhere to our [style guidelines for both code and docstrings](#code-style-guidelines). Once you're satisfied with the result, it's time to write a unit test for it.

#### Writing tests

Tests are a critical part of building applications, and we [pity the fool who doesn't write them](https://blog.codinghorror.com/i-pity-the-fool-who-doesnt-write-unit-tests/). Unit tests help us monitor the health of the code checked into the repository and they provide a nice overview at the progress we make. Due to the size and nature of the library, it's unrealistic for us to manually test each component. Because of this, we require pull requests to A) have tests associated with the changes being made and B) pass those and all other tests.

You'll notice our tests live in the creatively named `tests` directory. Within that directory, you'll see several files in the form `test_[class].py` and another directory named `fixtures`. Depending on the scope of the issue you're solving, you'll be writing two different kinds of tests.

##### API Coverage Tests

We use the [requests-mock](https://pypi.python.org/pypi/requests-mock) library to simulate API responses. Those mock responses live inside the `fixtures` directory in JSON files. Each file's name describes the endpoints that are contained within. For example, course endpoints live in `course.json`. These fixtures are loaded on demand in a given test. Let's look at `test_get_user` in `test_course.py` as an example:

```python
# get_user()
def test_get_user(self, m):
    register_uris({'course': ['get_user']}, m)

    user = self.course.get_user(1)

    self.assertIsInstance(user, User)
    self.assertTrue(hasattr(user, 'name'))
```

Breakdown:

```python
# get_user()
```

It is common to have multiple tests for a single method. All related tests should be grouped together under a single comment with the name of the method being tested.

---

```python
def test_get_user(self, m):
```

This is a standard Python `unittest` test method with one addition: the `m` variable is passed to all methods with names starting with `test`. `m` is a Mocker object that can be used to override the routing of HTTP requests.

---

```python
register_uris({'course': ['get_user']}, m)
```

The `register_uris` function tells a mocker object which fixtures to load. It takes in two arguments: a dictionary describing which fixtures to load, and a mocker object.  The dictionary keys represent which file the desired fixtures are located in. The values are lists containing each desired fixture from that particular file. The example above will register the `get_user` fixture in `course.json`.

Example Fixture:

```json
"get_user": {
    "method": "GET",
    "endpoint": "courses/1/users/1",
    "data": {
        "id": 1,
        "name": "John Doe"
    },
    "status_code": 200
},
```

When this fixture is loaded, all `GET` requests to a url matching `courses/1/users/1` will return a status code of 200 and the provided user data for John Doe.

---

```python
user = self.course.get_user(1)

self.assertIsInstance(user, User)
self.assertTrue(hasattr(user, 'name'))
```

[truncated]