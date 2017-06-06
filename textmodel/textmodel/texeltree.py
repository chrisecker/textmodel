# -*- coding: latin-1 -*-


from copy import copy as shallow_copy


debug = 0
nmax = 15

def set_nmax(n):
    """Sets *nmax* to the value *i*.

       The value nmax determines the number of childs per group (which
       should be between nmax/2 and nmax for efficient trees).
    """
    global nmax
    nmax = n

EMPTYSTYLE = {}
style_pool = {():EMPTYSTYLE}

def hash_style(style):
    return tuple(sorted(style.items()))


def as_style(d):
    global style_pool
    key = hash_style(d)
    try:
        return style_pool[key]
    except KeyError:
        style_pool[key] = d
        return d


# ---- Tree objects ----
class Texel:
    is_single = 0
    is_container = 0
    is_group = 0
    is_text = 0
    is_endmark = 0
    weights = (0, 0, 0) # depth, length, lineno


class Single(Texel):
    is_single = 1
    weights = (0, 1, 0)
    style = EMPTYSTYLE
    text = '-'

    def __init__(self, style=None):
        if style:
            self.style = style

    def set_style(self, style):
        clone = shallow_copy(self)
        clone.style = style
        return clone

    def __setstate__(self, state):
        self.__dict__ = state
        self.style = as_style(self.style)


class Text(Texel):
    is_text = 1
    def __init__(self, text, style=EMPTYSTYLE):
        self.text = text
        self.style = style
        self.weights = (0, len(text), 0)

    def __repr__(self):
        return "T(%s)" % repr(self.text)

    def __setstate__(self, state):
        self.__dict__ = state
        self.style = as_style(self.style)

T = Text


class _TexelWithChilds(Texel):
    def compute_weights(self):
        if len(self.childs): # for empty groups, we use the default weights
            w_list = zip(*[child.weights for child in self.childs])
            self.weights = [f(l) for (l, f) in zip(w_list, self.functions)]



class Group(_TexelWithChilds):
    is_group = 1
    functions = (
        lambda l:max(l)+1, 
        sum,               
        sum)

    def __init__(self, childs):
        self.childs = childs
        self.compute_weights()

    def __repr__(self):
        return 'G(%s)' % repr(list(self.childs))
G = Group



class Container(_TexelWithChilds):
    is_container = 1
    functions = (
        lambda l:0,
        sum,               
        sum)
        
    def set_childs(self, childs):
        clone = shallow_copy(self)
        clone.childs = childs
        clone.compute_weights()
        return clone

    def __repr__(self):
        return 'C(%s)' % repr(list(self.childs))

    def get_mutability(self):
        return [i%2==1 for i in range(len(self.childs))]

        

class NewLine(Single):
    weights = (0, 1, 1)
    style = EMPTYSTYLE
    parstyle = EMPTYSTYLE
    text = u'\n'

    def __repr__(self):
        return 'NL'

    def set_parstyle(self, style):
        clone = shallow_copy(self)
        clone.parstyle = style
        return clone

    def __setstate__(self, state):
        self.__dict__ = state
        self.style = as_style(self.style)
        self.parstyle = as_style(self.parstyle)


class Tabulator(Single):
    text = u'\t'

    def __repr__(self):
        return 'TAB'


class Fraction(Container):
    # A simple math object for debugging
    def __init__(self, denominator, nominator):
        self.childs = [TAB, denominator, TAB, nominator, TAB]
        self.compute_weights()
    

TAB = Tabulator()
NL = NewLine()
ENDMARK = NewLine()
ENDMARK.is_endmark = 1
NULL_TEXEL = T(u'')

# ---- functions -----
def depth(texel):
    """Returns the depth of an element.

       The depth can be definied as the number of generations of
       groups. By definition empty groups have depth 0.

       >>> depth(Text('abc'))
       0

       >>> depth(G(Text('abc')))
       1

       >>> depth(G()) # empty groups are ignored
       0
    """
    return texel.weights[0]


def length(texel):
    """Returns the length of *texel* in index units."""
    return texel.weights[1]


def spans(texel):
    r = []
    mutable = texel.get_mutability()
    k = -1    
    for i1, i2, child in iter_childs(texel):
        k += 1
        if mutable[k]:
            r.append((i1, i2))
    return r


def iter_childs(texel):
    assert texel.is_group or texel.is_container
    i1 = 0
    for child in texel.childs:
        i2 = i1+length(child)
        yield i1, i2, child
        i1 = i2    


def iter_d0(texel): # not needed, but might be useful in future
    """Iterate through all depth-zero elements. """
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
            while l and not l[-1]:
                l.pop()


def iter_leaves(texel): # not needed, but might be useful in future
    """Iterate through all leaf-elements """
    l = [[texel]]
    i1 = 0
    while 1:
        while l and not l[-1]:
            l.pop()
        if not l:
            break
        ll = l[-1]
        elem = ll[0]
        del ll[0]
        if elem.is_group or elem.is_container:
            l.append(list(elem.childs))
        else:
            i2 = i1+length(elem)
            yield i1, i2, elem
            i1 = i2


def groups(l):
    """Transform the list of texels *l* into a list of groups.

       If texels have depth d, groups will have depth d+1. All
       returned groups are efficient.

       pre:
           is_elementlist(l)
           is_list_efficient(l)
           is_clean(l)

       post[l]:
           is_homogeneous(__return__)
           calc_length(l) == calc_length(__return__)
           #out("groups check: ok")
           #is_list_efficient(__return__) # XXX
           depth(__return__[0]) == depth(l[0])+1

    """
    r = []
    N = len(l)
    if N == 0:
        return r

    n = N // nmax
    if n*nmax < N:
        n = n+1
    rest = n*nmax-N

    a = nmax-float(rest)/n
    b = a
    while l:
        i = int(b+1e-10)
        r.append(Group(l[:i]))
        l = l[i:]
        b = b-i+a
    return r


def _join(l1, l2):
    """
    pre:
       is_homogeneous(l1)
       is_homogeneous(l2)
       is_clean(l1)
       is_clean(l2)
    post:
       is_clean(__return__)
       calc_length(l1)+calc_length(l2) == calc_length(__return__)
    """
    l1 = filter(length, l1) # strip off empty elements
    l2 = filter(length, l2) #
    if not l1:
        return l2
    if not l2:
        return l1
    t1 = l1[-1]
    t2 = l2[0]
    d1 = depth(t1)
    d2 = depth(t2)
    if d1 == d2:
        return l1+l2
    elif d1 > d2:
        return l1[:-1]+groups(_join(t1.childs, l2))
    # d1 < d2
    return groups(_join(l1, t2.childs))+l2[1:]


def join(*args):
    """Join several homogeneous lists of elements.

       The returned list is homogeneous.

       pre:
           forall(args, is_elementlist)
           forall(args, is_list_efficient)
       post[args]:
           is_homogeneous(__return__)
           is_clean(__return__)
           sum([calc_length(x) for x in args]) == calc_length(__return__)
           #out("join check: ok")
    """
    return reduce(_join, args)


def _fuse(l1, l2):
    """
    pre:
       is_homogeneous(l1)
       is_homogeneous(l2)
       is_clean(l1)
       is_clean(l2)
    post:
       is_clean(__return__)
       is_homogeneous(l2)
       calc_length(l1)+calc_length(l2) == calc_length(__return__)
    """
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
        return join(l1, remove_leftmost(t2), l2[1:])
    return _join(l1, l2)
    

def fuse(*args):
    """Like join(...) but also merge the arguments if possible.

       The returned list is homogeneous.

       pre:
           forall(args, is_elementlist)
           forall(args, is_homogeneous)

       post[args]:
           is_homogeneous(__return__)
           is_clean(__return__)
           sum([calc_length(x) for x in args]) == calc_length(__return__)
           #out("join check: ok")
    """
    return reduce(_fuse, args)


def insert(texel, i, stuff):
    """Inserts the list *stuff* at position *i*.

       *Texel* must be root-efficient, *stuff* must be
       list-efficient. Note that insert can increase the texels
       depth. The returned list is always list efficient.

       pre:
           isinstance(texel, Texel)
           is_elementlist(stuff)
           is_list_efficient(stuff)

       post:
           calc_length(__return__) == length(texel)+calc_length(stuff)
           is_list_efficient(__return__)
           is_clean(__return__)
    """
    if not 0 <= i <= length(texel):
        raise IndexError(i)
    if texel.is_group:
        k = -1
        for i1, i2, child in iter_childs(texel):
            k += 1
            if i1 <= i <= i2:
                l = insert(child, i-i1, stuff)
                r1 = texel.childs[:k]
                r2 = texel.childs[k+1:]
                return join(r1, l, r2)
    elif texel.is_container:
        mutable = texel.get_mutability()
        k = -1
        for i1, i2, child in iter_childs(texel):
            k += 1
            if (i1 < i < i2) or ((i1 <= i <= i2) and mutable[k]):
                l = insert(child, i-i1, stuff)
                r1 = texel.childs[:k]
                r2 = texel.childs[k+1:]
                return [texel.set_childs(r1+[grouped(l)]+r2)]
        if i == 0:
            return join(stuff, [texel])
        elif i == length(texel):
            return join([texel], stuff)
        assert False

    return fuse(copy(texel, 0, i), stuff, copy(texel, i, length(texel)))


def takeout(texel, i1, i2):
    """Takes out all content between *i1* and *i2*.

    Returns the rest and the cut out piece (kernel), i.e.
    G([a, b, c]).takeout(i1, i2) will return G([a, c]), b.

    *Texel* must be root efficient. Kernel and rest are guaranteed to
    be list efficient. Depths can change.

    pre:
        is_root_efficient(texel)
        #out(texel, i1, i2)

    post:
        is_elementlist(__return__[0])
        is_elementlist(__return__[1])
        is_homogeneous(__return__[0])
        is_homogeneous(__return__[1])
        calc_length(__return__[0])+i2-i1 == length(texel)
        calc_length(__return__[1]) == i2-i1
        #out("takeout", texel, i1, i2)
        #out(__return__[0])
        #out(__return__[1])
        #dump_list(__return__[0])
        is_clean(__return__[0])
        is_clean(__return__[1])
        is_list_efficient(__return__[0])
        is_list_efficient(__return__[1])

    """
    if not (0 <= i1 <= i2 <= length(texel)): 
        raise IndexError([i1, i2])
    if not length(texel): # 1. empty texel
        return [], []
    if i1 == i2:          # 2. empty interval
        return strip2list(texel), []
    if i1 <= 0 and i2 >= length(texel): # 3. fully contained
        return [], strip2list(texel)

    # Note that singles always fall under case 2 or 3. Beyond ths
    # point we only have G, C or T.

    if texel.is_group:
        r1 = []; r2 = []; r3 = []; r4 = []
        k1 = []; k2 = []; k3 = []
        for j1, j2, child in iter_childs(texel):
            if j2 <= i1:
                r1.append(child)
            elif i1 <= j1 <= j2 <= i2:
                k2.append(child)
            elif j1 <= i1 <= j2:
                r, k = takeout(child, max(i1-j1, 0), min(i2-j1, length(child)))
                r2.extend(r)
                k1.extend(k)
            elif j1 <= i2 <= j2:
                r, k = takeout(child, max(i1-j1, 0), min(i2-j1, length(child)))
                r3.extend(r)
                k3.extend(k)
            elif i2 <= j1:
                r4.append(child)
        # Note that we are returning a list of elements which have
        # been in the content before. So even if texel is only root
        # efficient, the elements muss be element efficient.  Each of
        # the list r1, r2, r3, r4 and k1, k2, k3 is
        # homogeneous. Therefore join gives us list efficient return
        # values.
        if not is_clean(r2):
            dump_list(r2)
        if not is_clean(r3):
            dump_list(r3)

        tmp = fuse(r2, r3)
        return join(r1, tmp, r4), join(k1, k2, k3)
        
    elif texel.is_container:
        for k, (j1, j2, child) in enumerate(iter_childs(texel)):
            if  i1 < j2 and j1 < i2: # test of overlap
                if not (j1 <= i1 and i2 <= j2):
                    raise IndexError((i1, i2))
                childs = list(texel.childs) # this always creates a new list!
                tmp, kernel = takeout(
                    child, max(0, i1-j1), min(length(texel), i2-j1))
                childs[k] = grouped(tmp)
                return [texel.set_childs(childs)], kernel
        raise IndexError((i1, i2))

    elif texel.is_text:
        r1 = texel.text[:i1]
        r2 = texel.text[i2:]
        r3 = texel.text[i1:i2]
        s = texel.style
        return [Text(r1+r2, s)], [Text(r3, s)]

    assert False


def copy(root, i1, i2):
    """Copy all content of *root* between *i1* and *i2*.

       pre:
           isinstance(root, Texel)

       post:
           calc_length(__return__) == (i2-i1)
    """
    return takeout(root, i1, i2)[1]


def grouped(stuff):
    """Creates a single group from the list of texels *stuff*.

       If the number of texels exceeds nmax, subgroups are formed.
       Therefore, the depth can increase. 

       pre:
           is_elementlist(stuff)
           is_homogeneous(stuff)
           is_clean(stuff) 
           
       post:
           length(__return__) == calc_length(stuff)
    """
    while len(stuff) > nmax:
        stuff = groups(stuff)
    g = Group(stuff)
    return strip(g)


def strip(element):
    """Removes unnecessary Group-elements from the root."""
    n = length(element)
    while element.is_group and len(element.childs) == 1:
        element = element.childs[0]
    assert n == length(element)
    return element


def strip2list(texel):
    """Returns a list of texels which is list efficient. 
       pre:
           is_root_efficient(texel)
       post:
           is_list_efficient(__return__)
    """
    if texel.is_group:
        return texel.childs
    return [texel]


def provides_childs(texel):
    """Returns True if *texel* provides the childs_interface."""
    return texel.is_group or texel.is_container


def get_rightmost(element):
    if provides_childs(element):
        return get_rightmost(element.childs[-1])
    return element


def get_leftmost(element):
    if provides_childs(element):
        return get_leftmost(element.childs[0])
    return element


def exchange_rightmost(element, new):
    """Replace the rightmost subelement of *element* by *new*.

       pre:
           depth(new) == 0
       post:
           depth(__return__) == depth(element)
    """
    if provides_childs(element):
        l = exchange_rightmost(element.childs[-1], new)
        return Group(element.childs[:-1]+[l])
    return new


def remove_leftmost(element):
    """Removes the leftmost subelement of *element*. Returns a list.

       Note that this function can change the depth. 

       post:
           is_homogeneous(__return__)
           is_list_efficient(__return__)
    """

    if length(element) == 0 or depth(element) == 0:
        return []

    l = remove_leftmost(element.childs[0])
    return join(l, element.childs[1:])


def can_merge(texel1, texel2):
    return texel1.is_text and texel2.is_text and \
           texel1.style is texel2.style


def merge(texel1, texel2):
    """Merge the rightmost child of *texel1* with the leftmost child of
*texel2*.

       pre:
           isinstance(texel1, Texel)
           isinstance(texel2, Texel)
           can_merge(texel1, texel2)

       post:
           length(__return__) == length(texel1)+length(texel2)
    """
    return Text(texel1.text+texel2.text, texel1.style)


def compute_hull(texel, i1, i2, i0=0):
    if texel.is_text or texel.is_single:
        return i1, i2
    elif texel.is_container:
        overlapp = False
        for j1, j2 in spans(texel):
            if j1+i0 <= i1 <= i2 <= j2+i0: # inside
                overlapp = True
                continue
            if i1 < j2+i0 and j1+i0 < i2: # overlapp but not inside
                overlapp = True
                i1 = min(i1, j1+i0)
                i2 = max(i2, j2+i0)
        if not overlapp:
            i1 = min(i0, i1)
            i2 = max(i0+length(texel), i1)

    for j1, j2, child in iter_childs(texel):
        if j1+i0 <= i1 <= i2 <= j2+i0:
            i1, i2 = compute_hull(child, i1, i2, i0+j1)
    return i1, i2


def get_text(texel):
    if texel.is_single or texel.is_text:
        return texel.text
    assert texel.is_group or texel.is_container
    return u''.join([get_text(x) for x in texel.childs])


# ---- Debug Tools ---

def get_pieces(texel):
    """For debugging: returns a list of text pieces in *texel*."""
    if type(texel) == list:
        texel = grouped(texel)
    if provides_childs(texel):
        r = []
        for child in texel.childs:
            r.extend(get_pieces(child))
        return r
    if texel.is_text:
        return [texel.text]
    return [' '] # Glyph


def calc_length(l):
    """Calculates the total length of all elements in list *l*."""
    return sum([length(x) for x in l])


def is_clean(l):
    """Returns True if no element in list *l* has zero length. """
    for texel in l:                
        if length(texel) == 0:
            return False
        if texel.is_group:
            if not is_clean(texel.childs):
                return False
    return True
    

def is_homogeneous(l):
    """Returns True if the elements in list *l* are homogeneous.

       Elements are homogeneous if they have alle the same depth.
    """
    return maxdepth(l) == mindepth(l)


def is_efficient(element):
    """Returns True if *element* is efficient.

       An element is efficient, if it is not a group or otherwise if
       all of the following criteria are fulfilled:

       1. if each descendant group has between nmax/2 and nmax childs
       2. the depth of all childs is homogeneous

       In an efficient tree all groups (with the exception of the root
       node) must be element_efficient.

       Note: this function is very slow and should only be used for
       debugging.
    """
    if not is_group(element):
        return True
    if not is_homogeneous(element.childs):
        return False
    if len(element.childs) < nmax/2 or len(element.childs) > nmax:
        return False
    if not is_list_efficient(element.childs):
        return False
    return True


def is_list_efficient(l):
    """Returns True if each element in the list *l* is efficient.
       pre:
           isinstance(l, list)
    """
    if not is_homogeneous(l):
        return False
    for element in l:
        if not is_efficient(element):
            return False
    return True


def is_root_efficient(root):
    """Returns True if *root* is efficient.

       The tree spawned by *root* is efficient if it is either not a
       group or otherwise if it fulfills all of the following
       conditions:

       1. all childs are efficient
       2. the number of childs is <= nmax

       Note: this function is very slow and should only be used for
       debugging.
    """
    if not is_group(root):
        return True
    if len(root.childs) > nmax:
        return False
    return is_list_efficient(root.childs)


def is_group(element):
    return element.is_group


def is_elementlist(l):
    """Returns True if *l* is a list of Elements.
    """
    if not type(l) in (tuple, list):
        print "not a list or tuple", type(l), l.__class__ # XXX remove this
        return False
    return not False in [isinstance(x, Texel) for x in l]


def maxdepth(l):
    """Computes the maximal depth of all elements in list *l*.
    """
    m = [depth(x) for x in l if length(x)]
    if not m:
        return 0
    return max(m)


def mindepth(l):
    """Computes the minimal depth of all elements in list *l*.
    """
    m = [depth(x) for x in l if length(x)]
    if not m:
        return 0
    return min(m)


def out(*args):
    print repr(args)[1:-1]
    return True


def dump(texel, i=0):
    print (" "*i)+str(texel.__class__.__name__), texel.weights,
    if texel.is_text:
        print repr(texel.text), texel.style
    elif isinstance(texel, NewLine):
        print texel.parstyle
    else:
        print
    if texel.is_group or texel.is_container:
        for i1, i2, child in iter_childs(texel):
            dump(child, i+2)
    return True


def dump_list(l):
    print "Dumping list (efficient: %s)" % is_list_efficient(l)
    for i, element in enumerate(l):
        print "Dumping element no. %i" % i,
        print "(efficient: %s)" % is_efficient(element)
        dump(element)
    return True


# ---- Testing ----

if debug: # enable contract checking
     import contract
     contract.checkmod(__name__)


def test_00():
    "insert"
    set_nmax(4)
    s = G([T('1'), T('2'), T('3')])
    element = G([s, s, s])

    tmp = grouped(insert(element, 3, [T('X'), T('Y')]))
    assert depth(tmp) == depth(element)
    assert get_pieces(tmp) == ['1', '2', '3X', 'Y', '1', '2', '3', '1', '2', '3']

    tmp = insert(element, 3, [G([T('X'), T('Y')])])
    assert depth(grouped(tmp)) == depth(element)
    assert get_pieces(tmp) == ['1', '2', '3X', 'Y', '1', '2', '3', '1', '2', '3']


def test_01():
    "growth in insert"
    set_nmax(3)
    g = Group([T("a"), T("b"), T("c")])
    assert depth(g) == 1
    assert get_pieces(g) == ['a', 'b', 'c']
    n = grouped(insert(g, 0, [T("d")]))
    assert get_pieces(n) == ['da', 'b', 'c']


def test_02():
    "maintaining tree efficency in insert / takeout"
    set_nmax(3)
    texel = Group([])
    import random
    for i in range(100):
        x = random.choice("abcdefghijklmnopqrstuvwxyz")
        tmp = insert(texel, i, [Text(x)])
        assert is_list_efficient(tmp)
        texel = grouped(tmp)
    assert is_root_efficient(texel)
    #dump(texel)

    while length(texel):
        i1 = random.randrange(length(texel)+1)
        i2 = random.randrange(length(texel)+1)
        i1, i2 = sorted([i1, i2])
        r, k = takeout(texel, i1, i2)
        assert is_list_efficient(r)
        texel = grouped(r)
    assert is_root_efficient(texel)


def test_03():
    "depth"
    assert depth(Text('abc')) == 0
    assert depth(G([Text('abc')])) == 1
    assert depth(G([])) == 0
    element = G([G([G([T('1'), T('2')]), G([T('3')])])])
    assert depth(element) == 3


def test_04():
    "fuse"
    l1 = [T("01234")]
    l2 = [T("56789")]
    t = fuse([G(l1)], l2)
    assert get_pieces(t) == ['0123456789']

    t = fuse([G(l1)], [G(l2)])
    assert get_pieces(t) == ['0123456789']

    t = fuse(l1, [G(l2)])
    assert get_pieces(t) == ['0123456789']


def test_05():
    "iter_d0"
    t1 = T("012345678")
    t2 = T("ABC")
    t3 = T("xyz")
    c = Container().set_childs((t2, t3))
    g = G((t1, c))
    #texeltree.dump(g)
    l = []
    for i1, i2, elem in iter_d0(g):
        l.append((i1, i2, elem))
    assert repr(l) == "[(0, 9, T('012345678')), (0, 6, C([T('ABC'), T('xyz')]))]"
    

def test_06():
    "insert in container"
    fraction = Fraction(T("Sin(alpha)"), T("Cos(alpha)"))
    t = T("X") #, dict(color='red'))
    l = insert(fraction, 0, [t])
    assert get_pieces(grouped(l)) == ['X', ' ', 'Sin(alpha)', ' ', 'Cos(alpha)', ' ']
    l = insert(fraction, 1, [t])
    assert get_pieces(grouped(l)) == [' ', 'XSin(alpha)', ' ', 'Cos(alpha)', ' ']
    l = insert(fraction, 2, [t])
    assert get_pieces(grouped(l)) == [' ', 'SXin(alpha)', ' ', 'Cos(alpha)', ' ']
    l = insert(fraction, 11, [t])
    assert get_pieces(grouped(l)) == [' ', 'Sin(alpha)X', ' ', 'Cos(alpha)', ' ']
    l = insert(fraction, 12, [t])
    assert get_pieces(grouped(l)) == [' ', 'Sin(alpha)', ' ', 'XCos(alpha)', ' ']
    l = insert(fraction, 22, [t])
    assert get_pieces(grouped(l)) == [' ', 'Sin(alpha)', ' ', 'Cos(alpha)X', ' ']
    l = insert(fraction, 23, [t])
    assert get_pieces(grouped(l)) == [' ', 'Sin(alpha)', ' ', 'Cos(alpha)', ' ', 'X']

    elem = fraction
    text = "0123456789"
    for i in range(len(text)):
        tmp = insert(elem, 12, [T(text[i])])
        elem = grouped(tmp)
    assert get_pieces(elem) == [' ', 'Sin(alpha)', ' ', '9876543210Cos(alpha)', ' ']

    fraction = Fraction(T(""), T("Cos(alpha)"))
    l = insert(fraction, 0, [t])
    assert get_pieces(grouped(l)) == ['X', ' ', '', ' ', 'Cos(alpha)', ' ']

    l = insert(fraction, 1, [t])
    assert get_pieces(grouped(l)) == [' ', 'X', ' ', 'Cos(alpha)', ' ']

    l = insert(fraction, 2, [t])
    assert get_pieces(grouped(l)) == [' ', '', ' ', 'XCos(alpha)', ' ']


def test_07():
    "compute_hull"
    fraction = Fraction(T("Sin(alpha)"), T("Cos(alpha)"))
    n = length(fraction)
    assert compute_hull(fraction, 0, 1) == (0, n)
    assert compute_hull(fraction, 1, 2) == (1, 2)
    assert compute_hull(fraction, 2, 3) == (2, 3)
    assert compute_hull(fraction, 9, 11) == (9, 11)
    assert compute_hull(fraction, 11, 12) == (0, n)
    assert compute_hull(fraction, n-2, n-1) == (n-2, n-1)
    assert compute_hull(fraction, n-1, n) == (0, n)


def test_08():
    "pickle"
    s1 = as_style(dict(color='red'))
    s2 = as_style(dict(color='blue'))
    t1 = T("012345678", style=s1)
    t2 = T("ABC", style=s2)
    g = G((t1, t2))
    from cPickle import dumps, loads 
    t1_ = loads(dumps(t1))
    assert t1.style is t1_.style
    assert t1.text == t1_.text    
    g_ = loads(dumps(g))
    t1_, t2_ = g_.childs
    assert not t1_ is t1
    assert not t2_ is t2
    assert t1.style is t1_.style
    assert t2.style is t2_.style
    assert t1.text == t1_.text    
    assert t2.text == t2_.text    
    
