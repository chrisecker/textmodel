# -*- coding: latin-1 -*-



"""treebase.py -- basic hierarchical data structure

This file defines a hierarchical data structure consisting of
elements. A special element is the group element, which can hold child
elements.

Elements have a certain length, a depth and a weights as defined below.

Technically, elements span a tree with groups as branches. Unlike
binary trees, groups can have more than two childs. Ideally groups
have between nmax/2 and nmax childs. If this condition is fulfilled
for all groups in the tree, the tree is said to be efficient.

With nmax = 15, one tree of depth 5 can carry up to 759,375 leave
elements, which is be more than enough for our purpose.

"""

from .listtools import calc_length
from . import listtools

debug = 0 # don't check
#debug = 1 # check
#debug = 2 # also check efficiency

nmax = 15
def set_nmax(i):
    """Sets $nmax$ to the value $i$.

       The value nmax determines the number of childs per group (which
       should be between nmax/2 and nmax for efficient trees).
    """
    global nmax
    nmax = i


def depth(element):
    """Returns the depth of an element.

       The depth can be definied as the number of generations of
       groups. By definition empty groups have depth 0.

       >>> depth(Characters('abc'))
       0

       >>> depth(G(Characters('abc')))
       1

       >>> depth(G()) # empty groups are ignored
       0
    """
    if isinstance(element, Group):
        return element.get_depth()
    return 0


def count(element):
    """Returns the number of elements.

       This function is very slow and is only ment for debugging. 
    """
    n = 1
    for i1, i2, child in element.iter_childs():
        n += count(child)
    return n



def is_homogeneous(l):
    """Returns True if the elements in list *l* are homogeneous.

       Elements are homogeneous if they have alle the same depth.
    """
    return maxdepth(l) == mindepth(l)


def is_element_efficient(element):
    """Returns True if $element$ is efficient.

       An element is efficient, if it is not a group or otherwise if
       all of the following criteria are fulfilled:

       1. if each descendant group has between nmax/2 and nmax childs
       2. the depth of all childs is homogeneous

       In an efficient tree all groups (with the exception of the root
       node) must be element_efficient.

       Note: this function is very slow and should only be used for
       debugging.
    """
    if not isinstance(element, Group):
        return True
    if not is_homogeneous(element.childs):
        return False
    if len(element.childs) < nmax/2 or len(element.childs) > nmax:
        return False
    if not is_list_efficient(element.childs):
        return False
    return True


def is_list_efficient(l):
    """Returns True if the list of $l$ of elements is efficient.
    """
    if not is_homogeneous(l):
        return False
    for element in l:
        if not is_element_efficient(element):
            return False
    return True


def is_root_efficient(root):
    """Returns True if $root$ is efficient.

       The tree spawned by $root$ is efficient if it is either not a
       group or otherwise if it fulfills all of the following
       conditions:

       1. all childs are efficient
       2. the number of childs is <= nmax

       Note: this function is very slow and should only be used for
       debugging.
    """
    if not isinstance(root, Group):
        return True
    if len(root.childs) > nmax:
        return False
    return is_list_efficient(root.childs)


def is_elementlist(l):
    """Returns True if $l$ is a list of Elements.
    """
    if not type(l) in (tuple, list):
        print "not a list or tuple", type(l), l.__class__ # XXX remove this
        return False
    return not False in [isinstance(x, Element) for x in l]


def maxdepth(l):
    """Computes the maximal depth of all elements in list $l$.
    """
    m = [depth(x) for x in l if len(x)]
    if not m:
        return 0
    return max(m)


def mindepth(l):
    """Computes the minimal depth of all elements in list $l$.
    """
    m = [depth(x) for x in l if len(x)]
    if not m:
        return 0
    return min(m)


def strip(element):
    """Removes unnecessary Group-elements from the root.
    """
    n = len(element)
    while isinstance(element, Group) and len(element.childs) == 1:
        element = element.childs[0]
    assert n == len(element)
    return element


def out(*args): # XXX remove this
    print repr(args)
    return True


def dump(element): # XXX remove this
    print "Dump:"
    element.dump()
    return True

def dump_list(l):
    print "Dumping list (efficient: %s)" % is_list_efficient(l)
    for i, element in enumerate(l):
        print "Dumping element no. %i" % i,
        print "(efficient: %s)" % is_element_efficient(element)
        element.dump()
    return True



class Element:
    """Baseclass for all tree elements.

If element is a container, it must provide the "iter_childs" and
"replace_child" methods. Containers are marked by the flag "has_childs"."""
    weights = (0, 0)
    functions = (
        lambda l:max(l)+1, # depth
        sum,               # length
        )

    has_childs = False # if true, childs can be accessed using the
                       # iter_childs method

    def get_depth(self):
        """Returns the depth of $self$."""
        return self.weights[0]

    def __len__(self):
        """Returns the length of $self$ in index units."""
        return self.weights[1]

    def iter_childs(self):
        """Iterates over all child elements.

        Usage:
        for i1, i2, child in element.iter_childs():
            ...
        """
        if 0: yield 0, 0, None

    def replace_child(self, i1, i2, stuff):
        """Replace the direct childs between $i1$ and $i2$ by $stuff$.

        Returns a list of elements. The indices $i1$ and $i2$ must lie
        at boundaries. Replace_Child can be used to insert, replace_child or
        remove child elements.

        element.replace_child(i1, i1, new) -- insert at index i1
        element.replace_child(len(element), len(element), new) -- append
        element.replace_child(i1, i2, []) -- remove everything in i1..i2

        The interval i1..i2 can contain any number of childs (including zero).
        XXX It probably should be renamed in "replace_childs".


        pre:
            is_elementlist(stuff)

        post[]:
            is_elementlist(__return__)
            is_homogeneous(__return__)
            #out(repr(self)[:100])
            #dump(G(__return__))
            calc_length(__return__) == len(self)-(i2-i1)+calc_length(stuff)
        """
        raise NotImplementedError()

    def takeout(self, i1, i2):
        """Takes out all content between $i1$ and $i2$.

        Returns the rest and the cut out piece, i.e.
        G([a, b, c]).takeout(i1, i2) will return G([a, c]), b.

        pre:
            0 <= i1 <= i2 <= len(self)
            is_root_efficient(self)

        post[i1, i2, self]:
            is_elementlist(__return__[0])
            is_elementlist(__return__[1])
            is_homogeneous(__return__[0])
            is_homogeneous(__return__[1])
            calc_length(__return__[0])+i2-i1 == len(self)
            calc_length(__return__[1]) == i2-i1
            is_list_efficient(__return__[0])
            is_list_efficient(__return__[1])
        """
        raise NotImplementedError()

    def can_merge(self, other):
        """Can element $self$ be merged to other?"""
        return False

    def merge(self, other):
        """Merges $self$ and $other$ to into a single element.

        post[self, other]:
            len(__return__) == len(self)+len(other)
        """
        raise Exception()

    def dump(self, i=0):
        """Print out a graphical representation of the tree."""
        print (" "*i)+str(self.__class__.__name__), self.weights
        for i1, i2, child in self.iter_childs():
            child.dump(i+2)

    @staticmethod
    def create_group(l):
        """Creates a group with childs $l$.

        pre:
            is_elementlist(l)
        """
        # should be overriden by derived classes
        return Group(l)



class Group(Element):
    has_childs = True

    def __init__(self, items):
        self.childs = filter(len, items)
        if len(self.childs):            
            self.compute_weights()

    def compute_weights(self):
        w_list = zip(*[child.weights for child in self.childs])
        self.weights = [f(l) for (l, f) in zip(w_list, self.functions)]

    def iter_childs(self):
        i1 = 0
        for child in self.childs:
            i2 = i1+len(child)
            yield i1, i2, child
            i1 = i2

    def replace_child(self, i1, i2, stuff):
        assert 0 <= i1 <= i2 <= len(self)
        stuff = filter(len, stuff) # XXX is necessary. But why do we
                                   # get empty groups?
        r1 = []
        r2 = []
        j1 = 0
        for item in self.childs:
            j2 = j1+len(item)
            if j2 <= i1:
                r1.append(item)
            elif j1 >= i2:
                r2.append(item)
            elif i1 <= j1 <= j2 <= i2:
                # Item is beeing replaced
                pass
            else:
                # Item overlaps i1, i2. This is not allowed!
                raise IndexError((i1, i2))
            j1 = j2
        # XXX TODO: remove debug code
        tmp = groups(join(r1, stuff, r2))
        try:
            assert calc_length(tmp) == len(self)+calc_length(stuff)-(i2-i1)
        except:
            dump(self)
            print i1, i2
            dump(G(stuff))
            dump(G(tmp))
            raise
        return tmp

    def takeout(self, i1, i2):
        # Preconditions don't seem to be evaluated. Therefore we use
        # an additional assertion here.
        if debug > 1: # XXX remove this
            if not is_root_efficient(self):
                dump(self)
                print "nmax=", nmax
            assert is_root_efficient(self)

        if not (0 <= i1 <= i2 <= len(self)):
            raise IndexError([i1, i2])
        r1 = []; r2 = []; r3 = []; r4 = []
        k1 = []; k2 = []; k3 = []
        for j1, j2, child in self.iter_childs():
            if j2 <= i1:
                r1.append(child)
            elif i1 <= j1 <= j2 <= i2:
                k2.append(child)
            elif j1 <= i1 <= j2:
                r, k = child.takeout(max(i1-j1, 0), min(i2-j1, len(child)))
                r2.extend(r)
                k1.extend(k)
            elif j1 <= i2 <= j2:
                r, k = child.takeout(max(i1-j2, 0), min(i2-j1, len(child)))
                r3.extend(r)
                k3.extend(k)
            elif i2 <= j1:
                r4.append(child)
        # Note that we are returning a list of elements which have
        # been in the content before. Therefore, we are decreasing the
        # depth by 1 (or more). This is the reason why the returned
        # lists are list_efficient. The correctness of the approach
        # can be seen from full induction.
        return join(r1, r2, r3, r4), join(k1, k2, k3)

    def __repr__(self):
        return 'G(%s)' % repr(list(self.childs))
G = Group



def homogenize(stuff):
    """Transforms $stuff$ into a homogeneous list of elements.

       The depth of the returned elements equals to the maxmimum depth
       in $stuff$.

       pre:
           is_elementlist(stuff)

       post[]:
           maxdepth(__return__) == mindepth(__return__)
    """
    l = []
    ll = [l]
    stuff = list(stuff[:])
    d = None
    while len(stuff):
        element = stuff[0]
        delement = depth(element)
        if delement == d or not l:
            l.append(element)
        else:
            l = [element]
            ll.append(l)
        d = delement
        stuff = stuff[1:]
    return join(*ll)



def simple_insert(element, i, stuff):
    """Inserts $stuff$ in $element$ at position $i$.

       All elements in stuff must have zero depth. This restriction makes
       it simpler and faster compared to the general insert-function.

       Returns a list of texels.

       pre:
           is_elementlist(stuff)

       post[stuff, element]:
           calc_length(__return__) == calc_length(stuff)+len(element)
    """
    assert type(stuff) is list
    if maxdepth(stuff) > 0:
        raise Exception("maxdepth(stuff) must be 0 for simple_insert")

    for i1, i2, child in element.iter_childs():
        if i1 <= i <= i2:
            new = simple_insert(child, i-i1, stuff)
            return element.replace_child(i1, i2, new)
    return element.replace_child(i, i, stuff)


def _join(l1, l2):
    """
    Joins the lists of elements $l1$ and $l2$.

    Given that l1 and l2 are each homogeneous then also the returned
    list is homogeneous. No healing is performed.

    pre:
        is_elementlist(l1)
        is_elementlist(l2)
        is_homogeneous(l1)
        is_homogeneous(l2)

    post[l1, l2]:
        is_homogeneous(__return__)
        calc_length(l1)+calc_length(l2) == calc_length(__return__)
        maxdepth(__return__) == max(maxdepth(l1), maxdepth(l2))
    """
    l1 = filter(len, l1) # strip off empty elements
    l2 = filter(len, l2) #
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
           forall(args, is_homogeneous)

       post[args]:
           is_homogeneous(__return__)
           sum([calc_length(x) for x in args]) == calc_length(__return__)
           #out("join check: ok")
    """
    return reduce(_join, args)


def insert(element, i, stuff):
    """Inserts the list $stuff$ at position $i$.

       Returns a list of elements. Unlike simple_insert, stuff can
       contain elements with depth>0.  Note that insert can increase
       the elements depth. The returned list is always homogeneous.

       pre:
           isinstance(element, Element)
           is_elementlist(stuff)
           is_homogeneous(stuff)

       post[element, stuff]:
           calc_length(__return__) == len(element)+calc_length(stuff)
           is_homogeneous(__return__)

    """
    if element.has_childs:
        k = -1
        for i1, i2, child in element.iter_childs():
            k += 1
            if i1 <= i <= i2:
                new = insert(child, i-i1, stuff)
                return element.replace_child(i1, i2, new)
    return join(copy(element, 0, i), stuff, copy(element, i, len(element)))



def groups(l):
    """Transform the list of texels $l$ into a list of groups.

       If texels have depth d, groups will have depth d+1.

       pre:
           is_elementlist(l)
           is_homogeneous(l)

       post[l]:
           is_homogeneous(__return__)
           calc_length(l) == calc_length(__return__)
           #out("groups check: ok")
    """
    r = []
    N = len(l)
    if N == 0:
        return r
    Group = l[0].create_group

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


def remove(root, i1, i2):
    """Removes all content of $root$ between $i1$ and $i2$.

       pre:
           isinstance(root, Element)

       post[root, i1, i2]:
           calc_length(__return__) == len(root)-(i2-i1)
    """
    return root.takeout(i1, i2)[0]


def copy(root, i1, i2):
    """Copy all content of $root$ between $i1$ and $i2$.

       pre:
           isinstance(root, Element)

       post[i1, i2]:
           calc_length(__return__) == (i2-i1)
    """
    return root.takeout(i1, i2)[1]


def ungroup(element):
    """Recursively removes all groups. Returns a list of texels.

       pre:
           isinstance(element, Element)

       post[element]:
           calc_length(__return__) == len(element)
           maxdepth(__return__) == 0
    """
    if isinstance(element, Group):
        l = []
        for child in element.childs:
            l.extend(ungroup(child))
        return l
    return [element]


def grouped(stuff):
    """Creates a single group from the list of elements $stuff$.

       If the number of elements exceeds nmax, subgroups are formed.
       Therefore, the depth can increase. Note that stuff is not
       allowed to be empty.

       pre:
           is_elementlist(stuff)
           is_homogeneous(stuff)
           len(stuff) > 0

       post[stuff]:
           len(__return__) == calc_length(stuff)
    """
    n = listtools.calc_length(stuff)
    while len(stuff) > nmax:
        stuff = groups(stuff)
    g = stuff[0].create_group(stuff)
    return strip(g)

def _grouped(stuff):
    # For testing only.
    if not stuff:
        return Group([])
    return grouped(stuff)


def get_rightmost(element):
    """Returns the rightmost subelement of $element$."""
    if isinstance(element, Group):
        return get_rightmost(element.childs[-1])
    return element


def get_leftmost(element):
    """Returns the leftmost subelement of $element$."""
    if isinstance(element, Group):
        return get_leftmost(element.childs[0])
    return element


def exchange_rightmost(element, new):
    """Replace the rightmost subelement of $element$ by $new$."""
    if isinstance(element, Group):
        l = exchange_rightmost(element.childs[-1], new)
        return element.create_group(element.childs[:-1]+[l])
    return new


def exchange_leftmost(element, new):
    """Replace the lefttmost subelement of $element$ by $new$."""
    if isinstance(element, Group):
        l = exchange_leftmost(element.childs[0], new)
        return element.create_group([l]+element.childs[1:])
    return new


def remove_leftmost(element):
    """Removes the leftmost subelement of $element$.

       Note that this function can return an empty group.
    """
    if isinstance(element, Group):
        l = remove_leftmost(element.childs[0])
        return element.create_group([l]+element.childs[1:])
    return element.create_group([])



def _heal(element, i):
    """Recursively heal $element$ at position $i$.

       Algorithm:
       . iterate until i is at the edge of an element
       . find the leftmost and rightmost elements
       . if both can be merged, replace the left one by the merged pair
         and replace remove the right one

       pre:
           isinstance(element, Element)

       post[element]:
           calc_length(__return__) == len(element)
           extract_text(__return__) == extract_text(element)
    """
    n = len(element)
    if not element.has_childs:
        return [element]
    last_child = None
    l1 = None # indices of last texel
    l2 = None # 
    for i1, i2, child in element.iter_childs():
        if i1 == i and last_child is not None and i1 == l2:
            left = get_rightmost(last_child)
            right = get_leftmost(child)
            if left.can_merge(right):
                new = left.merge(right)
                l = [exchange_rightmost(last_child, new),
                     remove_leftmost(child)]
                return element.replace_child(l1, i2, l)

        elif i1 < i < i2:
            return element.replace_child(i1, i2, _heal(child, i-i1))
        last_child = child
        l1 = i1
        l2 = i2
    return [element]


def heal(element, *indices):
    """Heal element at the positions $indices$.

       pre:
           isinstance(element, Element)

       post[element]:
           len(__return__) == len(element)
           extract_text(__return__) == extract_text(element)
           depth(__return__) <= depth(element)
    """
    if not len(element): # necessary because grouped() can't handle empty
                         # elements
        return element
    n = len(element)
    for i in indices:
        element = grouped(_heal(element, i))
    return element


class Text(Element):
    # An element which holds string data (for testing)
    def __init__(self, text):
        self.text = text
        self.weights = (0, len(text))

    def can_merge(self, other):
        return isinstance(other, Text)

    def merge(self, other):
        return Text(self.text+other.text)

    def replace_child(self, i1, i2, stuff):
        r1 = Text(self.text[:i1])
        r2 = Text(self.text[i2:])
        l = []
        if len(r1):
            l.append(r1)
        l = join(l, stuff)
        if len(r2):
            l = join(l, [r2])
        return l

    def takeout(self, i1, i2):
        i1 = max(0, i1)
        i2 = min(len(self), i2)
        r1 = self.text[:i1]
        r2 = self.text[i2:]
        r3 = self.text[i1:i2]
        return [Text(r1+r2)], [Text(r3)]

    def __repr__(self):
        return "T(%s)" % repr(self.text)

    def dump(self, n=0):
        print (" "*n)+str(self), self.weights
T = Text


class TextNoMerge(Text):
    # Another class for testing.
    def can_merge(self, other):
        return False


def extract_text(element):
    # for testing
    if type(element) in (list, tuple):
        return u''.join([extract_text(x) for x in element])
    elif isinstance(element, Text):
        return element.text
    else:
        return u''.join([extract_text(x) for i1, i2, x in \
                         element.iter_childs()])
    return u''


if debug:
     #enable contract checking
     import contract
     contract.checkmod(__name__)
     print "enabled contracts"

def test_00():
    "homogenize"
    global debug
    debug = True
    assert str(homogenize([G([T('X')]), T('0'), T('1')])) == \
        "[G([T('X'), T('0'), T('1')])]"


def test_01():
    "is_homogeneous"
    assert not is_homogeneous([G([T('X')]), T('0'), T('1')])
    for x in G([T('X')]), G([T('0'), T('1')]):
        print depth(x), x
    assert is_homogeneous([G([T('X')]), G([T('0'), T('1')])])


def test_02():
    "strip"
    element = G([G([G([T('1'), T('2')]), G([T('3')])])])
    element.dump()
    print depth(element)
    assert depth(element) == 3
    assert depth(strip(element)) == 2
    #strip(element).dump()


def test_03():
    "is_root_efficient"
    assert is_root_efficient(G([T('1')]))
    assert not is_root_efficient(G([G([T('1')])]))
    set_nmax(3)
    assert is_root_efficient(G([T('1'), T('2'), T('3')]))
    set_nmax(2)
    #G([T('1'), T('2'), T('3')]).dump()
    assert not is_root_efficient(G([T('1'), T('2'), T('3')]))

def test_04():
    "insert"
    set_nmax(4)
    s = G([T('1'), T('2'), T('3')])
    element = G([s, s, s])

    tmp = insert(element, 3, [T('X'), T('Y')])
    assert depth(grouped(tmp)) == depth(element)
    assert extract_text(tmp) == '123XY123123'

    tmp = insert(element, 3, [G([T('X'), T('Y')])])
    assert depth(grouped(tmp)) == depth(element)
    assert extract_text(tmp) == '123XY123123'

    tmp = insert(grouped(tmp), 3, [G([T('Z'), T('#')])])
    assert extract_text(tmp) == '123Z#XY123123'


def test_05():
    "growth in insert"
    set_nmax(3)
    g = Group([Text("a"), Text("b"), Text("c")])
    assert depth(g) == 1
    assert repr(insert(g, 0, [Text("d")])) == \
        "[G([T('d'), T('a')]), G([T('b'), T('c')])]"


def test_06():
    "efficient insert / takeout"
    set_nmax(3)
    texel = Group([])
    import random
    for i in range(100):
        x = random.choice("abcdefghijklmnopqrstuvwxyz")
        tmp = insert(texel, i, [TextNoMerge(x)])
        assert is_list_efficient(tmp)
        texel = _grouped(tmp)
    assert is_root_efficient(texel)

    while len(texel):
        i1 = random.randrange(len(texel)+1)
        i2 = random.randrange(len(texel)+1)
        i1, i2 = sorted([i1, i2])
        r, k = texel.takeout(i1, i2)
        assert is_list_efficient(r)
        texel = _grouped(r)
    assert is_root_efficient(texel)


def test_07():
    "depth"
    assert depth(Text('abc')) == 0
    assert depth(G([Text('abc')])) == 1
    assert depth(G([])) == 0
    element = G([G([G([T('1'), T('2')]), G([T('3')])])])
    assert depth(element) == 3


# XXX TODO: add more tests

