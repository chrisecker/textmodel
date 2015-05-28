# -*- coding: latin-1 -*-


from .texeltree import defaultstyle, create_style, check, Characters, Group, \
    NewLine, Tabulator, heal, insert, ENDMARK
from .treebase import is_homogeneous
from .treebase import grouped as _grouped
from .container import iter_extended
from .modelbase import Model
from . import treebase
import re



class NotFound(Exception): 
    pass


# Warning: The following helper functions for searching indices only
# work with certain weight functions. They will work for weights
# aggregated by 'sum', such as lengths and line numbers. But trying to
# find depth values will lead to unexpected and unpredicted behaviour.

def _find_weight(texel, w, windex):
    """Returns position *i* at which weight *windex* switches to value *w*."""
    assert type(w) is int
    if w == 0:
        return 0
    if texel.has_childs:
        sum_w = 0
        for i1, i2, child in iter_extended(texel):
            delta = child.weights[windex]
            if sum_w+delta >= w:
                return _find_weight(child, w-sum_w, windex)+i1
            sum_w += delta
    if w == texel.weights[windex]:
        return len(texel)
    raise NotFound(w)


def _next_change(texel, windex, i):
    """Returns the next position from *i* at which weight *windex* changes."""
    if texel.has_childs:
        for j1, j2, child in iter_extended(texel):
            if i1 < j2 and j1 < i2: # intersection
                n = _next_change(texel, windex, i-j1)
                if n is not None:
                    return n+j1
    if texel.weights[windex]:
        return 0


def _get_weight(texel, windex, i): 
    """Returns the weight *windex* at index *i*."""
    if i<0:
        raise IndexError
    if i >= len(texel):
        return texel.weights[windex]
    w = 0
    if i == 0:
        return w

    for i1, i2, child in iter_extended(texel):
        if i2 <= i:
            w += child.weights[windex]
        elif i1 <= i <= i2:
            w += _get_weight(child, windex, i-i1)
        else:
            break
    return w


def _get_text(texel, i1, i2):
    r = []
    if isinstance(texel, Group):
        for j1, j2, child in iter_extended(texel):
            if i1 < j2 and j1 < i2: # intersection
                r.append(_get_text(child, i1-j1, i2-j1))
        return u''.join(r)
    text = texel.get_text()
    return text[max(0, i1):min(i2, len(text))]



def dump_range(texel, i1, i2, i0=0, indent=0):
    s = texel.__class__.__name__
    if isinstance(texel, Characters):
        s += " "+repr(texel.text)
    print " "*indent+"%i:%i %s" % (i0, i0+len(texel), s)
    if texel.has_childs:
        complete = True
        for j1, j2, child in iter_extended(texel):
            if i1 < j2 and j1 < i2: # intersection
                dump_range(child, i1-j1, i2-j1, i0+j1, indent+4)
            else:
                complete = False
        if not complete:
            print " "*indent+'...'


_split = re.compile(r"([\t\n])", re.MULTILINE).split
class TextModel(Model):
    """A data type for storing and manipulating styled text. Changes to
    the data are notified to views by emitting the following signals:
    - "inserted" (arguments: i, length)
    - "removed" (arguments: i, removed data)
    - "properties changed" (arguments: i1, i2)

    """
    _NewLine = NewLine
    _Tabulator = Tabulator
    _Characters = Characters
    _Group = Group
    
    def create_textmodel(self, text=u'', **properties):
        """Creates a new textmodel with text $text$ and uniform style."""
        return self.__class__(text, **properties)

    def _grouped(self, stuff):
        for texel in stuff:
            if len(texel):
                return _grouped(stuff)
        return self._Group([])

    def __init__(self, text=u'', **properties):
        NewLine = self._NewLine
        Tabulator = self._Tabulator
        Characters = self._Characters
        style = create_style(**properties)
        l = []
        text = text.replace('\r', '')
        for part in _split(text):
            if part == '\n':
                l.append(NewLine(style))
            elif part == '\t':
                l.append(Tabulator(style))
            else:
                l.append(Characters(part, style))
        assert is_homogeneous(l)
        self.texel = self._grouped(l)

    def __len__(self):
        return len(self.texel)

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__ = state

    def get_xtexel(self):
        """Returns the texel tree extended by an ENDMARK glyph."""
        texel = self.texel
        return texel.create_group([texel, ENDMARK])

    def nlines(self):
        """Returns the number of lines."""
        return self.texel.weights[2]+1

    def get_text(self, i1=None, i2=None):
        """Retuns the text between *i1* and *i2* as unicode string."""
        if i1 is None:
            i1 = 0
        if i2 is None:
            i2 = len(self.texel)
        if i1<0:
            raise IndexError, i1
        if i2>len(self):
            raise IndexError, i2
        return _get_text(self.texel, i1, i2)

    def get_style(self, i):
        """Returns the style at index *i*."""
        return self.texel.get_style(i)

    def position2index(self, row, col):
        """Returns the index corresponding to *row* and *col*."""
        i = _find_weight(self.texel, row, 2)
        if i is None:
            raise IndexError(row)
        return i+col

    def _lfromt(self, t):
        # for debugging
        splitter = t.split('\n')
        l = [len(s)+1 for s in splitter[:-1]]
        return l

    def index2position(self, i):
        """Returns the (row, col)-tuple corresponding to index *i*."""
        texel = self.texel
        if i > len(texel):
            raise IndexError(i)
        if i < 0:
            raise IndexError(i)

        row = _get_weight(texel, 2, i)
        assert type(row) is int
        j = _find_weight(texel, row, 2)
        col = i-j
        return row, col

    def linestart(self, row):
        """Returns the index where line number *row* starts."""
        try:
            return _find_weight(self.texel, row, 2)
        except NotFound:
            raise IndexError(row)

    def lineend(self, row):
        """Returns the index where line number *row* ends."""
        try:
            return _find_weight(self.get_xtexel(), row+1, 2)-1
        except NotFound:
            raise IndexError(row)

    def linelength(self, row):
        """Returns the length of line *row*."""
        try:
            i1 = _find_weight(self.texel, row, 2)
        except NotFound:
            raise IndexError(row)
        try:
            i2 = _find_weight(self.texel, row+1, 2)
        except NotFound:
            i2 = len(self)
        return i2-i1

    def set_properties(self, i1, i2, **properties):
        """Sets the text properties between *i1* and *i2*."""
        memo = self.texel.get_styles(i1, i2)
        self.texel = heal(self._grouped(
            self.texel.set_properties(i1, i2, properties)), \
            i1, i2)
        #assert check(self.texel)
        self.notify_views('properties_changed', i1, i2)
        return memo

    def set_styles(self, i, styles):
        """Sets the styling of a span of text. Usually used by undo."""
        n = sum([entry[0] for entry in styles])
        memo = self.texel.get_styles(i, i+n)
        self.texel = self.texel.set_styles(i, styles)
        self.notify_views('properties_changed', i, i+n)
        return memo

    def insert(self, i, text):
        """Inserts *text* at position *i*."""
        
        if not isinstance(text, TextModel):
            return self.insert_text(i, text)

        row, col = self.index2position(i)
        n = len(self.texel) + len(text.texel)
        tmp = heal(self._grouped(
            insert(self.texel, i, [text.texel])), i, i+n)
        self.texel = tmp
        assert len(self.texel) == n
        self.notify_views('inserted', i, len(text))

    def append(self, text):
        """Appends textmodel *texel*."""
        return self.insert(len(self), text)

    def insert_text(self, i, text):
        """Inserts a unicode text string *text* at index *i*.""" 
        textmodel = self.create_textmodel(text)
        d = treebase.depth(self.texel)
        self.insert(i, textmodel)
        assert treebase.depth(self.texel) <= d+1

    def copy(self, i1, i2):
        """Returns a copy of all data between *i1* and *i2*."""
        row1, col1 = self.index2position(i1)
        row2, col2 = self.index2position(i2)

        rest, removed = self.texel.takeout(i1, i2)
        model = self.create_textmodel()
        model.texel = self._grouped(removed)
        return model

    def __getitem__(self, slice):
        if slice.start is None:
            i1 = 0
        else:
            i1 = slice.start
            if i1 < 0:
                i1 = len(self)+i1
                if i1 < 0:
                    raise IndexError(slice.start)

        if slice.stop is None:
            i2 = len(self)
        else:
            i2 = slice.stop
            if i2 < 0:
                i2 = len(self)+i2
                if i2 < 0:
                    raise IndexError(slice.stop)
        return self.copy(i1, i2)

    def remove(self, i1, i2):
        """Removes everything between *i1* and *i2*."""
        row1, col1 = self.index2position(i1)
        row2, col2 = self.index2position(i2)

        rest, kern = self.texel.takeout(i1, i2)
        grouped = self._grouped
        self.texel = grouped([heal(grouped(rest), i1)])

        model = self.create_textmodel()
        model.texel = grouped(kern)

        self.notify_views('removed', i1, model)
        #assert check(self.texel)
        return model



def pycolorize(rawtext, coding='latin-1'):
    # used for benchmarking
    import cStringIO
    instream = cStringIO.StringIO(rawtext).readline

    import token, keyword
    KEYWORD = token.NT_OFFSET + 1
    TEXT = token.NT_OFFSET + 2
    def tokeneater(toktype, toktext, (srow,scol), (erow,ecol), line):
        i1 = model.position2index(srow-1, scol)
        i2 = model.position2index(erow-1, ecol)
        if toktype == token.STRING:
            color = 'grey'
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            color = 'red'
        elif toktype == TEXT:
            color = 'green'
        else:
            return
        model.set_properties(i1, i2, textcolor=color)

    text = rawtext.decode(coding)
    model = TextModel(text)

    from tokenize import tokenize
    tokenize(instream, tokeneater)
    return model



text1 = "0123456789"
text2 = "abcdefghijklmnopqrstuvwxyz"
text3 = "01\n345\n\n89012\n45678\n"


def test_00():
    "remove w. simplify"
    t2 = TextModel(text2)

    for i in range(len(text1)):
        t = TextModel(text1)
        t.remove(i, i+1)
        if not isinstance(t.texel, Characters):
            t.texel.dump()
        assert isinstance(t.texel, Characters)

    for i in range(len(text1)):
        t = TextModel(text1)
        t.texel = Group([t.texel])
        t.remove(i, i+1)
        assert isinstance(t.texel, Characters)

    # Groups of onyl one element should be opened
    for i in range(len(text1)):
        t = TextModel(text1)
        t.texel = Group([t.texel])
        t.remove(i, i+1)
        assert isinstance(t.texel, Characters)

    # Characters with different styling should not be merged
    for i in range(2*len(text1)):
        t = TextModel(text1)
        t1 = TextModel(text1, fontsize=20)
        t.insert(len(t), t1)
        t.remove(i, i+1)
        assert isinstance(t.texel, Group)
        assert len(t.texel.childs) == 2
        assert isinstance(t.texel.childs[0], Characters)
        assert isinstance(t.texel.childs[1], Characters)
        text = '01234567890123456789'
        text = text[:i]+text[i+1:]
        assert t.get_text() == text

# XXX MISSING: more simplification tests


def test_01():
    "row, col"

    def index2position(t, i):
        row = t[:i].count('\n')
        i0 = 0
        for j in range(row):
            i0 = t.index('\n', i0)+1
        col = i-i0
        return row, col

    texts = [text3]
    text = '0123456789'
    import random
    while text.count('\n')<len(text):
        i = random.randrange(len(text))
        if text[i] == '\n':
            continue
        text = text[:i]+'\n'+text[i+1:]
        texts.append(text)

    for text in texts:
        t = TextModel(text)
        ll_text = t._lfromt(text)


        for i in range(len(text)):
            row, col = t.index2position(i)
            assert (row, col) == index2position(text, i)

        for i in range(len(text)):
            row, col = index2position(text, i)
            i_ = t.position2index(row, col)
            assert i == i_



def test_03():
    "TextModel"
    t1 = TextModel(text1)
    assert t1.get_text() == text1
    t2 = TextModel(text2)
    assert t2.get_text() == text2
    t3 = TextModel(text1+'\n'+text2)
    assert t3.get_text() == text1+'\n'+text2
    assert t3.nlines() == 2
    assert t3.position2index(0, 5) == 5
    assert t3.position2index(1, 0) == 11
    assert t3.get_text()[10] == '\n'
    assert t3.get_text()[11] == 'a'
    assert t3.linelength(0) == len(text1)+1 # the newline counts!
    assert t3.linelength(1) == len(text2)

    t1.insert(0, t2)
    assert  t1.get_text() == text2+text1
    t1.remove(0, len(text2))
    assert t1.get_text() == text1

    t1.insert(3, t3)
    tmp = text1[:3]+text1+'\n'+text2+text1[3:]
    assert t1.get_text() == tmp
    n = len(t1)
    old = t1.remove(3, 3+len(t3))
    assert len(old) + len(t1) == n
    assert t1.get_text() == text1


def test_04():
    "indices"
    t = TextModel(text1+'\n'+text2)
    row = col = 0

    for i in range(len(t)):

        assert t.index2position(i) == (row, col)
        if t.get_text(i, i+1) == '\n':
            row += 1
            col = 0
        else:
            col += 1


def test_05():
    "style"
    t1 = TextModel(text1)
    assert t1.get_text() == text1
    t2 = TextModel(text2)
    assert t2.get_text() == text2
    t3 = TextModel(text1+'\n'+text2)

    # Styles are compared by their id. Same styles always have the
    # same id. This is assured by the factory function "new_style()"
    assert defaultstyle is create_style() 
    assert t3.get_style(0) == defaultstyle
    assert id(t3.get_style(0)) == id(defaultstyle)

    t3.set_properties(5, 10, textcolor='red')
    t3.set_properties(3, 8, fontsize=8)

    for i in range(len(t3)):
        style = t3.get_style(i)
        if i<5:
            assert style['textcolor'] == 'black'
        elif i<10:
            assert style['textcolor'] == 'red'
        else:
            assert style['textcolor'] == 'black'

        if i<3:
            assert style['fontsize'] == 10
        elif i<8:
            assert style['fontsize'] == 8
        else:
            assert style['fontsize'] == 10

    #assert len(style_pool) == 4 # depends on gc

    t3.set_properties(0, len(t3), **defaultstyle)
    for i in range(len(t3)):
        style = t3.get_style(i)
        assert style == defaultstyle
        assert id(style) == id(defaultstyle)

    t3.set_properties(0, len(t3), fontsize = 6)
    s0 = t3.get_style(0)
    for i in range(len(t3)):
        style = t3.get_style(i)
        assert id(style) == id(s0)
    assert s0['fontsize'] == 6


def test_06():
    "get_style"
    t = TextModel(text1)
    assert t.get_text() == text1

    t.set_properties(3, 5, fontsize=8)
    s = t.get_style(4)
    n = len(t)
    t.insert(4, TextModel('x', **s))
    assert len(t) == n+1
    assert t.get_style(3) is s
    assert t.get_style(4) is s
    assert t.get_style(5) is s


def test_08():
    "insert/remove"
    text = text1+'\n'+text2
    for i in range(len(text)):
        t = TextModel(text)
        n = len(t)
        x = TextModel('x')
        t.insert(i, x)
        assert len(t) == n+1
        t.remove(i, i+1)
        assert len(t) == n


def test_09():
    "slice"
    text = "Text A"
    model = TextModel(text)

    assert model.get_text() == text
    assert model[5:6].get_text() == text[5:6]
    assert model[-1:].get_text() == text[-1:]
    for i in range(len(text)):
        for n in range(1, len(text)-i):
            j = i+n
            assert model[i:j].get_text() == text[i:j]
            assert model[i:-n].get_text() == text[i:-n]
            assert model[-i:].get_text() == text[-i:]


def test_10():
    "split"
    t = TextModel(text1+'\n'+text2)
    n = len(t)
    for i in range(len(t)+1):
        item1 = t[:i]
        item2 = t[i:]
        assert len(item1)+len(item2) == n


def test_11():
    "properties"
    t = TextModel(text1+'\n'+text2)
    t.set_properties(5, 15, selected=True)
    t.set_properties(5, 15, selected=False)
    #print t.texel
    t.get_style(5) == {
        'bgcolor': 'white', 'textcolor': 'black', 'fontsize': 10,
        'selected': False}


def test_12():
    "remove all"
    t = TextModel(text1+'\n'+text2)
    t.remove(0, len(t))

def test_13():
    'ENDMARK'
    t = TextModel(text1+'\n'+text2)
    assert len(t.get_xtexel()) == len(t.texel)+1
    #t.extended_texel().dump()

def heavy_test():
    'pycolorize'
    filename = 'textmodel/textmodel.py'
    rawtext = open(filename).read()
    pycolorize(rawtext)


def test_14():
    "random insert/remove"
    defaultstyle.clear()
    defaultstyle['s'] = 10

    model = TextModel(u'0123')
    from random import randrange, choice


    n = len(model)
    for j in range(1000):
        i1 = randrange(n)
        i2 = randrange(n)
        i1, i2 = sorted([i1, i2])

        model.remove(i1, i2)

        m = i2-i1
        text = u'abcdefghijkl'[:m]
        i1 = randrange(len(model))

        size = choice([6, 8, 10, 14])

        model.insert(i1, TextModel(text, s=size))

        assert not "C(u'')" in str(model.texel)


def test_15():
    "get/set styles"

    from .texeltree import grouped

    s0 = defaultstyle
    s1 = create_style(bgcolor='red')

    t = Characters(text1)
    assert t.get_styles(0, len(t)) == [(len(t), s0)]

    t = grouped(t.set_properties(3, 5, {'bgcolor':'red'}))
    styles = t.get_styles(0, len(t))
    assert styles == [
        (3, s0),
        (2, s1),
        (5, s0),
        ]

    # Override styling
    t = t.set_styles(0, [(len(t), s0)])
    assert t.get_styles(0, len(t)) == [(len(t), s0)]

    # And revert
    t = t.set_styles(0, styles)
    styles = t.get_styles(0, len(t))
    assert styles == [
        (3, s0),
        (2, s1),
        (5, s0),
        ]

    # Merge styles:
    styles = Group([Characters(text1), Characters(text1)]). \
             get_styles(0, 2*len(text1))
    assert len(styles) == 1
    assert styles[0][0] == 2*len(text1)


def test_16():
    "undo properties"
    s0 = defaultstyle
    s1 = create_style(fontsize=3)

    model = TextModel(text1)
    old = model.set_properties(2, 5, fontsize=3)
    styles = model.texel.get_styles(0, len(model))
    assert styles == [
        (2, s0),
        (3, s1),
        (5, s0),
        ]
    model.set_styles(2, old)
    styles = model.texel.get_styles(0, len(model))
    assert styles == [
        (10, s0)
        ]

def test_17():
    "Tabulator"
    text = "line 1\nline 2\tcol 1\tcol2\n\n"
    model = TextModel(text)
    #model.texel.dump()
    assert model.get_text() == text


def test_18():
    "dump_range"
    t = TextModel(text1+'\n'+text2)
    dump_range(t.texel, 1, 10)
