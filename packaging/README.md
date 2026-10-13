# Desktop app and installers

For people who would rather not install Python or open a terminal. The desktop app is the same app
as `pdq ui`, packed together with its own copy of Python.

| File | What it is |
|:--|:--|
| `../pydataquality/desktop.py` | The launcher: starts the app, opens the browser, shows a small window with **Open** and **Quit**. Opening it twice does not start two copies. |
| `launch.py` | The entry point PyInstaller packs. |
| `build.py` | Builds `dist/PyDataQuality/` (or `dist/PyDataQuality.app` on a Mac) with PyInstaller. |
| `installer.iss` | Wraps the Windows build in `dist/PyDataQuality-Setup.exe` with Inno Setup 6. |

## Build it

```bash
pip install . pyinstaller
python packaging/build.py
```

Check that the result works. A windowed app cannot print, so it writes `ok` or the error to a file:

```bash
dist/PyDataQuality/PyDataQuality.exe --self-test result.txt
```

On Windows, with [Inno Setup 6](https://jrsoftware.org/isinfo.php) installed:

```bash
iscc /DAppVersion=0.3.0 packaging\installer.iss
```

## Releases

`.github/workflows/installer.yml` does all of the above on Windows and macOS, installs the Windows
setup program on the build machine, runs the installed app's self-test, and attaches the files to a
release when one is published. It can also be started by hand from the Actions tab.

## Known limits

- Not code-signed. Windows SmartScreen and macOS Gatekeeper warn before the first run.
- The Mac build is for Apple Silicon only.
- Parquet is left out to keep the download small. Charts from the older profiling API are not included.
- The installer does not update itself. Installing a newer version replaces the old one.
