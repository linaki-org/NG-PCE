from dataclasses import dataclass, field
from typing import Any

@dataclass
class PropAssign:
    name: str
    value: Any

@dataclass
class StateAssign:
    obj: str | None   # None = implicit self
    prop: str
    value: Any

@dataclass
class ObjAction:
    obj: str | None   # None = bare call like "fracture"
    action: str
    arg: Any = None

@dataclass
class EventName:
    actor: str
    verb: str | None = None
    target: str | None = None

@dataclass
class Event:
    trigger: EventName
    body: list

@dataclass
class Scene:
    name: str
    properties: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

@dataclass
class Hotspot:
    name: str
    scene: str
    properties: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

@dataclass
class Exit:
    name: str
    scene: str
    properties: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

@dataclass
class DynamicValue:
    value: str