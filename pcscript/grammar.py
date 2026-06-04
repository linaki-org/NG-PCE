"""Lark Grammar definition for the PCScript language."""

pcs_grammar = r"""
    %declare _INDENT _DEDENT

    %import common.CNAME -> NAME
    %import common.ESCAPED_STRING -> STRING
    %import common.NUMBER
    %import common.WS_INLINE

    COMMENT: /#[^\n]*/
    _NEWLINE: /(\r?\n[\t ]*(#[^\n]*)?)+/

    %ignore WS_INLINE
    %ignore COMMENT

    start: (_NEWLINE | definition)*

    definition: scene_def | hotspot_def | exit_def | ambient_def | script_def | dialogue_def

    scene_def:   NAME "is" "scene" ":" def_block
    hotspot_def: NAME "is" "hotspot" "of" NAME ":" def_block
    exit_def:    NAME "is" "exit" "of" NAME ":" def_block
    ambient_def: NAME "is" "ambient" "of" NAME ":" def_block
    script_def:  NAME "is" "script" ":" cmd_block
    dialogue_def:NAME "is" "dialogue" ":" dialogue_block

    def_block: _NEWLINE _INDENT def_statement+ _DEDENT

    def_statement: prop_assign _NEWLINE?
                 | event_trigger

    prop_assign: NAME ":" value

    cmd_block: (_NEWLINE _INDENT)? cmd_statement+ (_DEDENT | _NEWLINE)

    cmd_statement: state_assign _NEWLINE?
                 | action _NEWLINE?

    state_assign: NAME "." NAME ":" value
    action: NAME value
    
    dialogue_block: _NEWLINE _INDENT branch_def+ _DEDENT
    branch_def: NAME ":" branch_block
    branch_block: _NEWLINE _INDENT option_def+ _DEDENT
    option_def: "-" option_block
    option_block: (prop_assign _NEWLINE?)+

    value: STRING | NUMBER | BOOL | NAME

    BOOL.2: "true" | "false"

    event_trigger: "@" event_head ":" cmd_block

    event_head: NAME NAME "on" NAME  -> interaction
              | NAME                 -> simple
"""

if __name__=="__main__":
    import __init__