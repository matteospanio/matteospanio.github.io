---
layout: post
title: "Python's virtual environments"
author: Matteo Spanio
categories: Python, Programming
tags: [python, programming, code]
giscus_comments: true
description: A brief introduction to Python's virtual environments.
date: 2024-06-21

toc:
    - name: Managing environments
    - name: pip and virtual environments
    - name: Installing packages
    - name: Managing requirements
    - name: pipx
    - name: conda
    - name: poetry & friends
---
# Managing environments

In embarking on projects, I've learned the hard way that starting without the right tools can lead to wasted time and frustration. This has been evident in my tendency to recklessly install packages, turning my system's Python environment into a chaotic mess. Despite the availability of better alternatives, I've also stuck with the default Python shell. Investing upfront time and effort to avoid these pitfalls can greatly benefit your journey as a Python enthusiast.

While most programming languages provide a standard library with diverse functionalities, managing additional libraries can be challenging. It's crucial to effectively utilize the standard library, which includes features like file handling, string manipulation, and date/time management. However, to fully leverage Python's capabilities, additional libraries are often required. Python's vibrant developer community produces a plethora of third-party packages, allowing for quick and easy installation. Yet, it's essential to exercise caution and avoid the temptation to install every intriguing package, as it can lead to a chaotic environment where nothing functions properly.

With this understanding, let's delve into pip, the default package manager tool that accompanies Python installation.

## pip and virtual environments

`pip` is Python's package manager. Its name is a recursive acronym that stands for *Pip Installs Packages*. `pip` is a powerful tool that allows you to install, upgrade, and remove additional libraries, and it is included in Python installation starting from version 3.4.

> ##### Legacy Python
> If you are using an older version of Python, you can install pip manually. To do so, simply download the `get-pip.py` file from the official Python website at [https://bootstrap.pypa.io/get-pip.py](https://bootstrap.pypa.io/get-pip.py) and run it with Python.
{: .block-tip }

### Installing packages

To install a Python package using pip, simply use the install command followed by the name of the package. For example, to install the requests package, which is commonly used for making HTTP requests, you would type:

```bash
pip install requests
```

pip will then download and install the [requests package ](https://docs.python-requests.org/en/latest/index.html) and any dependencies it requires.

Now that you have installed requests, you can use it in your Python code by importing it as usual:

```python
import requests

response = requests.get('https://www.example.com')
print(response.text)
```

To uninstall a package that you no longer need, you can use the uninstall command followed by the name of the package. For example, to uninstall the requests package, you would type:

```bash
pip uninstall requests
```

As you can see, pip is a simple and straightforward tool for managing Python packages. However, it has one major limitation: it installs packages **globally**, which can lead to conflicts between different projects that require different versions of the same package.

To avoid these conflicts, it is best to use **virtual environments**. A virtual environment is an isolated environment that contains its own Python interpreter and its own set of installed packages. This allows you to work on multiple projects with different dependencies without worrying about conflicts. Python provides a built-in module called [venv](https://docs.python.org/3/library/venv.html) that allows you to create and manage virtual environments. To create a new virtual environment, you can use the following command:

```{bash}
python -m venv myenv
```

This will create a new directory called `myenv` that contains a copy of the Python interpreter and a copy of the `pip` package manager.
Let's look in detail at the folder structure of the virtual environment with the shell utility `tree`:
```bash
$ tree -L 4 myenv

myenv
├── bin
│   ├── activate
│   ├── activate.csh
│   ├── activate.fish
│   ├── Activate.ps1
│   ├── pip
│   ├── pip3
│   ├── pip3.10
│   ├── python -> python3
│   ├── python3 -> /usr/bin/python3
│   └── python3.10 -> python3
├── include
├── lib
│   └── python3.10
│       └── site-packages
│           ├── _distutils_hack
│           ├── distutils-precedence.pth
│           ├── pip
│           ├── pip-22.0.2.dist-info
│           ├── pkg_resources
│           ├── setuptools
│           └── setuptools-59.6.0.dist-info
├── lib64 -> lib
└── pyvenv.cfg
```
As you can see the `bin` directory contains the `activate` script that allows you to activate the virtual environment. The `lib` directory contains the installed packages, and the `include` directory contains the header files needed to compile C extensions. The `pyvenv.cfg` file contains the configuration of the virtual environment.

To activate the virtual environment, you can use the following command:

```bash
source myenv/bin/activate
```
This will activate the virtual environment, and you will see the name of the virtual environment in your shell prompt.

> ##### TIP
> On Windows, the command to activate the virtual environment is slightly different:
> ```{bash}
> myenv\Scripts\activate
> ```
{: .block-tip }

Once the virtual environment is activated, any packages you install using `pip` will be installed in the virtual environment rather than globally. This allows you to work on your project without worrying about conflicts with other projects.

For example, to install the requests package in the virtual environment, you would type:

```bash
pip install requests
```

but this time the package will be installed in the `myenv` directory rather than globally. In fact if you look at the `lib` directory of the virtual environment you will see the installed packages:

```bash
$ tree -L 1 myenv/lib/python3.10/site-packages

myenv/lib/python3.10/site-packages
├── certifi
├── certifi-2024.6.2.dist-info
├── charset_normalizer
├── charset_normalizer-3.3.2.dist-info
├── _distutils_hack
├── distutils-precedence.pth
├── idna
├── idna-3.7.dist-info
├── pip
├── pip-22.0.2.dist-info
├── pkg_resources
├── requests
├── requests-2.32.3.dist-info
├── setuptools
├── setuptools-59.6.0.dist-info
├── urllib3
└── urllib3-2.2.2.dist-info
```

When you are finished working on your project, you can deactivate the virtual environment using the following command:

```bash
deactivate
```

This will return you to the global Python environment.

### Managing requirements

When working on a project, it is common to have a list of required packages that need to be installed. This list is often stored in a file called `requirements.txt`, which can be used to install all the required packages at once. To create a `requirements.txt` file, you can use the following command:

```{bash}
pip freeze > requirements.txt
```

This will create a `requirements.txt` file that contains a list of all the packages installed in the current environment. To install the packages listed in a `requirements.txt` file, you can use the following command:

```{bash}
pip install -r requirements.txt
```

This will install all the packages listed in the `requirements.txt` file.

## pipx

Sometimes, you may want to install a Python application that is not a library, but a standalone program. In this case, you can use `pipx`. `pipx` is a tool that allows you to install and manage Python applications in an isolated environment. This means that when you install an application with `pipx`, it is not installed in the system, but in a dedicated virtual environment. This allows you to avoid conflicts between different versions of libraries and keep your system clean.

```{bash}
pipx install <package_name>
```

To uninstall a package installed with `pipx`, you can use the following command:

```{bash}
pipx uninstall <package_name>
```

It is important to note that `pipx` is not a replacement for `pip`. It is a complementary tool that is used specifically for installing and managing Python applications. If you want to install a library, you should use `pip` instead. `pipx` is particularly useful for installing command-line tools that are written in Python, such as `black`, `flake8`, `isort`, and many others that you will likely to use transversally in your projects.

## conda

`conda` is an open-source package management system and environment management system that runs on Windows, macOS, and Linux. It is a powerful tool that allows you to create and manage virtual environments, install and update packages, and manage dependencies. `conda` is particularly popular in the scientific computing community, as it provides access to a wide range of scientific computing libraries and tools. I suggest to have a look at the official documentation at [https://docs.conda.io/en/latest/](https://docs.conda.io/en/latest/) to get started with `conda`. An important thing to note is that `conda` has its own way to install packages through the `conda install` command, which is different from `pip`. This is because `conda` manages its own package repositories, which are separate from the Python Package Index (PyPI). This means that some packages may be available on `conda` but not on PyPI, and vice versa, anyway `conda` can install packages from PyPI as well using the `pip` package manager.

`conda` solves the virtual environment problem its own way, it lets you create and activate virtual environments creating them for you. When you install `conda` for the first time it comes with a default virtual environment called `base`. As stated before a good practice is to create a virtual environment for each project, anyway the `conda` design encourages you to reuse a virtual environment. For example, you can create a virtual environment called `torch` and install the `torch` package in it, then you can create another virtual environment called `tensorflow` and install the `tensorflow` package in it. This way you can switch between the two environments when you need to work on a project that requires `torch` or `tensorflow`. This is a different approach from `venv` where you create a new virtual environment for each project. If you find yourself working on multiple projects that require the same set of packages, `conda` can be a good choice for you.

## poetry & friends

`poetry` is a tool for dependency management and packaging in Python. It allows you to declare the libraries your project depends on and it will manage (install/update) them for you. It also allows you to specify the Python version and the Python interpreter to use. `poetry` is particularly popular in the data science community, as it provides a simple and powerful way to manage dependencies and package your projects. This tool is really similar to `npm` in the JavaScript world, or `cargo` in the Rust world, and it is a great way to manage your Python projects. You can find more information about `poetry` at [https://python-poetry.org/](https://python-poetry.org/).

One of the most interesting features of `poetry`, in my opinion, is the fact that you are *enforced* to organize your project in a specific way. This is because `poetry` expects your project to have a specific structure, with a `pyproject.toml` file that contains the project's metadata and dependencies. This makes it easier to manage your project and share it with others, as they will know exactly where to find the project's dependencies and how to install them.

`poetry` is not the only tool in this category. Other popular tools include `pipenv` and `pip-tools`. Each of these tools has its own strengths and weaknesses, and the best tool for you will depend on your specific needs and preferences.
