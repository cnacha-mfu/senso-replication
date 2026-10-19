## Repository context

The following contributor guidance is taken from the repository at the task's base commit.

### CONTRIBUTING.rst

.. _contributor_guide:

Contributor Guide
=================

.. note::
   This document assumes some familiarity with contributing to open source
   scientific Python projects using GitHub pull requests. If this does not
   describe you, you may first want to see the :ref:`contributing_faq`.

.. _dev_workflow:

Development Workflow
--------------------

1. If you are a first-time contributor:

   * Go to `https://github.com/networkx/networkx
     <https://github.com/networkx/networkx>`_ and click the
     "fork" button to create your own copy of the project.

   * Clone the project to your local computer::

      git clone git@github.com:your-username/networkx.git

   * Navigate to the folder networkx and add the upstream repository::

      git remote add upstream git@github.com:networkx/networkx.git

   * Now, you have remote repositories named:

     - ``upstream``, which refers to the ``networkx`` repository
     - ``origin``, which refers to your personal fork

   * Next, you need to set up your build environment.
     Here are instructions for two popular environment managers:

     * ``venv`` (pip based)

       ::

         # Create a virtualenv named ``networkx-dev`` that lives in the directory of
         # the same name
         python -m venv networkx-dev
         # Activate it
         source networkx-dev/bin/activate
         # Install main development and runtime dependencies of networkx
         pip install -r requirements/default.txt -r requirements/test.txt -r requirements/developer.txt
         #
         # (Optional) Install pygraphviz and pydot packages
         # These packages require that you have your system properly configured
         # and what that involves differs on various systems.
         # pip install -r requirements/extra.txt
         #
         # Build and install networkx from source
         pip install -e .
         # Test your installation
         pytest --pyargs networkx

     * ``conda`` (Anaconda or Miniconda)

       ::

         # Create a conda environment named ``networkx-dev``
         conda create --name networkx-dev
         # Activate it
         conda activate networkx-dev
         # Install main development and runtime dependencies of networkx
         conda install -c conda-forge --file requirements/default.txt --file requirements/test.txt --file requirements/developer.txt
         #
         # (Optional) Install pygraphviz and pydot packages
         # These packages require that you have your system properly configured
         # and what that involves differs on various systems.
         # conda install -c conda-forge --file requirements/extra.txt
         #
         # Install networkx from source
         pip install -e .
         # Test your installation
         pytest --pyargs networkx

   * Finally, we recommend you install pre-commit which checks
     that your code matches formatting guidelines::

       pre-commit install

2. Develop your contribution:

   * Pull the latest changes from upstream::

      git checkout main
      git pull upstream main

   * Create a branch for the feature you want to work on. Since the
     branch name will appear in the merge message, use a sensible name
     such as 'bugfix-for-issue-1480'::

      git checkout -b bugfix-for-issue-1480 main

   * Commit locally as you progress (``git add`` and ``git commit``)

3. Test your contribution:

   * Run the test suite locally (see `Testing`_ for details)::

      PYTHONPATH=. pytest networkx

   * Running the tests locally *before* submitting a pull request helps catch
     problems early and reduces the load on the continuous integration
     system.

4. Ensure your contribution is properly formatted.

   * If you installed ``pre-commit`` as recommended in step 1, all necessary
     linting should run automatically at commit time. If there are any
     formatting issues, the commit will not be successful and linting
     suggestions will be applied to the patch automatically.
     Simply ``git add`` and ``git commit`` a second time to accept the proposed
     formatting changes.

   * If the above fails for whatever reason, you can also run the linter over
     the entire codebase with::

         pre-commit run --all-files

5. Submit your contribution:

   * Push your changes back to your fork on GitHub::

      git push origin bugfix-for-issue-1480

   * Go to GitHub. The new branch will show up with a green Pull Request
     button---click it.

   * If you want, post on the `mailing list
     <http://groups.google.com/group/networkx-discuss>`_ to explain your changes or
     to ask for review.

6. Review process:

   * Every Pull Request (PR) update triggers a set of `continuous integration
     <https://en.wikipedia.org/wiki/Continuous_integration>`_ services
     that check that the code is up to standards and passes all our tests.
     These checks must pass before your PR can be merged.  If one of the
     checks fails, you can find out why by clicking on the "failed" icon (red
     cross) and inspecting the build and test log.

   * Reviewers (the other developers and interested community members) will
     write inline and/or general comments on your PR to help
     you improve its implementation, documentation, and style.  Every single
     developer working on the project has their code reviewed, and we've come
     to see it as friendly conversation from which we all learn and the
     overall code quality benefits.  Therefore, please don't let the review
     discourage you from contributing: its only aim is to improve the quality
     of project, not to criticize (we are, after all, very grateful for the
     time you're donating!).

   * To update your PR, make your changes on your local repository
     and commit. As soon as those changes are pushed up (to the same branch as
     before) the PR will update automatically.

   .. note::

      If the PR closes an issue, make sure that GitHub knows to automatically
      close the issue when the PR is merged.  For example, if the PR closes
      issue number 1480, you could use the phrase "Fixes #1480" in the PR
      description or commit message.

7. Document deprecations and API changes
   
   If your change introduces any API modifications including deprecations,
   please make sure the PR has the ``type: API`` label.

   To set up a function for deprecation:

   - Use a deprecation warning to warn users. For example::

         msg = "curly_hair is deprecated and will be removed in v3.0. Use sum() instead."
         warnings.warn(msg, DeprecationWarning)

   - Add a warnings filter to ``networkx/conftest.py``::

         warnings.filterwarnings(
             "ignore", category=DeprecationWarning, message=<start of message>
         )

   - Add a reminder to ``doc/developer/deprecations.rst`` for the team
     to remove the deprecated functionality in the future. For example:

     .. code-block:: rst

        * In ``utils/misc.py`` remove ``generate_unique_node`` and related tests.

   .. note::

      To reviewers: make sure the merge message has a brief description of the
      change(s) and if the PR closes an issue add, for example, "Closes #123"
      where 123 is the issue number.


Divergence from ``upstream main``
---------------------------------

If GitHub indicates that the branch of your Pull Request can no longer
be merged automatically, merge the main branch into yours::

   git fetch upstream main
   git merge upstream/main

If any conflicts occur, they need to be fixed before continuing.  See
which files are in conflict using::

   git status

Which displays a message like::

   Unmerged paths:
     (use "git add <file>..." to mark resolution)

     both modified:   file_with_conflict.txt

Inside the conflicted file, you'll find sections like these::

   <<<<<<< HEAD
[truncated]