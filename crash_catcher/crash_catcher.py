"""Error logger/crash reporter decorator"""

from __future__ import annotations

import datetime
import functools
import pathlib
import platform
import sys
import time
import traceback
from typing import Any, Callable

from ._version import __version__

# store data to print out in crash log, set by set_crash_data
_global_crash_data = {}

# store callback functions to execute if a crash is handled
_global_callbacks = {}

__all__ = [
    "crash_catcher",
    "register_crash_callback",
    "set_crash_data",
    "unregister_crash_callback",
]


def set_crash_data(key_: Any, data: Any):
    """Set data to be printed in crash log"""
    _global_crash_data[key_] = data


def register_crash_callback(
    func: Callable[[], None], message: str | None = None
) -> int:
    """Register callback to be run if crash is caught.

    Args:
        func: callable that will be called (with no args) by crash_catcher
        message: optional message

    Returns:
        id for callback which may be used with unregister_crash_callback() to remove the callback.

    Note: Multiple callabacks may be registered by calling this function repeatedly.
        Callbacks will be executed in order they are registered.
    """

    callback_id = time.monotonic_ns()
    _global_callbacks[callback_id] = (func, message)
    return callback_id


def unregister_crash_callback(callback_id: int):
    """Unregister a crash callback previously registered with register_crash_callback().

    Args:
        callback_id: the ID of the callback to unregister as returned by register_crash_callback()

    Raises:
        ValueError if the callback_id is not valid

    Note: After a callback is unregisterd, it will not be called if a crash is caught.
    """
    try:
        del _global_callbacks[callback_id]
    except KeyError:
        raise ValueError(f"Invalid callback_id: {callback_id}")


def crash_catcher(
    filename: str,
    message: str,
    title: str,
    postamble: str | None,
    overwrite: bool = True,
    **extra: dict[str:Any],
):
    """Catch crash (uncaught exception) and create a crash dump file on error named filename

    Args:
        filename: name of crash dump file to create
        message: message to print to stderr upon crash
        title: title to print to start of crash dump file
        postamble: message to print to stderr after On error, create a crash dump file named filename with exception and stack trace.
        message is printed to stderr.
        postamble is printed to stderr after crash dump file is created.
        overwrite: if True, overwrite existing file, otherwise increment filename until a non-existent filename is found
        extra: If kwargs provided, any additional arguments to the function will be printed to the crash file.

    Note: This decorator should be applied to the main function of the program.
        The message, title, and postamble arguments may include the template {filename} which
        will be replaced with the actual filename of the crash log. For example, if overwrite=False
        and the crash file `crash_catcher.log` already exists, the filename will be incremented to
        `crash_catcher (1).log`, `crash_catcher (2).log`, and so on until a non-existent filename is found.
        This filename will be used to render the {filename} template.
    """

    filename = pathlib.Path(filename)
    filename = filename.resolve()
    if filename.exists() and not overwrite:
        filename = _increment_filename(filename)

    # handle any templates in message and title
    # currently, only supported template is {filename}
    class Default(dict):
        def __missing__(self, key):
            return key

    message = message.format_map(Default(filename=filename))
    title = title.format_map(Default(filename=filename))
    postamble = postamble.format_map(Default(filename=filename))

    def decorated(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            caller = sys._getframe().f_back.f_code.co_name
            name = func.__name__
            timestamp = datetime.datetime.now().isoformat()
            start_t = time.perf_counter()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                stop_t = time.perf_counter()
                print(message, file=sys.stderr)
                print(f"{e}", file=sys.stderr)

                # handle any callbacks
                for f, msg in _global_callbacks.values():
                    if msg:
                        print(msg)
                    f()

                with open(filename, "w") as f:
                    f.write(f"{title}\n")
                    f.write(f"Created: {datetime.datetime.now()}\n")
                    f.write("\nSYSTEM INFO:\n")
                    f.write(f"Platform: {platform.platform()}\n")
                    f.write(f"Python: {pathlib.Path(sys.executable).resolve()}\n")
                    f.write(f"Python version: {sys.version}\n")
                    f.write(f"Python path: {sys.path}\n")
                    f.write(f"sys.argv: {sys.argv}\n")
                    f.write("\nCRASH DATA:\n")
                    f.write(
                        f"{name} called by {caller} at {timestamp} crashed after {stop_t-start_t} seconds\n"
                    )
                    f.write(f"{args=}\n")
                    f.write(f"{kwargs=}\n")
                    for k, v in _global_crash_data.items():
                        f.write(f"{k}: {v}\n")
                    for arg, value in extra.items():
                        f.write(f"{arg}: {value}\n")
                    f.write(f"Error: {e}\n")
                    traceback.print_exc(file=f)
                print(f"Crash log written to '{filename}'", file=sys.stderr)
                print(f"{postamble}", file=sys.stderr)
                sys.exit(1)

        return wrapped

    return decorated


def _increment_filename(filename: str | pathlib.Path) -> pathlib.Path:
    """Increment a filename if it exists, e.g. file.ext -> file (1).ext, and so on.

    Args:
        filename: filename to increment

    Returns:
        pathlib.Path object with incremented filename

    Note: This is a simple implementation that is subject to race conditions.
    Don't use this in cases where a race condition is likely to occur.
    """
    filename = pathlib.Path(filename)
    if not filename.exists():
        return filename
    stem = filename.stem
    suffix = filename.suffix
    i = 1
    while True:
        new_filename = pathlib.Path(f"{stem} ({i}){suffix}")
        if not new_filename.exists():
            return new_filename
        i += 1
