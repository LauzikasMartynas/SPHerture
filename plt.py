import wx
import numpy as np
import matplotlib
matplotlib.use('WXAgg', force=True)
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx

class hist(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.pos = parent.h5_data.get_pos()
        self.rho = parent.h5_data.get_the('Density')
        self.CreateCtrls()
        self.DoLayout()
        self.Draw()
        self.Show()

    def CreateCtrls(self):
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)

        self.canvas = FigureCanvas(self, -1, self.figure)

        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()

    def DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.RIGHT | wx.GROW)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()

    def Draw(self):
        self.axes.hist(self.rho, bins=100)
