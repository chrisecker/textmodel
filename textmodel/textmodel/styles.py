# -*- coding: latin-1 -*-

from . import texeltree
from .texeltree import G, T, length, grouped, provides_childs, iter_childs, \
    is_root_efficient, is_list_efficient, is_homogeneous, calc_length, \
    get_pieces, fuse, EMPTYSTYLE, NL, NewLine


debug = 1


class StyleIterator:
    n = 0
    style = None
    total = 0
    finished = False
    def __init__(self, iterable):
        self.iterable = iterable
        self.advance(0)
        
    def advance(self, m):
        #print "advance", m
        self.total += m
        self.n -= m
        try:
            while self.n <= 0:
                n, self.style = self.iterable.next()
                self.n += n
        except StopIteration:
            self.finished = True



style_pool = {():EMPTYSTYLE}


def hash_style(style):
    return tuple(sorted(style.items()))


def create_style(**kwds):
    global style_pool
    key = hash_style(kwds)
    try:
        return style_pool[key]
    except KeyError:
        style_pool[key] = kwds
        return kwds


def updated_style(style, properties):
    new = style.copy()
    new.update(properties)
    return create_style(**new)


def get_style(texel, i):
    if i < 0 or i >= length(texel):
        raise IndexError(i)
    if provides_childs(texel):
        for i1,i2, child in iter_childs(texel):
            if i1 <= i < i2:
                return get_style(child, i-i1)
    return texel.style


def fuse_styles(l1, l2):
    if len(l1) and len(l2):
        tail = l1[-1]
        n, style = l2[0]
        if tail[1] is style:
            return l1[:-1]+[(tail[0]+n, style)]+l2[1:]
    return l1+l2


def get_styles(texel, i1, i2):
    """
    pre:
        0 <= i1 <= i2 <= length(texel)
    post:
        style_length(__return__) == i2-i1
    """
    if i1 == i2:
        return []
    if provides_childs(texel):
        j1 = i1
        j2 = i2
        styles = []
        for child in texel.childs:
            n = length(child)
            if j1 < n and j2 > 0:
                new = get_styles(child, j1, min(j2, n))
                styles = fuse_styles(styles, new)
            j1 = max(0, j1-n)
            j2 = max(0, j2-n)
        return styles
    return [(i2-i1, texel.style)]




def set_styles(texel, i, iterator):
    """Sets the styles from position $i$ on.

       pre:
           is_root_efficient(texel)
       post:
           #out(__return__)
           is_homogeneous(__return__)
           is_list_efficient(__return__)
           length(texel) == calc_length(__return__)
    """

    if texel.is_group:
        r1 = []; r2 = []; r3 = []
        for j1, j2, child in iter_childs(texel):
            if j2 <= i:
                r1.append(child)
            elif iterator.finished:
                r3.append(child)
            else:
                r2 = fuse(r2, set_styles(child, i-j1, iterator))
        return fuse(r1, r2, r3)
    elif texel.is_single:
        if i >= 1:
            return [texel]
        new = texel.set_style(iterator.style)
        iterator.advance(1)
        return [new]
    elif texel.is_text:
        r = []
        text = texel.text
        if i>0:
            r.append(T(text[:i], texel.style))
            text = text[i:]

        while text and not iterator.finished:
            n = min(len(text), iterator.n)
            r.append(T(text[:n], iterator.style))
            iterator.advance(n)
            text = text[n:]
        if text and iterator.finished:
            r.append(T(text, texel.style))
        return r
    elif texel.is_container:
        r1 = []; r2 = []; r3 = []
        for j1, j2, child in iter_childs(texel):
            if j2 <= i:
                r1.append(child)
            elif iterator.finished:
                r3.append(child)
            else:
                r2.append(grouped(set_styles(child, i-j1, iterator)))
        return [texel.set_childs(r1+r2+r3)]
    assert False



def set_properties(texel, i1, i2, properties):
    """Sets text properties in $i1$...$i2$."""
    l1 = get_styles(texel, i1, i2)
    l2 = [(n, updated_style(s, properties)) for n, s in l1]
    return set_styles(texel, i1, StyleIterator(iter(l2)))



def get_parstyles(texel, i1, i2):
    """
    pre:
        0 <= i1 <= i2 <= length(texel)
    post:
        style_length(__return__) == i2-i1
    """
    if i1 == i2:
        return []
    if texel.weights[2]>0 and provides_childs(texel):
        j1 = i1
        j2 = i2
        styles = []
        for child in texel.childs:
            n = length(child)
            if j1 < n and j2 > 0:
                new = get_parstyles(child, j1, min(j2, n))
                styles = fuse_styles(styles, new)
            j1 = max(0, j1-n)
            j2 = max(0, j2-n)
        return styles
    elif isinstance(texel, NewLine):
        return [(i2-i1, texel.parstyle)]
    return [(i2-i1, EMPTYSTYLE)]



def set_parstyles(texel, i, iterator):
    """Sets the paragraph styles from position $i$ on.

       pre:
           is_root_efficient(texel)
       post:
           #out(__return__)
           is_homogeneous(__return__)
           is_list_efficient(__return__)
           length(texel) == calc_length(__return__)
    """
    if not texel.weights[2]:
        iterator.advance(length(texel)-max(0, i))
        return [texel]

    if texel.is_group:
        r1 = []; r2 = []; r3 = []
        for j1, j2, child in iter_childs(texel):
            if j2 <= i:
                r1.append(child)
            elif iterator.finished:
                r3.append(child)
            else:
                r2 = fuse(r2, set_parstyles(child, i-j1, iterator))
        return fuse(r1, r2, r3)
    elif isinstance(texel, NewLine):
        if i >= 1:
            return [texel]
        new = texel.set_parstyle(iterator.style)
        iterator.advance(1)
        return [new]
    elif texel.is_container:
        r1 = []; r2 = []; r3 = []
        for j1, j2, child in iter_childs(texel):
            if j2 <= i:
                r1.append(texel)
            elif iterator.finished:
                r3.append(texel)
            else:
                r2.append(grouped(set_parstyles(child, i-j1, iterator)))
        assert len(r2) == 1
        return texel.set_childs(r1+r2+r3)
    assert False


def set_parproperties(texel, i1, i2, properties):
    """Sets paragraph properties in $i1$...$i2$."""
    l1 = get_parstyles(texel, i1, i2)
    l2 = [(n, updated_style(s, properties)) for n, s in l1]
    return set_parstyles(texel, i1, StyleIterator(iter(l2)))


# -- debug --

def style_length(styles):
    n = 0
    for i, s in styles:
        n += i
    return n


if debug: # enable contract checking
     import contract
     contract.checkmod(__name__)


def test_00():
    "get_style"
    s10 = dict(size=10)
    s12 = dict(size=12)
    g = G([T("01", s10), 
           T("23", s12), 
           T("4567890", s10)])

    #texeltree.dump(g)
    assert get_style(g, 0) is s10
    assert get_style(g, 2) is s12
    assert get_style(g, 4) is s10

def test_01():
    "get_styles"
    s10 = dict(size=10)
    s14 = dict(size=14)
    t = G([T("01234", s10), T("5678", s14)])
    #texeltree.dump(t)
    assert get_styles(t, 0, 2) == [(2, s10)]
    assert get_styles(t, 1, 3) == [(2, s10)]
    assert get_styles(t, 2, 5) == [(3, s10)]
    assert get_styles(t, 0, 9) == [(5, s10), (4, s14)]
    assert get_styles(t, 2, 4) == [(2, s10)]
    assert get_styles(t, 5, 7) == [(2, s14)]


def test_10():
    "set_styles"
    s10 = dict(size=10)
    s12 = dict(size=12)
    s14 = dict(size=14)
    t = T("0123456789", s10)
    styles = [(2, s12), (5, s14)]
    iterator = StyleIterator(iter(styles))
    if 0:
        i = 0
        while not iterator.finished:
            print i, iterator.n, iterator.style
            iterator.advance(1)
            i += 1
    g = grouped(set_styles(t, 2, iterator))
    assert get_pieces(g) == ['01', '23', '45678', '9']

    iterator = StyleIterator(iter([(10, s10)]))
    n = grouped(set_styles(g, 0, iterator))
    assert get_pieces(n) == ['0123456789']

    iterator = StyleIterator(iter([(10, s10)]))
    n = grouped(set_styles(g, 2, iterator))
    assert get_pieces(n) == ['0123456789']

    iterator = StyleIterator(iter([(10, s12)]))
    n = grouped(set_styles(g, 2, iterator))
    assert get_pieces(n) == ['01', '23456789']


def test_11():
    "set_properties"
    s10 = dict(size=10)
    s12 = dict(size=12)
    t = T("0123456789", s10)
    g = grouped(set_properties(t, 2, 4, dict(size=12)))
    #texeltree.dump(g)
    assert get_styles(g, 0, 10) == [(2, s10), (2, s12), (6, s10)]


def test_12():
    "set_parstyles"
    t = grouped([T("0123456789"), NL, T("abcdef"), NL]) 
    iterator = StyleIterator(iter([(10, {'bold':True})]))
    g = grouped(set_parstyles(t, 5, iterator))
    texeltree.dump(g)

    print get_parstyles(g, 0, length(g))

