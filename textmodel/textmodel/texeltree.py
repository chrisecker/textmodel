# -*- coding: latin-1 -*-


from . import treebase
from copy import copy as shallow_copy
from .treebase import remove, copy, simple_insert, insert, groups, \
    depth, get_rightmost, get_leftmost, exchange_rightmost, \
    remove_leftmost, ungroup, strip, heal, is_homogeneous, \
    is_root_efficient, join, homogenize, maxdepth
from .treebase import grouped as _grouped
from .listtools import listjoin, calc_length


debug = 0 # no checks
#debug = 1 # do checks

def hash_style(style):
    return tuple(sorted(style.items()))

style_pool = {}
defaultstyle = {}
def create_style(**kwds):
    global style_pool
    style = defaultstyle.copy()
    style.update(kwds)
    key = hash_style(style)
    try:
        return style_pool[key]
    except KeyError:
        style_pool[key] = style
        return style

defaultstyle = create_style(
    textcolor='black',
    bgcolor='white',
    fontsize=10
    )


def updated_style(style, properties):
    new = style.copy()
    new.update(properties)
    return create_style(**new)


def _style_add((n1, style1), (n2, style2)):
    # used as argument for listjoin: listjoin(a, b, _style_add)
    if style1 is style2:
        return [(n1+n2, style1)]
    return [(n1, style1), (n2, style2)]



class Texel:
    """Baseclass of all text elements.

    Texts consist of texels (TExt-ELements) similar as pictures
    consist of pixels (PICture-ELements).

    All texels need to be derived from Texel. In addition they need to
    be derived from treebase.Element.
    """
    weights = treebase.Element.weights+(0,) # new weight: number of new lines
    functions = treebase.Element.functions+(sum,)

    def get_style(self, i):
        """Returns the style at index $i$"""
        return {}

    def get_text(self):
        """Returns an unicode string with all textual content.

           post:
               len(self) == len(__return__)
        """
        return u' '

    def get_styles(self, i1, i2):
        """Returns all format information between $i1$ and $i2$.

        The return value has the form [(n0, s0), (n1, s1), ...], where
        n is the number of characters formated with style s.
        """
        return []

    def set_styles(self, i, styles):
        """Sets the styles from position $i$ on according to the list $styles$


        Styles is a list of the form [(n1, s1), (n2, s2), ... ], where
        each s is a style and n is a length in index positions. The
        combination get_styles / set_styles is only used for undoing
        the set_properties-operation.
        """
        pass

    def set_properties(self, i1, i2, properties):
        """Sets style-properties for all texels in the range $i1$ to $i2$.

        The value $properties$ is a dic, e.g.  {'fontsize':16,
        'bgcolor':'red'}.
        """
        pass

    @staticmethod
    def create_group(l):
        return Group(l)



class Group(Texel, treebase.Group):
    """A class which can hold a list (childs) of other texels."""

    def __getstate__(self):
        state = self.__dict__.copy()
        try:
            del state['weights']
        except KeyError:
            pass
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self.compute_weights()

    def get_text(self):
        return u''.join(texel.get_text() for texel in self.childs)

    def get_style(self, i):
        for texel in self.childs:
            n = len(texel)
            if n > i:
                return texel.get_style(i)
            i -= n

    def get_styles(self, i1, i2):
        styles = []
        for texel in self.childs:
            n = len(texel)
            if i1 < n and i2 >= 0:
                styles = listjoin(styles, texel.get_styles(i1, i2), _style_add)
            i1 -= n
            i2 -= n
        return styles

    def set_styles(self, i, styles):
        data = []
        for texel in self.childs:
            # XXX should be optimized
            data.append(texel.set_styles(i, styles))
            i -= len(texel)
        assert calc_length(data) == len(self)
        g = self.create_group(homogenize(data))
        # merge childs if possible
        j = 0
        for texel in data:
            j += len(texel)
            g = heal(g, j)
        return g

    def set_properties(self, i1, i2, properties):
        assert i2 >= i1
        r = []
        i = 0
        for texel in self.childs:
            n = len(texel)
            if i1 < n and i2 > 0:
                r += texel.set_properties(i1, i2, properties)
            else:
                r.append(texel)
            i1 -= n
            i2 -= n
        try:
            assert is_homogeneous(r)
        except:
            print "before:"
            self.dump()
            print "after:"
            for i, x in enumerate(r):
                print "item", i
                x.dump()
        return groups(r)
G = Group


class Glyph(Texel, treebase.Element):
    """ Baseclass for texels representing a single character (examples:
        newline, tabulator)"""
    style = defaultstyle
    weights = (0, 1, 0)

    def __init__(self, style=None):
        if style is not None:
            self.style = style

    def get_style(self, i):
        return self.style

    def get_text(self):
        return ' '

    def get_styles(self, i1, i2):
        if i2 > 0 >= i1:
            return [(1, self.style)]
        return []

    def set_styles(self, i, styles):
        styles = styles[:]
        while styles:
            l, style = styles[0]
            del styles[0]
            if i <= 0 and i+l > 0:
                clone = shallow_copy(self)
                clone.style = style
                return clone
            i += l
        return self

    def set_properties(self, i1, i2, properties):
        if i1 <= 0 and i2 > 0:
            clone = shallow_copy(self)
            clone.style = updated_style(self.style, properties)
            return [clone]
        return [self]

    def replace_child(self, i1, i2, stuff):
        if i1 == i2 == 0:
            return join(stuff, [self])
        elif i1 == i2 == 1:
            return join([self], stuff)
        raise IndexError, (i1, i2)

    def takeout(self, i1, i2):
        if i1 == i2:
            return [self], []
        return [], [self]



class Characters(Texel, treebase.Element):
    """Texel holding a string of unicode characters."""
    def __init__(self, text, style=defaultstyle):
        unicode(text) # check proper encoding
        self.text = text
        self.style = style
        self.compute_weights()

    def compute_weights(self):
        self.weights = list(self.weights)
        self.weights[1] = len(self.text)

    def __str__(self):
        return "C(%s)" % repr(self.text)

    def __repr__(self):
        return "C(%s, %s)" % (repr(self.text), repr(self.style))

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['weights']
        return state

    def __setstate__(self, state):        
        self.__dict__ = state
        self.compute_weights()

    def get_text(self):
        return self.text

    def get_style(self, i):
        return self.style

    def get_styles(self, i1, i2):
        i1 = max(0, i1)
        i2 = min(len(self), i2)
        if i2 > i1:
            return [(i2-i1, self.style)]
        return []

    def set_styles(self, i, styles):
        text = self.text
        r = []
        while text:
            if not styles:
                texel = self.__class__(text, self.style)
                r.append(texel)
                break
            l, style = styles[0]
            n = len(text)
            if i > n:
                # entry is right of text
                texel = self.__class__(text, self.style)
                r.append(texel)
                break
            elif i+l <= 0:
                # entry is left of text
                i += l
                styles = styles[1:]
                continue
            if i < 0:
                l += i
                i = 0
            assert i >= 0
            if i > 0:
                texel = self.__class__(text[:i], self.style)
                r.append(texel)
                text = text[i:]
                i = 0
            assert l > 0
            assert i == 0
            m = min(l, n)
            texel = self.__class__(text[:m], style)
            r.append(texel)
            if l >= n:
                break
            text = text[m:]
            styles = [(l-m, style)]+list(styles[1:])

        assert calc_length(r) == len(self)
        return self.create_group(r)

    def set_properties(self, i1, i2, properties):
        if i1 == i2:
            return [self]
        style = updated_style(self.style, properties)
        if style is self.style:
            return [self]
        i1 = max(0, i1)
        i2 = min(len(self), i2)
        assert i2 >= i1
        data = self.text
        Characters = self.__class__
        l = Characters(data[:i1], self.style)
        c = Characters(data[i1:i2], style)
        r = Characters(data[i2:], self.style)
        return [x for x in (l, c, r) if len(x)]

    def replace_child(self, i1, i2, stuff):
        Characters = self.__class__
        r1 = Characters(self.text[:i1], self.style)
        r2 = Characters(self.text[i2:], self.style)
        return join(*filter(calc_length, [[r1], stuff, [r2]]))

    def takeout(self, i1, i2):
        if not 0 <= i1 <= i2 <= len(self):
            raise IndexError((i1, i2))
        r1 = self.text[:i1]
        r2 = self.text[i2:]
        r3 = self.text[i1:i2]
        s = self.style
        Characters = self.__class__
        return [Characters(r1+r2, s)], [Characters(r3, s)]

    def can_merge(self, other):
        if isinstance(other, Characters) and self.style is other.style:
            return True

    def merge(self, other):
        assert self.can_merge(other)
        return self.__class__(self.text+other.text, self.style)

    def dump(self, i=0):
        print (" "*i)+str(self), id(self.style)

C = Characters
NULL_TEXEL = Characters('')
SPACE = Characters(' ')



class NewLine(Glyph):
    weights = (0, 1, 1)
    is_endmark = False
    def __repr__(self):
        return 'NL'

    def __str__(self):
        return 'NL'

    def get_text(self):
        return u'\n'

NL = NewLine()
ENDMARK = NewLine()
ENDMARK.is_endmark = True


class Tabulator(Glyph):
    def get_text(self):
        return u'\t'

TAB = Tabulator()




def grouped(stuff):
    # A modified version of treebase.grouped() which can also handle
    # empty lists.
    if not stuff:
        return Group([])
    return _grouped(stuff)





text1 = "0123456789"
text2 = "abcdefghijklmnopqrstuvwxyz"
text3 = "01\n345\n\n89012\n45678\n"

def check(texel):
    """Test wether $texel$ behaves properly."""
    assert isinstance(texel, Texel)

    # pickle/restore must be possible
    import cPickle
    s = cPickle.dumps(texel)
    clone = cPickle.loads(s)
    assert depth(clone) == depth(texel)
    assert len(clone) == len(texel)
    assert clone.weights == texel.weights

    # insert must be possible in alle positions
    x = Characters('X')
    for i in range(len(texel)+1):
        simple_insert(texel, i, [x])

    # inserting via "replace_child" must be possible at first and last and
    # for all child positions
    for i in [0, len(texel)]+[i1 for (i1, i2, c) in texel.iter_childs()]:
        texel.replace_child(i, i, [x])
        texel.replace_child(i, i, [x])

    # removing via "replace_child" must be possible for all child intervals
    for i1, i2, child in texel.iter_childs():
        texel.replace_child(i1, i2, [])

    # takeout must be possible for all positions in a child
    for i1, i2, child in texel.iter_childs():
        for i in range(i2-i1):
            texel.takeout(i1+i, i1+i+1)

    # takeout must be possible across child boundaries
    l = []
    for i1, i2, child in texel.iter_childs():
        if l:
            if l[-1][1] == i1:
                j1, j2 = l.pop()
                l.append((j1, i2))
                continue
        l.append([i1, i2])
    for i1, i2 in l:
        for i in range(i2-i1-1):
            texel.takeout(i1+i, i1+i+2)

    # takeout must raise an IndexError if it is tried to remove an
    # empty position
    l = [] # empty positions
    last = None
    for i1, i2, child in texel.iter_childs():
        if last is not None:
            if i1 > last:
                assert i1-last == 1 # empty positions can't be neighbours
                l.append(last)
        last = i2
    for i in l:
        ok = False
        try:
            texel.takeout(i, i+1)
        except IndexError:
            ok = True
        assert ok

    # Style must be defined and writeable for all n positions
    s1 = create_style(fontsize = -1)
    s2 = create_style(fontsize = -2)
    for i in range(len(texel)):
        texel.get_style(i)
        tmp = texel.set_styles(i, [(1, s1)])
        try:
            assert tmp.get_style(i) == s1
        except:
            print i, tmp.get_text()[i:i+1]
            tmp.dump()
            raise
        tmp = texel.set_properties(i, i+1, {'fontsize':-2})
        assert G(tmp).get_style(i) == s2
    return True


def check_split(texel):
    for i in range(len(texel)+1):
        texel.takeout(0, i)
        texel.takeout(i, len(texel))
    return True

if debug:
     #enable contract checking
     import contract
     contract.checkmod(__name__)


def test_00():
    "Characters"
    s = Characters(text1)
    assert check_split(s)
    assert check(s)


def test_01():
    "Group"
    s = Characters(text1)
    s1 = Characters(text1)
    s2 = Characters(text1)

    s1 = Characters(text1)
    s2 = Characters(text1, style=create_style(fontsize=4))

    # we need to set nmax to avoid that the efficiency tests to
    # complain about our constructed groups.
    treebase.set_nmax(3)

    c = Group([s1, s2])
    assert check(c)
    assert check_split(c)

    c1 = Group([c, c])
    assert check(c1)
    check_split(c1)

    c1 = Group([c, Group([Characters("X"), Characters("Y")]), c])
    assert is_root_efficient(c1)
    assert check(c1)
    assert check_split(c1)

    c1 = Group([c]*20)



def test_02():
    "insert and heal"

    t1 = Characters(text1)
    t2 = Characters(text2)

    # check that texts with same styling are merged
    for i in range(len(t1)+1):
        t = heal(grouped(insert(t1, i, [t2])), i, i+len(t2))
        if not isinstance(t, Characters):
            t.dump()
        assert isinstance(t, Characters)

    g = Group([t2])
    # check that group is removed by heal
    for i in range(len(t1)+1):
        t = grouped(insert(t1, i, [g]))
        t = heal(t, i, i+len(g))
        assert isinstance(t, Characters)


def test_05():
    "insert"
    c = Characters(text1)
    g = Group([c])
    n = NL
    items = [c, g, n]
    for item in items:
        for other in items:
            n = len(item)
            no = len(other)
            item_text = item.get_text()
            other_text = other.get_text()
            for i in range(len(item)+1):
                r = grouped(insert(item, i, [other]))
                assert len(r) == n+no
                assert r.get_text() == item_text[:i]+other_text+item_text[i:]


def test_06():
    "heal"
    C = Characters
    G = Group
    t = G([C("01234"), C(""), C("56789")])
    assert str(heal(t, 5)) == "C('0123456789')"

    t = G([G([C("01234")]), G([ C(""), C("56789")])])
    assert str(heal(t, 5)) == "C('0123456789')"

    t = G([G([C("01234"), C(""), C("")]), G([ C(""), C("56789")])])
    assert str(heal(t, 5)) == "C('0123456789')"


def test_07():
    "set properties"
    texel = Characters('0123')
    from random import randrange, choice

    defaultstyle.clear()
    defaultstyle['s'] = 10

    n = len(texel)
    for j in range(2000):
        i1 = randrange(n)
        i2 = randrange(n)
        i1, i2 = sorted([i1, i2])
        size = choice([10, 14])
        new = heal(grouped(texel.set_properties(i1, i2, {'s':size})), i1, i2)
        assert not "C(u'')" in str(texel)
        assert not "C(u'')" in str(new)
        texel = new
    #texel.dump()


def test_08():
    "get/set styles"

    s0 = defaultstyle
    s1 = create_style(bgcolor='red')
    s2 = create_style(bgcolor='yellow')

    def styles2str(styles):
        r = []
        for l, style in styles:
            i = 'x'
            if style == s0:
                i = "0"
            elif style == s1:
                i = "1"
            elif style == s2:
                i = "2"
            r.append(i*l)
        return ''.join(r)

    t = Characters(text1)
    assert t.get_styles(0, len(t)) == [(len(t), s0)]
    t = t.set_styles(6, [(1, s2)])
    #print styles2str(t.get_styles(0, len(t)))
    assert styles2str(t.get_styles(0, len(t))) == '0000002000'

    t = Characters(text1)
    t = grouped(t.set_properties(3, 5, {'bgcolor':'red'}))
    assert styles2str(t.get_styles(0, len(t))) == '0001100000'
    assert styles2str(t.get_styles(1, len(t))) == '001100000'
    assert styles2str(t.get_styles(4, len(t))) == '100000'

    t = t.set_styles(6, [(1, s2)])
    assert styles2str(t.get_styles(0, len(t))) == '0001102000'

    # override styling
    n = len(t)
    styles = t.get_styles(1, len(t))
    t = t.set_styles(5, [(len(t)-5, s0)])
    assert styles2str(t.get_styles(0, len(t))) == '0001100000'

    # restore styling
    t = t.set_styles(1, styles)
    styles = t.get_styles(1, len(t))
    assert styles2str(t.get_styles(0, len(t))) == '0001102000'

    # strings with same styling should be merged
    t = t.set_styles(3, [(10, s0)])
    assert isinstance(t, Characters) # assert that we have only one texel

    # merging styles
    styles = Group([Characters(text1), Characters(text1)]).\
        get_styles(0, 2*len(text1))
    assert len(styles) == 1
    assert styles[0][0] == 2*len(text1)

def test_09():
    "NewLine"
    texel = NewLine()
    assert check(texel)

    c = Group([C('0123456789'), NewLine(), C('BCD')])
    assert check(c)


def test_10():
    "optimized growth"

    def maxn(texel):
        if isinstance(texel, Group):
            n = len(texel.childs)
            return max(n, max([maxn(g) for g in texel.childs]))
        return 1

    def check_depth(texel):
        # assert uniform_depth(texel)
        if not isinstance(texel, Group):
            return True
        if not len(texel.childs):
            return True
        d = depth(texel)
        for child in texel.childs:
            if not depth(child) == d-1:
                texel.dump()
            assert depth(child) == d-1
        for child in texel.childs:
            assert check_depth(child)
        return True

    def check_nchilds(texel, is_root=True):
        if isinstance(texel, Group):
            if not is_root:
                assert len(texel.childs) >= treebase.nmax/2
            assert len(texel.childs) <= treebase.nmax
            for child in texel.childs:
                assert check_nchilds(child, False)
        return True

    for n in (3, 4, 5, 6):
        treebase.set_nmax(n)
        t =  Characters("X")
        for i in range(30):
            # create new styles to suppress merging of strings
            tt = Characters("%i " % i, style=create_style(fontsize=i))
            old = t
            t = grouped(insert(t, 0, [tt]))
            assert check_depth(t)
            assert check_nchilds(t)
    #t.dump()

def test_10():
    "optimized growth"

    for n in (3, 4, 5, 6):
        #print "nmax = ", n
        treebase.set_nmax(n)
        t =  Characters("X")
        for i in range(30):
            # create new styles to suppress merging of strings
            tt = Characters("%i " % i, style=create_style(fontsize=i))
            old = t
            t = grouped(insert(t, 0, [tt]))
            try:
                assert is_root_efficient(t)
            except:
                print "t is not efficient:"
                t.dump()
                raise


