"""Lark Grammar definition for the PCScript language."""

pcs_grammar = r"""
    %declare _INDENT _DEDENT

    %import common.CNAME -> NAME
    %import common.ESCAPED_STRING -> STRING
    %import common.NUMBER
    %import common.WS_INLINE
    
    COMMENT: /#[^\n]*/
    _NEWLINE: /(\r?\n[\t ]*)+/
    
    %ignore WS_INLINE
    %ignore COMMENT
    
    start: (_NEWLINE | definition)*
    
    definition: scene_def | hotspot_def | exit_def
    
    scene_def:     NAME "is" "scene" ":" def_block
    hotspot_def:  NAME "is" "hotspot" "of" NAME ":" def_block
    exit_def: NAME "is" "exit" "of" NAME ":" def_block
    
    def_block: _NEWLINE _INDENT def_statement+ _DEDENT
    
    def_statement: prop_assign _NEWLINE?
             | event_trigger
             
    prop_assign: NAME ":" value          // simple:  title = "Kitchen"
           | NAME "." NAME ":" value  // scoped:  sound = ambient:music
    
    cmd_block: _NEWLINE _INDENT cmd_statement+ _DEDENT

    cmd_statement: obj_action _NEWLINE?   // bernard:say "hi"  or  dish:fracture
                 | state_assign _NEWLINE? // game:flag = true
    
    obj_action:   (NAME ".")? NAME value?   // object:method optional_arg
    state_assign: NAME "." NAME ":" value // object.prop: value
    
    assignment:  NAME "=" value
    value:       STRING | NUMBER | NAME
    
    action_call: NAME "." NAME value
    
    event_trigger: "@" event_head ":" cmd_block

    event_head: NAME
               | NAME "with" NAME  -> interaction  // @bernard.use with floor
               | NAME "." NAME             -> verb_only    // @bernard.look
               | NAME "." NAME "with" NAME
    
"""

if __name__=="__main__":
    import __init__