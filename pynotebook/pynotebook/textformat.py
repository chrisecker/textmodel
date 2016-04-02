# -*- coding: latin-1 -*-


from .textmodel.textmodel import TextModel
from .textmodel.texeltree import NULL_TEXEL

from .nbtexels import Cell, TextCell, ScriptingCell, mk_textmodel

import re


def get_cells(texel):
    if isinstance(texel, Cell):
        return [texel]
    r = []
    for i1, i2, child in texel.iter_childs():
        r.extend(get_cells(child))
    return r


def totext(model):
    r = []
    for cell in get_cells(model.texel):
        if isinstance(cell, TextCell):
            text = cell.text.get_text()
            r.append("[Text]:\n"+text)
        else:
            text = cell.input.get_text()
            if text:
                r.append(("[In %i]:\n"%cell.number)+text)
            text = cell.output.get_text()
            if text:
                r.append(("[Out %i]:\n"%cell.number)+text)
    return u"\n".join(r)


rx_out = re.compile('\[Out\s*(\w*)\]\:$').match
rx_in = re.compile('\[In\s*(\w*)\]\:$').match
rx_text = re.compile('\[Text\]\:$').match

def fromtext(s, ScriptingCell=ScriptingCell):
    model = TextModel()
    cells = []
    l = []
    fields = [NULL_TEXEL, NULL_TEXEL]
    mode = None
    number = None
    IN = "IN"
    OUT = "OUT"
    TEXT = "TEXT"

    def create_texel():
        texel = TextModel(u'\n'.join(l)).texel
        del l[:]
        return texel

    def flush():
        texel = create_texel()
        if not mode:
            return
        if mode == TEXT:
            cell = TextCell(texel)
        else:
            if mode == IN:
                fields[0] = texel
            else:
                fields[1] = texel
            cell = ScriptingCell(*fields)
            fields[0] = fields[1] = NULL_TEXEL
        cells.append(cell)

    
    for line in s.split('\n'):
        if rx_in(line):
            flush()
            mode = IN
        elif rx_out(line):
            if mode != IN:
                flush()
            else:
                fields[0] = create_texel()
            mode = OUT
        elif rx_text(line):
            flush()
            mode = TEXT
        else:
            l.append(line)
    if l:
        flush()
    model = TextModel()
    for cell in cells:
        model.append(mk_textmodel(cell))
    return model


def test_00():
    text = """[In 1]:
1+2
[Out 2]:
3
[Text]:
Zeile 1
Zeile 2
"""
    m = fromtext(text)
    #m.texel.dump()
    print totext(m)
    t = totext(m)
    print repr(text)
    print repr(t)
    assert t == text
