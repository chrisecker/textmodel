# -*- coding: latin-1 -*-


from .textmodel.textmodel import TextModel, dump_range
from .textmodel.texeltree import Texel, T, G, NL, Container, Single, \
    iter_childs, dump, NULL_TEXEL, length, grouped, copy

import wx
import StringIO
import base64    



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


def strip_output(texel):
    if isinstance(texel, ScriptingCell):
        clone = texel.__class__(texel.input, NULL_TEXEL)
        return clone
    elif texel.is_group:
        r = []
        for child in texel.childs:
            r.append(strip_output(child))
        return G(r)
    else: 
        return texel


def _split_cell(texel, i):
    if i<=0 or i>=length(texel): return [texel]
    if texel.is_group:
        r = []
        for i1, i2, child in iter_childs(texel):
            if i1<i<i2:
                r.append(split_cell(child, i-i1))
            else:
                r.append(child)
        return r
    if isinstance(texel, Cell):
        r1 = []
        r2 = []
        for i1, i2, child in iter_childs(texel):
            if i1<i<i2:
                j = i-i1
                r1.append(grouped(copy(child, 0, j)))
                r2.append(grouped(copy(child, j, i2-i1)))
            else:
                r1.append(child)
                r2.append(child)
        return [texel.set_childs(r1), texel.set_childs(r2)]        
    return [texel]

def split_cell(texel, i):
    return grouped(_split_cell(texel, i))


class NotFound(Exception): pass

def find_cell(texel, i, i0=0):
    if isinstance(texel, Cell):
        return i0, texel
    elif texel.is_group:
        for j1, j2, child in iter_childs(texel):
            if j1<=i<j2:
                return find_cell(child, i-j1, i0+j1)
    raise NotFound()


def _bitmap_saver(bitmap):
    # we convert images to png before saving to save disk space
    w, h = bitmap.size
    im = wx.ImageFromData(w, h, bitmap.data)
    if isinstance(bitmap, BitmapRGBA):
        im.SetAlphaBuffer(bitmap.alpha)
    output = StringIO.StringIO()
    im.SaveStream(output, wx.BITMAP_TYPE_PNG)

    r = base64.b64encode(output.getvalue())
    return base64.b64encode(output.getvalue())



def _bitmap_loader(data):
    pngdata = base64.b64decode(data)
    stream = StringIO.StringIO(pngdata)
    image = wx.ImageFromStream(stream, type=wx.BITMAP_TYPE_ANY)
    return (image.Width, image.Height), image.Data, image.AlphaData



class BitmapRGB(Single):
    def __init__(self, data, size):
        self.data = data
        self.size = size

    def __repr__(self):
        return 'BitmapRGB(...)'

    def __getstate__(self):
        return _bitmap_saver(self)

    def __setstate__(self, data):
        self.size, self.data = _bitmap_loader(data)[:2]



class BitmapRGBA(Single):
    def __init__(self, data, alpha, size):
        self.data = data
        self.alpha = alpha
        self.size = size

    def __repr__(self):
        return 'BitmapRGB(...)'

    def __getstate__(self):
        return _bitmap_saver(self)

    def __setstate__(self, data):
        self.size, self.data, self.alpha = _bitmap_loader(data)



class Graphics(Single):
    def __init__(self, item, size=(100, 100), frame=False):
        if type(item) is tuple:
            self.items = item
        elif type(item) is list:
            self.items = tuple(item)
        else:
            self.items = (item)
        self.size = size
        self.frame = frame



def test_00():
    "TextCell"
    cell = TextCell(T('0123456789'))
    model = TextModel()
    cellmodel = mk_textmodel(cell)
    model.insert(0, cellmodel)
    dump(model.texel)
    model.insert_text(4, "xyz")
    dump(model.texel)


def test_01():
    import pickle
    app = wx.App()

    im = wx.ArtProvider.GetBitmap(wx.ART_WARNING, size=(128, 128)).ConvertToImage()
    texel = BitmapRGBA(im.GetData(), im.GetAlphaData(), im.GetSize())
    s = pickle.dumps(texel)
    obj = pickle.loads(s)
    s2 = pickle.dumps(obj)
    assert s == s2

    texel = BitmapRGB(im.GetData(), im.GetSize())
    s = pickle.dumps(texel)
    obj = pickle.loads(s)
    s2 = pickle.dumps(obj)
    assert s == s2
