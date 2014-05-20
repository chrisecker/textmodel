# -*- coding: latin-1 -*-


"""
Demo of Math Typesetting
~~~~~~~~~~~~~~~~~~~~~~~~

The purpose of this demo is to show how to do some non trivial
typesetting. 

Usually text is linear, i.e. it consists of characters and one
character follows the other. This is what simple text editor can
display. However in real life, text can be nested. This means that
there are certain text elements which itself contain texts. Think of
tables or math formulas.

"""

import sys
sys.path.insert(0, '..')

from textmodel import listtools
from textmodel.base import NewLine, Group, Characters, group, defaultstyle
from textmodel.container import Container, EMPTY
from textmodel.textmodel import TextModel
from wxtextview.layout import Box, Row, Rect, TextBox, IterBox, check_box
from wxtextview.layout import Factory as _Factory
from wxtextview.wxtextview import WXTextView
from wxtextview.wxdevice import WxDevice

from copy import copy as shallowcopy
import wx




class Fraction(Container):
    def __init__(self, denominator=(), nominator=()):
        self.denominator = group(denominator)
        self.nominator = group(nominator)

    def get_childs(self):
        return EMPTY, self.denominator, EMPTY, \
            self.nominator, EMPTY

    def from_childs(self, childs):
        return self.__class__(childs[1:2], childs[3:4])
    
    def dump(self, i=0):
        print (" "*i)+"Frac(["
        self.denominator.dump(i+4)
        self.nominator.dump(i+4)
        print (" "*i)+"])"



class EmptyBox(Box):
    length = 1
    def draw(self, x, y, dc, styler):
        pass

    def draw_selection(self, i1, i2, x, y, dc):
        pass

EMPTY_BOX = EmptyBox()


class EntryBox(IterBox):
    # hat am Ende eine Leerstelle: 1235789x
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



def extend_range_seperated(iterbox, i1, i2):
    # Extend-Range für seperierte Kindfelder. I1 und i2 werden
    # ausgeweitet, wenn mehr als ein Kind enthalten sind. 
    last = 0
    for j1, j2, x, y, child in iterbox.iter(0, 0, 0):
        if not (i1<j2 and j1<i2):
            continue
        if i1 < j1 or i2>j2:
            return min(i1, 0), max(i2, len(iterbox))
        k1, k2 = child.extend_range(i1-j1, i2-j1)
        return min(i1, k1+j1), max(i2, k2+j1)
    return i1, i2


class FractionBox(IterBox):
    # x123456789
    def __init__(self, denomboxes, nomboxes, style=defaultstyle, device=None):
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
        j1 = i+1
        j2 = j1+len(d)
        height = self.height
        width = self.width
        yield j1, j2, x+0.5*(width-d.width), y, d
        y += max(self.m, d.height+d.depth)
        j1 = j2
        j2 += len(n) 
        yield j1, j2, x+0.5*(width-n.width), y, n

    def layout(self):
        # w und h bestimmen
        m = self.device.measure("M", self.style)[1]
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
        return extend_range_seperated(self, i1, i2)
        
    def can_leftappend(self):
         return False

        

class Root(Container):
    def __init__(self, content=()):
        self.content = group(content)

    def get_childs(self):
        return EMPTY, self.content, EMPTY

    def from_childs(self, childs):
        return self.__class__(childs[1:2])
    


class RootBox(IterBox):
    # x123456789
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
            
    def can_leftappend(self):
        return False

    def extend_range(self, i1, i2):
        for i in (0, len(self)-1):
            if i1<= i<i2:
                return 0, len(self)
        return extend_range_seperated(self, i1, i2)


class Factory(_Factory):
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
    def create_factory(self):
        self.factory = Factory(WxDevice())
    


def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    model.linelengths = texel.get_linelengths()
    return model

def init_testing(redirect=True):
    app = wx.App(redirect=redirect)
    model = TextModel(u"")

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = WXMathTextView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    layout = view.updater.layout
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()    
    return locals()

def test_00():
    ns = init_testing(False)
    frac = Fraction([Characters(u'Zähler')], [Characters(u'Nenner')])
    factory = Factory()
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
    
    layout = ns['layout']
    assert check_box(layout)

def test_01():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    model.insert(0, TextModel(__doc__))

    text = """Try to edit the following formulas:

        tan(x) = """
    model.insert(len(model), TextModel(text))
    frac = Fraction([Characters(u'sin(x)')], [Characters(u'cos(x)')])
    model.insert(len(model), mk_textmodel(frac))
    model.insert(len(model), TextModel("\n\n        "))
    root = Root([Characters(u'2')])
    model.insert(len(model), mk_textmodel(root))
    model.insert(len(model), TextModel("= 1.4142135623730951\n"))
    view = ns['view']
    view.cursor = len(model)
    return ns

def test_02():
    "insert/remove"
    ns = init_testing(False)
    model = ns['model']
    frac = Fraction([Characters(u'Zähler')], [Characters(u'Nenner')])
    model.insert(0, mk_textmodel(frac))
    model.insert_text(6, 'test')
    model.remove(6, 7)

def test_03():
    ns = init_testing(False)
    model = mk_textmodel(Characters('0123456789'))
    frac = mk_textmodel(Fraction([Characters(u'Zähler')], [Characters(u'Nenner')]))
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
    frac = Fraction([Characters(u'Zähler')], [Characters(u'Nenner')])
    model.insert(0, mk_textmodel(frac))
    root = Root([Characters(u'1+x')])
    model.insert(2, mk_textmodel(root))

    view = ns['view']
    view.cursor = 5
    view.selection = 3, 6    
    return ns


def test_05():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    model.insert_text(0, '\n')
                 
    frac = Fraction([Characters(u'Zähler')], [Characters(u'Nenner')])
    model.insert(1, mk_textmodel(frac))
    model.insert_text(1, 'Bruch = ')
    n = len(model)
    root = Root([Characters(u'1+x')])
    model.insert(n, mk_textmodel(root))
    model.insert_text(n, '\nWurzel = ')

    view = ns['view']
    view.cursor = 5
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
    frac = Fraction([Characters(u'Zähler')], [Characters(u'Nenner')])
    model.insert(0, mk_textmodel(frac))
    model.insert(14, mk_textmodel(frac))    

    layout = ns['layout']
    box2 = layout.childs[0].childs[0].childs[0]
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
    from textmodel import alltests
    import sys

    if len(sys.argv) <= 1:
        sys.argv.append('demo_00')
    alltests.dotests()
    
