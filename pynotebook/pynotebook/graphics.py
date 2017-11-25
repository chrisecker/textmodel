# -*- coding:utf-8 -*-

#
# graphics.py
#
#
# This module defines graphics operations which are used in connection
# with the 'Graphics'-Texel. Each instance of an operations definies a
# certain graphical object (e.g. a line or circle) or sets certain
# drawing properties (.e.g. line color or fill color).
#
# Lists of graphic operations represent a vector graphic. They can be
# saved, loaded or displayed.


# XXX missing: 
# - SetLogicalFunction
# - fill styles
# - gradient fills
# - rounded rectangle
# - clipping
# - spline


import wx
from .nbtexels import Graphics



def _normalize_color(color):
    if isinstance(color, wx.Colour):
        return color.asTuple()+(color.Alpha(), )
    elif isinstance(color, str):
        c = wx.Colour()
        c.SetFromString(color)
        return tuple(c,)+(c.Alpha(), )
    elif isinstance(color, list) or isinstance(color, tuple):
        return tuple(color)
    else:
        raise ValueError('Not a valid color specification: %s' % repr(color))


class LineColor:
    def __init__(self, color):
        self.color = _normalize_color(color)
        
    def draw(self, gc, state):
        pen = state["pen"]
        pen.SetColour(self.color)
        gc.SetPen(pen)


class LineWidth:
    def __init__(self, width):
        self.width = width
        
    def draw(self, gc, state):
        pen = state["pen"]
        pen.SetWidth(self.width)
        gc.SetPen(pen)


class LineDashes:
    # Dashes is a list of length values. Example: [5, 5] will draw a
    # line of length 5, a space of length 5, a line of length 5, ...
    def __init__(self, dashes):
        self.dashes = dashes
        
    def draw(self, gc, state):
        pen = state["pen"]
        pen.SetDashes(self.dashes)
        gc.SetPen(pen)

line_joins = dict(
    bevel=wx.JOIN_BEVEL, miter=wx.JOIN_MITER, round=wx.JOIN_ROUND)

class LineJoin:
    def __init__(self, join_style):
        if not join_style in line_joins:
            raise ValueError("join_style mus be 'bevel, 'miter or 'round'")
        self.join_style = join_style
        
    def draw(self, gc, state):
        pen = state["pen"]
        pen.SetJoin(line_joins[self.join_style])
        gc.SetPen(pen)


line_caps = dict(
    round=wx.CAP_ROUND, projecting=wx.CAP_PROJECTING, butt=wx.CAP_BUTT)

class LineCap:
    def __init__(self, cap_style):
        if not cap_style in line_caps:
            raise ValueError("cap_style mus be 'round', 'projecting' or 'butt'")
        self.cap_style = cap_style
        
    def draw(self, gc, state):
        pen = state["pen"]
        pen.SetCap(line_caps[self.cap_style])
        gc.SetPen(pen)

        
class FillColor:
    def __init__(self, color):
        self.color = _normalize_color(color)
        
    def draw(self, gc, state):
        brush = state["brush"]
        brush.SetColour(self.color)
        brush.SetStyle(wx.BRUSHSTYLE_SOLID)
        gc.SetBrush(brush) 


class Dot: # remove this?
    def __init__(self, (x, y)):
        self.x = x
        self.y = y

    def draw(self, gc, state):
        p = gc.CreatePath()
        p.AddCircle(self.x, self.y, 5)
        p.Transform(state['matrix'])
        gc.DrawPath(p)


class Line:
    def __init__(self, *points):
        self.points = tuple(points)

    def draw(self, gc, state):
        points = self.points
        if len(points)<2:
            return
        p = gc.CreatePath()
        for point in points:
            p.AddLineToPoint(point)
        p.Transform(state['matrix'])
        gc.DrawPath(p)


# class Spline:
#     def __init__(self, *points):
#         self.points = tuple(points)
#
#     def draw(self, gc, state):
#         gc.DrawSpline(self.points)
#         # XXX TODO


class Polygon:
    def __init__(self, *points):
        self.points = tuple(points)
        # XXX should we be able to set the fill rule?

    def draw(self, gc, state):
        points = self.points
        if len(points)<2:
            return
        p = gc.CreatePath()
        for point in points:
            p.AddLineToPoint(point)
        p.CloseSubpath()
        p.Transform(state['matrix'])
        gc.DrawPath(p)


class Circle:
    def __init__(self, (x, y), r):
        self.x = x
        self.y = y
        self.r = r
        
    def draw(self, gc, state):
        p = gc.CreatePath()
        p.AddCircle(self.x, self.y, self.r)
        p.Transform(state['matrix'])
        gc.DrawPath(p)


class Ellipse:
    def __init__(self, (x, y), r1, r2):
        self.x = x
        self.y = y
        self.r1 = r1
        self.r2 = r2
        
    def draw(self, gc, state):
        p = gc.CreatePath()
        p.AddEllipse(self.x, self.y, self.r1, self.r2)
        p.Transform(state['matrix'])
        gc.DrawPath(p)

        

class Arc:
    def __init__(self, (x, y), r, start, end):
        self.x = x
        self.y = y
        self.r = r
        self.start = start
        self.end = end
        # XXX do we need clockwise?
        
    def draw(self, gc, state):
        p = gc.CreatePath()
        p.AddArc(self.x, self.y, self.r, self.start, self.end)
        p.Transform(state['matrix'])
        gc.DrawPath(p)



class Rectangle:
    def __init__(self, (x1, y1), (x2, y2)):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        
    def draw(self, gc, state):
        x = min(self.x1, self.x2)
        w = max(self.x1, self.x2)-x
        y = min(self.y1, self.y2)
        h = max(self.y1, self.y2)-y        
        p = gc.CreatePath()
        p.AddRectangle(x, y, w, h)
        p.Transform(state['matrix'])
        gc.DrawPath(p)

        

class Font:
    def __init__(self, size, family, style, weight, 
                 underline=False, face="", 
                 encoding=wx.FONTENCODING_DEFAULT):
        self.size = size
        self.family = family
        self.style = style
        self.weight = weight
        self.underline = underline
        self.face = face
        self.encoding = encoding
        
    def draw(self, gc, state):
        font = wx.Font(self.size, self.family, self.style,
                       self.weight, self.underline, 
                       self.face, self.encoding)
        gc.SetFont(font)


class Text:
    regname = 'GraphicsText'
    def __init__(self, text, point, align=(0, 0)):
        self.text = text
        self.point = point
        self.align = align
        
    def draw(self, gc, state):
        x, y = self.point
        w, h = gc.GetTextExtent(self.text)
        dx = 0.5*w*(self.align[0]-1)
        dy = 0.5*h*(self.align[1]-1)
        gc.SetTransform(state['matrix'])
        gc.DrawText(self.text, x+dx, y+dy)
        gc.SetTransform(state['trafo'])


class Translate:
    def __init__(self, offset):
        self.offset = offset
        
    def draw(self, gc, state):
        dx, dy = self.offset
        state['matrix'].Translate(dx, dy) 
        #gc.Translate(dx, dy)


class Rotate:
    def __init__(self, angle):
        self.angle = angle
        
    def draw(self, gc, state):
        state['matrix'].Rotate(self.angle) 


class Scale:
    def __init__(self, fx, fy=None):
        if fy is None:
            fy = fx
        self.fx = fx
        self.fy = fy
        
    def draw(self, gc, state):
        state['matrix'].Scale(self.fx, self.fy)



def register_classes():
    from cerealizerformat import register
    import types
    for name, value in globals().items():
        if type(value) is types.ClassType:
            if hasattr(value, 'regname'):
                register(value, classname=value.regname)
            else:
                register(value)


def init_testing(redirect=True):
    import wx
    from .nbview import TextModel, NBView
    app = wx.App(redirect=redirect)
    model = TextModel('')

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = NBView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()
    return locals()

def test_00():
    "Graphics"
    from .nbview import mk_textmodel
    ns = init_testing(False)
    model = ns['model']
    model.insert(len(model), mk_textmodel(Graphics([Circle((0, 0), 5)])))
    segments = [
        (0, 0), (0, 10), (10, 10), (10, 0)
    ]
    l = Line(*segments)
    model.insert(len(model), mk_textmodel(Graphics([l])))
    return ns


    
def demo_00():
    import wx
    from .wxtextview import testing
    ns = test_00()
    testing.pyshell(ns)
    py = ns['view']._clients._clients['direct python']
    py.namespace.update(
        dict(Graphics=Graphics, Dot=Dot, Line=Line))
    ns['app'].MainLoop()





