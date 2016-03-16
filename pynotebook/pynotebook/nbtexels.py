# -*- coding: latin-1 -*-


from .textmodel.container import Container
from .textmodel.textmodel import TextModel, dump_range
from .textmodel.texeltree import Texel, Glyph, NL

import wx



def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    return model



class Cell(Container):
    # XXX currently there is only one cell type. In future we should
    # also have text cells or cells for different scripting
    # languages. We should have a generla ScriptCell.

    client_name = 'direct python'

    def __init__(self, input, output, number = 0, **kwargs):
        assert isinstance(input, Texel)
        assert isinstance(output, Texel)
        self.input = input
        self.output = output
        self.number = number
        Container.__init__(self, **kwargs)

    def get_empties(self):
        return NL, NL, NL

    def get_emptychars(self):
        return '\n\n\n'

    def get_content(self):
        return self.input, self.output

    def get_kwds(self):
        kwds = Container.get_kwds(self)
        kwds['number'] = self.number
        return kwds



class NotFound(Exception): pass

def find_cell(texel, i, i0=0):
    if isinstance(texel, Cell):
        return i0, texel
    elif texel.is_group:
        for j1, j2, child in texel.iter_childs():
            if j1<=i<j2:
                return find_cell(child, i-j1, i0+j1)
    raise NotFound()



class BitmapRGB(Glyph):
    def __init__(self, data, size):
        self.data = data
        self.size = size

    def __repr__(self):
        return 'BitmapRGB(...)'



class BitmapRGBA(Glyph):
    def __init__(self, data, alpha, size):
        self.data = data
        self.alpha = alpha
        self.size = size

    def __repr__(self):
        return 'BitmapRGB(...)'



