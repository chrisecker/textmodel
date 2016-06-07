# -*- coding: latin-1 -*-

from . import texeltree
from .texeltree import G, T, Container, Glyph, length, _join, heal, provides_childs, \
    iter_childs, grouped, get_rightmost, get_leftmost, exchange_rightmost, remove_leftmost, \
    can_merge, merge, join


class StyleIterator:
    n = 0
    style = None
    total = 0
    finished = False
    def __init__(self, iterable):
        self.iterable = iterable
        self.advance(0)
        
    def advance(self, m):
        self.total += m
        self.n -= m
        try:
            while self.n <= 0:
                n, self.style = self.iterable.next()
                self.n += n
        except StopIteration:
            self.finished = True


def hash_style(style):
    return tuple(sorted(style.items()))

style_pool = {}

def style_add((n1, style1), (n2, style2)):
    # used as argument for listjoin: listjoin(a, b, style_add)
    if style1 is style2:
        return [(n1+n2, style1)]
    return [(n1, style1), (n2, style2)]


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


def get_styles(texel, i1, i2):
    if provides_childs(texel):
        styles = []
        for child in texel.childs:
            n = length(child)
            if i1 < n and i2 >= 0:
                new = get_styles(child, i1, i2)
                if len(new) and len(styles):
                    head = new[0]
                    tail = styles[-1]
                    if head[1] is tail[1]:
                        styles = styles[:-1]+[(tail[0]+head[0], head[1])]+new[1:]
                        continue
                styles = styles+new
            i1 -= n
            i2 -= n
        return styles
    return [(length(texel), texel.style)]
        
def merge_append(l, texel): # XXX remove this
    # besser: combine(l1,l2)

    if not l:
        return [texel]
    last = l[-1]
    a = get_rightmost(last) 
    b = get_leftmost(texel)
    if can_merge(a, b):
        l.pop()
        l.append(exchange_rightmost(last, merge(a, b)))
        return l
    return join(l, [textel])


def _merge_join(l1, l2):
    l1 = filter(length, l1) # strip off empty elements
    l2 = filter(length, l2) #
    if not l1:
        return l2
    if not l2:
        return l1
    t1 = l1[-1]
    t2 = l2[0]
    left = get_rightmost(t1)
    right = get_leftmost(t2)
    if can_merge(left, right):
        new = merge(left, right)
        l1.pop()
        l1.append(exchange_rightmost(t1, new))
        return join(l1, [remove_leftmost(t2)], l2[1:])
    return _join(l1, l2)
    

def merge_join(*args):
    # like join(...) but also heal the arguments
    return reduce(_merge_join, args)


def set_styles(texel, i, iterator):
    """Sets the styles from position $i$ on.

       pre:
           is_root_efficient(texel)
       post:
           #out(__return__)
           is_homogeneous(__return__)
           #out("texel:", length(texel))
           #out("return:", calc_length(__return__))
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
                r2 = merge_join(r2, set_styles(child, i-j1, iterator))
        return merge_join(r1, r2, r3)
    elif texel.is_glyph:
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
    else:
        assert False



def iter_d0(texel):
    l = [[texel]]
    i1 = 0
    while l:
        ll = l[-1]
        elem = ll[0]
        del ll[0]
        if elem.is_group:
            l.append(list(elem.childs))
        else:
            i2 = i1+length(elem)
            yield i1, i2, elem
            while not l[-1]:
                l.pop()
                if not l:
                    break


def iter_leaves(texel):
    l = [[texel]]
    i1 = 0
    while l:
        ll = l[-1]
        elem = ll[0]
        del ll[0]
        if elem.is_group or elem.is_container:
            l.append(list(elem.childs))
        else:
            i2 = i1+length(elem)
            yield i1, i2, elem
            while not l[-1]:
                l.pop()
                if not l:
                    break


def get_texts(texel):
    # for debugging
    if provides_childs(texel):
        r = []
        for child in texel.childs:
            r.extend(get_texts(child))
        return r
    if texel.is_text:
        return [texel.text]
    return [' '] # Glyph


class TestContainer(Container):
    def __init__(self, childs):
        self.childs = childs


def test_00():
    "get_styles"
    s10 = dict(size=10)
    s14 = dict(size=14)
    t = G([T("01234", s10), T("5678", s14)])
    assert str(heal(t, 5)) == "G([T('01234'), T('5678')])"
    assert get_styles(t, 0, 9) == [(5, s10), (4, s14)]


def test_01():
    "iter_d0"
    t1 = T("012345678")
    t2 = T("ABC")
    t3 = T("xyz")
    c = TestContainer((t2, t3))
    g = G((t1, c))
    #texeltree.dump(g)
    l = []
    for i1, i2, elem in iter_d0(g):
        l.append((i1, i2, elem))
    assert repr(l) == "[(0, 9, T('012345678')), (0, 0, C([T('ABC'), T('xyz')]))]"
    

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
    #texeltree.dump(g)    
    assert get_texts(g) == ['01', '23', '45678', '9']

    #texeltree.dump(g)    
    iterator = StyleIterator(iter([(10, s10)]))
    n = grouped(set_styles(g, 0, iterator))
    assert get_texts(n) == ['0123456789']

    iterator = StyleIterator(iter([(10, s10)]))
    n = grouped(set_styles(g, 2, iterator))
    assert get_texts(n) == ['0123456789']

    iterator = StyleIterator(iter([(10, s12)]))
    n = grouped(set_styles(g, 2, iterator))
    assert get_texts(n) == ['01', '23456789']

if __name__ == '__main__':
    import alltests
    alltests.dotests()
    
