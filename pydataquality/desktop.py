"""
The desktop app: PyDataQuality for people who would rather not open a terminal.

This is what the installer puts on the Start menu. It starts the same local app
as ``pdq ui``, opens it in the browser, and shows one small window whose only
jobs are to say that it is running and to give a way to stop it.

Opening it a second time does not start a second copy. It brings the first
one's page back up in the browser.
"""

import json
import os
import socket
import sys
import threading
import urllib.request
import webbrowser
from typing import Optional, Tuple

PREFERRED_PORT = 8765
STATE_FILE = "desktop.json"


def _state_path(home: str) -> str:
    return os.path.join(home, STATE_FILE)


def _is_ours(url: str) -> bool:
    """True if a PyDataQuality app answers at this address."""
    try:
        with urllib.request.urlopen(url, timeout=1.5) as response:
            return response.status == 200 and b"PyDataQuality" in response.read(4096)
    except Exception:
        return False


def _in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def running_url(home: str) -> Optional[str]:
    """The address of a copy that is already running, or None."""
    try:
        with open(_state_path(home), "r", encoding="utf-8") as handle:
            port = int(json.load(handle)["port"])
    except Exception:
        return None
    url = f"http://127.0.0.1:{port}/"
    return url if _is_ours(url) else None


def start(home: str, port: int = PREFERRED_PORT) -> Tuple[object, object, str]:
    """Start the local app in the background. Returns (server, app, url)."""
    from .server import make_server

    # If something else already listens on the usual port, take any free one. Asking first
    # matters on Windows, where a second program can otherwise open the same port.
    if port and _in_use(port):
        port = 0
    try:
        server, app = make_server(port, home=home)
    except OSError:
        server, app = make_server(0, home=home)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    os.makedirs(home, exist_ok=True)
    with open(_state_path(home), "w", encoding="utf-8") as handle:
        json.dump({"port": server.server_address[1], "pid": os.getpid()}, handle)
    return server, app, url


def stop(server, app, home: str) -> None:
    server.shutdown()
    server.server_close()
    app.close()
    try:
        os.remove(_state_path(home))
    except OSError:
        pass


def _open(url: str) -> None:
    """Open the page in the browser. Tests set PYDATAQUALITY_NO_BROWSER to keep it closed."""
    if not os.environ.get("PYDATAQUALITY_NO_BROWSER"):
        webbrowser.open(url)


def _window(url: str) -> None:
    """Show the small "it is running" window. Returns when the user quits."""
    import tkinter as tk

    root = tk.Tk()
    root.title("PyDataQuality")
    root.resizable(False, False)
    root.configure(bg="#ffffff", padx=28, pady=24)
    try:
        icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "icon.ico")
        if os.path.isfile(icon):
            root.iconbitmap(icon)
    except Exception:
        pass

    font = "Segoe UI" if sys.platform == "win32" else "Helvetica"
    tk.Label(root, text="PyDataQuality is running", font=(font, 14, "bold"), bg="#ffffff", fg="#090a0f").pack(anchor="w")
    tk.Label(
        root,
        text="It has opened in your browser.\nKeep this window open while you use it.\nYour files stay on this computer.",
        font=(font, 10), bg="#ffffff", fg="#525866", justify="left",
    ).pack(anchor="w", pady=(8, 18))

    buttons = tk.Frame(root, bg="#ffffff")
    buttons.pack(anchor="w")
    tk.Button(
        buttons, text="Open PyDataQuality", command=lambda: _open(url),
        font=(font, 10, "bold"), bg="#090a0f", fg="#ffffff", activebackground="#1f2937", activeforeground="#ffffff",
        relief="flat", padx=16, pady=7, cursor="hand2",
    ).pack(side="left")
    tk.Button(
        buttons, text="Quit", command=root.destroy,
        font=(font, 10), bg="#f3f4f6", fg="#090a0f", activebackground="#e5e7eb",
        relief="flat", padx=16, pady=7, cursor="hand2",
    ).pack(side="left", padx=(10, 0))

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


def _report(message: str) -> None:
    """Tell the user something went wrong. A windowed app has no terminal to print to."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("PyDataQuality", message)
        root.destroy()
    except Exception:
        if sys.stderr:
            print(message, file=sys.stderr)


def _exercise_files(folder: str) -> None:
    """Read an Excel file, write the summary page and save a baseline: the parts that need extra libraries."""
    import pandas as pd

    from .checker import accept, check
    from .server import sample_frame

    path = os.path.join(folder, "selftest_customers.xlsx")
    sample_frame().to_excel(path, index=False)
    result = check(path)
    if not result.problems:
        raise RuntimeError("The Excel copy of the sample file came back with no problems.")
    if "<html" not in result.to_html().lower():
        raise RuntimeError("The summary page was not written.")
    accept(path)
    if check(path).baseline is None:
        raise RuntimeError("The saved baseline was not found again.")
    if not len(pd.read_excel(path)):
        raise RuntimeError("The Excel file could not be read back.")


def self_test(result_path: Optional[str] = None) -> int:
    """
    Start the app in a temporary folder, load its page and check the built-in
    sample file. Used to prove that a packaged copy really works. Writes
    "ok" or the error to ``result_path``, because a windowed app cannot print.
    """
    import tempfile

    outcome = "ok"
    with tempfile.TemporaryDirectory(prefix="pdq_selftest_") as home:
        try:
            server, app, url = start(home, port=0)
            try:
                if not _is_ours(url):
                    raise RuntimeError(f"The page at {url} did not load.")
                result = app.check_sample()
                if not result.get("findings"):
                    raise RuntimeError("The sample file was checked but nothing was found in it.")
                _exercise_files(home)
            finally:
                stop(server, app, home)
        except Exception as error:  # the whole point is to report any failure
            outcome = f"failed: {type(error).__name__}: {error}"
    if result_path:
        with open(result_path, "w", encoding="utf-8") as handle:
            handle.write(outcome)
    elif sys.stdout:
        print(outcome)
    return 0 if outcome == "ok" else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--self-test":
        return self_test(argv[1] if len(argv) > 1 else None)

    from .server import HOME

    try:
        already = running_url(HOME)
        if already:
            _open(already)
            return 0
        server, app, url = start(HOME)
    except Exception as error:
        _report(f"PyDataQuality could not start.\n\n{error}")
        return 1

    try:
        _open(url)
        _window(url)
    finally:
        stop(server, app, HOME)
    return 0


if __name__ == "__main__":
    sys.exit(main())
