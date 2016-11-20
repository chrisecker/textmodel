# -*- coding: latin-1 -*-

import wx


defaultstyle = dict(
    fontsize=10, bgcolor='white', textcolor='black', 
    underline=False, facename='', italic=False, bold=False)


def filled(style, defaultstyle=defaultstyle):
    # fill empty properties with default values
    new = defaultstyle.copy()
    new.update(style)
    return new


def invert_rect_INV(self, x, y, w, h, dc):
    if 1:
        dc.SetLogicalFunction(wx.INVERT)
        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.TRANSPARENT_PEN)
    else:
        # Alternative which gives a light blue selection: 
        dc.SetLogicalFunction(wx.XOR)
        dc.SetBrush(wx.RED_BRUSH)
    dc.DrawRectangle(x, y, w, h)


def invert_rect_BLIT(self, x, y, w, h, dc):
    dc.Blit(x, y, w, h, dc, x, y, wx.SRC_INVERT)


def get_font(style):
    weight = {False : wx.FONTWEIGHT_NORMAL,
              True : wx.FONTWEIGHT_BOLD}[style.get('bold', False)]
    slant = {False : wx.FONTSTYLE_NORMAL,
              True : wx.FONTSTYLE_ITALIC}[style.get('italic', False)]

    family = dict(
        roman = wx.FONTFAMILY_ROMAN,
        modern = wx.FONTFAMILY_MODERN, 
        swiss = wx.FONTFAMILY_SWISS,        
    )[style.get('family', 'modern')]
    return wx.Font(
        style['fontsize'], family, slant, weight,
        style['underline'], style['facename'])


# Profiling revelead that a lot of time is spent in the measure_*
# functions. We therefore cache the results in a fixed size dict. This
# reduces the time spent by ~90%.
_cache = dict()
_cache_keys = []

def measure_win(self, text, style):
    key = text, tuple(style.items())
    try:
        return _cache[key]
    except:
        pass
    style = filled(style)
    font = get_font(style)
    dc = wx.MemoryDC()
    dc.SetFont(font)
    w, h = dc.GetTextExtent(text)
    _cache[key] = w, h
    _cache_keys.insert(0, key)
    if len(_cache_keys) > 1000:
        _key = _cache_keys.pop()
        del _cache[key]        
    return w, h

def measure_mac(self, text, style):
    key = text, tuple(style.items())
    try:
        return _cache[key]
    except:
        pass
    style = filled(style)
    font = get_font(style)
    gc = wx.GraphicsContext_CreateMeasuringContext()
    gc.SetFont(font)
    w, h = gc.GetTextExtent(text)
    _cache[key] = w, h
    _cache_keys.insert(0, key)
    if len(_cache_keys) > 1000:
        _key = _cache_keys.pop()
        del _cache[key]        
    return w, h

def measure_gtk(self, text, style):
    key = text, tuple(style.items())
    try:
        return _cache[key]
    except:
        pass
    style = filled(style)
    text = text.replace('\n', ' ') # replace newlines to avoid double lines
    font = get_font(style)
    # GC returns wrong font metric values in gtk! We therefore use the DC.  
    dc = wx.MemoryDC()
    dc.SetFont(font)
    w, h = dc.GetTextExtent(text)
    _cache[key] = w, h
    _cache_keys.insert(0, key)
    if len(_cache_keys) > 1000:
        _key = _cache_keys.pop()
        del _cache[key]        
    return w, h


def measure_parts_win(self, text, style):
    style = filled(style)
    font = get_font(style)
    dc = wx.MemoryDC()
    dc.SetFont(font)
    return dc.GetPartialTextExtents(text)


def measure_parts_gtk(self, text, style):
    style = filled(style)
    font = get_font(style)
    dc = wx.MemoryDC()
    dc.SetFont(font)
    return dc.GetPartialTextExtents(text)


def measure_parts_mac(self, text, style):
    style = filled(style)
    font = get_font(style)
    gc = wx.GraphicsContext_CreateMeasuringContext()
    gc.SetFont(font)
    return gc.GetPartialTextExtents(text)


class WxDevice:
    def intersects(self, dc, rect):
        r = wx.Rect(rect.x1, rect.y1, rect.x2-rect.x1, rect.y2-rect.y1)
        return dc.ClippingRect.Intersects(r)

    def draw_text(self, text, x, y, dc):
        dc.DrawText(text, x, y)

    if "msw" in wx.version():
        invert_rect = invert_rect_BLIT
        measure = measure_win
        measure_parts = measure_parts_win
        buffering = True
    elif "gtk" in wx.version():
        invert_rect = invert_rect_BLIT
        #invert_rect = invert_rect_INV
        measure = measure_gtk
        measure_parts = measure_parts_gtk
        buffering = True
    elif 'mac' in wx.version():
        invert_rect = invert_rect_INV
        measure = measure_mac
        measure_parts = measure_parts_mac
        buffering = False



class DCStyler:
    last_style = None
    def __init__(self, dc):
        self.dc = dc
        
    def set_style(self, style):
        if style is self.last_style:
            return
        self.last_style = style

        _style = filled(style)
        font = get_font(_style)
        self.dc.SetFont(font)            
        try: # Phoenix
            self.dc.SetTextBackground(wx.Colour(_style['bgcolor']))
            self.dc.SetTextForeground(wx.Colour(_style['textcolor']))
        except TypeError: # Classic
            self.dc.SetTextBackground(wx.NamedColour(_style['bgcolor']))
            self.dc.SetTextForeground(wx.NamedColour(_style['textcolor']))


