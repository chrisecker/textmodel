# -*- coding: latin-1 -*-


from .texeltree import length, provides_childs, iter_childs, Texel


debug = 1


class NotFound(Exception): 
    pass


# NOTE: The following helper functions for searching indices only
# work with certain weight functions. They will work for weights
# aggregated by 'sum', such as lengths and line numbers. But trying to
# find depth values will lead to unexpected and unpredicted behaviour.

def find_weight(texel, w, windex):
    """Returns position *i* at which weight *windex* switches to value *w*."""
    assert type(w) is int
    if w == 0:
        return 0
    if provides_childs(texel):
        sum_w = 0
        for i1, i2, child in iter_childs(texel):
            delta = child.weights[windex]
            if sum_w+delta >= w:
                return find_weight(child, w-sum_w, windex)+i1
            sum_w += delta
    if w == texel.weights[windex]:
        return length(texel)
    raise NotFound(w)


def next_change(texel, windex, i):
    """Returns the next position from *i* at which weight *windex* changes."""
    if provides_childs(texel):
        for j1, j2, child in iter_childs(texel):
            if i1 < j2 and j1 < i2: # intersection
                n = next_change(texel, windex, i-j1)
                if n is not None:
                    return n+j1
    if texel.weights[windex]:
        return 0


def get_weight(texel, windex, i): 
    """Returns the weight *windex* at index *i*.
       pre:
         isinstance(texel, Texel)
    """
    if i<0:
        raise IndexError
    if i >= length(texel):
        return texel.weights[windex]
    w = 0
    if i == 0:
        return w

    if provides_childs(texel):
        for i1, i2, child in iter_childs(texel):
            if i2 <= i:
                w += child.weights[windex]
            elif i1 <= i <= i2:
                w += get_weight(child, windex, i-i1)
            else:
                break
    return w


if debug: # enable contract checking
     import contract
     contract.checkmod(__name__)
