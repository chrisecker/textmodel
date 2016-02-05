# -*- coding: latin-1 -*-

from .testdevice import TESTDEVICE
from .boxes import TabulatorBox, TextBox, EmptyTextBox, NewlineBox, Row


def find_bestbreak(box, w):
    if not isinstance(box, TextBox):
        return 0
    text = box.text
    parts = box.measure_parts(text)

    # 1. try to break after a space
    for i, part in reversed(tuple(enumerate(parts))):
        if i>0 and part <= w and text[i] == ' ':
            return i+1

    # 2. brute force break
    for i, part in enumerate(parts):
        if part > w:
            return i
    return 0


def split_box(box, i):
    if not isinstance(box, TextBox):
        assert i == 0
        return EmptyTextBox(), box
    text = box.text
    style = box.style
    device = box.device
    b1 = box.__class__(text[:i], style, device)
    b2 = box.__class__(text[i:], style, device)
    return b1, b2


def simple_linewrap(boxes, maxw, tabstops=(), device=TESTDEVICE):
    assert isinstance(maxw, int)
    l = []
    rows = [l]
    w = 0
        
    boxes = list(boxes[:])
    last = None
    while boxes:
        box = boxes[0]
        boxes = boxes[1:]
        if not len(box):
            continue
        if w+box.width <= maxw:
            l.append(box)
            w += box.width
            if isinstance(box, TextBox) and ' ' in box.text:
                i = box.text.rindex(' ')+1
                last = len(l)-1, i
            continue
        # too wide -> break somewhere and start a new line
        if last:
            k, i = last
            lastbox = l[k]
            a, b = split_box(lastbox, i)
            assert len(a)+len(b) == len(lastbox)
            boxes = [b]+l[k+1:]+[box]+boxes
            del l[k:]            
            l.append(a)
        else:
            i = find_bestbreak(box, maxw-w)
            if i == 0:
                if l: # create new line
                    boxes = [box]+boxes
                else:
                    l.append(box)
            else:
                a, b = split_box(box, i)
                l.append(a)
                boxes = [b]+boxes
        w = 0
        l = []
        rows.append(l)
        last = None
    if not rows[-1]:
        rows = rows[:-1]
    return [Row(l, device) for l in rows]


def test_00():
    "find_bestbreak"
    box = TextBox("123 567 90")
    assert find_bestbreak(box, 3) == 3
    assert find_bestbreak(box, 4) == 4
    assert find_bestbreak(box, 5) == 4
    assert find_bestbreak(box, 6) == 4
    assert find_bestbreak(box, 7) == 4
    assert find_bestbreak(box, 8) == 8
    assert find_bestbreak(box, 9) == 8
    assert find_bestbreak(box, 10) == 8
    assert find_bestbreak(box, 11) == 8 # XXX Hmm?


def test_01():
    boxes = []
    for text in "aa bb cc dd ee".split():
        boxes.append(TextBox(text))
        if text == 'dd':
            boxes.append(NewlineBox())
    
    assert str(simple_linewrap(boxes, 5)) == \
        "[Row[TB('aa'), TB('bb'), TB('c')], Row[TB('c'), TB('dd'), NL, "\
        "TB('ee')]]"
