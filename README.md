# Automation for downloading PDFs from SITS:eVision

This program assists in mass-downloading PDF documents from
https://evision.as.it.ubc.ca.

## Installing

Prerequisites:

- [Firefox](https://getfirefox.com) web browser
- [Python](https://python.org) programming language, version >= 3.8

`evision-dl` uses the [Selenium WebDriver](https://selenium.dev) framework for
controlling Firefox.

Run the installation, taking code directly from the source code repository:

```console
$ python3 -m pip install --force-reinstall git+https://github.com/dpoon/evision-dl@stable
```

## Running

Run `evision-dl` in a command shell (such as `bash` on Linux or macOS, or `cmd`
or `powershell` on Windows) in a graphical desktop environment.

- Create a directory to serve as a destination for the PDFs to be downloaded:

  ```console
  $ mkdir evision_pdfs
  ```

- Run `evision-dl`:

  ```console
  $ evision-dl evision_pdfs
  Waiting for user to log into eVision, bring up folder, and open the application of interest.
  ```

  The program should launch a sandboxed instance of Firefox showing the login
  page for eVision.

- Log into eVision, navigate to a folder containing applications, and open the
  first application of interest to you.

  Once `evision-dl` detects that an application has been opened in a new
  Firefox tab, it will start automating clicks to generate PDFs and download
  them to the destination directory on your computer.
