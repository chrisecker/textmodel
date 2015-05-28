# -*- coding: latin-1 -*-



def pyshell(namespace=None):
    import wx.py
    style = wx.DEFAULT_FRAME_STYLE 
    f = wx.Frame(None,
                 pos=wx.DefaultPosition,
                 style=style
                 )
    f.Bind(wx.EVT_CLOSE, lambda e: f.Hide())
    box = wx.BoxSizer(wx.HORIZONTAL)
    if namespace is None:
        namespace = {}
    shell = wx.py.shell.Shell(
        f, -1, locals=namespace,                  
        size=(1000, 200),
        )
    f.shell = shell
    box.Add(shell, 1, wx.EXPAND)
    f.SetSizer(box)
    box.Fit(f)
    f.Fit()
    f.Show()




    
