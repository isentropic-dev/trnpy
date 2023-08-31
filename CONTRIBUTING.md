# How to contribute to TrnPy

### First time setup in your local environment

-   Make sure you have a `GitHub account`_.
-   Download and install the `latest version of git`_.
-   Configure git with your `username`_ and `email`_.

    .. code-block:: text

        $ git config --global user.name 'your name'
        $ git config --global user.email 'your email'

-   Fork TrnPy to your GitHub account by clicking the `Fork`_ button.
-   `Clone`_ your fork locally, replacing ``your-username`` in the command below with
    your actual username.

    .. code-block:: text

        $ git clone https://github.com/your-username/trnpy
        $ cd trnpy

-   Create a virtualenv. Use the latest version of Python.

    - Linux/macOS

      .. code-block:: text

         $ python3 -m venv .venv --prompt trnpy
         $ source .venv/bin/activate

    - Windows

      .. code-block:: text

         > py -3 -m venv .venv --prompt trnpy
         > .venv\Scripts\activate

-   Install the development dependencies, then install Flask in editable mode.

    .. code-block:: text

        $ python -m pip install -U pip
        $ pip install -e ".[lint,test,typing]"

.. _GitHub account: https://github.com/join
.. _latest version of git: https://git-scm.com/downloads
.. _username: https://docs.github.com/en/github/using-git/setting-your-username-in-git
.. _email: https://docs.github.com/en/github/setting-up-and-managing-your-github-user-account/setting-your-commit-email-address
.. _Fork: https://github.com/isentropic-dev/trnpy/fork
.. _Clone: https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#step-2-create-a-local-clone-of-your-fork
