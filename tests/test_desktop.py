"""Tests for the desktop app's launcher: starting, finding a running copy, and its self-test."""

import json
import os

from pydataquality import desktop


def test_start_writes_where_it_is_running_and_stop_removes_it(tmp_path):
    home = str(tmp_path)
    server, app, url = desktop.start(home, port=0)
    try:
        state = json.load(open(os.path.join(home, desktop.STATE_FILE), encoding="utf-8"))
        assert url == f"http://127.0.0.1:{state['port']}/"
        assert state["pid"] == os.getpid()
        assert desktop.running_url(home) == url
    finally:
        desktop.stop(server, app, home)
    assert not os.path.exists(os.path.join(home, desktop.STATE_FILE))
    assert desktop.running_url(home) is None


def test_no_running_copy_when_nothing_was_started(tmp_path):
    assert desktop.running_url(str(tmp_path)) is None


def test_a_stale_record_is_not_mistaken_for_a_running_copy(tmp_path):
    # the app was killed without cleaning up, and nothing answers on that port any more
    server, app, _ = desktop.start(str(tmp_path), port=0)
    port = server.server_address[1]
    desktop.stop(server, app, str(tmp_path))
    with open(os.path.join(str(tmp_path), desktop.STATE_FILE), "w", encoding="utf-8") as handle:
        json.dump({"port": port, "pid": 1}, handle)
    assert desktop.running_url(str(tmp_path)) is None


def test_a_taken_port_falls_back_to_a_free_one(tmp_path):
    first = desktop.start(str(tmp_path / "a"), port=0)
    taken = first[0].server_address[1]
    second = desktop.start(str(tmp_path / "b"), port=taken)
    try:
        assert second[0].server_address[1] != taken
    finally:
        desktop.stop(first[0], first[1], str(tmp_path / "a"))
        desktop.stop(second[0], second[1], str(tmp_path / "b"))


def test_self_test_passes_and_writes_its_result(tmp_path):
    result = tmp_path / "result.txt"
    assert desktop.self_test(str(result)) == 0
    assert result.read_text(encoding="utf-8") == "ok"


def test_second_launch_opens_the_running_copy_instead_of_starting_another(tmp_path, monkeypatch):
    home = str(tmp_path)
    server, app, url = desktop.start(home, port=0)
    opened = []
    monkeypatch.setattr("pydataquality.server.HOME", home)
    monkeypatch.setattr(desktop, "_open", opened.append)
    monkeypatch.setattr(desktop, "_window", lambda url: (_ for _ in ()).throw(AssertionError("a second window was opened")))
    try:
        assert desktop.main([]) == 0
        assert opened == [url]
    finally:
        desktop.stop(server, app, home)
