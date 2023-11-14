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
    extra1="xyzzy",
    extra2="fizzbuzz",
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
