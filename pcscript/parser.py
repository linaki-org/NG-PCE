from lark import Lark, Transformer
from .grammar import pcs_grammar
from lark.indenter import Indenter
from .dataclasses import *


class PCIndenter(Indenter):
    NL_type = "_NEWLINE"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_indent = False
    tab_len = 8

class PCTransformer(Transformer):

    def start(self, items):
        return [i for i in items if i is not None]

    def definition(self, items):
        return items[0]

    def scene_def(self, items):
        name, statements = str(items[0]), items[1]
        scene = Scene(name=name)
        for s in statements:
            if isinstance(s, PropAssign): scene.properties[s.name] = s.value
            elif isinstance(s, Event):    scene.events.append(s)
        return scene

    def hotspot_def(self, items):
        name, scene_name, statements = str(items[0]), str(items[1]), items[2]
        hotspot = Hotspot(name=name, scene=scene_name)
        for s in statements:
            if isinstance(s, PropAssign): hotspot.properties[s.name] = s.value
            elif isinstance(s, Event):    hotspot.events.append(s)
        return hotspot

    def def_block(self, items):     return items
    def cmd_block(self, items):     return items
    def def_statement(self, items): return items[0]
    def cmd_statement(self, items): return items[0]

    def prop_assign(self, items):
        return PropAssign(name=str(items[0]), value=items[1])

    def state_assign(self, items):
        if len(items) == 2:
            # bare: prop = value (implicit self)
            return StateAssign(obj=None, prop=str(items[0]), value=items[1])
        else:
            # obj.prop = value
            return StateAssign(obj=str(items[0]), prop=str(items[1]), value=items[2])

    def obj_action(self, items):
        if len(items) == 1:
            # bare: fracture
            return ObjAction(obj=None, action=str(items[0]))
        elif len(items) == 2:
            if isinstance(items[1], str):
                # obj.action
                return ObjAction(obj=str(items[0]), action=str(items[1]))
            else:
                # action value (bare with arg)
                return ObjAction(obj=None, action=str(items[0]), arg=items[1])
        else:
            # obj.action value
            return ObjAction(obj=str(items[0]), action=str(items[1]), arg=items[2])

    # Event head variants
    def interaction(self, items):
        return EventName(actor=str(items[0]), verb=str(items[1]), target=str(items[2]))

    def verb_only(self, items):
        return EventName(actor=str(items[0]), verb=str(items[1]))

    def simple(self, items):
        return EventName(actor=str(items[0]))

    def event_trigger(self, items):
        return Event(trigger=items[0], body=items[1])

    def value(self, items):
        s = str(items[0])
        if s in ("true", "false"):              return s == "true"
        if s.startswith('"') and s.endswith('"'): return s[1:-1]
        try:    return int(s)
        except ValueError: pass
        try:    return float(s)
        except ValueError: pass
        return s



PCS_parser = Lark(
    pcs_grammar,
    parser="earley",
    propagate_positions=False,
    maybe_placeholders=False,
    postlex=PCIndenter(),
)
