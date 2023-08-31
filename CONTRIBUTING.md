# How to contribute to TrnPy

### First time setup in your local environment

- Make sure you have a [GitHub account][].
- Download and install the [latest version of git][].
- Configure git with your [username][] and [email][].

  ```sh
  $ git config --global user.name 'your name'
  $ git config --global user.email 'your email'
    ```

- Fork TrnPy to your GitHub account by clicking the [Fork][] button.
- [Clone][] your fork locally, replacing ``your-username`` in the command below
  with your actual username.

  ```sh
  $ git clone https://github.com/your-username/trnpy
  $ cd trnpy
  ```

- Create a virtualenv. Use the latest version of Python.

    - Linux/macOS

      ```sh
      $ python3 -m venv .venv --prompt trnpy
      $ source .venv/bin/activate
      ```

    - Windows

      ```sh
      > py -3 -m venv .venv --prompt trnpy
      > .venv\Scripts\activate
      ```

- Install TrnPy in editable mode with development dependencies.

  ```sh
  $ python -m pip install -U pip
  $ pip install -e ".[lint,test,typing]"
  ```

[Github account]: https://github.com/join
[latest version of git]: https://git-scm.com/downloads
[username]: https://docs.github.com/en/github/using-git/setting-your-username-in-git
[email]: https://docs.github.com/en/github/setting-up-and-managing-your-github-user-account/setting-your-commit-email-address
[Fork]: https://github.com/isentropic-dev/trnpy/fork
[Clone]: https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#step-2-create-a-local-clone-of-your-fork
