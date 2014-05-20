# -*- coding: latin-1 -*-


"""Python Notebook Demo
~~~~~~~~~~~~~~~~~~~~

The notebook consists of cells. Input cells can be executed by
moving the cursor in the cell and pressing shift + return.

Output is shown in output cells. Output usually consists of text
printed to stdout or stderr by the python interpreter. To demonstrate
non textual output, we implemented plotting here.

Try to execute the following cells."""

# Konzept für Zellen:
# ~~~~~~~~~~~~~~~~~~~
# Zellen könnten auf zwei verschiedene Arten realisiert werden: durch
# ein Spezielles Glyph, dass den Anfang einer Zelle Markiert oder
# durch einen Tag <cell> ... </cell>.
#
# Hier soll der zweite Ansatz explorativ erprobt werden. Der Nachteil
# ist, dass dafür gesorgt werden muss, dass das Modell "sinnvoll" ist
# und bleibt. Beispielsweise würde es keinen Sinn machen, wenn eine
# Zelle in eine andere eingefügt wird.
#
# Daher wird Paste modifiziert. Wenn das einzufügende Stück eine Liste
# von Zellen (oder eine einzelne) ist, dann wird nur eingefügt, wenn
# der index genau zwischen zwei Zellen steht. Bei anderen
# Indexpositionen wird der Inhalt in einfachere Textelemente (alle
# außer Zellen) umgewandelt.
#
# Ebenso muss darauf geachtet werden, dass beim Einfügen zwischen
# Zellen nichts anderes als Zellen in das Modell eingefügt werden.
#
# Konzept für die grafishe Ausgabe:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# - cell.execute bekommt als Argument das komplette Modell und i1, i2
#
# - cell.execute übergibt an den Interpreter eine Ausgabe Fnuktion (output). 
#
# - Der Interpreter benutzt die Ausgabefunktion um Stdout, Stderr zu
#   schreiben.

import sys
sys.path.insert(0, '..')

from textmodel import listtools, create_style
from textmodel.base import NewLine, Group, Characters, group, defaultstyle, \
    NULL_TEXEL, Glyph
from textmodel.container import Container, EMPTY_NL
from textmodel.textmodel import TextModel
from wxtextview.layout import Box, VBox, Row, Rect, IterBox, check_box
from wxtextview.wxdevice import WxDevice
from wxtextview import layout
from wxtextview import WXTextView as _WXTextView

import traceback
import matplotlib
import matplotlib.pyplot

import wx




class Aborted(Exception):
    pass


class TextBuffer:
    # Simple output for testing
    stdout = stderr = ""
    def __init__(self):
        self.out = []
        self.err = []

    def output(self, arg, iserr=False):
        if isinstance(arg, matplotlib.figure.Figure):
            u = 'Graphics ---'
        else:
            try:
                u = unicode(arg, 'latin-1')
            except:
                u = unicode(arg)
        if iserr:
            l = self.err
        else:
            l = self.out
            
        l.append(u)
        self.stdout = ''.join(self.out)
        self.stderr = ''.join(self.err)


class TexelBuffer:
    def __init__(self, texel, i):
        self.i = i
        self.texel = texel

    def output(self, obj, iserr=False):
        if isinstance(obj, matplotlib.figure.Figure):
            texel = Figure(obj)
        elif isinstance(obj, unicode):
            texel = TextModel(obj).texel
        else:
            texel = TextModel(unicode(obj)).texel
        self.texel = self.texel.insert(self.i, texel)
        self.i += len(texel)
            

class FakeFile:
    def __init__(self, fun):
        self.fun = fun
    def write(self, s):
        self.fun(s)


class SimpleInterpreter:
    break_flag = False
    counter = 0
    def __init__(self, namespace=None):
        if namespace is None:
            namespace = {}
        self.namespace = namespace

    def trace_fun(self, *args):
        if self.break_flag:
            self.break_flag = False
            raise Aborted()

    def execute(self, lines, output):
        self.namespace['output'] = output
        self.counter += 1
        name = 'input[%s]' % self.counter
        bkstdout, bkstderr = sys.stdout, sys.stderr
        stdout = sys.stdout = FakeFile(lambda s:output(s))
        stderr = sys.stderr = FakeFile(lambda s:output(s, iserr=True))
        self.ok = False
        self.expression = False
        try:
            try:
                try:
                    code = compile(lines, name, 'eval')
                    self.expression = True
                except SyntaxError:
                    code = compile(lines, name, 'exec')
                sys.settrace(self.trace_fun)
                ans = eval(code, self.namespace)
                self.namespace['ans'] = ans
                self.ok = True
            except Exception, e:
                self.show_traceback()
                self.namespace['ans'] = None
        finally:
            sys.settrace(None)
            sys.stdout, sys.stderr = bkstdout, bkstderr
        if self.expression and self.ok:
            ans = self.namespace['ans']
            output(ans)
        
    def show_traceback(self):
        type, value, tb = sys.exc_info()
        skip = 1
        entries = traceback.format_tb(tb)[skip:]
        msg = traceback.format_exc().splitlines()[-1]
        tb = ''.join(entries)+msg
        print >>sys.stderr, tb

INTERPRETER = SimpleInterpreter()


def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    model.linelengths = texel.get_linelengths()
    return model


class Cell(Container):
    # Eine Zelle enthält drei Trennzeichen (x) nach dem folgenden
    # Schema: x1234567890x1234567890x
    def __init__(self, input=(), output=(), number = 0):
        self.input = group(input)
        self.output = group(output)
        self.number = number

    def __len__(self):
        return len(self.input)+len(self.output)+3

    def get_childs(self):
        # Wir verwenden hier EMPTY_NL statt EMPTY, um die
        # Spaltennummerierung zurückzusetzen. D.h. nach EMPTY_NL ist
        # die Spaltennummer wieder 0. Das hat z.B. auf die
        # Cursurbewegung Auswirkungen.
        return EMPTY_NL, self.input, EMPTY_NL, \
            self.output, EMPTY_NL

    def from_childs(self, childs):
        return self.__class__(input=childs[1:2], output=childs[3:4], 
                              number = self.number)

    def execute(self):
        buf = TexelBuffer(Group([]), 0)
        INTERPRETER.execute(self.input.get_text(), buf.output)
        number = INTERPRETER.counter
        return self.__class__([self.input], [buf.texel], number)



def extend_range_seperated(self, i1, i2):
    # Extend-Range für seperierte Kindfelder 
    for j1, j2, x, y, child in self.iter(0, 0, 0):
        if not (i1<j2 and j1<i2):
            continue
        if i1 < j1 or i2>j2:
            return min(i1, 0), max(i2, len(self))
        k1, k2 = child.extend_range(i1-j1, i2-j1)
        return min(i1, k1+j1), max(i2, k2+j1)
    return i1, i2


class EntryBox(IterBox):
    # hat am Ende eine Leerstelle: 1235789x
    def __init__(self, boxes, device=None):
        if device is not None:
            self.device = device
        self.content = Row(boxes, device=device)
        self.length = self.content.length+1
        self.height = self.content.height
        self.width = self.content.width

    def iter(self, i, x, y):
        content = self.content
        yield i, i+len(content), x, y, content


promptstyle = create_style(
    textcolor = 'blue',
    weight = 'bold'
    )

sepwidth = 200 # eine große Zahl, die sicher größer als die
                 # Textbreite ist
class CellBox(IterBox):
    # x123456789x123456789x
    # x|--input-||-output-|
    def __init__(self, inboxes, outboxes, number=0, device=None):
        self.number = number
        if device is not None:
            self.device=device
        self.input = EntryBox(inboxes, device)
        self.output = EntryBox(outboxes, device)
        self.length = len(self.input)+len(self.output)+1
        assert self.length == len(self.input)+len(self.output)+1
        self.layout()

    def iter(self, i, x, y):
        input = self.input
        output = self.output
        height = self.height
        j1 = i+1
        j2 = j1+len(input)
        yield j1, j2, x+80, y, input
        j1 = j2
        j2 = j1+len(output)
        y += input.height+input.depth+20
        yield j1, j2, x+80, y, output        

    def layout(self):
        # w und h bestimmen
        dh = h = w = 0
        for j1, j2, x, y, child in self.iter(0, 0, 0):
            w = max(x+child.width, w)
            child_height =  max(20, child.height)
            h = max(y+child_height, h) # XXX Minimale Höhe sollte auf
                                       # depth angerechnet werden!!
            dh = max(y+child_height+child.depth, dh)
        self.width = w
        self.height = h
        self.depth = dh-h

    def __repr__(self):
        return self.__class__.__name__+'(%s, %s)' % \
            (repr(list(self.input.content.childs)), 
             repr(list(self.output.content.childs)))

    def get_index(self, x, y):
        if y<3:
            return 0
        elif y>=self.height-2:
            return len(self)
        return IterBox.get_index(self, x, y)

    def extend_range(self, i1, i2):
        for i in (0, len(self.input), len(self)-1):
            if i1<= i<i2:
                return 0, len(self)
        return extend_range_seperated(self, i1, i2)

    def draw(self, x, y, dc, styler):
        a, b = list(self.iter(0, x, y))
        styler.set_style(promptstyle)
        n = self.number or ''
        dc.DrawText("In[%s]:" % n, x, a[3])
        dc.DrawText("Out[%s]:" % n, x, b[3])
        IterBox.draw(self, x, y, dc, styler)

    def draw_selection(self, i1, i2, x, y, dc):
        if i1<=0 and i2>=self.length:
            self.device.invert_rect(x, y, self.width, self.height, dc)
        else:
            IterBox.draw_selection(self, i1, i2, x, y, dc)

    def responding_child(self, i, x0, y0):
        # Die Indexposition n+1 würde normalerweise durch das Kind
        # verwaltet. Wir geben daher hier bekannt, dass wir uns selber
        # darum kümmern.
        if i == len(self):
            return None, i, x0, y0 # None => kein Kind kümert sich darum
        return IterBox.responding_child(self, i, x0, y0)
 
    def get_cursorrect(self, i, x0, y0, style):
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is not None:
            return child.get_cursorrect(i-j, x1, y1, style)
        return self.get_rect(i, x0, y0)

    def get_rect(self, i, x0, y0):
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is not None:
            return child.get_rect(i-j, x1, y1)
        if i == 0:
            return Rect(x0, y0, sepwidth, y0+2)
        assert i == len(self)
        h = self.height
        return Rect(x0, y0+h, sepwidth, y0+h+2)            


class CellStack(VBox):
    _maxw = 0
    def __init__(self, cells, maxw=0, device=None):
        self._maxw = maxw
        VBox.__init__(self, cells, device)

    ### Methoden für den Updater
    def replace(self, i1, i2, new_cells):
        boxes = self.childs
        j1, j2 = self.get_envelope(i1, i2)
        assert i1 == j1 and i2 == j2 
        cells = listtools.replace(boxes, j1, j2, new_cells)
        return CellStack(cells, self._maxw, self.device)

    def get_envelope(self, i1, i2):        
        j1, j2 = listtools.get_envelope(self.childs, i1, i2)
        if i1 == self.length and self.childs:
            j1 -= len(self.childs[-1])
        return max(0, j1), min(j2, self.length)



class NotFound(Exception): pass

def find_cell(texel, i, i0=0):
    if isinstance(texel, Cell):
        return i0, texel
    elif isinstance(texel, Group):
        for child in texel.data:
            n = len(child)
            if i>=0 and i<n:
                return find_cell(child, i, i0)
            i0 += n
            i -= n
    raise NotFound()


class Figure(Glyph):
    def __init__(self, figure):
        figure.canvas.draw()
        self.data = figure.canvas.tostring_rgb()
        w, h = figure.canvas.get_width_height()
        buf = figure.canvas.tostring_argb()
        image = wx.EmptyImage(w, h)
        image.SetData(self.data)
        self.size = w, h

    def __repr__(self):
        return 'Figure(...)'


class FigureBox(IterBox):
    # Problem: Plots zu erzeugen ist sehr zeitaufwändig. Bisher werden
    # bei jeder Änderung nalle Boxen der kompletten Zelle neu erzeugt.
    def __init__(self, texel, device=None):
        if device is not None:
            self.device = device
        self.length = 1
        w, h = texel.size
        image = wx.EmptyImage(w, h)
        image.SetData(texel.data)
        self.bitmap = wx.BitmapFromImage(image, -1)

        self.width = w
        self.height = h
        self.depth = 0

    def iter(self, i, x, y):
        if 0: yield 0,0,0

    def draw(self, x, y, dc, styler):
        dc.DrawBitmap(self.bitmap, x, y, useMask=False)

    def get_index(self, x, y):
        if x>self.width/2.0:
            return 1
        return 0

    def draw_selection(self, i1, i2, x, y, dc):
        self.device.invert_rect(x, y, self.width, self.height, dc)
        


# Wir fassen hier Updater und Factory in eine Klasse zusammen.  
class Updater(layout.Factory):        
    _maxw = 0

    CellStack = CellStack
    def __init__(self, model, device=layout.TESTDEVICE):
        self.model = model
        self.device = device
        self.rebuild()

    def set_maxw(self, maxw):
        if maxw != self._maxw:
            self._maxw = maxw
            self.rebuild()

    def Cell_handler(self, texel, i1, i2):
        boxes = self.create_boxes(texel.input)
        l = layout.create_paragraphs(
            boxes, maxw=self._maxw, 
            Paragraph = self.Paragraph,
            device = self.device)
        inbox = self.ParagraphStack(l, device=self.device)

        boxes = self.create_boxes(texel.output)
        l = layout.create_paragraphs(
            boxes, maxw=0, 
            Paragraph = self.Paragraph,
            device = self.device)
        outbox = self.ParagraphStack(l, device=self.device)

        return [CellBox([inbox], [outbox], number=texel.number, 
                        device=self.device)]

    def Plot_handler(self, texel, i1, i2):
        return [PlotBox(device=self.device)]

    def Figure_handler(self, texel, i1, i2):
        return [FigureBox(texel, device=self.device)]

    def xxcreate_paragraphs(self, i1, i2):
        factory = self.factory
        boxes = factory.create_boxes(self.model.texel, i1, i2)
        return create_paragraphs(
            boxes, self._maxw, 
            Paragraph = factory.Paragraph,
            device = factory.device)

    def create_cells(self, i1, i2):
        boxes = self.create_boxes(self.model.texel, i1, i2)
        for box in boxes:
            assert isinstance(box, CellBox) 
        return boxes

    def rebuild(self):
        boxes = self.create_cells(0, len(self.model))
        self.layout = self.CellStack(boxes, device=self.device)

    def properties_changed(self, i1, i2):
        layout = self.layout
        j1, j2 = layout.get_envelope(i1, i2)
        new = self.create_cells(j1, j2)
        self.layout = layout.replace(j1, j2, new)
        assert len(self.layout) == len(self.model)

    def inserted(self, i, n):
        layout = self.layout
        j1, j2 = layout.get_envelope(i, i)
        new = self.create_cells(j1, j2+n)
        self.layout = layout.replace(j1, j2, new)
        assert len(self.layout) == len(self.model)

    def removed(self, i, n):
        layout = self.layout
        j1, j2 = layout.get_envelope(i, i+n)
        new = self.create_cells(j1, j2-n)
        self.layout = layout.replace(j1, j2, new)
        assert len(self.layout) == len(self.model)


from textmodel.viewbase import ViewBase

class WXTextView(_WXTextView):
    def __init__(self, parent, id=-1,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        _WXTextView.__init__(self, parent, id=id, pos=pos, size=size, style=style)

    def create_factory(self):
        pass # Wir brauchen hier nichts zu tun, da die Factory
             # später zusammen mit dem Updater erzeugt wird.

    def create_updater(self):
        device = WxDevice()
        updater = Updater(self.model, device)
        self.factory = updater        
        self.updater = updater

    def on_char(self, event):
        keycode = event.GetKeyCode()
        ctrl = event.ControlDown()
        shift = event.ShiftDown()
        if keycode == wx.WXK_RETURN and shift and not ctrl:
            try:
                self.execute()
            except NotFound:
                pass
        else:
            _WXTextView.on_char(self, event)

    def find_cell(self):
        return find_cell(self.model.texel, self.index)

    def execute(self):
        i0, cell = self.find_cell()    
        n = len(cell)
        new = cell.execute()
        assert i0>=0
        assert i0+n<=len(self.model)
        self.model.remove(i0, i0+n)
        self.model.insert(i0, mk_textmodel(new))        
        
    def insert(self, i, textmodel):
        needscell = True
        try:
            i0, cell = self.find_cell()            
            if not (i == i0 or i == i0+len(cell)):
                needscell = False
        except NotFound:
            pass
        try:
            find_cell(textmodel.texel, 0)
            hascell = True
        except NotFound:
            hascell = False
        if needscell and not hascell:
            cell = Cell([], [])
            info = self.model.insert(i, mk_textmodel(cell))
            i = i+1
        _WXTextView.insert(self, i, textmodel)
            
        
        
        

def output_plot():
    import matplotlib
    import matplotlib.pyplot as plt
    plt.plot([1,2,3,4])
    plt.ylabel('some numbers')
    figure = plt.figure()
    figure.canvas.draw()
    w,h = figure.canvas.get_width_height()
    buf = figure.canvas.tostring_argb()
    bitmap = wx.BitmapFromBufferRGBA(w, h, buf)

def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    model.linelengths = texel.get_linelengths()
    return model


def init_testing(redirect=True):
    app = wx.App(redirect=redirect)
    model = TextModel('')

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = WXTextView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    layout = view.updater.layout
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()
    return locals()

# http://nbviewer.ipython.org/github/jrjohansson/scientific-python-lectures/
# blob/master/Lecture-4-Matplotlib.ipynb
examples = """from pylab import *
x = linspace(-5, 5, 20)
y = x ** 3

f = figure(figsize=(6, 4), facecolor='white')
plot(x, y, 'r')
xlabel('x')
ylabel('y')
title('title')
output(f)
---
subplot(1,2,1)
plot(x, y, 'r--')
subplot(1,2,2)
plot(y, x, 'g*-')
---
f
---
fig, ax = plt.subplots(facecolor='white')
ax.plot(x, x**2, label=r"$y = \\alpha^2$")
ax.plot(x, x**3, label=r"$y = \\alpha^3$")
ax.set_xlabel(r'$\\alpha$', fontsize=18)
ax.set_ylabel(r'$y$', fontsize=18)
ax.set_title('title')
ax.legend(loc=2); # upper left corner
output(fig)
---
from pylab import *
from numpy import cos
alpha = 0.7
phi_ext = 2 * pi * 0.5

def flux_qubit_potential(phi_m, phi_p):
    return 2 + alpha - 2 * cos(phi_p)*cos(phi_m) - alpha * cos(phi_ext - 2*phi_p)

phi_m = linspace(0, 2*pi, 100)
phi_p = linspace(0, 2*pi, 100)
X,Y = meshgrid(phi_p, phi_m)
Z = flux_qubit_potential(X, Y).T

fig, ax = plt.subplots()
fig.set_facecolor('white')

p = ax.pcolor(X/(2*pi), Y/(2*pi), Z, cmap=cm.RdBu, vmin=abs(Z).min(), vmax=abs(Z).max())
cb = fig.colorbar(p, ax=ax)
output(fig)
---
fig, ax = plt.subplots(facecolor='white')
cnt = contour(Z, cmap=cm.RdBu, vmin=abs(Z).min(), vmax=abs(Z).max(), extent=[0, 1, 0, 1])
output(fig)
"""

def test_00():
    "cell"
    ns = init_testing(False)
    cell = Cell([Characters(u'1234567890')], [Characters(u'abcdefghij')])
    assert len(cell.input) == 10
    assert len(cell.output) == 10
    assert len(cell) == 23

    texel = cell.insert(1, Characters(u'x'))
    assert texel.get_text()[1:2] == u'x'

def test_01():
    "interpreter"
    buf = TextBuffer()
    inter = SimpleInterpreter()
    inter.execute("asdasds", buf.output)    
    assert buf.stderr == '  File "input[1]", line 1, in <module>\nNameError: ' \
        'name \'asdasds\' is not defined\n'
    assert inter.ok == False
    assert buf.stdout == ''
    #return
    #print "buf.stderr=", repr(buf.stderr)
    buf = TextBuffer()
    inter.execute("a=1", buf.output)
    assert inter.namespace['a'] == 1
    assert not buf.stderr
    
    inter.execute("a", buf.output)
    assert not buf.stderr
    assert inter.namespace['ans'] == 1
    inter.execute("a+3", buf.output)
    assert not buf.stderr
    assert inter.namespace['ans'] == 4
    inter.execute("print a\n", buf.output)
    assert not buf.stderr
    assert buf.stdout
    buf = TextBuffer()
    inter.execute("if a:\n    print a", buf.output)
    assert not buf.stderr
    assert buf.stdout.strip() == '1'
    assert not buf.stderr
    inter.break_flag = True
    buf = TextBuffer()
    inter.execute("a+3", buf.output)
    assert not inter.ok
    assert buf.stderr

def test_02():
    "execute"
    ns = init_testing(False)
    cell = Cell([Characters(u'1+2')], [Characters(u'')])
    cell = cell.execute()
    assert cell.output.get_text() == '3'
    #print repr(cell.output.get_text())
    
    cell = Cell([Characters(u'for a in range(2):\n    print a')], [Characters(u'')])
    cell = cell.execute()
    assert cell.output.get_text() == u'0\n1\n'

    cell = Cell([Characters(u'asdsad')], [Characters(u'')])
    cell = cell.execute()
    #print repr(cell.output.get_text())
    assert cell.output.get_text() == u'  File "input[3]", line 1, ' \
        'in <module>\nNameError: name \'asdsad\' is not defined\n'

def test_03():
    "find_cell"
    tmp1 = TextModel(u'for a in range(3):\n    print a')
    tmp2 = TextModel(u'for a in range(10):\n    print a')
    cell1 = Cell([tmp1.texel], [Characters(u'')])
    cell2 = Cell([tmp2.texel], [Characters(u'')])
    
    model = TextModel('')
    model.insert(len(model), mk_textmodel(cell1))
    model.insert(len(model), mk_textmodel(cell2))

    assert find_cell(model.texel, 1) == (0, cell1)
    assert find_cell(model.texel, len(cell1)-1) == (0, cell1)

    assert find_cell(model.texel, len(cell1)) == (len(cell1), cell2)
    assert find_cell(model.texel, len(cell1)+5) == (len(cell1), cell2)


def test_04():
    "copy cells"
    model = TextModel('')
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = Cell([tmp.texel], [Characters(u'')])
    model.insert(len(model), mk_textmodel(cell))
    tmp = model.copy(0, len(model))
    model.insert(0, tmp)

def test_05():
    "cellstack"
    cell1 = CellBox([], [])
    check_box(cell1.input)
    check_box(cell1)
    cell2 = CellBox([], [])
    check_box(cell2)
    stack = CellStack([cell1, cell2])
    check_box(stack)

    stack = CellStack([])
    check_box(stack)

def test_06():
    "output"
    buf = TextBuffer()
    inter = SimpleInterpreter()
    inter.execute("output(1)", buf.output)    
    assert not buf.stderr
    inter.execute("output(1.1)", buf.output)    
    assert not buf.stderr
    inter.execute(u"output('ö')", buf.output)  
    assert not buf.stderr

    code = '''import matplotlib.pyplot as plt
plt.plot([1,2,3,4])
plt.ylabel('some numbers')
figure = plt.figure()
output(figure)
'''
    buf = TextBuffer()    
    inter.execute(code, buf.output)
    assert buf.stdout == 'Graphics ---'
    assert not buf.stderr


def test_10():
    "Factory"
    ns = init_testing(False)
    cell = Cell([Characters(u'a')], [Characters(u'b')])
    factory = Updater(TextModel(''))
    boxes = factory.create_boxes(cell)
    assert len(boxes) == 1
    cellbox = boxes[0]
    assert len(cellbox) == 5
    assert len(cell) == 5

    check_box(cellbox)
    check_box(cellbox.input)
    check_box(cellbox.output)
    return ns


def test_11():
    ns = init_testing(False)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = Cell([tmp.texel], [Characters(u'')])
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)
    
    view = ns['view']
    view.index = 1
    #print model.texel
    view.execute()

    check_box(view.updater.layout, model.texel)
    return ns

def test_12():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = Cell([tmp.texel], [])
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)
    
    view = ns['view']
    view.index = 1
    #print model.texel
    #view.execute()
    return ns


def test_13():
    ns = init_testing(False)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'''import matplotlib.pyplot as plt
figure = plt.figure(
    facecolor='white', 
    figsize=(3, 2.5))
figure.set_frameon(False)
plot = figure.add_subplot ( 111 )
plt.plot([1,2,3,4])
plt.ylabel('some numbers')
output(figure)''')
    cell = Cell([tmp.texel], [])
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)
    
    view = ns['view']
    view.index = 1
    view.execute()
    return ns

def test_14():
    "cell cursor"
    ns = init_testing(False)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = Cell([tmp.texel], [])
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)
    
    view = ns['view']
    view.index = 1
    layout = view.updater.layout
    r1 = layout.get_rect(0, 0, 0)
    assert r1.x2-r1.x1 == sepwidth

    r2 = layout.get_cursorrect(0, 0, 0, defaultstyle)
    r3 = layout.get_cursorrect(len(model), 0, 0, defaultstyle)
    assert r3.x2-r3.x1 == sepwidth
    assert r3.y1 > r2.y1


def demo_00():
    from wxtextview import testing
    ns = test_11()
    #print "app=", repr(ns['app'])
    testing.pyshell(ns)    
    ns['app'].MainLoop()

def demo_01():
    from wxtextview import testing
    ns = test_13() #12
    #print "app=", repr(ns['app'])
    testing.pyshell(ns)    
    ns['app'].MainLoop()

def demo_02():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(__doc__)
    cell = Cell([tmp.texel], [])
    model.insert(len(model), mk_textmodel(cell))

    for code in examples.split('---'):
        code = code.strip()

        tmp = TextModel(code)
        cell = Cell([tmp.texel], [])
        model.insert(len(model), mk_textmodel(cell))
    
    view = ns['view']
    view.index = 1
    ns['app'].MainLoop()
    
    
if __name__ == '__main__':
    from textmodel import alltests
    import sys

    if len(sys.argv) <= 1:
        sys.argv.append('demo_02')

    alltests.dotests()
    
