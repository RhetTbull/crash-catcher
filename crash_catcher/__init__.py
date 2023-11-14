"""Error logger/crash reporter decorator"""

from .crash_catcher import (
    _reset_crash_catcher,
    crash_catcher,
    register_crash_callback,
    set_crash_data,
    unregister_crash_callback,
)

__all__ = [
    "crash_catcher",
    "register_crash_callback",
    "set_crash_data",
    "unregister_crash_callback",
]
