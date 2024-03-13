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
        self.drop_list = wx.Choice(self, choices=self.available_data)
        self.drop_list.SetStringSelection('Density')
        self.control_sizer.Add(self.drop_list, 0, wx.ALIGN_CENTER)
        
        self.slider = wx.Slider(self, value=20, minValue=0, maxValue=100)
        self.control_sizer.AddSpacer(10)
        #self.control_sizer.Add(wx.StaticText(self, label='Hue:'), 0, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.slider, 0, wx.ALIGN_CENTER)
        
        self.available_cmaps = ['HSL', 'SingleHue', 'CHC', 'Diverging', 'PLT', 'RYBC', 'Gray']
        self.drop_cmap = wx.Choice(self, choices=self.available_cmaps)
        self.drop_cmap.SetStringSelection('HSL')
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.drop_cmap, 0, wx.ALIGN_CENTER)
        
        self.check_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.check_vol = wx.CheckBox(self, label='Volume')
        self.check_vol.SetValue(False)
        self.check_sizer.Add(self.check_vol, wx.ALIGN_CENTER)
        
        self.check_log = wx.CheckBox(self, label='Log')
        self.check_log.SetValue(True)
        self.check_sizer.Add(self.check_log, wx.ALIGN_CENTER)
        
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.check_sizer, 0, wx.ALIGN_CENTER)
        
        self.available_vectors = self.h5_data.vector_keys
        self.drop_vectors = wx.Choice(self, choices=self.available_vectors)
        self.drop_vectors.SetStringSelection('None')
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.drop_vectors, 0, wx.ALIGN_CENTER)
        
        self.image_panel = DisplayPanel(self)
        
        self.box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer.Add(self.image_panel, 1, wx.EXPAND|wx.ALL, 1)
        self.box_sizer.Add(self.control_sizer, 0, wx.ALIGN_CENTER)
        
        self.slider.Bind(wx.EVT_SCROLL, self.OnScroll)
        self.drop_list.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.drop_cmap.Bind(wx.EVT_CHOICE, self.OnCmap)
        self.check_vol.Bind(wx.EVT_CHECKBOX, self.OnCheck_vol)
        self.check_log.Bind(wx.EVT_CHECKBOX, self.OnCheck_log)
        self.drop_vectors.Bind(wx.EVT_CHOICE, self.OnVector)
        
        self.SetSizer(self.box_sizer)
        
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        
        self.SetAutoLayout(True)
        self.Fit()
        self.SetMinSize(self.GetSize())
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
            self.h5_data = H5Data(dialog.GetPath())
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
        if self.check_vol.GetValue():
            self.image_panel.draw_volume(True)
        else:
            self.image_panel.draw_scatter()
    
    def OnCheck_vol(self, evt):
        evtobj = evt.GetEventObject()
        if evtobj.GetValue():
            self.drop_vectors.SetStringSelection('None')
            self.drop_vectors.Disable()
            self.image_panel.canvas.plane_position[1] = self.slider.GetValue()
            self.image_panel.draw_volume(True)
            self.image_panel.canvas.vol.threshold = self.slider.GetValue()/100
            self.image_panel.canvas.vol.attenuation = self.slider.GetValue()/100
            #self.image_panel.canvas.vol.gamma = self.slider.GetValue()/50
            self.image_panel.canvas.update()
        else:
            self.image_panel.canvas.vol.visible = False
            self.drop_vectors.Enable()
            self.image_panel.draw_scatter()
            
    
    def OnScroll(self, evt):
        if self.check_vol.GetValue():
            self.image_panel.canvas.vol.threshold = self.slider.GetValue()/100
            self.image_panel.canvas.vol.attenuation = self.slider.GetValue()/100
            #self.image_panel.canvas.vol.gamma = self.slider.GetValue()/50
            self.image_panel.canvas.plane_position[1] = self.slider.GetValue()
            self.image_panel.canvas.update()
        else:
            self.image_panel.draw_scatter()

    def OnVector(self, evt):
        self.image_panel.draw_scatter()

    def OnChoice(self, evt):
        if self.check_vol.GetValue():
            self.image_panel.draw_volume(True)
        else:
            self.image_panel.draw_scatter()

    def OnCmap(self, evt):
        if self.check_vol.GetValue():
            self.image_panel.draw_volume(True)
        else:
            self.image_panel.draw_scatter()

if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame()
    
    # Uncomment for debug
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
