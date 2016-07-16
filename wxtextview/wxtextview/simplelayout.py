# -*- coding: latin-1 -*-

# Simple layout for text editors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# The layout can be characterized by three different layers of boxes:

# paragraphs, lines and boxes. The top layer is the paragraph
# layer. It consists of a tree formed by ParagraphStacks and
# Paragraphs. Each paragraph has a tree of lines. Each line has a list
# of boxes.
#
# All paragraphs are stacked on top of each other. Each line has
# exactly the same width.
#
# When the model changes, we identify the corresponding paragraph
# objects, rebuild them and replace them.

from . import boxes
from .boxes import HBox, VBox, VGroup, TextBox, EmptyTextBox, NewlineBox, EndBox, \
                   check_box, Box, tree_depth, replace_boxes, Row, groups, \
                   calc_length
from .boxes import grouped as _grouped
from ..textmodel.texeltree import NewLine, length

from .testdevice import TESTDEVICE
from .linewrap import simple_linewrap
from .rect import Rect
from .builder import BuilderBase
from .builder import Factory as _Factory



class Paragraph(VBox):
    # A paragraph consists of one or several rows, which are stacked
    # on top of each other. It is assumed, that the text consists of
    # one single page with a constant left margin and uniform row
    # width. These assumptions correspond to the typical behaviour in
    # a text editor. If there are different requirements, e.g. in a
    # word processor, Paragraph could be redefined.
    #
    # The number of paragraphs can be very long. Therefore we group
    # paragraph into VGroups. This makes the GUI considerably faster.

    def create_group(self, l):
        return VGroup(l, device=self.device)




def get_envelope(tree, i0, i):
    # Returns i1, i2 where i1<=i<=i2 and there is one or none
    # paragraph in i1 .. i2.
    assert i>=0 
    assert i<=len(tree)
    if i == 0 or i == len(tree):
        return i0+i, i0+i
    if isinstance(tree, Paragraph):
        return i0, i0+len(tree)
    else:
        for i1, i2, child in tree.iter_childs():
            if i1<=i<=i2:
                return get_envelope(child, i0+i1, i-i1)
    raise IndexError(i)



def create_paragraphs(textboxes, maxw=0, Paragraph=Paragraph, \
                      device=TESTDEVICE):
    try:
        if len(textboxes):        
            assert isinstance(textboxes[-1], NewlineBox) or \
                isinstance(textboxes[-1], EndBox)
    except:
        i1 = 0
        for box in textboxes:
            i2 = i1+len(box)
            print i1, i2, repr(box)[:50]
            i1 = i2
        raise
    r = []
    l = []
    for box in textboxes:
        assert isinstance(box, Box)
        l.append(box)
        if isinstance(box, NewlineBox) or isinstance(box, EndBox):
            if maxw>0:
                rows = simple_linewrap(l, maxw, tabstops=(), device=device)
            else:
                rows = [Row(l, device)]
            r.append(Paragraph(rows, device))
            l = []
    #print l
    assert not l # There is always one final box which is either a
                 # NewLine or an EndBox. Therefore there is no rest in
                 # l.

    assert calc_length(r) == calc_length(textboxes)
    while len(r)>boxes.nmax:
        r = groups(r)
    return r


class Factory(_Factory):
    def create_paragraphs(self, texel, i1, i2):
        # creates a list of paragraphs
        textboxes = self.create_boxes(texel, i1, i2)
        assert len(textboxes)
        assert isinstance(textboxes[-1], EndBox) or isinstance(textboxes[-1], \
                                                               NewlineBox)
        return create_paragraphs(
            textboxes, self._maxw, 
            Paragraph = self.Paragraph,
            device = self.device,
        )



class Builder(BuilderBase, Factory):
    Paragraph = Paragraph

    def __init__(self, model, device=TESTDEVICE, maxw=0):
        self.model = model
        self._maxw = maxw
        Factory.__init__(self, device)

    def grouped(self, stuff):
        # We need to create a new version of grouped, again. This time
        # it must be aware of VGroup. Since it must be able to pass
        # device, this time it is a method and not a function.
        if not stuff:
            r = VGroup([], device=self.device)
            return r
        return _grouped(stuff)

    def replace_paragraphs(self, i1, i2, stuff):
        # Helper: replaces all paragraphs between $i1$ and $i2$ by
        # $stuff$, where $stuff$ is a list of paragraphs.
        self._layout = self.grouped(replace_boxes(self._layout, i1, i2, stuff))

    def get_envelope(self, i1, i2):
        # Helper: adjust $i1$ and $i2$ to the beginning / end of a paragraph 
        k1, k2 = get_envelope(self._layout, 0, i1)
        j1, j2 = get_envelope(self._layout, 0, i2)
        return k1, j2

    def extended_texel(self):
        return self.model.get_xtexel()
        
    def set_maxw(self, maxw):
        if maxw != self._maxw:
            self._maxw = maxw
            self.rebuild()
        
    ### Builder-Protocol
    def rebuild(self):
        texel = self.extended_texel()
        l = self.create_paragraphs(texel, 0, length(texel))
        self._layout = self.grouped(l)
        assert isinstance(self._layout, Box)

    ### Signal handlers
    def properties_changed(self, i1, i2):
        #print "properties changed", i1, i2
        j1, j2 = self.get_envelope(i1, i2)
        texel = self.extended_texel()
        new = self.create_paragraphs(texel, j1, j2)
        self.replace_paragraphs(j1, j2, new)

    def inserted(self, i, n):
        j1, j2 = self.get_envelope(i, i+1) # +1 is needed when we
                                            # insert between two
                                            # paragraphs
        texel = self.extended_texel()
        new = self.create_paragraphs(texel, j1, j2+n)
        self.replace_paragraphs(j1, j2, new)

    def removed(self, i, n):
        #print "removed", i, n
        i1 = i
        i2 = i+n
        if i2<len(self._layout):
            # Removing the NL at the paragraph end meens, that the
            # paragraph sould be merged with the next paragraph. We
            # therefore have to extend the interval so that both
            # paragraphs are rebuild.
            i2 = i2+1
        j1, j2 = self.get_envelope(i1, i2)
        texel = self.extended_texel()
        new = self.create_paragraphs(texel, j1, j2-n)
        self.replace_paragraphs(j1, j2, new)



def _create_testobjects(s):
    from ..textmodel.textmodel import TextModel
    texel = TextModel(s).texel    
    box = TextBox(s)
    return box, texel


def test_00():
    "Paragraph"
    box1, tmp = _create_testobjects("0123")
    box2, tmp = _create_testobjects("5678")
    tmp, texel = _create_testobjects("0123\n5678\n")
    box = Paragraph([
        Row([box1, NewlineBox()]), 
        Row([box2, NewlineBox()]),
        Row([EmptyTextBox()])
    ])
    assert check_box(box, texel)
    #box.dump_boxes(0, 0, 0)
    assert (box.height, box.width, box.depth) == (3, 4, 0)

    assert str(box.get_info(0, 0, 0)) == "(TB('0123'), 0, 0, 0)"
    assert str(box.get_info(1, 0, 0)) == "(TB('0123'), 1, 1, 0)"
    assert str(box.get_info(2, 0, 0)) == "(TB('0123'), 2, 2, 0)"
    assert str(box.get_info(3, 0, 0)) == "(TB('0123'), 3, 3, 0)"
    assert str(box.get_info(4, 0, 0)) == "(NL, 0, 4, 0)"
    assert str(box.get_info(5, 0, 0)) == "(TB('5678'), 0, 0, 1)"
    assert str(box.get_info(6, 0, 0)) == "(TB('5678'), 1, 1, 1)"
    assert str(box.get_info(7, 0, 0)) == "(TB('5678'), 2, 2, 1)"
    assert str(box.get_info(8, 0, 0)) == "(TB('5678'), 3, 3, 1)"
    assert str(box.get_info(9, 0, 0)) == "(NL, 0, 4, 1)"
    assert str(box.get_info(10, 0, 0)) == "(ETB, 0, 0, 2)"


def test_01():
    "Row"
    box1, tmp = _create_testobjects("0123")
    box2, tmp = _create_testobjects("5678")
    tmp, texel1 = _create_testobjects("0123\n")
    tmp, texel2 = _create_testobjects("5678\n")
    tmp, texel = _create_testobjects("0123\n5678\n")
    p1 = Paragraph([
        Row([box1, NewlineBox()]), 
    ])
    p2 = Paragraph([
        Row([box2, NewlineBox()]), 
        Row([EmptyTextBox()])
    ])
    assert check_box(p1, texel1)
    assert check_box(p2, texel2)
    box = _grouped([p1, p2])
    assert isinstance(box, VBox)
    assert check_box(box, texel)

    assert str(box.get_info(0, 0, 0)) == "(TB('0123'), 0, 0, 0)"
    assert str(box.get_info(1, 0, 0)) == "(TB('0123'), 1, 1, 0)"
    assert str(box.get_info(2, 0, 0)) == "(TB('0123'), 2, 2, 0)"
    assert str(box.get_info(3, 0, 0)) == "(TB('0123'), 3, 3, 0)"
    assert str(box.get_info(4, 0, 0)) == "(NL, 0, 4, 0)"
    assert str(box.get_info(5, 0, 0)) == "(TB('5678'), 0, 0, 1)"
    assert str(box.get_info(6, 0, 0)) == "(TB('5678'), 1, 1, 1)"
    assert str(box.get_info(7, 0, 0)) == "(TB('5678'), 2, 2, 1)"
    assert str(box.get_info(8, 0, 0)) == "(TB('5678'), 3, 3, 1)"
    assert str(box.get_info(9, 0, 0)) == "(NL, 0, 4, 1)"
    assert str(box.get_info(10, 0, 0)) == "(ETB, 0, 0, 2)"

    #box.dump_boxes(0, 0, 0)

    box2 = _grouped(replace_boxes(box, 5, 10, []))
    box2.dump_boxes(0, 0, 0)
    assert len(box2) == 5

    xbox, tmp = _create_testobjects("X")
    p = Paragraph([xbox])
    box2 = _grouped(replace_boxes(box, 5, 10, [p]))
    #box2.dump_boxes(0, 0, 0)
    assert len(box2) == 6
    boxes.nmax = 5
    box2 = Paragraph([
        Row([EmptyTextBox()])
    ])

    l = []
    for i in range(15):
        ibox, tmp = _create_testobjects(str(i))
        r = Row([ibox, NewlineBox()])
        l.append(Paragraph([r]))
    for x in l:
        assert isinstance(x, Paragraph)
    box2 = _grouped(replace_boxes(box, 5, 10, l))
    #box2.dump_boxes(0, 0, 0) # check that the tree is balenced    
    return box2


def test_02():
    "get_envelope"
    box = test_01()
    #box.dump_boxes(0, 0, 0)
    assert get_envelope(box, 0, 0) == (0, 0)
    assert get_envelope(box, 0, 1) == (0, 5)
    assert get_envelope(box, 0, 5) == (5, 5)
    assert get_envelope(box, 0, 6) == (5, 7)

def _mk_pars(text):
    # for testing
    from .wxdevice import defaultstyle
    l = []
    for line in text.split('\n'):
        for word in line.split():
            l.append(TextBox(word))
        l.append(NewlineBox(defaultstyle))
    return create_paragraphs(l)

def test_02a():
    "create_paragraphs"
    paragraphs = _mk_pars("word1 word2 word3")
    assert str(paragraphs) == "[Paragraph[Row[TB('word1'), TB('word2'), TB('word3'), NL]]]"
    paragraphs = _mk_pars("word1\nword2\nword3")
    assert str(paragraphs) == "[Paragraph[Row[TB('word1'), NL]], Paragraph[Row[TB('word2')," \
                              " NL]], Paragraph[Row[TB('word3'), NL]]]"

def xxtest_02b():
    "insert_paragraphs"
    box = test_01()
    paragraphs = _mk_pars("xx yy zz")
    box = _grouped(insert_paragraphs(box, 5, paragraphs))
    box.dump_boxes(0, 0, 0)
    assert get_envelope(box, 0, 1) == (0, 5)
    print get_envelope(box, 0, 6)
    assert get_envelope(box, 0, 6) == (5, 12)

def test_03():
    t1 = TextBox("0123456789")
    t2 = TextBox("0123456789")
    p1 = Paragraph([Row([t1, NewlineBox()])])
    row = p1.childs[0]
    assert p1.height == 1
    assert p1.width == 10
    assert len(p1) == 11
    p2 = VBox([Row([t2])])
    assert p2.height == 1
    s = VBox([p1, p2])
    assert s.height == 2    


def test_04():
    # Problem: get_rect always returns 0, 0
    t1 = TextBox("0123456789")
    t2 = TextBox("0123456789")
    p1 = Paragraph([Row([t1, t2, NewlineBox()])])

    assert p1.get_rect(0, 0, 0) == Rect(0, 0.0, 1, 1.0)
    assert p1.get_rect(10, 0, 0) == Rect(10, 0.0, 11, 1.0)

def test_05():
    t1 = TextBox("0123456789")
    t2 = TextBox("0123456789")
    NL = NewlineBox()
    p1 = Paragraph([Row([t1, NL])])
    assert tree_depth(p1) == 0
    tmp = _grouped([p1])
    assert not tmp.is_group
    print tmp
    tmp.dump()
    assert tmp is p1

    p2 = Paragraph([Row([t2, NL])])
    print p2, tree_depth(p2)
    assert tree_depth(p2) == 0
    
    tmp = _grouped([p1, p2])
    tmp.dump()
    assert tmp.is_group
    print tree_depth(tmp)
    assert tree_depth(tmp) == 1
    # ...


