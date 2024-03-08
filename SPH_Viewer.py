import wx
import numpy as np
import matplotlib
matplotlib.use('WXAgg', force=True)
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx

import multiprocessing as mp

#from MyOpenGL import GLCanvas
from Julia import JuliaSet
from hdf5 import H5Data
from display import DisplayPanel
from plt import hist

class JuliaPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create a placement style for widgets
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create canvas for OpenGL
        #self.canvas = GLCanvas(self)
        # Add widget
        #box_sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND, 5)

        self.bitmap = wx.Bitmap()
        self.julia = JuliaSet()
        self.img_ctrl = wx.StaticBitmap(self, bitmap=self.bitmap)
        box_sizer.Add(self.img_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        # Arrange placement style
        self.SetSizer(box_sizer)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.julia_zoom, self.timer)
        
        self.timer2 = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.julia_rot, self.timer2)

        self.Bind(wx.EVT_MOTION, self.OnMouseMove)

        self.Bind(wx.EVT_SIZE, self.OnChange)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPress)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)

    def OnLeftDown(self, event):
        self.mouse_pos_init = event.GetPosition()

    def OnMouseMove(self, event):
        self.mouse_pos_current = event.GetPosition()
        if event.LeftIsDown():
            size = self.GetSize()
            delta = self.mouse_pos_current - self.mouse_pos_init
            self.julia.shift(delta, size)
            self.mouse_pos_init = self.mouse_pos_current
            self.OnChange()

    def julia_zoom(self, event):
        self.julia.set_zoom(1.005)
        self.OnChange()

    def julia_rot(self, event):
        self.julia.set_rot(0.005)
        self.OnChange()

    def OnKeyPress(self, event):
        keycode = event.GetUnicodeKey()
        if keycode in [90, 122]:
            if self.timer.IsRunning():
                self.timer.Stop()
            else:
                self.timer.Start(100)
        if keycode in [88, 120]:
            if self.timer2.IsRunning():
                self.timer2.Stop()
            else:
                self.timer2.Start(50)

    def OnChange(self, evt=None):
        size = self.Size
        self.bitmap = wx.Bitmap.FromBuffer(size[0], size[1],
            self.julia.get_julia_jit(size[0], size[1]))
        self.Refresh()

    def OnPaint(self, evt=None):
        dc = wx.PaintDC(self)
        try:
            dc.DrawBitmap(self.bitmap, 0, 0)
        except ValueError:  # in case bitmap has not yet been initialized
            pass

class SecondaryFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title='Scatter plot')
        self.h5_data = parent.h5_data
        
        self.SetMinSize(self.GetSize())

        self.box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.image_panel = DisplayPanel(self)
        
        self.box_sizer.Add(self.image_panel, 1, wx.EXPAND|wx.ALL, 1)
        
        self.control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.slider = wx.Slider(self, value=20, minValue=0, maxValue=40)
        self.control_sizer.Add(wx.StaticText(self, label='Hue:'), 0, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.slider, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        #self.text = wx.StaticText(self, label=str(self.slider.GetValue()))
        #self.control_sizer.Add(self.text, wx.ALIGN_CENTER|wx.ALL, 5)
        
        self.check_sizer = wx.BoxSizer(wx.VERTICAL)
        self.check1 = wx.CheckBox(self, label='Smoothing')
        self.check1.SetValue(False)
        self.check_sizer.Add(self.check1, wx.ALIGN_CENTER)
        self.check2 = wx.CheckBox(self, label='Log')
        self.check_sizer.Add(self.check2, wx.ALIGN_CENTER)
        
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.check_sizer, 0, wx.ALIGN_CENTER)
        
        self.box_sizer.Add(self.control_sizer, 0, wx.ALIGN_CENTER)
        
        self.slider.Bind(wx.EVT_SCROLL, self.OnScroll)
        self.check1.Bind(wx.EVT_CHECKBOX, self.OnCheck1)
        self.check2.Bind(wx.EVT_CHECKBOX, self.OnCheck2)
        
        self.SetSizer(self.box_sizer)
        
        self.init_controls()
        
        self.image_panel.Bind(wx.EVT_KEY_DOWN, self.OnKeyPress)
        
        self.Show()
        
        
    def OnKeyPress(self, event):
        keycode = event.GetUnicodeKey()
        if keycode in [76, 108]:
            self.h5_data.switch_log()

        if keycode in [68, 100]:
            if self.image_panel.mode == 'scatter':
                self.image_panel.mode = 'density'
            else:
                self.image_panel.mode = 'scatter'

        if keycode in [83, 115]:
            if self.image_panel.mode == 'scatter':
                return
            if self.image_panel.mode == 'density':
                self.image_panel.mode = 'slice'
            else:
                self.image_panel.mode = 'density'
        

        self.image_panel.Refresh()
        self.SetTicks()
    
    def SetTicks(self, evt=None):
        if self.image_panel.mode == 'density':
            self.check1.SetValue(True)
        if self.image_panel.mode == 'scatter':
            self.check1.SetValue(False)
        self.check2.SetValue(self.h5_data.log)
        
    def init_controls(self):
        self.SetTicks()
        self.OnScroll()
        
    def OnCheck1(self, evt):
        evtobj = evt.GetEventObject()
        if evtobj.GetValue():
            self.image_panel.mode = 'density'
        else:
            self.image_panel.mode = 'scatter'
        self.image_panel.OnChange()
    
    def OnCheck2(self, evt):
        self.h5_data.switch_log()
        self.image_panel.OnChange()
    
    def OnScroll(self, evt=None):
        value = self.slider.GetValue()
        self.h5_data.change_color(value)
        #self.text.SetLabel(str(value))
        self.image_panel.OnChange()

class Frame(wx.Frame):
    def __init__(self):
        # Create a window with a panel where widgets are placed
        super().__init__(parent=None, title='SPH Viewer')
        self.SetMinSize(self.GetSize())
        self.SetSize(self.GetSize())
        self.InitUI()

        # Create a panel
        self.panel = JuliaPanel(self)

        # Data place holder
        self.h5_data = None
        
        # Uncomment for Julia
        self.h5_data = H5Data('/Users/martynas/App/App/snap_050.hdf5')
        SecondaryFrame(self)

    def InitUI(self):
        # Create File menu
        file_menu = wx.Menu()
        file_menu_open_item = file_menu.Append(wx.ID_ANY, 'Open snapshot')
        
        tools_menu = wx.Menu()
        tools_menu_hist_item = tools_menu.Append(wx.ID_ANY, 'Histogram')
        
        # Create menu bar and add File menu
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, '&File')
        menu_bar.Append(tools_menu, '&Tools')
        
        # Add events
        self.Bind(wx.EVT_MENU, self.on_open_dialog, source=file_menu_open_item)
        self.Bind(wx.EVT_MENU, self.on_hist, source=tools_menu_hist_item)

        self.SetMenuBar(menu_bar)

    def on_open_dialog(self, event):
        dialog = wx.FileDialog(self, 'Open snapshot:', style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.h5_data = H5Data(dialog.GetPath())
            SecondaryFrame(self)
        dialog.Destroy()
    
    def on_hist(self, evt):
        hist(self)

if __name__ == '__main__':
    app = wx.App(False)
    frame = Frame()
    frame.Show()
    
    # Uncomment for debug
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
