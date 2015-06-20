# -*- coding: latin-1 -*-


"""The updater is responsible for creating and updating the layout. 

The methods build, insert, remove and update return a hierarchical
boxobject (layout).

The Box tree always exceeds the models length by one. The additional
position is the end mark.

"""

from textmodel import listtools
from textmodel import treebase
from textmodel.textmodel import TextModel
from textmodel.texeltree import NewLine, Group, Characters, defaultstyle
from .testdevice import TESTDEVICE
from .layout import TextBox, NewlineBox, TabulatorBox, EmptyTextBox, Row, \
    Paragraph, ParagraphStack, EndBox, check_box
from .linewrap import simple_linewrap






def create_paragraphs(textboxes, maxw=0, Paragraph=Paragraph, \
                      device=TESTDEVICE):
    r = []
    l = []
    for box in textboxes:
        l.append(box)
        if isinstance(box, NewlineBox) or isinstance(box, EndBox):
            if maxw>0:
                rows = simple_linewrap(l, maxw, tabstops=(), device=device)
            else:
                rows = [Row(l, device)]
            r.append(Paragraph(rows, device))
            l = []
    assert not l # There is always one final box which is either a
                 # NewLine or an EndBox. Therefore there is no rest in
                 # l.

    assert listtools.calc_length(r) == listtools.calc_length(textboxes)
    return r


class Factory:
    TextBox = TextBox
    NewlineBox = NewlineBox
    TabulatorBox = TabulatorBox
    EndBox = EndBox
    Paragraph = Paragraph
    ParagraphStack = ParagraphStack

    def __init__(self, device=TESTDEVICE):
        self.device = device

    def get_device(self):
        return self.device

    ### Factory methods
    def create_paragraphs(self, texel, i1, i2):
        # creates a list of paragraphs
        textboxes = self.create_boxes(texel, i1, i2)
        return create_paragraphs(
            textboxes, self._maxw, 
            Paragraph = self.Paragraph,
            device = self.device,
        )

    def create_boxes(self, texel, i1=None, i2=None):
        if i1 is None:
            assert i2 is None
            i1 = 0 
            i2 = len(texel)
        else:
            assert i1 <= i2
            i1 = max(0, i1)
            i2 = min(len(texel), i2)
        if i1 == i2:
            return ()
        name = texel.__class__.__name__+'_handler'
        handler = getattr(self, name)
        boxes = handler(texel, i1, i2)
        if not i2-i1 == listtools.calc_length(boxes):
            print i1, i2, texel
            k1 = 0
            for box in boxes:
                k2 = k1+len(box)
                print k1, k2, 
                box.dump_boxes(k1, 0, 0)
                k1 = k2
        assert i2-i1 == listtools.calc_length(boxes)
        return tuple(boxes)

    def Group_handler(self, texel, i1, i2):
        r = []
        for j1, j2, child in texel.iter_childs():
            if i1 < j2 and j1 < i2: # Test for overlap
                r.extend(self.create_boxes(child, i1-j1, i2-j1))
        return r

    def Characters_handler(self, texel, i1, i2):
        return [self.TextBox(texel.text[i1:i2], texel.style, self.device)]

    def NewLine_handler(self, texel, i1, i2):
        if texel.is_endmark:
            return [self.EndBox(texel.style, self.device)]
        return [self.NewlineBox(texel.style, self.device)] # XXX: Hmmmm

    def Tabulator_handler(self, texel, i1, i2):
        return [self.TabulatorBox(texel.style, self.device)]



class Updater(Factory):

    def __init__(self, model, device=TESTDEVICE, maxw=0):
        self.model = model
        self._maxw = maxw
        Factory.__init__(self, device)
        self.rebuild()

    def _grouped(self, stuff):
        if not stuff:
            return ParagraphStack(
                [], 
                device=self.device)
        return treebase.grouped(stuff)

    def _replaced(self, element, i1, i2, stuff):
        # replaces everything between $i1$ and $i2$ in $element$ by
        # $stuff$
        grouped = self._grouped
        n = len(element)
        assert i2>=i1
        assert i2<=len(element)
        if i2>i1:
            rest = treebase.remove(element, i1, i2)
            element = grouped(rest)
        r = treebase.insert(element, i1, stuff)
        from textmodel.listtools import calc_length
        assert len(grouped(r)) == n-(i2-i1)+calc_length(stuff)
        return grouped(r)

    def extended_texel(self):
        return self.model.get_xtexel()
        
    def rebuild(self):
        #print "rebuild"
        texel = self.extended_texel()
        l = self.create_paragraphs(texel, 0, len(texel))
        self._layout = self._grouped(l)

    def get_layout(self):
        return self._layout

    def set_maxw(self, maxw):
        if maxw != self._maxw:
            self._maxw = maxw
            self.rebuild()

        
    ### Signal handlers
    def properties_changed(self, i1, i2):
        #print "properties changed", i1, i2
        j1, j2 = self._layout.get_envelope(i1, i2)
        texel = self.extended_texel()
        new = self.create_paragraphs(texel, j1, j2)
        self._layout = self._replaced(self._layout, j1, j2, new)
        assert len(self._layout) == len(self.model)+1
        return self._layout

    def inserted(self, i, n):
        #print "inserted", i, n
        j1, j2 = self._layout.get_envelope(i, i)
        texel = self.extended_texel()
        new = self.create_paragraphs(texel, j1, j2+n)
        old = self._layout # XXX
        self._layout = self._replaced(self._layout, j1, j2, new)
        try:
            assert len(self._layout) == len(self.model)+1
        except:
            print len(self._layout), len(old), len(self.model)
            old.dump_boxes(0, 0, 0)
            self._layout.dump_boxes(0, 0, 0)
            raise 
        return self._layout

    def removed(self, i, n):
        #print "removed", i, n
        i1 = i
        i2 = i+n
        if i2<len(self._layout):
            # When the NL at the paragrpah end is removed. the
            # paragraph is merged with its right neighbour. We
            # therefore have to extend the interval.
            i2 = i2+1

        j1, j2 = self._layout.get_envelope(i1, i2)
        texel = self.extended_texel()
        new = self.create_paragraphs(texel, j1, j2-n)
        self._layout = self._replaced(self._layout, j1, j2, new)
        assert len(self._layout) == len(self.model)+1
        return self._layout




def test_01():
    factory = Factory()
    boxes = factory.create_boxes(TextModel("123").texel)
    assert listtools.calc_length(boxes) == 3
    boxes = factory.create_boxes(TextModel("123\n567").get_xtexel())
    assert listtools.calc_length(boxes) == 8
    paragraphs = create_paragraphs(boxes)
    assert len(paragraphs) == 2
    assert len(paragraphs[0]) == 4
    assert len(paragraphs[1]) == 4
    assert listtools.calc_length(paragraphs) == 8

def test_02():
    "ParagraphStack"
    factory = Factory()
    texel = TextModel("123\n567\n").texel
    boxes = factory.create_boxes(texel)
    assert listtools.calc_length(boxes) == 8
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert check_box(stack, texel)

    texel = TextModel("123\n\n5\n67\n").texel
    boxes = factory.create_boxes(texel)
    assert listtools.calc_length(boxes) == 10
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert check_box(stack, texel)

    texel = TextModel("123\n").texel
    boxes = factory.create_boxes(texel)
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    par = stack.childs[-1]
    assert len(par) == 4
    assert len(stack) == 4

    if 0:
        for p in paragraphs:
            p.dump_boxes(0, 0, 0)

    assert stack.get_info(3, 0, 0)[-2:] == (3, 0)

    texel = TextModel("").texel
    boxes = factory.create_boxes(texel)
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    

def test_03():
    "Factory"
    factory = Factory()
    texel = TextModel("123\n\n567890 2 4 6 8 0\n").texel
    boxes = factory.create_boxes(texel)
    assert str(boxes) == "(TB('123'), NL, NL, TB('567890 2 4 6 8 0'), NL)"
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert str(tuple(stack.childs)) == "(Paragraph[Row[TB('123'), NL]], " \
        "Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0'), NL]])"

    # line break
    paragraphs = create_paragraphs(boxes, 5) 
    # Depends on the line break algorithm. Here breaking after space
    # is assumed.
    assert repr(paragraphs) == "[Paragraph[Row[TB('123'), NL]]," \
        " Paragraph[Row[NL]], Paragraph[Row[TB('56789')], Row[TB('0 2 ')], " \
        "Row[TB('4 6 ')], Row[TB('8 0'), NL]]]"


    texel = TextModel("123\t\t567890 2 4 6 8 0\n").texel
    
    boxes = factory.create_boxes(texel)

    factory.create_boxes(texel)
    paragraphs = create_paragraphs(boxes)

def test_04():
    "insert/remove"
    factory = Factory()
    model = TextModel("123\n\n567890 2 4 6 8 0")
    updater = Updater(model, maxw=0)
    layout = updater._layout
    assert repr(layout) == "ParagraphStack[Paragraph[Row[TB('123'), " \
        "NL]], Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0'), " \
        "ENDMARK]]]"
    assert len(layout) == len(model)+1
    assert layout.height == 3

    ins = TextModel("xyz\n")
    model.insert(2, ins)
    updater.inserted(2, len(ins))
    assert len(updater._layout) == len(model)+1
    assert repr(updater._layout) == "ParagraphStack[Paragraph[Row[TB('12xyz'),"\
        " NL]], Paragraph[Row[TB('3'), NL]], Paragraph[Row[NL]], "\
        "Paragraph[Row[TB('567890 2 4 6 8 0'), ENDMARK]]]"
    assert updater._layout.height == 4
    model.remove(2, 2+len(ins))
    updater.removed(2, len(ins))
    assert len(updater._layout) == len(model)+1
    assert repr(updater._layout) == "ParagraphStack[Paragraph[Row[TB('123'), " \
        "NL]], Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0'), " \
        "ENDMARK]]]"
    assert updater._layout.height == 3

    factory = Factory()
    model = TextModel("123")
    updater = Updater(model, maxw=0)
    layout = updater._layout

    ins = TextModel("xyz\n")    
    i = len(model)
    model.insert(i, ins)
    updater.inserted(i, len(ins))
    
    for c in "abc":
        ins = TextModel(c)    
        i = len(model)
        model.insert(i, ins)
        updater.inserted(i, len(ins))
    assert str(updater._layout) == \
        "ParagraphStack[Paragraph[Row[TB('123xyz'), NL]], " \
        "Paragraph[Row[TB('abc'), ENDMARK]]]"


def test_05():
    device = TESTDEVICE
    model = TextModel("123\n\n567890 2 4 6 8 0")
    updater = Updater(model, maxw=0)
    
    def check(box):
        if not box.device is device:
            print box
        assert box.device is device
        if hasattr(box, 'iter'):
            for j1, j2, x1, y1, child in box.riter(0, 0, 0):
                check(child)
    check(updater.get_layout())

def test_06():
    model = TextModel("123\n")
    updater = Updater(model, maxw=0)
    layout = updater._layout
    assert layout.get_info(4, 0, 0)
    assert str(layout.get_info(3, 0, 0)) == "(NL, 0, 3, 0)"
    assert layout.get_info(3, 0, 0)[-2:] == (3, 0)
    assert layout.get_info(4, 0, 0)[-2:] == (0, 1)

def test_07():
    # Problem: when clicking right beside a row the cursor is inserted
    # in a wrong position.
    model = TextModel("123\n567")
    updater = Updater(model, maxw=0)
    layout = updater._layout
    assert layout.get_index(100, 0.5) == 3

def test_08():
    "linewrap"
    model = TextModel("aa bb cc dd ee")
    updater = Updater(model, maxw=0)
    updater.get_layout().dump_boxes(0, 0, 0)

    model = TextModel("aa bb cc dd ee")
    updater.set_maxw(5)
    updater.get_layout().dump_boxes(0, 0, 0)
    
    layout = updater.get_layout()
    for j1, j2, x, y, child in layout.iter(0, 0, 0):
        print j1, j2, x, y, child
