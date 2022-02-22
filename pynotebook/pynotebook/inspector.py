# -*- coding: latin-1 -*-


import wx
import wx.lib.colourselect as csel

from .textmodel.viewbase import ViewBase
from .textmodel.texeltree import EMPTYSTYLE
from .textmodel.styles import create_style
from .wxtextview.wxdevice import defaultstyle



class Inspector(wx.Frame, ViewBase):
    sizes = (8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 26, 30)
    def __init__(self, *args, **kwds):
        ViewBase.__init__(self)
        wx.Frame.__init__(self, *args, title='Text format',
                          style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
                               |wx.FRAME_TOOL_WINDOW, **kwds)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy) 
        sizer1 = wx.BoxSizer( wx.VERTICAL )
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.SetBackgroundColour(panel.BackgroundColour)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.basestyle = wx.Choice(panel)
        self.basestyle.Bind(wx.EVT_CHOICE, self.on_basestyle)
        sizer2.Add(self.basestyle, 0, wx.ALL|wx.EXPAND, 5)
        sizer3 = wx.BoxSizer(wx.VERTICAL)

        choices = list(map(str, self.sizes))

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

    def on_destroy(self, event):
        self.destroy()

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

    def on_basestyle(self, event=None):
        textview = self.model
        textmodel = textview.model
        i1, i2  = sorted(textview.selection)

        # Ineffiziente Art, den nächsten NL zu finden
        row, col = textmodel.index2position(i2)
        tmp = textmodel.lineend(row)
        i2 = tmp+1
        
        stylesheet = textview.builder.stylesheet
        i = self.basestyle.Selection
        name = self._stylenames[i]

        textview.set_parproperties(i1, i2, base=name)
        
    def set_properties(self, **properties):        
        textview = self.model
        if not textview.has_selection():
            return
        i1, i2  = sorted(textview.selection)
        textview.set_properties(i1, i2, **properties)

    _stylenames = ()
    def update(self):
        textview = self.model
        index = textview.index
        textmodel = textview.model
        stylesheet = textview.builder.stylesheet
        parstyle = textmodel.get_parstyle(index)
        style = defaultstyle.copy()
        style.update(textmodel.get_parstyle(index))
        style.update(textmodel.get_style(max(0, index-1)))
        stylenames = sorted(stylesheet.keys())
        if stylenames != self._stylenames:            
            self.basestyle.SetItems(stylenames)
            self._stylenames = stylenames
        i = self._stylenames.index(parstyle.get('base', 'normal'))
        self.basestyle.SetSelection(i)        
        self.fgcolor.SetValue(style['textcolor'])
        self.bgcolor.SetValue(style['bgcolor'])
        self.underline.SetValue(style['underline'])
        self.italic.SetValue(style['italic'])
        self.bold.SetValue(style['bold'])
        self.size.SetValue(str(style['fontsize']))



def demo_00():
    from .nbview import NBView    
    from .nbtexels import TextCell, NULL_TEXEL, mk_textmodel, TextModel
    from .textmodel.texeltree import T
    
    app = wx.App(redirect=True)
    frame = wx.Frame(None)
    win = wx.Panel(frame)
    view = NBView(win)
    text = TextModel(u"Some\ntext\n...").texel
    cell = TextCell(text)
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
