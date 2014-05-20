# -*- coding: latin-1 -*-

# Nützliche Funktionen, die es erlauben mit listen die Funktion von
# intmaps zu emulieren.
#


# Ein wenig zur Mathematik von Intervallen
#
# [i1, i2]
# [j1, j2]
#
# Kein Überlapp:
#   i2 <= j1 oder j2 <= i1
#
# i liegt in j:
#   j1 <= i1 und j2 >= i2
#
# j liegt in i:
#   i1 <= j1 und i2 >= j2
#
# i und j haben eine nichtleere Schnittmenge:
#   i1 < j2 und j1 < i2
#
#
# Überlapp:
#    [max(i1, j1), min(i2, j2)]
#
# Größe des Überlapps:
#    min(i2, j2) - max(i1, j1)


def calc_length(l):
    r = 0
    for item in l:
        r += len(item)
    return r


def iter(l):
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
        if i1 < j2 and j1 < i2: # bei nichtleerer Schnittmenge ...
            r.append((j1, j2, item))
        j1 = j2
    return tuple(r)


def get_envelope(l, i1, i2):
    if len(l) == 0:
        return i1, i2 # XXX sollte i1, i2 auf den existierenden
                      # Bereich eingeschränkt werden?
    if i1 == i2:
        return get_interval(l, i1)
    if not i2 >= i1:
        raise ValueError, "i2 must be >= i1"
    j1 = 0
    k1 = k2 = None
    for item in l:
        j2 = j1+len(item)
        if i1 < j2 and j1 < i2: # bei nichtleerer Schnittmenge ...
            if k1 is None:
                k1 = j1
                k2 = j2
            else:
                k2 = j2
        j1 = j2
    return k1, k2


def get_item(l, i):
    # Gibt das Element zurück, das die Position i enthält. Wenn i an
    # einer Grenze liegt, dann wird das rechte Element
    # zurückgeliefert.
    j1 = 0
    k1 = k2 = None
    items = []
    for item in l:
        j2 = j1+len(item)
        if i < j2 and j1 <= i: # bei nichtleerer Schnittmenge ...
            return j1, j2, item
        j1 = j2


def get_interval(l, i):
    # Gibt das Element zurück, das die Position i enthält. Wenn i an
    # einer Grenze liegt, dann wird das rechte Element
    # zurückgeliefert. Achtung: die rechte Kante gehört dazu! Das
    # erlaubt es, "Anfügen" als "Ersetzen" zu beschreiben. 

    j1 = 0
    k1 = k2 = None
    items = []
    for item in l:
        j2 = j1+len(item)
        if i < j2 and j1 <= i: # bei nichtleerer Schnittmenge ...
            return j1, j2
        j1 = j2
    return j1, j1


def get_items(l, i1, i2):
    if not i2>i1:
        raise ValueError, "i2 must be larger i1"
    j1 = 0
    k1 = k2 = None
    items = []
    for item in l:
        j2 = j1+len(item)
        if i1 < j2 and j1 < i2: # bei nichtleerer Schnittmenge ...
            items.append(item)
            if k1 is None:
                k1 = j1
                k2 = j2
            else:
                k2 = j2
        j1 = j2
    return k1, k2, items

                                
def replace(l, i1, i2, new):
    # Achtung: das intervall kann auch leer sein!
    # -> replace(l, i1, i1, new) fügt an die Stelle i1 ein
    # -> replace(l, length, length, new) fügt an
    # -> replace(l, i1, i2, []) löscht von i1 bis i2
    r1 = []
    r2 = []
    j1 = 0
    for item in l:
        j2 = j1+len(item)
        #print j1, j2, repr(item)
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
    assert replace(['012345', '678', '9012345'], 6, 9, []) == ('012345', '9012345')

    # Das Target von replace kann auch die Breite 0 haben:
    assert replace(['012345', '678', '9012345'], 7, 7, []) == ('012345', '9012345')


def test_02():
    assert intersecting_items(['012345', '678', '9012345'], 8, 9) == ((6, 9, '678'),)
    assert intersecting_items(['012345', '678', '9012345'], 8, 10) == \
        ((6, 9, '678'), (9, 16, '9012345'),)

if __name__=='__main__':
    import alltests
    alltests.dotests()
