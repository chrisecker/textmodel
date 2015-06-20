# -*- coding: latin-1 -*-


"Python Notebook Demo\n" \
"~~~~~~~~~~~~~~~~~~~~\n\n" \
"The notebook consists of cells. Input cells can be executed by " \
"moving the cursor in the cell and pressing shift + return.\n" \
"Output is shown in output cells. Output usually consists of text " \
"printed to stdout or stderr by the python interpreter. To demonstrate " \
"non textual output, we implemented plotting "\
"(with the help of matplotlib).\n\n" \
"Try to execute the following cells.\n\n" \
"Notes:\n" \
" - Use the tab-key to complete. \n" \
" - To create a new cell, place the cursor below any output cell and start "\
"typing. \n" \
" - You can copy, paste and delete cells.\n" \
" - There is undo (ctrl z) and redo (ctrl u).\n"


import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../textmodel')

from textmodel import listtools, create_style
from textmodel.treebase import simple_insert, insert
from textmodel.texeltree import NewLine, Group, Characters, grouped, \
    defaultstyle, NULL_TEXEL, NL, Glyph, Texel
from textmodel.container import Container
from textmodel.textmodel import TextModel
from wxtextview.layout import Box, VBox, Row, Rect, IterBox, check_box, \
    NewlineBox, ParagraphStack
from wxtextview.testdevice import TESTDEVICE
from wxtextview.wxdevice import WxDevice
from wxtextview.updater import create_paragraphs
from wxtextview.updater import Factory as _Factory
from wxtextview.updater import Updater as _Updater
from wxtextview.wxtextview import WXTextView as _WXTextView


import traceback
import rlcompleter
import string
import wx




def has_classname(obj, classname):
    "returns True if $obj$ is an instance of a class with name $classname$"
    s = "<class '%s'>" % classname
    try:
        return str(obj.__class__) == s
    except AttributeError:
        return False


class Buffer:
    i = 0
    def __init__(self):
        self.model = TextModel()

    def output(self, obj, iserr=False):
        if iserr:
            properties = {'textcolor':'red'}
        else:
            properties = {}
        if has_classname(obj, "matplotlib.figure.Figure"):
            new = mk_textmodel(Figure(obj))
        elif isinstance(obj, unicode):
            new = TextModel(obj, **properties)
        elif isinstance(obj, str):
            u = unicode(obj, 'utf-8')
            new = TextModel(u, **properties)
        else:
            new = TextModel(str(obj), **properties)
        self.model.insert(self.i, new)
        self.i += len(new)


class TextBuffer:
    # for testing
    stdout = stderr = ""
    def __init__(self):
        self.out = []
        self.err = []

    def output(self, arg, iserr=False):
        if has_classname(arg, "matplotlib.figure.Figure"):
            u = 'Graphics ---'
        else:
            try:
                u = unicode(arg, 'latin-1')
            except:
                u = unicode(arg)
        if iserr:
            self.err.append(u)
        else:
            self.err.append(u)
        self.stdout = u''.join(self.out)
        self.stderr = u''.join(self.err)


class FakeFile:
    encoding = 'UTF-8'
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

    def execute(self, lines, output):
        self.namespace['output'] = output
        self.counter += 1
        name = 'In[%s]' % self.counter
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
                ans = eval(code, self.namespace)
                self.namespace['ans'] = ans
                self.ok = True
            except Exception, e:
                self.show_traceback(name)
                self.namespace['ans'] = None
            if self.expression and self.ok:
                ans = self.namespace['ans']
                # Note that we do not output the repr() of ans but ans
                # itself. This allow us to output drawings.
                try:
                    output(ans)
                except Exception, e:
                    self.show_traceback(name)
        finally:
            sys.stdout, sys.stderr = bkstdout, bkstderr

    def show_syntaxerror(self, filename):
        # stolen from "idle" by  G. v. Rossum
        type, value, sys.last_traceback = sys.exc_info()
        sys.last_type = type
        sys.last_value = value
        if filename and type is SyntaxError:
            # Work hard to stuff the correct filename in the exception
            try:
                msg, (dummy_filename, lineno, offset, line) = value
            except:
                # Not the format we expect; leave it alone
                pass
            else:
                # Stuff in the right filename
                try:
                    # Assume SyntaxError is a class exception
                    value = SyntaxError(msg, (filename, lineno, offset, line))
                except:
                    # If that failed, assume SyntaxError is a string
                    value = msg, (filename, lineno, offset, line)

        info = traceback.format_exception_only(type, value)
        sys.stderr.write(''.join(info))

    def show_traceback(self, filename):
        import types
        if type(sys.exc_value) == types.InstanceType:
            args = sys.exc_value.args
        else:
            args = sys.exc_value

        traceback.print_tb(sys.exc_traceback.tb_next, None)
        self.show_syntaxerror(filename)  


INTERPRETER = SimpleInterpreter()


def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    return model


class Cell(Container):
    # Eine Zelle enthält drei Trennzeichen (x) nach dem folgenden
    # Schema: x1234567890x1234567890x
    def __init__(self, input, output, number = 0, **kwargs):
        assert isinstance(input, Texel)
        assert isinstance(output, Texel)
        self.input = input
        self.output = output
        self.number = number
        Container.__init__(self, **kwargs)

    def get_empties(self):
        return NL, NL, NL

    def get_content(self):
        return self.input, self.output

    def get_kwds(self):
        kwds = Container.get_kwds(self)
        kwds['number'] = self.number
        return kwds

    def execute(self):
        buf = Buffer()
        INTERPRETER.execute(self.input.get_text(), buf.output)
        number = INTERPRETER.counter
        return self.__class__(self.input, buf.model.texel, number)



def extend_range_seperated(self, i1, i2):
    # extend_range-function for texel with separated child
    for j1, j2, x, y, child in self.iter(0, 0, 0):
        if not (i1<j2 and j1<i2):
            continue
        if i1 < j1 or i2>j2:
            return min(i1, 0), max(i2, len(self))
        k1, k2 = child.extend_range(i1-j1, i2-j1)
        return min(i1, k1+j1), max(i2, k2+j1)
    return i1, i2


def common(s1, s2):
    # find the common part of the strings
    r = ''
    i = 0
    try:
        while s1[i] == s2[i]:
            i += 1
    except IndexError:
        pass
    return s1[:i]


promptstyle = create_style(
    textcolor = 'blue',
    weight = 'bold'
    )

sepwidth = 20000 # a number which is just larger than the textwidth

class CellBox(IterBox):
    def __init__(self, inbox, outbox, number=0, device=None):
        # NOTE: Inbox and outbox should be PargraphStacks
        self.number = number
        if device is not None:
            self.device=device
        self.input = inbox
        self.output = outbox
        self.length = len(inbox)+len(outbox)+1
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
        y += input.height+input.depth
        yield j1, j2, x+80, y, output

    def layout(self):
        # compute w and h
        dh = h = w = 0
        for j1, j2, x, y, child in self.iter(0, 0, 0):
            w = max(x+child.width, w)
            h = max(y+child.height, h)
            dh = max(y+child.height+child.depth, dh)
        self.width = w
        self.height = h
        self.depth = dh-h

    def __repr__(self):
        return self.__class__.__name__+'(%s, %s)' % \
            (repr(self.input),
             repr(self.output))

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

    ### Methods for the Updater
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
        for child in texel.childs:
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




class Updater(_Updater):

    def create_cells(self, texel, i1, i2):
        boxes = self.create_boxes(texel, i1, i2)
        for box in boxes:
            assert isinstance(box, CellBox)
        return boxes

    def create_parstack(self, texel):
        boxes = self.create_boxes(texel)+(
            self.NewlineBox(device=self.device),)
        if self._maxw:
            maxw = max(100, self._maxw-80)
        else:
            maxw = 0
        l = create_paragraphs(
            boxes, maxw = maxw,
            Paragraph = self.Paragraph,
            device = self.device)
        return self.ParagraphStack(l, device=self.device)

    def rebuild(self):
        model = self.model
        boxes = self.create_cells(model.texel, 0, len(model))
        self._layout = CellStack(boxes, device=self.device)

    ### Handlers
    def Cell_handler(self, texel, i1, i2):
        inbox = self.create_parstack(texel.input)
        assert len(inbox) == len(texel.input)+1

        outbox = self.create_parstack(texel.output)
        assert len(outbox) == len(texel.output)+1

        return [CellBox(inbox, outbox, number=texel.number,
                        device=self.device)]

    def Plot_handler(self, texel, i1, i2):
        return [PlotBox(device=self.device)]

    def Figure_handler(self, texel, i1, i2):
        return [FigureBox(texel, device=self.device)]

    ### Signals
    def properties_changed(self, i1, i2):
        layout = self._layout
        j1, j2 = layout.get_envelope(i1, i2)
        new = self.create_cells(self.model.texel, j1, j2)
        self._layout = layout.replace(j1, j2, new)
        assert len(self._layout) == len(self.model)
        return self._layout

    def inserted(self, i, n):
        layout = self._layout
        j1, j2 = layout.get_envelope(i, i)
        new = self.create_cells(self.model.texel, j1, j2+n)
        self._layout = layout.replace(j1, j2, new)
        assert len(self._layout) == len(self.model)
        return self._layout

    def removed(self, i, n):
        layout = self._layout
        j1, j2 = layout.get_envelope(i, i+n)
        new = self.create_cells(self.model.texel, j1, j2-n)
        self._layout = layout.replace(j1, j2, new)
        assert len(self._layout) == len(self.model)
        return self._layout


class WXTextView(_WXTextView):
    temp_range = (0, 0)
    def __init__(self, parent, id=-1,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        _WXTextView.__init__(self, parent, id=id, pos=pos, size=size,
                             style=style)
        self.actions[(wx.WXK_TAB, False, False)] = 'complete'

    _resize_pending = False
    _new_size = None
    def on_size(self, event):
        # Note that resize involves computing all line breaks and is
        # therefore a very costly operation. We therefore try to
        # minimize resizes here.
        self._new_size = event.Size
        if self._resize_pending:
            return
        self._resize_pending = True
        wx.CallAfter(self._adjust_size)
        
    def _adjust_size(self):
        self._resize_pending = False
        maxw = self._new_size[0]
        if maxw == self._maxw:
            return
        self.set_maxw(maxw)
        self.keep_cursor_on_screen()

    def create_updater(self):
        return Updater(
            self.model,
            device=WxDevice(),
            maxw=self._maxw)

    def print_temp(self, text):
        new = TextModel(text)
        new.set_properties(0, len(new), textcolor='blue')
        i = self.index
        self.model.insert(i, new)
        j1, j2 = self.temp_range
        if j1 == j2:
            self.temp_range = i, i+len(new)
        else:
            self.temp_range = j1, i+len(new)

    def clear_temp(self):
        j1, j2 = self.temp_range
        if j1 != j2:
            self.model.remove(j1, j2)
            self.temp_range = j1, j1

    def has_temp(self):
        j1, j2 = self.temp_range
        return not j1 == j2

    def get_word(self, j):
        model = self.model
        row, col = model.index2position(j)
        text = model.get_text(model.linestart(row), j)
        i = len(text)-1
        while i>=0 and text[i] in string.letters+string.digits+"_.":
            i -= 1
        if j == i:
            return ''
        return text[i+1:]

    def handle_action(self, action, shift=False):
        if action != 'complete':
            self.clear_temp()
            return _WXTextView.handle_action(self, action, shift)
        try:
            i0, cell = self.find_cell()
        except NotFound:
            return
        index = self.index
        if index <= i0 or index >= i0+len(cell):
            return
        if self.has_temp():
            self.clear_temp()
            maxoptions = 2000
        else:
            maxoptions = 200
        word = self.get_word(index)
        completer = rlcompleter.Completer(INTERPRETER.namespace)
        options = set()
        i = 0
        while True:
            option = completer.complete(word, i)
            i += 1
            if option is None or len(options) == maxoptions:
                break
            options.add(option)
        if not options:
            self.print_temp( "\n[No completion]\n")
        else:
            completion = reduce(common, options)[len(word):]
            if completion and len(options) != maxoptions:
                self.model.insert_text(index, completion)
                info = self._remove, index, index+len(completion)
                self.add_undo(info)
                index += len(completion)
            else:
                options = list(sorted(options))
                s = ', '.join(options)
                s = s.replace('(', '') # I don't like the bracket
                if len(options) == maxoptions:
                    s += ' ... '
                self.print_temp('\n'+s+'\n')
        self.index = index

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
        infos = []
        infos.append(self._remove(i0, i0+n))
        self.model.insert(i0, mk_textmodel(new))
        infos.append((self._remove, i0, i0+len(new)))
        self.add_undo(infos) 
        self.adjust_viewport()

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
            cell = Cell(NULL_TEXEL, NULL_TEXEL)
            self.model.insert(i, mk_textmodel(cell))
            info = self._remove, i, i+len(cell)
            self.add_undo(info)
            i = i+1
        _WXTextView.insert(self, i, textmodel)


def init_testing(redirect=True):
    app = wx.App(redirect=redirect)
    model = TextModel('')

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = WXTextView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    INTERPRETER.namespace.update(dict(
        __notebook__ = view, 
        ))

    frame.Show()
    return locals()

# http://nbviewer.ipython.org/github/jrjohansson/scientific-python-lectures/
# blob/master/Lecture-4-Matplotlib.ipynb
examples = """import matplotlib
matplotlib.use('Agg')

from pylab import *
x = linspace(0, 3*pi, 500)
y = sin(x)*cos(20*x)

f = figure(facecolor='white')
plot(x, y, 'r')
xlabel('x')
ylabel('y')
title('title')
output(f)
---
fig = plt.figure(facecolor='white')
r = np.arange(0, 3.0, 0.01)
theta = 2 * np.pi * r

ax = plt.subplot(111, polar=True)
ax.plot(theta, r, color='r', linewidth=3)
ax.set_rmax(2.0)
ax.grid(True)

ax.set_title("A line plot on a polar axis", va='bottom')

# Note that nothing is drawn here
---
fig # Here comes the drawing!
---
fig, ax = plt.subplots(facecolor='white')
ax.plot(x, x**2, label=r"$y = \\alpha^2$")
ax.plot(x, x**3, label=r"$y = \\alpha^3$")
ax.set_xlabel(r'$\\alpha$', fontsize=18)
ax.set_ylabel(r'$y=f(\\alpha)$', fontsize=18)
ax.set_title('More 2D-Plotting')
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
    cell = Cell(Characters(u'1234567890'), Characters(u'abcdefghij'))
    assert len(cell.input) == 10
    assert len(cell.output) == 10
    assert len(cell) == 23

    texel = grouped(insert(cell, 1, [Characters(u'x')]))
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
    cell = Cell(Characters(u'1+2'), Characters(u''))
    cell = cell.execute()
    assert cell.output.get_text() == '3'

    cell = Cell(Characters(u'for a in range(2):\n    print a'),
                Characters(u''))
    cell = cell.execute()
    assert cell.output.get_text() == u'0\n1\n'

    cell = Cell(Characters(u'asdsad'), Characters(u''))
    cell = cell.execute()
    #print repr(cell.output.get_text())
    assert cell.output.get_text() == u'  File "input[3]", line 1, ' \
        'in <module>\nNameError: name \'asdsad\' is not defined\n'

def test_03():
    "find_cell"
    tmp1 = TextModel(u'for a in range(3):\n    print a')
    tmp2 = TextModel(u'for a in range(10):\n    print a')
    cell1 = Cell(tmp1.texel, Characters(u''))
    cell2 = Cell(tmp2.texel, Characters(u''))

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
    cell = Cell(tmp.texel, Characters(u''))
    model.insert(len(model), mk_textmodel(cell))
    tmp = model.copy(0, len(model))
    model.insert(0, tmp)

def test_05():
    "cellstack"
    empty = ParagraphStack([])
    cell1 = CellBox(empty, empty)
    check_box(cell1.input)
    check_box(cell1)
    cell1.dump_boxes(0, 0, 0)

    cell2 = CellBox(empty, empty)
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
    figure = inter.namespace['figure']

    assert has_classname(figure, 'matplotlib.figure.Figure')
    assert buf.stdout == 'Graphics ---'
    assert not buf.stderr


def test_10():
    "Factory"
    ns = init_testing(False)
    cell = Cell(Characters(u'a'), Characters(u'b'))
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
    ns = init_testing(True) #False)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'for a in range(25):\n    print a')
    cell = Cell(tmp.texel, Characters(u''))
    model.insert(len(model), mk_textmodel(cell))

    assert model.index2position(0) == (0, 0)
    assert model.index2position(1) == (1, 0)
    cell = model.texel

    assert find_cell(model.texel, 1) == (0, cell)

    view = ns['view']
    view.index = 1
    #print model.texel
    view.execute()

    check_box(view.updater._layout, model.texel)
    return ns

def test_12():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = Cell(tmp.texel, NULL_TEXEL)
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)

    view = ns['view']
    view.index = 1
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
    cell = Cell(tmp.texel, NULL_TEXEL)
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
    cell = Cell(tmp.texel, NULL_TEXEL)
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)

    view = ns['view']
    view.index = 1
    layout = view.updater.get_layout()
    r1 = layout.get_rect(0, 0, 0)
    assert r1.x2-r1.x1 == sepwidth

    r2 = layout.get_cursorrect(0, 0, 0, defaultstyle)
    r3 = layout.get_cursorrect(len(model), 0, 0, defaultstyle)
    assert r3.x2-r3.x1 == sepwidth
    assert r3.y1 > r2.y1

def test_15():
    "get_word, print_temp, remove_temp"
    ns = init_testing(False)
    model = ns['model']
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = Cell(tmp.texel, NULL_TEXEL)
    model.insert(len(model), mk_textmodel(cell))
    view = ns['view']
    assert view.get_word(12) == 'ra'

    text = model.get_text()
    view.index = 12
    view.print_temp('\n[raise range raw_input]\n')
    print model.get_text()

    view.clear_temp()
    assert model.get_text() == text


def demo_00():
    from wxtextview import testing
    ns = test_11()
    testing.pyshell(ns)
    ns['app'].MainLoop()

def demo_01():
    ns = test_13()
    from wxtextview import testing
    testing.pyshell(ns)
    ns['app'].MainLoop()

def demo_02():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(__doc__)
    cell = Cell(tmp.texel, NULL_TEXEL)
    model.insert(len(model), mk_textmodel(cell))

    for code in examples.split('---'):
        code = code.strip()

        tmp = TextModel(code)
        cell = Cell(tmp.texel, NULL_TEXEL)
        model.insert(len(model), mk_textmodel(cell))

    view = ns['view']
    view.index = 1
    wx.CallAfter(view.Scroll, 0, 0)
    view.SetFocus()
    if 0:
        INTERPRETER.namespace.update(ns)
        from wxtextview import testing
        testing.pyshell(ns)
    ns['app'].MainLoop()


if __name__ == '__main__':
    demo_02()

