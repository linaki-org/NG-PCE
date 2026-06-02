"""Parser and abstraction layer for the PCScript language.
PCScript is a YAML-like scripting language made to simplify creation of games in NG-PCE.
It is the successor of the JSON-based way to make games in PCS-ANS, which was highly impractical."""
from .parser import PCS_parser, PCTransformer
from os import listdir
from os.path import join

def parse_string(string_to_parse):
    tree = PCS_parser.parse(string_to_parse)
    print(tree.pretty())
    transformer=PCTransformer()
    result = transformer.transform(tree)
    return result

def parse_file(file_to_parse):
    with open(file_to_parse) as f:
        result=parse_string(f.read())
    return result

def parse_directory(dir_to_parse):
    dir_list=listdir(dir_to_parse)
    result=[]
    for filename in dir_list:
        filepath=join(dir_to_parse, filename)
        result+=parse_file(filepath)
    return result