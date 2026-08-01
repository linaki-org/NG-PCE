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
    action: str
    arg: Any = None

@dataclass
class EventName:
    actor: str
    verb: str | None = None
    target1: str | None = None
    target2: str | None = None

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
class Ambient:
    name: str
    scene: str
    properties: dict = field(default_factory=dict)

@dataclass
class DynamicValue:
    value: str


@dataclass
class TupleValue:
    first: Any
    second: Any

    def __iter__(self):
        yield self.first
        yield self.second

    def __len__(self):
        return 2

    def __getitem__(self, index):
        return (self.first, self.second)[index]

    def __eq__(self, other):
        if isinstance(other, tuple):
            return (self.first, self.second) == other
        return super().__eq__(other)