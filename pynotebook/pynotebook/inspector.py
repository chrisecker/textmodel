# -*- coding: latin-1 -*-


import wx
import  wx.lib.colourselect as  csel
import  wx.lib.rcsizer  as rcs

from .textmodel.viewbase import ViewBase
from .textmodel.texeltree import EMPTYSTYLE
from .textmodel.styles import create_style
from .wxtextview.wxdevice import defaultstyle



class Inspector(wx.Frame, ViewBase):
    def __init__(self, *args, **kwds):
        ViewBase.__init__(self)
        wx.Frame.__init__(self, *args, title='Text format',
                          style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
                               |wx.FRAME_TOOL_WINDOW, **kwds)
        sizer1 = wx.BoxSizer( wx.VERTICAL )
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.SetBackgroundColour(panel.BackgroundColour)
        sizer2 = wx.BoxSizer(wx.VERTICAL)

        e = wx.FontEnumerator()
        e.EnumerateFacenames()
        faces = sorted(e.GetFacenames())
        self.faces = ['']+faces
        self.fontface = wx.Choice(
            panel, choices=['<default font>']+faces)
        self.fontface.Bind(wx.EVT_CHOICE, self.on_face)

        sizer2.Add(self.fontface, 0, wx.ALL|wx.EXPAND, 5)
        sizer3 = wx.BoxSizer(wx.VERTICAL)

        choices = map(str, (8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 26, 30))

        fun = lambda e:self.set_properties(fontsize=int(self.size.GetValue()))
        self.size = wx.ComboBox(
            panel, value = "12", choices=choices,
            style = wx.CB_DROPDOWN| wx.TE_PROCESS_ENTER
        )
        self.size.SetMinSize((100, -1))
        for binder in wx.EVT_TEXT_ENTER, wx.EVT_KILL_FOCUS, wx.EVT_COMBOBOX:
            self.size.Bind(binder, fun)
        sizer3.Add(self.size, 0, wx.ALL|wx.EXPAND, 5)

        sizer4 = wx.BoxSizer(wx.HORIZONTAL )
        self.fgcolor = csel.ColourSelect(panel, -1)
        sizer4.Add(self.fgcolor, 1, wx.ALL, 5)
        self.fgcolor.Bind(
            csel.EVT_COLOURSELECT,
            lambda e:self.set_properties(
                textcolor=self.fgcolor.GetValue().GetAsString()))

        self.bgcolor = csel.ColourSelect(panel, -1)
        sizer4.Add(self.bgcolor, 1, wx.ALL, 5)
        self.bgcolor.Bind(
            csel.EVT_COLOURSELECT,
            lambda e:self.set_properties(
                bgcolor=self.bgcolor.GetValue().GetAsString()))

        sizer3.Add(sizer4, 0, wx.EXPAND, 5)

        self.underline = wx.CheckBox(panel, -1, "Underline")
        sizer3.Add( self.underline, 0, wx.ALL|wx.EXPAND, 5 )
        self.underline.Bind(
            wx.EVT_CHECKBOX,
            lambda e:self.set_properties(underline=self.underline.GetValue()))

        self.bold = wx.CheckBox(panel, -1, "Bold")
        sizer3.Add( self.bold, 0, wx.ALL|wx.EXPAND, 5 )
        self.bold.Bind(
            wx.EVT_CHECKBOX,
            lambda e:self.set_properties(bold=self.bold.GetValue()))

        self.italic = wx.CheckBox(panel, -1, "Italic")
        sizer3.Add( self.italic, 0, wx.ALL|wx.EXPAND, 5 )
        self.italic.Bind(
            wx.EVT_CHECKBOX,
            lambda e:self.set_properties(italic=self.italic.GetValue()))

        button = wx.Button(panel, -1, "Clear")
        button.Bind(wx.EVT_BUTTON, self.on_clear)
        sizer3.Add( button, 0, wx.ALL, 5 )


        sizer2.Add( sizer3, 1, wx.ALL|wx.EXPAND, 5 )

        panel.SetSizer( sizer2 )
        panel.Layout()
        sizer2.Fit( panel )
        sizer1.Add( panel, 1, wx.EXPAND |wx.ALL, 5 )

        self.SetSizer( sizer1 )
        self.Layout()
        sizer1.Fit( self )


    def index_changed(self, textview):
        self.update()

    def selection_changed(self, textview):
        self.update()

    def on_clear(self, event):
        textview = self.model
        i1, i2 = sorted(textview.selection)
        textview.clear_styles(i1, i2)

    def on_face(self, event=None):
        i = self.fontface.Selection
        facename = self.faces[i]
        self.set_properties(facename = facename)

    def set_properties(self, **properties):
        textview = self.model
        i1, i2  = sorted(textview.selection)
        textview.set_properties(i1, i2, **properties)

    def update(self):
        textview = self.model
        index = textview.index
        textmodel = textview.model
        style = defaultstyle.copy()
        style.update(textmodel.get_parstyle(index))
        style.update(textmodel.get_style(max(0, index-1)))
        face = style['facename']
        i = self.faces.index(face)
        self.fontface.Selection = i
        self.fgcolor.SetValue(style['textcolor'])
        self.bgcolor.SetValue(style['bgcolor'])
        self.underline.SetValue(style['underline'])
        self.italic.SetValue(style['italic'])
        self.bold.SetValue(style['bold'])
        self.size.SetValue(str(style['fontsize']))


class ParagraphSettings:
    title = 'Paragraph'
    style = EMPTYSTYLE
    bullets = False
    enumeration = False # is this an enumerated element?
    section = False     # is this a section change?
    align = 'left'


class HeadingSettings(ParagraphSettings):
    title = 'Heading'
    section = True
    style = create_style(
        fontsize = 16,
        facename = 'Courier',
        weight = 'bold'
        )


class ListSettings(ParagraphSettings):
    title = 'List'
    enumeration = True


def demo_00():
    from .nbview import NBView
    from .nbtexels import TextCell, NULL_TEXEL, mk_textmodel
    app = wx.App(redirect=True)
    frame = wx.Frame(None)
    win = wx.Panel(frame)
    view = NBView(win)
    cell = TextCell(NULL_TEXEL)
    view.model.insert(0, mk_textmodel(cell))
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)
    inspector = Inspector(None)
    inspector.model = view
    inspector.Show()
    
    frame.Show()
    app.MainLoop()
