# -*- coding: latin-1 -*-


from .textmodel.textmodel import TextModel
from .textmodel.texeltree import NULL_TEXEL

from .nbtexels import ScriptingCell, mk_textmodel

import re


def get_cells(texel):
    if isinstance(texel, ScriptingCell):
        return [texel]
    r = []
    for i1, i2, child in texel.iter_childs():
        r.extend(get_cells(child))
    return r


def totext(model):
    r = []
    for cell in get_cells(model.texel):
        text = cell.input.get_text()
        if text:
            r.append(("[In %i]:\n"%cell.number)+text)
        text = cell.output.get_text()
        if text:
            r.append(("[Out %i]:\n"%cell.number)+text)
    return u"\n".join(r)


rx_out = re.compile('\[Out\s*(\w*)\]\:$').match
rx_in = re.compile('\[In\s*(\w*)\]\:$').match

def fromtext(s, ScriptingCell):
    model = TextModel()
    cells = []
    l = []
    def create_texel(l):
        texel = TextModel(u'\n'.join(l)).texel
        del l[:]
        return texel

    def append_cell():
        cells.append(ScriptingCell(intexel, outtexel))


    intexel = outtexel = NULL_TEXEL
    for line in reversed(s.split('\n')):
        if rx_in(line):
            intexel = create_texel(l)
            if not (intexel == outtexel == NULL_TEXEL):                
                append_cell()
                intexel = outtexel = NULL_TEXEL
        elif rx_out(line):
            outtexel = create_texel(l)
        else:
            l.insert(0, line)
    if l:
        intexel = create_texel(l)
    if not (intexel == outtexel == NULL_TEXEL):                
        append_cell()
    model = TextModel()
    for cell in cells:
        model.insert(0, mk_textmodel(cell))
    return model



