# Automation for downloading PDFs from SITS:eVision

This program assists in mass-downloading PDF documents from
https://evision.as.it.ubc.ca.

## Installing

Prerequisites:

- [Firefox](https://getfirefox.com) web browser
- [Python](https://python.org) programming language, version >= 3.8.

  On Windows, you may obtain Python for free from either the Python website
  or the Microsoft Store.

`evision-dl` uses the [Selenium WebDriver](https://selenium.dev) framework for
controlling Firefox.  The installation method described here will take care
of installing Selenium and other dependencies.

### Installing from the Wheel package

`pip` is a package installer that comes with Python.  (On some systems, it
might be called `pip3` instead.)  Run a command like the following to download
and install `evision-dl`:

```console
$ pip install --force-reinstall https://github.com/dpoon/evision-dl/releases/download/v2023.2.2/evision_dl-2023.2.2-py3-none-any.whl
```

Releases of `evision-dl` are listed at
https://github.com/dpoon/evision-dl/releases.
Change the command as needed to reflect the desired version.

### Installing from the source code repository

If you have [`git`](https://git-scm.org) installed, you can also install
the latest version fresh from the source code repository:

```console
$ pip install --force-reinstall git+https://github.com/dpoon/evision-dl@stable
```

## Running

Run `evision-dl` in a command shell (such as `bash` on Linux or macOS, or `cmd`
or `powershell` on Windows) in a graphical desktop environment.

- Create a directory to serve as a destination for the PDFs to be downloaded:

  ```console
  $ mkdir 2023-phd-applicants
  ```

- Run `evision-dl`:

  ```console
  $ evision-dl 2023-phd-applicants
  Waiting for user to log into eVision, bring up folder, and open the application of interest.
  ```

  The program should launch a sandboxed instance of Firefox showing the login
  page for eVision.

- Log into eVision, navigate to a folder containing applications, and open the
  first application of interest to you.

  Once `evision-dl` detects that an application has been opened in a new
  Firefox tab, it will start automating clicks to generate PDFs and download
  them to the destination directory on your computer.
