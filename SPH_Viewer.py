import wx
import numpy as np

from VPJulia import VPJulia
from hdf5 import H5Data
from plt import hist
from VP import DisplayPanel

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='SPH Viewer')
        
        self.InitUI()
        
        self.on_open_dialog()
        
        self.control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.available_data = self.h5_data.keys
        self.drop_list = wx.Choice(self, choices=self.available_data, style=wx.CB_READONLY)
        self.drop_list.SetStringSelection('Density')
        self.control_sizer.Add(self.drop_list, 0, wx.ALIGN_CENTER)
        
        self.slider = wx.Slider(self, value=20, minValue=0, maxValue=40)
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(wx.StaticText(self, label='Hue:'), 0, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.slider, 0, wx.ALIGN_CENTER)
        
        self.available_cmaps = ['HSL', 'SingleHue']
        self.drop_cmap = wx.Choice(self, choices=self.available_cmaps, style=wx.CB_READONLY)
        self.drop_cmap.SetStringSelection('HSL')
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.drop_cmap, 0, wx.ALIGN_CENTER)
        
        self.check_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.check_sc = wx.CheckBox(self, label='Smoothing')
        self.check_sc.SetValue(False)
        self.check_sizer.Add(self.check_sc, wx.ALIGN_CENTER)
        
        self.check_log = wx.CheckBox(self, label='Log')
        self.check_log.SetValue(True)
        self.check_sizer.Add(self.check_log, wx.ALIGN_CENTER)
        
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.check_sizer, 0, wx.ALIGN_CENTER)
        
        self.image_panel = DisplayPanel(self)
        
        self.box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer.Add(self.image_panel, 1, wx.EXPAND|wx.ALL, 1)
        self.box_sizer.Add(self.control_sizer, 0, wx.ALIGN_CENTER)
        
        self.slider.Bind(wx.EVT_SCROLL, self.OnScroll)
        self.drop_list.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.drop_cmap.Bind(wx.EVT_CHOICE, self.OnCmap)
        self.check_sc.Bind(wx.EVT_CHECKBOX, self.OnCheck_log)
        self.check_log.Bind(wx.EVT_CHECKBOX, self.OnCheck_sc)
        
        self.SetSizer(self.box_sizer)
        
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        
        self.Fit()
        self.Show()
        
            
    def InitUI(self):
        # Create File menu
        file_menu = wx.Menu()
        file_menu_open_item = file_menu.Append(wx.ID_ANY, 'Open snapshot')
        
        tools_menu = wx.Menu()
        tools_menu_hist_item = tools_menu.Append(wx.ID_ANY, 'Histogram')
        tools_menu_VPjulia_item = tools_menu.Append(wx.ID_ANY, 'VP Julia Set')
                
        # Create menu bar and add File menu
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, '&File')
        menu_bar.Append(tools_menu, '&Tools')
        
        # Add events
        self.Bind(wx.EVT_MENU, self.on_open_dialog, source=file_menu_open_item)
        self.Bind(wx.EVT_MENU, self.on_hist, source=tools_menu_hist_item)
        self.Bind(wx.EVT_MENU, self.on_VPjulia, source=tools_menu_VPjulia_item)

        self.SetMenuBar(menu_bar)

    def on_open_dialog(self, event=None):
        dialog = wx.FileDialog(self, 'Open Gadget snapshot:',
                                style=wx.DD_DEFAULT_STYLE,
                                wildcard="HDF5 files (*.hdf5)|*.hdf5")
                
        if dialog.ShowModal() == wx.ID_OK:
            try:
                self.h5_data = H5Data(dialog.GetPath())
            except:
                dlg = wx.MessageDialog(self, "", "No bueno!", wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                self.on_open_dialog()
        dialog.Destroy()
    
    def on_hist(self, evt):
        hist(self)
        
    def on_VPjulia(self, evt):
        frame = VPJulia(self)
        frame.Show()

    def OnExit(self, evt):
        self.Destroy()
        
    def OnCheck_log(self, evt):
        self.image_panel.refresh()
    
    def OnCheck_sc(self, evt):
        self.image_panel.refresh()
    
    def OnScroll(self):
        value = self.slider.GetValue()
        self.h5_data.change_color(value)
        self.image_panel.Refresh()

    def OnChoice(self, evt):
        evtobj = evt.GetEventObject()
        dataset = evtobj.GetStringSelection()
        self.image_panel.refresh()

    def OnCmap(self, evt):
        evtobj = evt.GetEventObject()
        cm = evtobj.GetStringSelection()
        self.h5_data.cmap = cm
        self.image_panel.refresh()

if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame()
    
    # Uncomment for debug
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
