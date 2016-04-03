# -*- coding: latin-1 -*-


import sys
sys.path.insert(0, '..')

import wx
import  wx.lib.colourselect as  csel

from pynotebook.textmodel.viewbase import ViewBase
from pynotebook.textmodel import TextModel




class Inspector(wx.Frame, ViewBase):
    def __init__(self, *args, **kwds):
        ViewBase.__init__(self)
        wx.Frame.__init__(self, *args, title='Inspector',
                          style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
                               |wx.FRAME_TOOL_WINDOW, **kwds)
        sizer1 = wx.BoxSizer( wx.VERTICAL )
        #self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
        panel = wx.Panel(self)
        panel.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
        self.SetBackgroundColour(panel.BackgroundColour)
        sizer2 = wx.BoxSizer( wx.VERTICAL )

        sizer3 = wx.StaticBoxSizer( wx.StaticBox( panel, wx.ID_ANY, u"Style" ), wx.VERTICAL )

        choices = map(str, (8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 26, 30))

        fun = lambda e:self.set_properties(fontsize=int(self.size.GetValue()))
        self.size = wx.ComboBox(
            panel, value = "12", choices=choices,
            style = wx.CB_DROPDOWN| wx.TE_PROCESS_ENTER
        )
        self.size.SetMinSize((100, -1))
        for binder in wx.EVT_TEXT_ENTER, wx.EVT_KILL_FOCUS, wx.EVT_COMBOBOX:
            self.size.Bind(binder, fun)
        sizer3.Add( self.size, 0, wx.ALL|wx.EXPAND, 5 )

        self.fgcolor = csel.ColourSelect(panel, -1)
        self.bgcolor = csel.ColourSelect(panel, -1)
        sizer4 = wx.BoxSizer( wx.HORIZONTAL )
        sizer4.Add( self.fgcolor, 1, wx.ALL, 5 )
        sizer4.Add( self.bgcolor, 1, wx.ALL, 5 )
        sizer3.Add( sizer4, 0, wx.EXPAND, 5 )

        self.fgcolor.Bind(
            csel.EVT_COLOURSELECT,
            lambda e:self.set_properties(textcolor=self.fgcolor.GetValue()))
        self.bgcolor.Bind(
            csel.EVT_COLOURSELECT,
            lambda e:self.set_properties(bgcolor=self.bgcolor.GetValue()))

        self.underline = wx.CheckBox(panel, -1, "Underline")
        sizer3.Add( self.underline, 0, wx.ALL|wx.EXPAND, 5 )

        self.underline.Bind(
            wx.EVT_CHECKBOX,
            lambda e:self.set_properties(underline=self.underline.GetValue()))

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


    def on_clear(self, event):
        textview = self.model
        textmodel = self.model.model
        selection = textview.selection
        i1, i2 = sorted(selection)
        textmodel.clear_styles(i1, i2)

    def index_changed(self, textview):
        self.update()

    def selection_changed(self, textview):
        self.update()

    def on_paragraph(self, event=None):
        i = self.paragraph.Selection
        setting = self.paragraph_settings[i]()
        textmodel = self.model.model
        #textmodel.set_paragraphsettings(self.model.index, setting)
        for i1, i2 in self.model.get_selected():
            textmodel.apply_paragraphsettings(i1, i2, setting)

    def set_properties(self, **properties):
        textview = self.model
        textmodel = self.model.model
        selection = textview.selection
        i1, i2 = sorted(selection)
        textmodel.set_properties(i1, i2, **properties)

    def update(self):
        import sys
        self.stderr = sys.stderr
        textview = self.model
        index = textview.index
        textmodel = textview.model
        if index>0:
            style = textmodel.get_style(index-1)
        else:
            # we query the style from the extended texel, because this
            # will work even for emtpy texts
            style = textmodel.get_xtexel().get_style(index)
        self.fgcolor.SetValue(style['textcolor'])
        self.bgcolor.SetValue(style['bgcolor'])
        self.underline.SetValue(style['underline'])
        self.size.SetValue(str(style['fontsize']))




def demo_00():
    from pynotebook.nbview import TextModel, NBView
    from pynotebook.nbtexels import TextCell, mk_textmodel

    app = wx.App(redirect=False)

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = NBView(win, -1, style=wx.SUNKEN_BORDER)
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()
    model = view.model
    cell = TextCell(TextModel('This is a text cell!').texel)
    print len(cell), cell.weights
    cell.dump()
    model.insert(0, mk_textmodel(cell))

    inspector = Inspector(frame)
    inspector.model = view
    inspector.Show()

    if 1:
        from pynotebook.wxtextview import testing
        testing.pyshell(locals())

    app.MainLoop()

if __name__ == '__main__':
    demo_00()
