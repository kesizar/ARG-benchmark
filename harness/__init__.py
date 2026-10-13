"""PuzzleBench harness. The model never receives judge files."""

__all__ = ["run"]


def run(*args, **kwargs):
    from harness.loop import run as loop_run

    return loop_run(*args, **kwargs)
