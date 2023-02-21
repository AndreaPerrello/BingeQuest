import json


def replace_characters(json_string):
    forbidden_chars = [{'old': '\n', 'new': '\u2424'}, {'old': '\/', 'new': '/'}, {'old': '\'', 'new': '%27'}]
    for char in forbidden_chars:
        json_string = str.replace(json_string, char['old'], char['new'])
    return json_string


def decode_json(json_str):
    return json.loads(replace_characters(json_str))


def encode_json(res_obj):
    return json.dumps(res_obj)
