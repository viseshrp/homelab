"""Backend-independent events. Callbacks run on the runner's event loop."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    task: str
    phase: str
    completed: int = 0
    total: int | None = None
    message: str = ""


EventSink = Callable[[Event], None]


def discard(event: Event) -> None:
    pass
