"""Test crash catcher"""

import pathlib

import pytest

from crash_catcher import (
    _reset_crash_catcher,
    crash_catcher,
    register_crash_callback,
    set_crash_data,
    unregister_crash_callback,
)


@pytest.fixture(autouse=True)
def reset_crash_catcher():
    _reset_crash_catcher()


def test_decorator(capsys, tmp_path: pathlib.Path):
    """Test the crash_catcher decorator"""

    @crash_catcher(
        filename=tmp_path / "crash_catcher.log",
        message="The app has crashed",
        title="Crash catcher demo",
        postamble="Please file a bug report with contents of {filename}",
        overwrite=True,
        extra1="xyzzy",
        extra2="fizzbuzz",
    )
    def demo_crash_catcher():
        """Demo crash_catcher decorator"""
        set_crash_data("crash_data", "foo bar baz")
        print("Hello world")

        # some critical section that requires cleanup
        callback_id = register_crash_callback(lambda: print("Cleaning up..."))

        # do work

        # any uncaught exception causes the crash_catcher decorator to catch the crash
        raise ValueError("Oh no, the app has crashed!")

    with pytest.raises(SystemExit):
        demo_crash_catcher()

    captured = capsys.readouterr()
    assert "Hello world" in captured.out
    assert "Cleaning up..." in captured.out
    assert "The app has crashed" in captured.err
    assert (
        f"Please file a bug report with contents of {tmp_path / 'crash_catcher.log' }"
        in captured.err
    )

    crash_log = open(tmp_path / "crash_catcher.log").read()
    assert "xyzzy" in crash_log
    assert "fizzbuzz" in crash_log
    assert "foo bar baz" in crash_log
    assert "Oh no, the app has crashed!" in crash_log


def test_decorator_no_crash(capsys, tmp_path: pathlib.Path):
    """Test the crash_catcher decorator without a crash"""

    @crash_catcher(
        filename=tmp_path / "crash_catcher.log",
        message="The app has crashed",
        title="Crash catcher demo",
        postamble="Please file a bug report with contents of {filename}",
        overwrite=True,
        extra={"extra": "xyzzy"},
    )
    def demo_crash_catcher():
        """Demo crash_catcher decorator"""
        set_crash_data("crash_data", "foo bar baz")
        print("Hello world")

        # some critical section that requires cleanup
        callback_id = register_crash_callback(lambda: print("Cleaning up..."))

        # do work

    demo_crash_catcher()

    captured = capsys.readouterr()
    assert "Hello world" in captured.out
    assert "Cleaning up..." not in captured.out
    assert "The app has crashed" not in captured.err
    assert (
        f"Please file a bug report with contents of {tmp_path / 'crash_catcher.log' }"
        not in captured.err
    )

    assert not (tmp_path / "crash_catcher.log").exists()


def test_decorator_unregister(capsys, tmp_path: pathlib.Path):
    """Test the crash_catcher decorator with unregister_crash_callback()"""

    @crash_catcher(
        filename=tmp_path / "crash_catcher.log",
        message="The app has crashed",
        title="Crash catcher demo",
        postamble="Please file a bug report with contents of {filename}",
        overwrite=True,
        extra={"extra": "xyzzy"},
    )
    def demo_crash_catcher():
        """Demo crash_catcher decorator"""
        set_crash_data("crash_data", "foo bar baz")
        print("Hello world")

        # some critical section that requires cleanup
        callback_id = register_crash_callback(lambda: print("Cleaning up..."))

        # do work

        # unregister callback
        unregister_crash_callback(callback_id)

        raise ValueError("Oh no, the app has crashed!")

    with pytest.raises(SystemExit):
        demo_crash_catcher()

    captured = capsys.readouterr()
    assert "Hello world" in captured.out
    assert "Cleaning up..." not in captured.out
    assert "The app has crashed" in captured.err
    assert (
        f"Please file a bug report with contents of {tmp_path / 'crash_catcher.log' }"
        in captured.err
    )


def test_overwrite(tmp_path):
    """Test that crash_catcher overwrites existing file"""

    crash_file = tmp_path / "crash_catcher.log"

    @crash_catcher(filename=crash_file, message="", title="", overwrite=True)
    def demo_crash_catcher():
        """Demo crash_catcher decorator"""
        raise ValueError("Oh no, the app has crashed!")

    # create file
    with open(crash_file, "w") as fd:
        fd.write("xyzzy")

    # crash_catcher should overwrite file
    with pytest.raises(SystemExit):
        demo_crash_catcher()

    assert "xyzzy" not in crash_file.read_text()


def test_not_overwrite(tmp_path):
    """Test that crash_catcher does not overwrites existing file with overwrite=False"""

    crash_file = tmp_path / "crash_catcher.log"

    @crash_catcher(filename=crash_file, message="", title="", overwrite=False)
    def demo_crash_catcher():
        """Demo crash_catcher decorator"""
        raise ValueError("Oh no, the app has crashed!")

    # create file
    with open(crash_file, "w") as fd:
        fd.write("xyzzy")

    # crash_catcher should overwrite file
    with pytest.raises(SystemExit):
        demo_crash_catcher()

    # crash file should not be overwritten
    assert "xyzzy" in crash_file.read_text()

    # crash file should be renamed
    actual_crash_file = tmp_path / "crash_catcher (1).log"
    assert actual_crash_file.exists()
    assert "Oh no, the app has crashed!" in actual_crash_file.read_text()
