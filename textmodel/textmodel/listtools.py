# -*- coding: latin-1 -*-

# Some usefull functions to work with lists of objects
#
#
#
# Background: a little math of intervals
#
#   interval i: [i1, i2]
#   interval j: [j1, j2]
#
# No overlap:
#   i2 <= j1 or j2 <= i1
#
# i lies in j:
#   j1 <= i1 and j2 >= i2
#
# j lies in i:
#   i1 <= j1 and i2 >= j2
#
# i and j have a nonempty intersection
#   i1 < j2 and j1 < i2
#
#
# Overlap of i and j:
#    [max(i1, j1), min(i2, j2)]
#
# Size of overlap:
#    min(i2, j2) - max(i1, j1)


def calc_length(l):
    r = 0
    for item in l:
        r += len(item)
    return r


def iter_items(l):
    i1 = 0
    for item in l:
        i2 = i1+len(item)
        yield i1, i2, item
        i1 = i2


def intersecting_items(l, i1, i2):
    if not i2>i1:
        raise ValueError, "i2 must be larger i1"
    r = []
    j1 = 0
    for item in l:
        j2 = j1+len(item)
        if i1 < j2 and j1 < i2:
            r.append((j1, j2, item))
        j1 = j2
    return tuple(r)


def get_envelope(l, i1, i2):
    if len(l) == 0:
        return i1, i2 # XXX should i1, i2 be reduced to the existing
                      # interval?
    if i1 == i2:
        return get_interval(l, i1)
    if not i2 >= i1:
        raise ValueError("i2 must be >= i1")
    j1 = 0
    k1 = k2 = None
    for item in l:
        j2 = j1+len(item)
        if i1 < j2 and j1 < i2:
            if k1 is None:
                k1 = j1
                k2 = j2
            else:
                k2 = j2
        j1 = j2
    return k1, k2


def get_item(l, i):
    # Return element containing position i. If i is at a border
    # between to elements, return the element on the right.
    j1 = 0
    k1 = k2 = None
    items = []
    for item in l:
        j2 = j1+len(item)
        if i < j2 and j1 <= i: # nonempty intersection
            return j1, j2, item
        j1 = j2


def get_interval(l, i):
    # Returns interval of the elemnt holding position i. If i is at
    # the border between two elements, the right one os returner.

    j1 = 0
    k1 = k2 = None
    items = []
    for item in l:
        j2 = j1+len(item)
        if i < j2 and j1 <= i:
            return j1, j2
        j1 = j2
    return j1, j1


def get_items(l, i1, i2):
    if not i2>i1:
        raise ValueError("i2 must be larger i1")
    j1 = 0
    k1 = k2 = None
    items = []
    for item in l:
        j2 = j1+len(item)
        if i1 < j2 and j1 < i2:
            items.append(item)
            if k1 is None:
                k1 = j1
                k2 = j2
            else:
                k2 = j2
        j1 = j2
    return k1, k2, items


def replace(l, i1, i2, new):
    # Replace all elements between i1 and i2 with the elements in list
    # "new".
    #
    # -> replace(l, i1, i1, new) inserts at position i1
    # -> replace(l, length, length, new) appends
    # -> replace(l, i1, i2, []) removes from i1 to i2
    r1 = []
    r2 = []
    j1 = 0
    for item in l:
        j2 = j1+len(item)
        if j2 <= i1:
            r1.append(item)
        elif j1 >= i2:
            r2.append(item)
        j1 = j2
    return tuple(r1+list(new)+r2)


def listjoin(a, b, fun):
    if not len(a):
        return b
    if not len(b):
        return a
    return a[:-1]+fun(a[-1], b[0])+b[1:]




def test_00():
    assert get_envelope(['012345', '678', '9012345'], 6, 10) == (6, 16)
    assert get_envelope(['012345', '678', '9012345'], 6, 7) == (6, 9)


def test_01():
    assert replace(['012345', '678', '9012345'], 6, 9, []) == \
        ('012345', '9012345')

    assert replace(['012345', '678', '9012345'], 7, 7, []) == \
        ('012345', '9012345')


def test_02():
    assert intersecting_items(['012345', '678', '9012345'], 8, 9) == \
        ((6, 9, '678'),)
    assert intersecting_items(['012345', '678', '9012345'], 8, 10) == \
        ((6, 9, '678'), (9, 16, '9012345'),)
