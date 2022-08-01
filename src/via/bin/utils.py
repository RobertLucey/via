import os


def disable_timers():
    """
    Dsiable things like cleaners that continue execution.
    If you want a script to actually terminate this should be done at
    the top of a script
    """
    os.environ["DISABLE_TIMERS"] = "True"
