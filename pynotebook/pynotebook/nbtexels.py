# -*- coding: latin-1 -*-


from .textmodel.textmodel import TextModel, dump_range
from .textmodel.texeltree import Texel, T, G, NL, Container, Single, \
    iter_childs, dump

import wx



def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    return model



class Cell(Container):
    pass


class TextCell(Cell):
    text = property(lambda s:s.childs[1])
    def __init__(self, text, **kwargs):
        assert isinstance(text, Texel)
        self.childs = [NL, text, NL]
        self.compute_weights()



class ScriptingCell(Cell):

    client_name = 'direct python'

    input = property(lambda s:s.childs[1])
    output = property(lambda s:s.childs[3])

    def __init__(self, input, output, number = 0, **kwargs):
        assert isinstance(input, Texel)
        assert isinstance(output, Texel)
        self.number = number
        self.childs = [NL, input, NL, output, NL]
        self.compute_weights()




class NotFound(Exception): pass

def find_cell(texel, i, i0=0):
    if isinstance(texel, Cell):
        return i0, texel
    elif texel.is_group:
        for j1, j2, child in iter_childs(texel):
            if j1<=i<j2:
                return find_cell(child, i-j1, i0+j1)
    raise NotFound()



class BitmapRGB(Single):
    def __init__(self, data, size):
        self.data = data
        self.size = size

    def __repr__(self):
        return 'BitmapRGB(...)'



class BitmapRGBA(Single):
    def __init__(self, data, alpha, size):
        self.data = data
        self.alpha = alpha
        self.size = size

    def __repr__(self):
        return 'BitmapRGB(...)'



def test_00():
    "TextCell"
    cell = TextCell(T('0123456789'))
    model = TextModel()
    cellmodel = mk_textmodel(cell)
    model.insert(0, cellmodel)
    dump(model.texel)
    model.insert_text(4, "xyz")
    dump(model.texel)
