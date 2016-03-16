# -*- coding: latin-1 -*-



from ..textmodel import listtools
from ..textmodel import treebase
from ..textmodel.textmodel import TextModel
from ..textmodel.texeltree import NewLine, Group, Characters, defaultstyle
from .testdevice import TESTDEVICE
from .boxes import TextBox, NewlineBox, TabulatorBox, EmptyTextBox, \
    EndBox, check_box, Box



class Factory:
    TextBox = TextBox
    NewlineBox = NewlineBox
    TabulatorBox = TabulatorBox
    EndBox = EndBox

    def __init__(self, device=TESTDEVICE):
        self.device = device

    def get_device(self):
        return self.device

    ### Factory methods
    def create_all(self, texel):
        # Convenience method
        return self.create_boxes(texel, 0, len(texel))

    def create_boxes(self, texel, i1, i2):
        assert i1>=0
        assert i2<=len(texel)
        assert i1<=i2
        if i1 == i2:
            return () # XXX Why is this needed?
        name = texel.__class__.__name__+'_handler'
        handler = getattr(self, name)
        #print "calling handler", name, i1, i2
        l = handler(texel, i1, i2)
        try:
            assert listtools.calc_length(l) == i2-i1
        except:
            print "handler=", handler
            raise
        return tuple(l)
        
    def Group_handler(self, texel, i1, i2):
        r = []
        for j1, j2, child in texel.iter_childs():
            if i1 < j2 and j1 < i2: # overlapp
                r.extend(self.create_boxes(
                    child, max(0, i1-j1), min(i2, j2)-j1))
        return r

    def Characters_handler(self, texel, i1, i2):
        return [self.TextBox(texel.text[i1:i2], texel.style, self.device)]

    def NewLine_handler(self, texel, i1, i2):
        if texel.is_endmark:
            return [self.EndBox(texel.style, self.device)]
        return [self.NewlineBox(texel.style, self.device)] # XXX: Hmmmm

    def Tabulator_handler(self, texel, i1, i2):
        return [self.TabulatorBox(texel.style, self.device)]





class BuilderBase:
    """The builder is responsible for creating and updating the layout. 

    The methods build, insert, remove and update return a tree of boxes (=
    "layout").

    The length of the box tree is always the length of the model +1,
    because we add a special box ("end mark").

    """

    _layout = None

    def rebuild(self):
        # sets self._layout
        pass

    def get_layout(self):
        assert self._layout is not None
        return self._layout

    ### Signal handlers
    def properties_changed(self, i1, i2):
        pass

    def inserted(self, i, n):
        pass

    def removed(self, i, n):
        pass



def test_01():
    factory = Factory()
    boxes = factory.create_all(TextModel("123").texel)
    assert listtools.calc_length(boxes) == 3
    boxes = factory.create_all(TextModel("123\n567").get_xtexel())
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
    boxes = factory.create_all(texel)
    assert listtools.calc_length(boxes) == 8
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert check_box(stack, texel)

    texel = TextModel("123\n\n5\n67\n").texel
    boxes = factory.create_all(texel)
    assert listtools.calc_length(boxes) == 10
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert check_box(stack, texel)

    texel = TextModel("123\n").texel
    boxes = factory.create_all(texel)
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
    boxes = factory.create_all(texel)
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    

def test_03():
    "Factory"
    factory = Factory()
    texel = TextModel("123\n\n567890 2 4 6 8 0\n").texel
    boxes = factory.create_all(texel)
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
    
    boxes = factory.create_all(texel)

    factory.create_all(texel)
    paragraphs = create_paragraphs(boxes)

def test_04():
    "insert/remove"
    factory = Factory()
    model = TextModel("123\n\n567890 2 4 6 8 0")
    builder = Builder(model, maxw=0)
    builder.rebuild()
    layout = builder.get_layout()
    assert repr(layout) == "ParagraphStack[Paragraph[Row[TB('123'), " \
        "NL]], Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0'), " \
        "ENDMARK]]]"
    assert len(layout) == len(model)+1
    assert layout.height == 3

    ins = TextModel("xyz\n")
    model.insert(2, ins)
    builder.inserted(2, len(ins))
    assert len(builder._layout) == len(model)+1
    assert repr(builder._layout) == "ParagraphStack[Paragraph[Row[TB('12xyz'),"\
        " NL]], Paragraph[Row[TB('3'), NL]], Paragraph[Row[NL]], "\
        "Paragraph[Row[TB('567890 2 4 6 8 0'), ENDMARK]]]"
    assert builder._layout.height == 4
    model.remove(2, 2+len(ins))
    builder.removed(2, len(ins))
    assert len(builder._layout) == len(model)+1
    assert repr(builder._layout) == "ParagraphStack[Paragraph[Row[TB('123'), " \
        "NL]], Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0'), " \
        "ENDMARK]]]"
    assert builder._layout.height == 3

    factory = Factory()
    model = TextModel("123")
    builder = Builder(model, maxw=0)
    layout = builder._layout

    ins = TextModel("xyz\n")    
    i = len(model)
    model.insert(i, ins)
    builder.inserted(i, len(ins))
    
    for c in "abc":
        ins = TextModel(c)    
        i = len(model)
        model.insert(i, ins)
        builder.inserted(i, len(ins))
    assert str(builder._layout) == \
        "ParagraphStack[Paragraph[Row[TB('123xyz'), NL]], " \
        "Paragraph[Row[TB('abc'), ENDMARK]]]"


def test_05():
    device = TESTDEVICE
    model = TextModel("123\n\n567890 2 4 6 8 0")
    builder = Builder(model, maxw=0)
    
    def check(box):
        if not box.device is device:
            print box
        assert box.device is device
        if hasattr(box, 'iter'):
            for j1, j2, x1, y1, child in box.riter(0, 0, 0):
                check(child)
    check(builder.get_layout())

def test_06():
    model = TextModel("123\n")
    builder = Builder(model, maxw=0)
    layout = builder._layout
    assert layout.get_info(4, 0, 0)
    assert str(layout.get_info(3, 0, 0)) == "(NL, 0, 3, 0)"
    assert layout.get_info(3, 0, 0)[-2:] == (3, 0)
    assert layout.get_info(4, 0, 0)[-2:] == (0, 1)

def test_07():
    # Problem: when clicking right beside a row the cursor is inserted
    # in a wrong position.
    model = TextModel("123\n567")
    builder = Builder(model, maxw=0)
    layout = builder._layout
    assert layout.get_index(100, 0.5) == 3

def test_08():
    "linewrap"
    model = TextModel("aa bb cc dd ee")
    builder = Builder(model, maxw=0)
    builder.get_layout().dump_boxes(0, 0, 0)

    model = TextModel("aa bb cc dd ee")
    builder.set_maxw(5)
    builder.get_layout().dump_boxes(0, 0, 0)
    
    layout = builder.get_layout()
    for j1, j2, x, y, child in layout.iter(0, 0, 0):
        print j1, j2, x, y, child
