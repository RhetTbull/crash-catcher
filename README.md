# Crash Catcher

Crash Catcher is a decorator to catch exceptions in a python function and log them to a file. Supports optional callbacks to perform cleanup operations before the crash log is written.

## Synopsis

```python
"""Demo crash_catcher with a simple example."""

from .crash_catcher import (
    crash_catcher,
    register_crash_callback,
    set_crash_data,
    unregister_crash_callback,
)


@crash_catcher(
    filename="crash_catcher.log",
    message="The app has crashed",
    title="Crash catcher demo",
    postamble="Please file a bug report with contents of '{filename}'",
    overwrite=True,
    extra={"extra": "data"},
)
def demo_crash_catcher():
    """Demo crash_catcher decorator"""
    set_crash_data("globals", globals())
    set_crash_data("locals", locals())
    print("Hello world")

    # some critical section that requires cleanup
    callback_id = register_crash_callback(lambda: print("Cleaning up..."))

    # any uncaught exception causes the crash_catcher decorator to catch the crash
    raise ValueError("Oh no, the app has crashed!")

    # exit critical section and deregister callback
    unregister_crash_callback(callback_id)


if __name__ == "__main__":
    demo_crash_catcher()
```

## Rationale

This decorator is intended to be used with python command line apps where you want to catch exceptions and display a nice message to the user instead of a stack trace. The stack trace and other crash data is logged to a file which you can then direct the user to send to you.

Instead of a traceback, the user sees a message like this:

```
Hello world
The app has crashed
Oh no, the app has crashed!
Cleaning up...
Crash log written to 'crash_catcher.log'
Please file a bug report with contents of 'crash_catcher.log'
```

## Installation

```bash
python3 -m pip install crash-catcher
```

## Usage

Import `crash_catcher` and apply the decorator to your main function. The decorator takes the following arguments:

- `filename`: The name of the file to write the crash log to.
- `message`: The message to display to the user when the app crashes.
- `title`: The title of the message box displayed to the user.
- `postamble`: Optional text to display to the user after the message. Defaults to None.
- `overwrite`: Whether to overwrite the crash log file if it already exists. If False, the crash filename will be incremented until a non-existent filename is found. Defaults to False.
- `**extra`: Optional **kwargs of extra data to include in the crash log.

For example:

```python
from crash_catcher import crash_catcher

@crash_catcher(
    filename="crash_catcher.log",
    message="The app has crashed",
    title="Crash catcher demo",
    postamble="Please file a bug report with contents of '{filename}'",
    overwrite=True,
    extra="data",
)
def main():
    # do stuff
    raise ValueError("Oh no, the app has crashed!")

if __name__ == "__main__":
    main()
```

In the decorated function, you may use the following utility functions to change the behavior of the crash catcher:

- `set_crash_data(key, value)`: Set a key/value pair in the crash log. The key and value will be printed to the crash log.
- `register_crash_callback(func: Callable[[], None], message: str | None = None) -> int`: Register a callback to be called when the app crashes. The callback will be called before the crash log is written and can be used to perform any cleanup operations, for example, deleting files or closing database connections. The optional message will be printed when calling the callback. Returns a callback id which can be used to unregister the callback with `unregister_crash_callback`.
- `unregister_crash_callback(callback_id: int)`: Unregister a callback. The callback will no longer be called when the app crashes. Use the callback_id returned by `register_crash_callback` to unregister the callback.

## Crash Log

The crash log file contains the following information:

- Title as defined by the `title` argument to the decorator.
- Date and time of the crash.
- System information including platform, python version, python path, and command line arguments.
- Crash data including any data set with `set_crash_data` and the traceback of the crash.

```
Crash catcher demo
Created: 2023-11-13 17:11:09.302745

SYSTEM INFO:
Platform: macOS-13.5.1-x86_64-i386-64bit
Python: /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11
Python version: 3.11.6 (v3.11.6:8b6ee5ba3b, Oct  2 2023, 11:18:21) [Clang 13.0.0 (clang-1300.0.29.30)]
Python path: [...]
sys.argv: ['myapp.py']

CRASH DATA:
demo_crash_catcher called by <module> at 2023-11-13T17:11:09.301593 crashed after 3.982799535151571e-05 seconds
args=()
kwargs={}
globals: {...}
locals: {...}
extra: {'extra': 'data'}
Error: Oh no, the app has crashed!
Traceback (most recent call last):
  File "myapp.py", line 115, in wrapped
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "myapp.py", line 29, in demo_crash_catcher
    raise ValueError("Oh no, the app has crashed!")
ValueError: Oh no, the app has crashed!
```
