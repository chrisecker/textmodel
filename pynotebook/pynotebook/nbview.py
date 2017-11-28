# -*- coding: latin-1 -*-


from .textmodel import texeltree
from .textmodel.textmodel import TextModel
from .textmodel.styles import create_style, updated_style, EMPTYSTYLE
from .textmodel.texeltree import Group, Text, grouped, insert, length, \
    get_text, join, get_rightmost, NULL_TEXEL, dump, iter_leaves

from .wxtextview.boxes import Box, VGroup, VBox, Row, Rect, check_box, \
    NewlineBox, TextBox, TabulatorBox, extend_range_seperated, replace_boxes, \
    ChildBox, calc_length
from .wxtextview.simplelayout import create_paragraphs, Paragraph
from .wxtextview.testdevice import TESTDEVICE
from .wxtextview.builder import BuilderBase
from .wxtextview.wxdevice import WxDevice
from .wxtextview.wxtextview import WXTextView as _WXTextView

from .nbtexels import Cell, ScriptingCell, TextCell, Graphics, find_cell, \
    mk_textmodel, NotFound, strip_output, split_cell
from .clients import ClientPool
from .pyclient import PythonClient
from .nbstream import Stream, StreamRecorder
from .nblogging import logged
import string
import wx
import sys
import weakref




sepwidth = 20000 # a number which is just larger than the textwidth
wleft = 80 # width of left column
tempstyle = dict(textcolor='blue', temp=True)


class ParagraphStack(VGroup):
    pass


class Frame(ChildBox):
    def __init__(self, childs, fillcolor=None, linecolor=None, border=(0, 0, 0, 0), 
                 device=None):
        self.border = border
        self.fillcolor = fillcolor or 'white'
        self.linecolor = linecolor or 'white'
        ChildBox.__init__(self, childs, device)

    def from_childs(self, childs):
        return Frame(childs, fillcolor, linecolor, border, device)

    def iter_boxes(self, i, x, y):
        border = self.border
        x += border[0]
        y += border[1]
        j1 = i
        for child in self.childs:
            j2 = j1+len(child)
            yield j1, j2, x, y, child
            y += child.height+child.depth
            j1 = j2

    def layout(self):
        w = h = d = 0
        border = self.border
        for child in self.childs:
            w += child.width
            h = max(h, child.height)
            d = max(d, child.depth)
        self.width = w+border[0]+border[2]
        self.height = h+border[1]+border[3]
        self.depth = d
        self.length = calc_length(self.childs)

    def get_index(self, x, y):
        l = [0, len(self)]
        for j1, j2, x1, y1, child in self.riter_boxes(0, 0, 0):
            if y1 <= y <= y1+child.height+child.depth:
                l.append(j1)
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    l.append(i+j1)
                if len(child):
                    l.append(j1+len(child))
                    l.append(j1+len(child)-1) # This is needed for rows
        return self._select_index(l, x, y)

    def draw(self, x, y, dc, styler):
        device = self.device
        dc.SetBrush(wx.Brush(self.fillcolor, wx.SOLID))
        dc.SetPen(wx.Pen(self.linecolor,style=wx.SOLID))
        dc.DrawRectangle(x, y, self.width, self.height)

        for j1, j2, x1, y1, child in self.iter_boxes(0, x, y):
            r = Rect(x1, y1, x1+child.width, y1+child.height)
            if device.intersects(dc, r):
                child.draw(x1, y1, dc, styler)



class TextCellBox(VBox):
    text = property(lambda s:s.childs[0])
    def __init__(self, textbox, device=None):
        # NOTE: textbox should be a PargraphStack
        if device is not None:
            self.device=device
        self.childs = [textbox]
        self.layout()

    def from_childs(self, childs):
        box = self.__class__(childs[0], self.device)
        return [box]

    def __len__(self):
        return self.length

    def create_group(self, l):
        return VGroup(l, device=self.device)

    def iter_boxes(self, i, x, y):
        text = self.text
        height = self.height
        j1 = i+1
        j2 = j1+len(text)
        yield j1, j2, x+wleft, y, text

    def layout(self):
        # compute w and h
        for j1, j2, x, y, child in self.iter_boxes(0, 0, 0):
            w = x+child.width
            h = y+child.height
            dh = y+child.height+child.depth
        self.width = w
        self.height = h
        self.depth = dh-h
        self.length = j2

    def __repr__(self):
        return self.__class__.__name__+'(%s)' % \
            (repr(self.text),)

    def extend_range(self, i1, i2):
        if i1<=0 or i2>=len(self):
            return 0, len(self)
        return extend_range_seperated(self, i1, i2) # XXX STIMMT DAS?

    def draw_selection(self, i1, i2, x, y, dc):
        if i1<=0 and i2>=self.length:
            self.device.invert_rect(x, y, sepwidth, self.height, dc)
        else:
            VBox.draw_selection(self, i1, i2, x, y, dc)

    def responding_child(self, i, x0, y0):
        # As default behaviour a VBox manages all index positions 0 to
        # n. Here we want position n to be managed by the next object. 
        if i == len(self):
            # Index i is between this box and the next box. We return
            # None to signal that the next box should be the
            # responding box.
            return None, i, x0, y0
        return VBox.responding_child(self, i, x0, y0)

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



class ScriptingCellBox(VBox):
    input = property(lambda s:s.childs[0])
    output = property(lambda s:s.childs[1])
    border = 8, 8, 8, 8
    inbackground = '#f7f7f7'
    inline = '#cfcfcf'
    promptstyle = create_style(
        textcolor = 'darkblue',
        #bold = True,
        italic = True,
        fontsize = 8,
        )


    def __init__(self, inbox, outbox, number=0, device=None):
        #assert isinstance(inbox, ParagraphStack)
        #assert isinstance(outbox, ParagraphStack)
        self.number = number
        if device is not None:
            self.device=device
        self.childs = [inbox, outbox]
        self.layout()

    def from_childs(self, childs):
        box = self.__class__(childs[0], childs[1], self.number, self.device)
        return [box]

    def __len__(self):
        return self.length

    def create_group(self, l):
        return VGroup(l, device=self.device)

    def iter_boxes(self, i, x, y):
        input = self.input
        output = self.output
        height = self.height        
        j1 = i+1
        j2 = j1+len(input)
        yield j1, j2, x+wleft, y, input
        j1 = j2
        j2 = j1+len(output)
        y += input.height+input.depth
        yield j1, j2, x+wleft, y, output

    def layout(self):
        # compute w and h
        dh = h = w = 0
        for j1, j2, x, y, child in self.iter_boxes(0, 0, 0):
            w = max(x+child.width, w)
            h = max(y+child.height, h)
            dh = max(y+child.height+child.depth, dh)
        self.width = w
        self.height = h
        self.depth = dh-h
        self.length = j2

    def __repr__(self):
        return self.__class__.__name__+'(%s, %s)' % \
            (repr(self.input),
             repr(self.output))

    def extend_range(self, i1, i2):
        for i in (0, len(self.input), len(self)-1):
            if i1<= i<i2:
                #print "empty in i1..i2", i, (i1, i2)
                #self.dump_boxes(0, 0, 0)
                return min(i1, 0), max(i2, len(self))
        return extend_range_seperated(self, i1, i2)

    def draw(self, x, y, dc, styler):
        a, b = list(self.iter_boxes(0, x, y))
        promptstyle = self.promptstyle
        styler.set_style(promptstyle)
        n = self.number or ''
        w1 = self.device.measure('Out', promptstyle)[0]
        w2 = self.device.measure('Out [%s]:' % n, promptstyle)[0]

        border = self.border
        x1 = x+wleft-w2
        x2 = x1+w1
        y1 = a[3]+border[1]
        y2 = b[3]+border[1]

        dc.DrawText("In", x1, y1)
        dc.DrawText("[%s]:" % n, x2, y1)
        if b[4].length > 1:
            dc.DrawText("Out", x1, y2)
            dc.DrawText("[%s]:" % n, x2, y2)

        VBox.draw(self, x, y, dc, styler)


    def draw_selection(self, i1, i2, x, y, dc):
        if i1<=0 and i2>=self.length:
            self.device.invert_rect(x, y, sepwidth, self.height, dc)
        else:
            VBox.draw_selection(self, i1, i2, x, y, dc)

    def responding_child(self, i, x0, y0):
        # Index position n+1 usually is managed by a child object. We
        # want the next object to be responsible, so we have to change
        # the return behaviour.
        if i == len(self):
            return None, i, x0, y0
        return VBox.responding_child(self, i, x0, y0)

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





 


class BitmapBox(Box):
    def __init__(self, bitmap, device=None):
        if device is not None:
            self.device = device
        self.bitmap = bitmap
        self.width, self.height = bitmap.Size
        self.depth = 0

    def __len__(self):
        return 1

    def iter_boxes(self, i, x, y):
        if 0: yield 0,0,0

    def draw(self, x, y, dc, styler):
        dc.DrawBitmap(self.bitmap, x, y, useMask=False)

    def get_index(self, x, y):
        if x>self.width/2.0:
            return 1
        return 0

    def draw_selection(self, i1, i2, x, y, dc):
        self.device.invert_rect(x, y, self.width, self.height, dc)



def copy_pen(pen):
    new = wx.Pen(pen.Colour, pen.Width, pen.Style)
    new.Cap = pen.Cap
    new.Dashes = pen.Dashes
    new.Join = pen.Join
    return new


def copy_brush(brush):
    new = wx.Brush(brush.Colour, brush.Style)
    if brush.Stipple.Ok():
        new.Stipple = brush.Stipple
    return new


class GraphicsBox(Box):
    def __init__(self, texel, device=None):
        if device is not None:
            self.device = device
        self.texel = texel
        self.width, self.height = texel.size

    def __len__(self):
        return 1

    def iter_boxes(self, i, x, y):
        if 0: yield 0,0,0

    def draw(self, x, y, dc, styler):
        gc = wx.GraphicsContext.Create(dc)
        gc.Clip(x, y, self.width, self.height)
        gc.Translate(x, y)
        pen = wx.Pen(colour='black', style=wx.USER_DASH)
        brush = copy_brush(wx.TRANSPARENT_BRUSH)
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        matrix = gc.CreateMatrix() # transforms paths
        trafo = gc.GetTransform() # transforms the canvas
        state = dict(pen=pen, brush=brush, font=font, matrix=matrix,
                     trafo=trafo)
        gc.SetPen(pen)
        gc.SetBrush(brush)
        gc.SetFont(font)

        texel = self.texel
        if texel.frame:
            gc.DrawRectangle(1, 1, self.width-2, self.height-2)

        def draw(item, state=state, gc=gc):
            if type(item) is list or type(item) is tuple:
                oldbrush = copy_brush(state['brush'])
                oldpen = copy_pen(state['pen'])
                oldmatrix = gc.CreateMatrix(*state['matrix'].Get())
                gc.PushState()
                for child in item:
                    draw(child)
                gc.PopState()
                gc.SetPen(oldpen)
                gc.SetBrush(oldbrush)
                state['brush'] = oldbrush
                state['pen'] = oldpen
                state['matrix'] = oldmatrix
            else:
                item.draw(gc, state)

        try:
            draw(texel.items)
        except Exception, e:
            dc.SetBrush(wx.RED_BRUSH)
            dc.SetPen(wx.RED_PEN)
            dc.DrawRectangle(x, y, self.width, self.height)
            print >>sys.stderr, e
        draw = None
        
    def get_index(self, x, y):
        if x>self.width/2.0:
            return 1
        return 0

    def draw_selection(self, i1, i2, x, y, dc):
        self.device.invert_rect(x, y, self.width, self.height, dc)



class BoxesCache:
    def __init__(self):
        self.buffer = dict()
        
    def set(self, key, box):
        def callback(*args):
            del self.buffer[key]        
        self.buffer[key] = weakref.ref(box, callback)
        
    def get(self, key):
        return self.buffer[key]()

    def clear(self):
        self.buffer.clear()



def reset_numbers(texel):
    if isinstance(texel, ScriptingCell):
        texel.number = 0
    elif texel.is_group:
        for child in texel.childs:
            reset_numbers(child)


def is_temp(model, i):
    return model.get_style(i).get('temp', False)


def find_temp(tree):
    j1 = j2 = None
    for i1, i2, texel in iter_leaves(tree):
        if texel.style.get('temp'):
            if j1 is None:
                j1 = i1
                j2 = i2
            else:
                j2 = max(j2, i2)
    return j1, j2



class Builder(BuilderBase):
    parstyle = EMPTYSTYLE

    def __init__(self, model, clients=None, device=TESTDEVICE, maxw=0):
        if clients is None:
            clients = ClientPool()
        self._clients = clients
        self.device = device
        self.model = model
        self._maxw = maxw
        self.cache = BoxesCache()

    def get_device(self):
        return self.device

    def mk_style(self, style):
        # This can overriden e.g. to implement style sheets. The
        # default behaviour is to use the paragraph style and add the
        # text styles.
        r = self.parstyle.copy()
        r.update(style)
        return r

    def extended_texel(self):
        return self.model.get_xtexel()
        
    def set_maxw(self, maxw):
        if maxw != self._maxw:
            self._maxw = maxw
            self.cache.clear()
            self.rebuild()

    ### Factory methods
    def create_boxes(self, texel):
        name = texel.__class__.__name__+'_handler'
        handler = getattr(self, name)
        #print "calling handler", name
        l = handler(texel)
        try:
            assert calc_length(l) == length(texel)
        except:
            print "handler=", handler
            raise
        return tuple(l)

    def Group_handler(self, texel):
        # Handles group texels. Note that the list of childs is
        # traversed from right to left. This way the "Newline" which
        # ends a line is handled before the content in the line. This
        # is important because in order to build boxes for the line
        # elements, we need to know the paragraph style which is
        # located in the NewLine-Texel.
        create_boxes = self.create_boxes
        r = ()
        for j1, j2, child in reversed(list(texeltree.iter_childs(texel))):
            r = create_boxes(child)+r
        return r

    def Text_handler(self, texel):
        # non caching version
        return [TextBox(texel.text, self.mk_style(texel.style), 
                self.device)]

    _textcache = dict()
    _textcache_keys = []
    def Text_handler(self, texel):
        # caching version
        key = texel.text, id(texel.style), id(self.parstyle), self.device
        try:
            return self._textcache[key]
        except: pass        
        r = [TextBox(texel.text, self.mk_style(texel.style), 
                     self.device)]
        self._textcache_keys.insert(0, key)        
        if len(self._textcache_keys) > 10000:
            _key = self._textcache_keys.pop()
            del self._textcache[_key]
        self._textcache[key] = r
        return r
    
    def NewLine_handler(self, texel):
        self.parstyle = texel.parstyle
        if texel.is_endmark:
            return [self.EndBox(self.mk_style(texel.style), self.device)]
        return [NewlineBox(self.mk_style(texel.style), self.device)] # XXX: Hmmmm

    def Tabulator_handler(self, texel):
        return [TabulatorBox(self.mk_style(texel.style), self.device)]

    def TextCell_handler(self, texel):
        try:
            cell = self.cache.get(texel)
        except KeyError:
            textbox = self.create_parstack(Group(texel.childs[1:]))
            cell = TextCellBox(textbox, device=self.device)
            self.cache.set(texel, cell)
        assert len(cell) == length(texel)
        return [cell]

    def ScriptingCell_handler(self, texel):
        sep1, inp, sep2, outp, sep3 = texel.childs

        border = ScriptingCellBox.border
        inbackground = ScriptingCellBox.inbackground
        inline = ScriptingCellBox.inline

        key = inp, 'input'
        try:
            inbox = self.cache.get(key)
        except KeyError:        
            client = self._clients.get_matching(texel)
            model = mk_textmodel(Group([inp, sep2]))

            t1, t2 = find_temp(inp)
            if t1 is not None:
                temp = model.remove(t1, t2)

            colorized = mk_textmodel(
                client.colorize(model.texel, bgcolor=inbackground))
            if t1 is not None:
                colorized.insert(t1, temp)
            inbox = self.create_parstack(colorized.texel)
            inbox.width = max(self._maxw+border[0]+border[1], inbox.width)
            self.cache.set(key, inbox)
            assert len(inbox) == length(inp)+1

        key = outp, 'out'
        try:
            outbox = self.cache.get(key)
        except KeyError:
            outbox = self.create_parstack(Group([outp, sep3]))
            self.cache.set(key, outbox)
            assert len(outbox) == length(outp)+1

        cell = ScriptingCellBox(
            Frame([inbox], border=border, fillcolor=inbackground,
                  linecolor=inline), 
            Frame([outbox], border=border), 
            number=texel.number,
            device=self.device)
        return [cell]

    def Plot_handler(self, texel):
        return [PlotBox(device=self.device)]

    def Graphics_handler(self, texel):
        return [GraphicsBox(texel, device=self.device)]

    def BitmapRGB_handler(self, texel):
        w, h = texel.size
        bitmap = wx.BitmapFromBuffer(w, h, texel.data)
        return [BitmapBox(bitmap, device=self.device)]

    def BitmapRGBA_handler(self, texel):
        w, h = texel.size
        im = wx.ImageFromData(w, h, texel.data)
        im.SetAlphaBuffer(texel.alpha)
        bitmap = wx.BitmapFromImage(im)
        return [BitmapBox(bitmap, device=self.device)]

    ### Builder methods
    def create_paragraphs(self, texel):
        boxes = self.create_boxes(texel)
        if self._maxw:
            maxw = max(100, self._maxw-wleft)
        else:
            maxw = 0
        l = create_paragraphs(
            boxes, maxw = maxw,
            Paragraph = Paragraph,
            device = self.device)
        return l

    def create_parstack(self, texel):
        l = self.create_paragraphs(texel)
        return ParagraphStack(l, device=self.device)

    def rebuild(self):
        model = self.model
        boxes = self.create_boxes(model.texel)
        vgroup = VGroup(boxes, device=self.device)
        if vgroup.length:
            # Put a frame around the cells so that there is empty
            # space at the top and at the bottom.
            self._layout = Frame([vgroup], border=(0, 10, 0, 10))
        else:
            # Here we avoid VGroup(...) because I don't like how it
            # draws the caret. Might be a bug!??
            self._layout = vgroup

    ### Signal handlers
    def properties_changed(self, i1, i2):
        self.rebuild()

    def inserted(self, i, n):
        self.rebuild()

    def removed(self, i, n):
        #print "removed", i, n
        self.rebuild()




def common(s1, s2):
    # Helper: find the common part of two strings. Needed by
    # completer.
    r = ''
    i = 0
    try:
        while s1[i] == s2[i]:
            i += 1
    except IndexError:
        pass
    return s1[:i]


def strip_cells(texel):
    # Helper: replace all cells in texel by their content
    if texel.is_group:
        l = []
        for child in group.childs:
            l.extend(strip_cells(child))
        return groupes(l)
    if isinstance(texel, Cell):
        return join(*[[c] for c in texel.childs]) 
    return [texel]


def logged(f):
    def new_f(nbview, *args, **kwds):
        nbview.log(f.__name__, args, kwds)
        return f(nbview, *args, **kwds)
    return new_f


class NBView(_WXTextView):
    temp_range = (0, 0)
    ScriptingCell = ScriptingCell
    _maxw = 600
    _logfile = None
    def __init__(self, parent, id=-1,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, 
                 resize=False, filename=None, maxw=None, logfile=None):
        if logfile:
            self._logfile = logfile

        if maxw is not None:
            self._maxw = maxw
        self.do_resize = resize
        self.init_clients()
        _WXTextView.__init__(self, parent, id=id, pos=pos, size=size,
                             style=style)
        if filename is not None:
            self._load(filename)
        self.actions[(wx.WXK_F1, False, False)] = 'help'
        self.actions[(wx.WXK_TAB, False, False)] = 'complete'
        self.actions[(wx.WXK_RETURN, True, False)] = 'execute'
        self.actions[(wx.WXK_RETURN, False, False)] = 'insert_newline_indented'
        self.actions[(2, True, False)] = 'split_cell'

    def _load(self, filename):
        s = open(filename, 'rb').read()
        import cerealizerformat        
        model = cerealizerformat.loads(s)
        reset_numbers(model.texel)
        self.set_model(model)

    @logged
    def set_model(self, model):
        # Only meant to be called on fresh NBViews. Therefore we do
        # not reset cursor, selection etc.
        _WXTextView.set_model(self, model)

    def save(self, filename):        
        import cerealizerformat
        s = cerealizerformat.dumps(self.model)
        open(filename, 'wb').write(s)

    def init_clients(self):
        self._clients = ClientPool()        
        client = PythonClient()
        client.namespace['__shell__'] = self
        self._clients.register(client)
        # Hack to be able to load file created with older versions:
        self._clients.add(client, 'direct python')

    _resize_pending = False
    _new_size = None
    def on_size(self, event):
        if not self.do_resize:
            return

        # Note that resize involves computing all line breaks and is
        # therefore a very costly operation. We therefore try to avoid
        # unnecessary resize events.
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

    def create_builder(self):
        return Builder(
            self.model,
            clients=self._clients,
            device=WxDevice(),
            maxw=self._maxw)

    def print_temp(self, text):
        # Notes: 
        #  - temp has to be removed before other temp can be produced
        #  - temp does not generate undo information
        #  - temp must be removed before any undo operation
        if self.has_temp():
            raise Exception("Temp already set")
        properties = tempstyle.copy()
        properties['bgcolor'] = ScriptingCellBox.inbackground
        new = TextModel(text, **properties)
        i = self.index
        self.model.insert(i, new)
        j1, j2 = self.temp_range
        if j1 == j2:
            self.temp_range = i, i+len(new)
        else:
            self.temp_range = j1, i+len(new)

    def clear_temp(self):
        self.complete_count = 0
        j1, j2 = self.temp_range
        if j1 != j2:
            self.model.remove(j1, j2)
            self.temp_range = j1, j1

    def has_temp(self):
        j1, j2 = self.temp_range
        return not j1 == j2

    def get_word(self, j):
        # get word which ends at *j*
        model = self.model
        row, col = model.index2position(j)
        text = model.get_text(model.linestart(row), j)
        i = len(text)-1
        while i>=0 and text[i] in string.letters+string.digits+"_.":
            i -= 1
        if j == i:
            return ''
        return text[i+1:]

    complete_count = 0
    def handle_action(self, action, shift=False, memo=None):
        complete_count = self.complete_count
        self.clear_temp()
        if action != 'paste':
            self.log('handle_action', (action, shift,), {})
        else:
            # Paste is a bit tricky to log. We have to make sure,
            # that in the replay situation the exact same material
            # is inserted. Therefore we figure out what has been
            # pasted and log this as an insertion.
            model = self.model
            i = self.index
            if memo is not None:
                self.insert(i, memo)
            else:
                n0 = len(model)
                _WXTextView.handle_action(self, action, shift)
                n = len(model)-n0
                memo = model.copy(i, i+n)
            self.log('handle_action', (action, shift, memo), {})
            return
        if action == 'complete_or_help':
            if complete_count > 0:
                action = 'help'
            else:
                action = 'complete'

        if action == 'split_cell':
            return self.split_cell()
        elif action == 'execute':
            try:
                self.execute()
            except NotFound:
                pass
            return
        if action not in ('complete', 'help'):
            return _WXTextView.handle_action(self, action, shift)
        # complete or help#
        try:
            i0, cell = self.find_cell()
        except NotFound:
            return
        index = self.index
        if index <= i0 or index >= i0+length(cell):
            return
        word = self.get_word(index)
        client = self._clients.get_matching(cell)

        if action == 'help':
            s = client.help(word)
            self.print_temp('\n'+s+'\n')

        elif action == 'complete':
            maxoptions = 50
            options = client.complete(word, maxoptions)
            if not options or list(options) == [word]:
                self.print_temp( "\n[No completion]\n")
                self.complete_count = 1
            else:
                completion = reduce(common, options)[len(word):]
                if completion and len(options) != maxoptions:
                    self.insert_text(index, completion)
                    index += len(completion)
                else:
                    options = list(sorted(options))
                    s = ', '.join(options)
                    if len(options) == maxoptions:
                        s += ' ... '
                    self.print_temp('\n'+s+'\n')
        self.index = index
        self.adjust_viewport()
        
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

    @logged
    def execute(self):
        self.clear_temp()
        i0, cell = self.find_cell()
        if not isinstance(cell, ScriptingCell):
            self.index = i0+length(cell)
            return
        n = length(cell)
        client = self._clients.get_matching(cell)
        stream = Stream()
        result = client.execute(cell.childs[1], stream.output)
        new = self.ScriptingCell(cell.childs[1], stream.model.texel, 
                                 client.counter)
        assert i0>=0
        assert i0+n<=len(self.model)
        infos = []
        infos.append(self._remove(i0, i0+n))
        self.model.insert(i0, mk_textmodel(new))
        infos.append((self._remove, i0, i0+length(new)))
        self.add_undo(infos) 
        self.adjust_viewport()
        return result

    def execute_all(self):
        self.index = 0
        while 1:
            try:
                i, cell = self.find_cell()
            except NotFound:
                break
            self.execute()

    @logged
    def reset_interpreter(self):
        self.init_clients()

    def insert(self, i, textmodel):
        insidecell = False
        try:
            i0, cell = self.find_cell()
            if i0 < i < i0+length(cell):
               insidecell = True
        except NotFound:
            pass
        try:
            find_cell(textmodel.texel, 0)
            hascells = True
        except NotFound:
            hascells = False
        if insidecell:
            if hascells:
                # We can't insert cells inside cells. Therefore we
                # remove all outer cells from what we insert.
                texel = grouped(strip_cells(textmodel.texel))
                _WXTextView.insert(self, i, mk_textmodel(texel))
            else:
                _WXTextView.insert(self, i, textmodel)
        else:
            if hascells:
                _WXTextView.insert(self, i, textmodel)
            else:
                cell = self.ScriptingCell(NULL_TEXEL, NULL_TEXEL)
                _WXTextView.insert(self, i, mk_textmodel(cell))
                _WXTextView.insert(self, i+1, textmodel)

    def undo(self):
        self.clear_temp()
        _WXTextView.undo(self)
                
    def redo(self):
        self.clear_temp()
        _WXTextView.redo(self)

    @logged
    def remove_output(self):
        self.transform(strip_output)

    @logged
    def split_cell(self):
        i = self.index
        self.transform(lambda texel, i=i:split_cell(texel, i))

    def between_cells(self):
        i = self.index
        insidecell = False
        try:
            i0, cell = self.find_cell()
            if i0 < i < i0+length(cell):
               insidecell = True
        except NotFound:
            pass
        return not insidecell

    can_insert_textcell = can_insert_pycell = between_cells

    @logged
    def insert_textcell(self):
        "Insert text cell"
        cell = TextCell(NULL_TEXEL)
        self.insert(self.index, mk_textmodel(cell))

    @logged
    def insert_pycell(self):
        "Insert python cell"
        cell = ScriptingCell(NULL_TEXEL, NULL_TEXEL)
        self.insert(self.index, mk_textmodel(cell))

    set_index = logged(_WXTextView.set_index)
    set_selection = logged(_WXTextView.set_selection)

    ### Simple logging facility ###    
    # It allows to record and replay everything the user
    # enters. Logging is ment for debugging. It will be removed once
    # all errors are fixed :-)

    def log(self, descr, args, kwds):
        if self._logfile is None: 
            return
        import cPickle
        s = cPickle.dumps((descr, args, kwds))
        f = open(self._logfile, 'ab')
        f.write("%i\n" % len(s))
        f.write(s)
        f.close()

    def load_log(self, filename):
        import cPickle
        log = []
        f = open(filename, 'rb')
        while 1:
            l = f.readline()
            if not l:
                break
            n = int(l)
            s = f.read(n)
            name, args, kwds = cPickle.loads(s)
            log.append((name, args, kwds))
        return log
                
    def replay(self, log):
        for name, args, kwds in log:
            f = getattr(self, name)
            f(*args, **kwds)

    def replay_logfile(self, filename):
        log = self.load_log(filename)
        self.replay(log)


def init_testing(redirect=True):
    app = wx.App(redirect=redirect)
    model = TextModel('')

    frame = wx.Frame(None)
    win = wx.Panel(frame)
    view = NBView(win)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)
    
    frame.Show()
    return locals()

def test_00():
    "cell"
    ns = init_testing(False)
    cell = ScriptingCell(Text(u'1234567890'), Text(u'abcdefghij'))
    assert length(cell.input) == 10
    assert length(cell.output) == 10
    assert length(cell) == 23

    texel = grouped(insert(cell, 1, [Text(u'x')]))
    assert get_text(texel)[1:2] == u'x'


def test_02():
    "execute"
    return # XXX skip this for now
    ns = init_testing(False)
    cell = ScriptingCell(Text(u'1+2'), Text(u''))
    cell = cell.execute()
    assert get_text(cell.output) == '3'

    cell = ScriptingCell(Text(u'for a in range(2):\n    print a'),
                         Text(u''))
    cell = cell.execute()
    assert get_text(cell.output) == u'0\n1\n'

    cell = ScriptingCell(Text(u'asdsad'), Text(u''))
    cell = cell.execute()
    
    assert get_text(cell.output) == u'  File "In[3]", line 1, ' \
        'in <module>\nNameError: name \'asdsad\' is not defined\n'

def test_03():
    "find_cell"
    tmp1 = TextModel(u'for a in range(3):\n    print a')
    tmp2 = TextModel(u'for a in range(10):\n    print a')
    cell1 = ScriptingCell(tmp1.texel, Text(u''))
    cell2 = ScriptingCell(tmp2.texel, Text(u''))

    model = TextModel('')
    model.insert(len(model), mk_textmodel(cell1))
    model.insert(len(model), mk_textmodel(cell2))

    assert find_cell(model.texel, 1) == (0, cell1)
    assert find_cell(model.texel, length(cell1)-1) == (0, cell1)

    assert find_cell(model.texel, length(cell1)) == (length(cell1), cell2)
    assert find_cell(model.texel, length(cell1)+5) == (length(cell1), cell2)


def test_04():
    "copy cells"
    model = TextModel('')
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = ScriptingCell(tmp.texel, Text(u''))
    model.insert(len(model), mk_textmodel(cell))
    tmp = model.copy(0, len(model))
    model.insert(0, tmp)


def test_05():
    "CellBox"
    empty = ParagraphStack([])
    cell1 = ScriptingCellBox(empty, empty)
    check_box(cell1.input)
    check_box(cell1)
    #cell1.dump_boxes(0, 0, 0)

    cell2 = ScriptingCellBox(empty, empty)
    check_box(cell2)
    stack = VGroup([cell1, cell2])
    check_box(stack)

    stack = VGroup([])
    check_box(stack)

    t1 = TextBox("0123456789")
    t2 = TextBox("abcdefghij")
    t3 = TextBox("xyz")
    NL = NewlineBox()
    p1 = Paragraph([Row([t1, NL])])
    cell1 = ScriptingCellBox(
        ParagraphStack([Paragraph([Row([t1, NL])]), Paragraph([Row([t2, NL])]),]), 
        ParagraphStack([Paragraph([Row([t3, NL])])]))

    (j1, j2, inp), (k1, k2, outp) = cell1.iter_childs()
    assert (j1, j2) == (1, 23) # input box

    cell2 = ScriptingCellBox(ParagraphStack([Row([t3, NL])]), empty)

    g = VGroup([cell1, cell2])


def test_10():
    "Factory"
    ns = init_testing(False)
    cell = ScriptingCell(Text(u'a'), Text(u'b'))
    factory = Builder(TextModel(''))
    factory._clients.register(PythonClient())
    boxes = factory.create_boxes(cell)
    assert len(boxes) == 1
    cellbox = boxes[0]
    assert len(cellbox) == 5
    assert length(cell) == 5

    check_box(cellbox)
    check_box(cellbox.input)
    check_box(cellbox.output)
    return ns


def test_11():
    ns = init_testing(redirect=False)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'for a in range(16):\n    print a')
    cell = ScriptingCell(tmp.texel, Text(u''))
    model.insert(len(model), mk_textmodel(cell))

    assert model.index2position(0) == (0, 0)
    assert model.index2position(1) == (1, 0)
    cell = model.texel

    assert find_cell(model.texel, 1) == (0, cell)

    view = ns['view']
    view.index = 1
    #print model.texel
    view.execute()

    check_box(view.builder._layout, model.texel)

    #view.layout.dump_boxes(0, 0, 0)
    #assert inside_cell(view.layout, 68, 68)

    #texeltree.dump(model.texel)

    model.insert_text(68, u'x')
    assert model.get_text()[65:71] == '14\nx15'
    #view.layout.dump_boxes(0, 0, 0)
    
    model.remove(68, 69)
    #view.layout.dump_boxes(0, 0, 0)
    assert model.get_text()[65:70] == '14\n15'

    model.insert(0, mk_textmodel(cell))
    model.remove(0, length(cell))

    # insert new cell, insert input
    view.insert(0, TextModel("a=1"))

    # insert output
    view.insert(5, TextModel("x"))

    # remove the complete input-part
    model.remove(1, 4)

    # remove the complete output-part
    model.remove(2,3)
    
    return ns

def test_12():
    ns = init_testing(True)
    model = ns['model']
    model.remove(0, len(model))
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = ScriptingCell(tmp.texel, NULL_TEXEL)
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)

    view = ns['view']
    view.index = 1
    return ns


def test_13():
    ns = init_testing(True)
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
    cell = ScriptingCell(tmp.texel, NULL_TEXEL)
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
    cell = ScriptingCell(tmp.texel, NULL_TEXEL)
    model.insert(len(model), mk_textmodel(cell))

    assert find_cell(model.texel, 1) == (0, cell)

    view = ns['view']
    view.index = 1
    layout = view.builder.get_layout()
    r1 = layout.get_rect(0, 0, 0)
    assert r1.x2-r1.x1 == sepwidth

    r2 = layout.get_cursorrect(0, 0, 0, {})
    r3 = layout.get_cursorrect(len(model), 0, 0, {})
    assert r3.x2-r3.x1 == sepwidth
    assert r3.y1 > r2.y1


def test_15():
    "get_word, print_temp, remove_temp"
    ns = init_testing(False)
    model = ns['model']
    tmp = TextModel(u'for a in range(5):\n    print a')
    cell = ScriptingCell(tmp.texel, NULL_TEXEL)
    model.insert(len(model), mk_textmodel(cell))
    view = ns['view']
    assert view.get_word(12) == 'ra'

    text = model.get_text()
    view.index = 12
    view.print_temp('\n[raise range raw_input]\n')
    #print model.get_text()

    view.clear_temp()
    assert model.get_text() == text


def test_16():
    "Graphics"
    ns = init_testing(False)
    model = ns['model']
    model.insert(len(model), mk_textmodel(Graphics([])))
    view = ns['view']


def test_17():    
    "parstyle"
    model = TextModel('')
    tmp = TextModel(u'Line 1\nLine 2\nLine 3')
    cell = TextCell(tmp.texel)
    model.insert(len(model), mk_textmodel(cell))
    i0 = 0
    i1 = model.linestart(1)
    i2 = model.linestart(2)
    #print i0, i1, i2
    assert model.get_parstyle(i0) == {}
    assert model.get_parstyle(i1) == {}
    assert model.get_parstyle(i2) == {}
    #dump(model.texel)
    #print
    model.set_parproperties(i1, i2, bullet = True)
    #dump(model.texel)
    assert model.get_parstyle(i0) == {}
    assert model.get_parstyle(i1) == {'bullet':True}
    assert model.get_parstyle(i2) == {}
    

def demo_00():
    from .wxtextview import testing
    ns = test_11()
    testing.pyshell(ns)
    ns['app'].MainLoop()


def demo_01():
    from .wxtextview import testing
    ns = test_13()
    testing.pyshell(ns)
    ns['app'].MainLoop()


