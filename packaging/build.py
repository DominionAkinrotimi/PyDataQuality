"""
Build the desktop app with PyInstaller.

    pip install . pyinstaller
    python packaging/build.py

Writes dist/PyDataQuality/ (Windows, Linux) or dist/PyDataQuality.app (macOS):
a folder holding its own copy of Python, so the person using it installs
nothing else. On Windows, packaging/installer.iss then wraps that folder in a
setup program.

Written as a script and not a .spec file because the repository's .gitignore
ignores *.spec.
"""

import os
import sys

import PyInstaller.__main__

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATIC = os.path.join(ROOT, "pydataquality", "static")

# The app never draws charts, so the plotting libraries (and what they pull in)
# are left out. This roughly halves the download.
LEFT_OUT = [
    "matplotlib", "seaborn", "scipy", "IPython", "jupyter", "notebook", "PIL",
    "pytest", "setuptools", "pip", "wheel", "pyarrow", "sphinx", "black", "flake8",
]

args = [
    os.path.join(HERE, "launch.py"),
    "--name", "PyDataQuality",
    "--noconfirm",
    "--clean",
    "--windowed",  # no terminal window
    "--onedir",    # starts faster than a single packed file, and antivirus tools trust it more
    "--add-data", os.path.join(STATIC, "app") + os.pathsep + os.path.join("pydataquality", "static", "app"),
    "--add-data", os.path.join(STATIC, "icon.ico") + os.pathsep + os.path.join("pydataquality", "static"),
    "--paths", ROOT,  # find the package in this checkout, however it was installed
    "--collect-submodules", "pydataquality",
    "--distpath", os.path.join(ROOT, "dist"),
    "--workpath", os.path.join(ROOT, "build", "pyinstaller"),
    "--specpath", os.path.join(ROOT, "build"),
]
if sys.platform == "win32":
    args += ["--icon", os.path.join(STATIC, "icon.ico")]
if sys.platform == "darwin":
    args += ["--osx-bundle-identifier", "io.github.dominionakinrotimi.pydataquality"]
for name in LEFT_OUT:
    args += ["--exclude-module", name]

PyInstaller.__main__.run(args)
