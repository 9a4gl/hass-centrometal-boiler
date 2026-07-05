from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from . import WebBoilerSystem
    from .centrometal_web_boiler import WebBoilerClient


@dataclass
class CentrometalRuntimeData:
    client: "WebBoilerClient"
    system: "WebBoilerSystem"
    stop_listener: Callable[[], None] | None = None
