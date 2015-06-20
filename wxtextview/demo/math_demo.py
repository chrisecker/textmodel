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
square root below is defined in only 7 lines of python code. It took
42 more lines to define the graphical representation.

"""

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../textmodel')


from textmodel import listtools
from textmodel.texeltree import NewLine, Group, Characters, grouped, \
    defaultstyle
from textmodel.container import Container
from textmodel.textmodel import TextModel
from wxtextview.layout import Box, Row, Rect, TextBox, IterBox, check_box
from wxtextview.updater import Updater as _Updater
from wxtextview.wxtextview import WXTextView
from wxtextview.wxdevice import WxDevice

from copy import copy as shallowcopy
import wx




class Fraction(Container):
    def __init__(self, denominator, nominator, **kwds):
        self.denominator = denominator
        self.nominator = nominator
        Container.__init__(self, **kwds)

    def get_content(self):
        return self.denominator, self.nominator

    def get_emptychars(self):
        return '(;)'

    def dump_boxes(self, i=0):
        print (" "*i)+"Frac(["
        self.denominator.dump_boxes(i+4)
        self.nominator.dump_boxes(i+4)
        print (" "*i)+"])"



class EntryBox(IterBox):
    # A box which has one empty index position at the end to seperate
    # the content from the following boxes.
    def __init__(self, boxes, device=None):
        if device is not None:
            self.device = device
        self.content = Row(boxes, device=device)
        self.length = self.content.length+1
        self.height = self.content.height
        self.depth = self.content.depth
        self.width = self.content.width

    def iter(self, i, x, y):
        content = self.content
        yield i, i+len(content), x, y, content



class FractionBox(IterBox):
    def __init__(self, denomboxes, nomboxes, style=defaultstyle,
                 device=None):
        if device is not None:
            self.device = device
        self.style = style
        self.denominator = EntryBox(denomboxes, device)
        self.nominator = EntryBox(nomboxes, device)
        self.length = len(self.denominator)+len(self.nominator)+1
        self.layout()

    def iter(self, i, x, y):
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
        IterBox.draw(self, x, y, dc, styler)
        h = self.denominator.height+self.denominator.depth
        dc.DrawLine(x, y+h, x+self.width, y+h)

    def extend_range(self, i1, i2):
        for i in (0, len(self.denominator), len(self)-1):
            if i1<= i<i2:
                return 0, len(self)
        return IterBox.extend_range(self, i1, i2)

    def can_leftappend(self):
        # There is one empty index position at index 0, so that
        # inserting in position 0 is not possible. We therefore
        # signal, that we can't append to the left side.
        return False



class Root(Container):
    def __init__(self, content, **kwds):
        self.content = content
        Container.__init__(self, **kwds)

    def get_content(self):
        return [self.content]



class RootBox(IterBox):
    def __init__(self, boxes, device=None):
        if device is not None:
            self.device = device
        content = self.content = EntryBox(boxes, device)
        self.length = len(content)+1
        self.width = content.width+12
        self.height = content.height+5
        self.depth = content.depth

    def iter(self, i, x, y):
        content = self.content
        yield i+1, i+len(content), x+8, y+5, content

    def draw(self, x, y, dc, styler):
        IterBox.draw(self, x, y, dc, styler)
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
            IterBox.draw_selection(self, i1, i2, x, y, dc)

    def extend_range(self, i1, i2):
        for i in (0, len(self)-1):
            if i1<= i<i2:
                return 0, len(self)
        return IterBox.extend_range(self, i1, i2)

    def can_leftappend(self):
        return False




class Updater(_Updater):
    def Fraction_handler(self, texel, i1, i2):
        denomboxes = self.create_boxes(texel.denominator)
        nomboxes = self.create_boxes(texel.nominator)
        return [FractionBox(denomboxes, nomboxes,
                            style=texel.get_style(0),
                            device=self.device)]

    def Root_handler(self, texel, i1, i2):
        boxes = self.create_boxes(texel.content)
        return [RootBox(boxes, device=self.device)]


class WXMathTextView(WXTextView):
    def create_updater(self):
        return Updater(
            self.model,
            device=WxDevice(),
            maxw=self._maxw)



def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    return model

def init_testing(redirect=True):
    app = wx.App(redirect=redirect)
    model = TextModel(u"")

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
    frac = Fraction(Characters(u'Zähler'), Characters(u'Nenner'))
    factory = Updater(TextModel()) # not very nice
    box = factory.Fraction_handler(frac, 0, len(frac))[0]
    assert len(box) == len(frac)
    assert check_box(box, frac)
    assert check_box(box.nominator)
    assert check_box(box.denominator)

    model = ns['model']
    model.insert(len(model), mk_textmodel(frac))
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
    ns = init_testing(False)
    model = ns['model']
    model.remove(0, len(model))
    model.insert(0, TextModel(__doc__))

    text = """Try to edit the following formulas:

        tan(x) = """
    model.insert(len(model), TextModel(text))
    frac = Fraction(Characters(u'sin(x)'), Characters(u'cos(x)'))
    model.insert(len(model), mk_textmodel(frac))
    model.insert(len(model), TextModel("\n\n        "))
    root = Root(Characters(u'2'))
    model.insert(len(model), mk_textmodel(root))
    model.insert(len(model), TextModel("= 1.4142135623730951 ...\n"))
    model.insert(len(model), TextModel("\n\n        "))

    i = len(model)
    root = Root(Characters(u''))
    for j in range(4):
        model.insert(i+j, mk_textmodel(root))
    model.insert(i+4, TextModel("2"))
    model.insert(len(model), TextModel("= 1.04427378243 ...\n"))

    view = ns['view']
    view.index = len(model)
    return ns

def test_02():
    "insert/remove"
    ns = init_testing(False)
    model = ns['model']
    frac = Fraction(Characters(u'Zähler'), Characters(u'Nenner'))
    model.insert(0, mk_textmodel(frac))
    model.insert_text(6, 'test')
    model.remove(6, 7)

def test_03():
    ns = init_testing(False)
    model = mk_textmodel(Characters('0123456789'))
    frac = mk_textmodel(
        Fraction(Characters(u'Zähler'), Characters(u'Nenner')))
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
    frac = Fraction(Characters(u'Zähler'), Characters(u'Nenner'))
    model.insert(0, mk_textmodel(frac))
    root = Root(Characters(u'1+x'))
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

    frac = Fraction(Characters(u'Zähler'), Characters(u'Nenner'))
    model.insert(1, mk_textmodel(frac))
    model.insert_text(1, 'Bruch = ')
    n = len(model)
    root = Root(Characters(u'1+x'))
    model.insert(n, mk_textmodel(root))
    model.insert_text(n, '\nWurzel = ')

    view = ns['view']
    view.index = 5
    view.selection = 3, 6
    return ns


def test_06():
    "Fraction"

    box1 = FractionBox([TextBox(u'Zähler')], [TextBox(u'Nenner')])
    box2 = FractionBox([TextBox(u'Zähler1')], [box1])
    assert box2.depth == box1.height+box1.depth-box1.m/2.

    # Jetzt mit echten Abmessungen
    ns = init_testing(False)
    model = ns['model']
    model.remove(0, len(model))
    frac = Fraction(Characters(u'Zähler'), Characters(u'Nenner'))
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
    #testing.pyshell(ns)
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
