"""Error logger/crash reporter decorator"""

from .crash_catcher import (
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
