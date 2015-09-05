# -*- coding: latin-1 -*-

import wx


# Device Infos
#
# Stattdessen k�nnte man auch:
# - ein Interface f�r den GC einrichten und
# - eine Font-Information an die Boxen weitergeben
#
# - man k�nnte auch wieder die Factory an die Boxen �bergeben. Das
#   macht die Boxen aber wieder von einer bestimmten Umgebung
#   abh�ngig.

def invert_rect_INV(self, x, y, w, h, dc):
    dc.SetLogicalFunction(wx.INVERT)
    dc.SetBrush(wx.BLACK_BRUSH)
    dc.DrawRectangle(x, y, w, h)


def invert_rect_BLIT(self, x, y, w, h, dc):
    dc.Blit(x, y, w, h, dc, x, y, wx.SRC_INVERT)


def measure_win(self, text, style):
    font = wx.Font(style['fontsize'], wx.MODERN, wx.NORMAL, wx.NORMAL,
                   style['underline'], style['facename'])
    dc = wx.MemoryDC()
    dc.SetFont(font)
    w, h = dc.GetTextExtent(text)
    return w, h


def measure_mac(self, text, style):
    font = wx.Font(style['fontsize'], wx.MODERN, wx.NORMAL, wx.NORMAL,
                   style['underline'], style['facename'])
    gc = wx.GraphicsContext_CreateMeasuringContext()
    gc.SetFont(font)
    w, h = gc.GetTextExtent(text)
    return w, h


def measure_gtk(self, text, style):
    # gc gibt auf gtk falsche Metriken! Wir verwenden daher den dc
    text = text.replace('\n', ' ') # sonst gibt es bei gtk doppelzeiligen Text
    font = wx.Font(style['fontsize'], wx.MODERN, wx.NORMAL, wx.NORMAL,
                   style['underline'], style['facename'])
    dc = wx.MemoryDC()
    dc.SetFont(font)
    w, h = dc.GetTextExtent(text)
    return w, h


def measure_parts_win(self, text, style):
    font = wx.Font(style['fontsize'], wx.MODERN, wx.NORMAL, wx.NORMAL,
                   style['underline'], style['facename'])
    dc = wx.MemoryDC()
    dc.SetFont(font)
    return dc.GetPartialTextExtents(text)


def measure_parts_gtk(self, text, style):
    font = wx.Font(style['fontsize'], wx.MODERN, wx.NORMAL, wx.NORMAL,
                   style['underline'], style['facename'])
    dc = wx.MemoryDC()
    dc.SetFont(font)
    return dc.GetPartialTextExtents(text)


def measure_parts_mac(self, text, style):
    font = wx.Font(style['fontsize'], wx.MODERN, wx.NORMAL, wx.NORMAL,
                   style['underline'], style['facename'])
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
        measure = measure_gtk
        measure_parts = measure_parts_gtk
        buffering = True
    elif 'mac' in wx.version():
        invert_rect = invert_rect_INV
        measure = measure_mac
        measure_parts = measure_parts_mac
        buffering = False


