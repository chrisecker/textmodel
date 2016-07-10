# -*- coding: latin-1 -*-


"""Demo of Math Typesetting
~~~~~~~~~~~~~~~~~~~~~~~~

The purpose of this demo is to show how to do typesetting of nested
texts.

Very often text is just an array of consecutive characters. This is
what most text editor can display. However in real life, text can be
nested such that there are text elements which itself contain
texts. Think of tables or math formulas.

Defining new and nested elements is possible in the textmodel
library. And is actualy not too difficult. The data model of the
square root below is defined in only 4 lines of python code. It took
42 more lines to define the graphical representation.

"""

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../textmodel')


from textmodel import texeltree
from textmodel.texeltree import NewLine, Group, Container, T, TAB, grouped, length
from textmodel.styles import get_style
from textmodel.textmodel import TextModel
from wxtextview.boxes import Box, Row, Rect, TextBox, check_box
from wxtextview.simplelayout import Builder as _Builder
from wxtextview.wxtextview import WXTextView
from wxtextview.wxdevice import WxDevice

from copy import copy as shallowcopy
import wx




EMPTY = Group([])

class Fraction(Container):
    def __init__(self, denominator, nominator):
        self.childs = [TAB, denominator, TAB, nominator, TAB]
        self.compute_weights()


class Root(Container):
    def __init__(self, content):
        self.childs = [TAB, content, TAB]
        self.compute_weights()


def _mk_textmodel(texel):
    model = MathTextModel()
    model.texel = texel
    return model



class MathTextModel(TextModel):
    def insert_fraction(self, i):
        return self.insert(i, _mk_textmodel(Fraction(EMPTY, EMPTY)))

    def insert_root(self, i):
        return self.insert(i, _mk_textmodel(Root(EMPTY)))





class EntryBox(Box):
    # A box which has one empty index position at the end to seperate
    # the content from the following boxes.
    def __init__(self, boxes, device=None):
        if device is not None:
            self.device = device
        content = self.content = Row(boxes, device=device)
        self.length = content.length+1
        self.height = content.height
        self.depth = content.depth
        self.width = content.width

    def __len__(self):
        return self.length

    def iter_boxes(self, i, x, y):
        yield 0, self.length-1, x, y, self.content



class FractionBox(Box):
    def __init__(self, denomboxes, nomboxes, style={},
                 device=None):
        if device is not None:
            self.device = device
        self.style = style
        self.denominator = EntryBox(denomboxes, device)
        self.nominator = EntryBox(nomboxes, device)
        self.length = len(self.denominator)+len(self.nominator)+1
        self.layout()

    def __len__(self):
        return self.length

    def iter_childs(self): # XXX not needed!
        d = self.denominator
        n = self.nominator
        yield 1, len(d), d
        yield 1+len(d), self.length, n

    def iter_boxes(self, i, x, y):
        d = self.denominator
        n = self.nominator
        j1 = i+1 # the denominator starts at index 1
        j2 = j1+len(d)
        height = self.height
        width = self.width
        yield j1, j2, x+0.5*(width-d.width), y, d
        y += max(self.m, d.height+d.depth)
        j1 = j2
        j2 += len(n)
        yield j1, j2, x+0.5*(width-n.width), y, n

    def layout(self):
        # Determine width and height
        m = self.device.measure("M", self.style)[1] # We use the capital
                                                    # M as a reference
        self.m = m
        nom = self.nominator
        den = self.denominator
        self.height = max(m, den.height+den.depth)+m/2.0
        self.depth = max(0, nom.height+nom.depth-m/2.0)
        self.width = max(nom.width, den.width)

    def draw(self, x, y, dc, styler):
        Box.draw(self, x, y, dc, styler)
        h = self.denominator.height+self.denominator.depth
        dc.DrawLine(x, y+h, x+self.width, y+h)

    def extend_range(self, i1, i2):
        for i in (0, len(self.denominator), len(self)-1):
            if i1<= i<i2:
                return 0, len(self)
        return Box.extend_range(self, i1, i2)

    def can_leftappend(self):
        # There is one empty index position at index 0, so that
        # inserting in position 0 is not possible. We therefore
        # signal, that we can't append to the left side.
        return False





class RootBox(Box):
    def __init__(self, boxes, device=None):
        if device is not None:
            self.device = device
        content = self.content = EntryBox(boxes, device)
        m = self.device.measure("M", {})[1] # We use the capital
                                                    # M as a reference

        self.width = content.width+12
        self.height = max(m, content.height)+5
        self.depth = content.depth
        self.length = len(content)+1

    def __len__(self):
        return self.length

    def iter_boxes(self, i, x, y):
        yield i+1, i+len(self.content), x+8, y+5, self.content

    def draw(self, x, y, dc, styler):
        Box.draw(self, x, y, dc, styler)
        w = self.width
        h = self.height
        w1 = 5
        w2 = self.content.width+2
        points = [
            (x, y+h/2),
            (x+w1/2, y+h),
            (x+w1, y),
            (x+w1+w2, y),
            ]
        dc.DrawLines(points)

    def draw_selection(self, i1, i2, x, y, dc):
        if i1<=0 or i2>=len(self):
            self.device.invert_rect(x, y, self.width, self.height, dc)
        else:
            Box.draw_selection(self, i1, i2, x, y, dc)

    def extend_range(self, i1, i2):
        for i in (0, len(self)-1):
            if i1<= i<i2:
                return 0, len(self)
        return Box.extend_range(self, i1, i2)

    def can_leftappend(self):
        return False




class Builder(_Builder):
    def Fraction_handler(self, texel, i1, i2):
        denominator = texel.childs[1]
        denomboxes = self.create_boxes(denominator, 0, length(denominator))
        nominator = texel.childs[3]
        nomboxes = self.create_boxes(nominator, 0, length(nominator))
        r = FractionBox(denomboxes, nomboxes,
                        style=get_style(texel, 0),
                        device=self.device)
        return [r]

    def Root_handler(self, texel, i1, i2):
        content = texel.childs[1]
        boxes = self.create_boxes(content, 0, length(content))
        return [RootBox(boxes, device=self.device)]


class WXMathTextView(WXTextView):
    def create_builder(self):
        return Builder(
            self.model,
            device=WxDevice(),
            maxw=self._maxw)



def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    return model

def init_testing(redirect=True):
    app = wx.App(redirect=redirect)
    model = MathTextModel(u"")

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = WXMathTextView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()
    return locals()


def test_00():
    ns = init_testing(False)
    model = ns['model']
    view = ns['view']
    model.insert_fraction(len(model))
    model.insert_text(1, 'x')
    #texeltree.dump(model.texel)
    view.layout.dump_boxes(0, 0, 0)
    fractionbox = view.layout.childs[0].childs[0]
    assert isinstance(fractionbox, FractionBox)


def test_000():
    ns = init_testing(False)
    frac = Fraction(T(u'Zähler'), T(u'Nenner'))
    factory = Builder(TextModel()) # not very nice
    box = factory.Fraction_handler(frac, 0, length(frac))[0]
    assert len(box) == length(frac)
    assert check_box(box, frac)
    assert check_box(box.nominator)
    assert check_box(box.denominator)

    model = ns['model']
    #model.insert_text(0, "1234")
    model.insert_fraction(len(model))
    #model.texel.dump()

    model.insert_text(0, "x")
    model.remove(0, 1)
    #model.texel.dump()

    model.insert_text(1, "x")
    model.remove(1, 2)
    #model.texel.dump()

    layout = ns['view'].layout
    assert check_box(layout)

def test_01():
    ns = init_testing(True) #False)
    model = ns['model']
    model.remove(0, len(model))
    model.append_text(__doc__)

    text = """Try to edit the following formulas:

        tan(x) = """
    model.insert(len(model), MathTextModel(text))
    #frac = Fraction(T(u'sin(x)'), T(u'cos(x)'))
    n = len(model)
    model.insert_fraction(len(model))
    model.insert_text(n+2, 'cos(x)')
    model.insert_text(n+1, 'sin(x)')
    model.append_text("\n\n        ")
    model.insert_root(len(model))
    model.append_text("= 1.4142135623730951 ...\n")
    model.append_text("\n\n        ")

    i = len(model)
    for j in range(4):
        model.insert_root(i+j)
    model.insert_text(i+4, "2")
    model.append_text("= 1.04427378243 ...\n")

    view = ns['view']
    view.index = len(model)
    return ns

def test_02():
    "insert/remove"
    ns = init_testing(False)
    model = ns['model']
    frac = Fraction(T(u'Zähler'), T(u'Nenner'))
    model.insert(0, mk_textmodel(frac))
    model.insert_text(6, 'test')
    model.remove(6, 7)

def test_03():
    ns = init_testing(False)
    model = mk_textmodel(T('0123456789'))
    frac = mk_textmodel(
        Fraction(T(u'Zähler'), T(u'Nenner')))
    tmodel = model.get_text()
    tfrac = frac.get_text()
    for i in range(len(tfrac)):
        frac.insert(i, model)

        tmp = tfrac[:i]+tmodel+tfrac[i:]
        #print repr(frac.get_text()), repr(tmp)
        assert tmp == frac.get_text()

        frac.remove(i, i+len(model))
        assert tfrac == frac.get_text()

def test_04():
    ns = init_testing(False)
    model = ns['model']
    frac = Fraction(T(u'Zähler'), T(u'Nenner'))
    model.insert(0, mk_textmodel(frac))
    root = Root(T(u'1+x'))
    model.insert(2, mk_textmodel(root))

    view = ns['view']
    view.index = 5
    view.selection = 3, 6
    return ns


def test_05():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    model.insert_text(0, '\n')

    frac = Fraction(T(u'Zähler'), T(u'Nenner'))
    model.insert(1, mk_textmodel(frac))
    model.insert_text(1, 'Bruch = ')
    n = len(model)
    root = Root(T(u'1+x'))
    model.insert(n, mk_textmodel(root))
    model.insert_text(n, '\nWurzel = ')

    view = ns['view']
    view.index = 5
    view.selection = 3, 6
    return ns


def test_06():
    "Fraction"

    box1 = FractionBox([TextBox(u'Zähler')], [TextBox(u'Nenner')])
    box1.dump_boxes(0, 0, 0)
    box2 = FractionBox([TextBox(u'Zähler1')], [box1])
    print box2.depth
    print box1.height+box1.depth-box1.m/2.0
    #assert box2.depth == box1.height+box1.depth-box1.m/2.0 # XXX Formel geändert

    # Jetzt mit echten Abmessungen
    ns = init_testing(False)
    model = ns['model']
    model.remove(0, len(model))
    frac = Fraction(T(u'Zähler'), T(u'Nenner'))
    model.insert(0, mk_textmodel(frac))
    model.insert(14, mk_textmodel(frac))

    layout = ns['view'].layout
    box2 = layout.childs[0].childs[0]
    box1 = box2.nominator.content.childs[-1]
    assert box2.depth == box1.height+box1.depth-box1.m/2.

    row = layout.childs[0].childs[0]
    assert row.height == box2.height
    assert row.depth == box2.depth
    return ns


def demo_00():
    ns = test_01()
    from wxtextview import testing
    testing.pyshell(ns)
    ns['app'].MainLoop()


def demo_01():
    ns = test_05()
    from wxtextview import testing
    testing.pyshell(ns)
    ns['app'].MainLoop()

def demo_02():
    ns = test_06()
    from wxtextview import testing
    testing.pyshell(ns)
    ns['app'].MainLoop()


if __name__ == '__main__':
    demo_00()
