# -*- coding: latin-1 -*-

"""This demo shows how to work directly with the texeltree. 
"""
import sys
sys.path.insert(0, "../")
from textmodel.texeltree import Group, Characters, G, C

# Am effizientesten wäre wohl, eine Finite State Machine durch die
# Hierarchie zu reichen.
#

        


def matches(texel, i, text):
    assert i>=0
    if isinstance(texel, Characters):
        print texel.text[i:], text[i:i+len(texel)],
        print texel.text[i:].startswith(text[i:i+len(texel)])
        return texel.text[i:].startswith(text[i:i+len(texel)])
    for i1, i2, child in texel.iter_childs():
        if i1<=i<i2:            
            if not matches(child, i-i1, text):
                return False
        elif i1<=i+len(text)<=i2:
            assert i<i1
            if not matches(child, 0, text[i1-i]):
                return False


def search(texel, text):
    """Simple text search. Can't handle containers. Returns -1 (not found)
or position of text.""" 
    if isinstance(texel, Characters):
        i = texel.text.find(text)
        return i
    for i1, i2, child in texel.iter_childs():
        i = search(child, text[:i2])
        if i == -1:
            return -1
        return i+i1


def get_char(texel, i):
    if isinstance(texel, Characters):
        return texel.text[i:i+1]
    for i1, i2, child in texel.iter_childs():
        if i1<=i<i2:
            return get_char(child, i-i1)
    
def search_charwise(texel, text):
    # Search character by character. Very slow.
    for i in range(len(texel)-len(text)):
        found = True
        for j in range(len(text)):
            if get_char(texel, i+j) != text[j]:
                found = False
                break
        if found:
            return i


class Matcher:
    fun = staticmethod(lambda x: x)
    state = 0
    def __init__(self, pattern, ignorecase):
        if ignorecase:
            pattern = pattern.upper()
            self.fun = lambda x: x.upper()
        self.pattern = pattern

    def match(self, text):
        j = self.state
        n = min(len(text), len(self.pattern)-j)
        if self.pattern[j:j+n] == self.fun(text[:n]):
            self.state += n
            return True
        return False

    def search(self, text):
        # simpler and slower version"
        for i in range(len(text)):
            self.state = 0
            if self.match(text[i:]):
                return i
        raise NotFound

    def finished(self):
        return self.state >= len(self.pattern)


class NotFound(Exception): pass

def _search_matcher(texel, i, matcher):
    "returns index position of substring; raises exception otherwise"
    if isinstance(texel, Characters):
        assert i>=0
        if matcher.state == 0:
            return matcher.search(texel.text)            
        if matcher.match(texel.text[i:]):
            return i
        raise NotFound

    for i1, i2, child in texel.iter_childs():
        if i1<=i:
            i = _search_matcher(child, i-i1, matcher)+i1
            if matcher.finished():
                break
    return i

def search_matcher(texel, text, ignorecase=False):
    try:
        return _search_matcher(texel, 0, Matcher(text, ignorecase))
    except NotFound, e:
        pass

# construct a weird tree to make this demo more interesting
tree = G([C("Hello"), G([C("wor"), C("ld")])])

if 0:
    print search_charwise(tree, "ell")
    print search_charwise(tree, "low")

    print search(tree, "ell")
    print search(tree, "low")
    print matches(tree, 3, "low")

if 1:
    assert search_matcher(tree, "ell") == 1
    assert search_matcher(tree, "low") == 3
    assert search_matcher(tree, "elx") is None
    assert search_matcher(tree, "ElL", ignorecase=True) == 1
    assert search_matcher(tree, "ElL", ignorecase=False) is None

if 0:
    print _search_matcher(C("Hello"), 1, Matcher("ell"))
    print _search_matcher(G([C("Hello")]), 1, Matcher("ell"))
