import wx
import numpy as np

from hdf5 import H5Data
from plt import hist
from VP import DisplayPanel
from  gl import GL_screen, GL_vbo

import os
import fnmatch


from vispy import scene

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title='SPH Viewer')
        # Create menu items and open dialog
        self.InitUI()
        FileDialog(self)
        
        self.h5_data = H5Data(self.path)
        
        # Sizers for image and controls
        self.root_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.layer_sizer = wx.BoxSizer(wx.VERTICAL)
        self.control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Setup control menu
        self.InitControls()
        # Preload data
        self.h5_data.get_dataset(self.drop_list.GetStringSelection())
        
        # Add controls and image to root sizer
        self.image_panel = DisplayPanel(self)
        
        self.root_sizer.Add(self.top_sizer, 1, wx.EXPAND)
        self.top_sizer.Add(self.image_panel, 1, wx.EXPAND)
        self.top_sizer.Add(self.layer_sizer, 0, wx.EXPAND)
        self.root_sizer.Add(self.control_sizer, 0, wx.ALIGN_CENTER)
        
        # Bind events
        self.slider.Bind(wx.EVT_SCROLL, self.OnScroll)
        self.slider_gamma.Bind(wx.EVT_SCROLL, self.OnScroll_gamma)
        self.drop_list.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.drop_cmap.Bind(wx.EVT_CHOICE, self.OnCmap)
        self.check_vol.Bind(wx.EVT_CHECKBOX, self.OnCheck_vol)
        self.check_log.Bind(wx.EVT_CHECKBOX, self.OnCheck_log)
        self.check_scatter.Bind(wx.EVT_CHECKBOX, self.OnCheck_scatter)
        self.check_iso.Bind(wx.EVT_CHECKBOX, self.OnCheck_iso)
        self.drop_vectors.Bind(wx.EVT_CHOICE, self.OnVector)
        
        self.prev_button.Bind(wx.EVT_BUTTON, self.On_Button)
        self.next_button.Bind(wx.EVT_BUTTON, self.On_Button)
        #self.Bind(wx.EVT_CLOSE, self.OnExit)
        
        # Setup window properties
        self.SetSizer(self.root_sizer)
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Show()

    def InitControls(self):
        # Right panel
        self.layer_sizer.Add(wx.StaticText(self, label='Layers'), 0, wx.ALIGN_LEFT)
        self.layer_list = wx.ListBox(self, choices=['Scatter', 'Scatter'], style=wx.LB_MULTIPLE)
        self.layer_sizer.Add(self.layer_list, 0, wx.EXPAND)
        self.layer_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_button = wx.Button(self, label='+')
        self.remove_button = wx.Button(self, label='-')
        self.layer_button_sizer.Add(self.add_button, 0, wx.ALIGN_CENTER)
        self.layer_button_sizer.Add(self.remove_button, 0, wx.ALIGN_CENTER)
        self.layer_sizer.Add(self.layer_button_sizer, wx.ALIGN_TOP)
        
        
        self.layer_sizer.AddStretchSpacer(1)
        self.layer_sizer.Add(wx.StaticText(self, label='Snapshot:'), 0, wx.ALIGN_LEFT)
        self.layer_button_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.prev_button = wx.Button(self, label='<')
        self.next_button = wx.Button(self, label='>')
        self.layer_button_sizer2.Add(self.prev_button, 0, wx.ALIGN_CENTER)
        self.layer_button_sizer2.Add(self.next_button, 0, wx.ALIGN_CENTER)
        self.layer_sizer.Add(self.layer_button_sizer2, wx.ALIGN_TOP)
        
        # Available data list
        self.available_data = self.h5_data.keys
        self.drop_list = wx.Choice(self, choices=self.available_data)
        self.drop_list.SetStringSelection('Density')
        self.control_sizer.Add(self.drop_list, 0, wx.ALIGN_CENTER)
        
        # First slider
        self.slider = wx.Slider(self, value=20, minValue=0, maxValue=100)
        self.control_sizer.AddSpacer(10)
        #self.control_sizer.Add(wx.StaticText(self, label='Hue:'), 0, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.slider, 0, wx.ALIGN_CENTER)
        
        # Colormap list
        self.available_cmaps = ['HSL', 'Viridis', 'Inferno', 'Heat', 'BlueRed', 'Copper', 'SingleHue', 'Gray']
        self.drop_cmap = wx.Choice(self, choices=self.available_cmaps)
        self.drop_cmap.SetStringSelection('HSL')
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.drop_cmap, 0, wx.ALIGN_CENTER)
        
        # Gamma slider
        self.slider_gamma = wx.Slider(self, value=100, minValue=1, maxValue=100)
        self.control_sizer.AddSpacer(10)
        #self.control_sizer.Add(wx.StaticText(self, label='Hue:'), 0, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.slider_gamma, 0, wx.ALIGN_CENTER)
        self.control_sizer.AddSpacer(10)
        
        # Check box sizer
        self.grid_sizer = wx.GridSizer(2, 2, 0, 0)
        self.check_vol = wx.CheckBox(self, label='Volume')
        self.check_vol.SetValue(False)
        self.grid_sizer.Add(self.check_vol, wx.ALIGN_CENTER)
        self.check_log = wx.CheckBox(self, label='Log')
        self.check_log.SetValue(True)
        self.grid_sizer.Add(self.check_log, wx.ALIGN_CENTER)
        self.check_scatter = wx.CheckBox(self, label='Scatter')
        self.check_scatter.SetValue(True)
        self.grid_sizer.Add(self.check_scatter, wx.ALIGN_CENTER)
        self.check_iso = wx.CheckBox(self, label='Iso')
        self.check_iso.SetValue(False)
        self.grid_sizer.Add(self.check_iso, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.grid_sizer, 0, wx.ALIGN_CENTER)
        
        # Vector field list
        self.available_vectors = self.h5_data.vector_keys
        self.drop_vectors = wx.Choice(self, choices=self.available_vectors)
        self.drop_vectors.SetStringSelection('None')
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.drop_vectors, 0, wx.ALIGN_CENTER)

    def On_Button(self, event):
        if event.GetEventObject().GetLabel() == '<':
            self.current_snapshot -= 1
        if event.GetEventObject().GetLabel() == '>':
            self.current_snapshot += 1
        
        path = os.path.join(self.current_dir, str(*self.snapshots[self.current_snapshot]))
        self.h5_data = H5Data(path)
        self.OnChoice(None)
        
    def open_dialog(self, event=None):
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
                self.open_dialog()
        dialog.Destroy()
    
    def on_open_snapshot(self, event=None):
        self.open_dialog()
        self.image_panel.draw_scatter()
    
    def on_hist(self, evt):
        hist(self)
    
    def on_gl(self, evt):
        GL_screen(data = self.h5_data)
        
    def on_gl_vbo(self, evt):
        self.image_panel.draw_image_vbo()
        #print(vbo.im)
        #scene.visuals.Image(vbo.im, parent=self.image_panel.canvas)
        
    def OnExit(self, evt=None):
        #self.image_panel.Destroy()
        self.Destroy()

    def preload_data(self):
        self.OnChoice(None)

    # Redraw on log
    def OnCheck_log(self, evt):
        if self.check_vol.GetValue():
            self.image_panel.draw_volume(True)
        else:
            self.image_panel.draw_scatter()

    def OnCheck_scatter(self, evt):
        self.image_panel.draw_scatter()
            
    # Draw Volume
    def OnCheck_vol(self, evt):
        evtobj = evt.GetEventObject()
        if evtobj.GetValue():
            self.image_panel.draw_volume(redraw=True)
            #self.image_panel.canvas.plane_position[1] = self.slider.GetValue()
            self.image_panel.canvas.vol.threshold = self.slider.GetValue()/100
            self.image_panel.canvas.vol.attenuation = self.slider.GetValue()/100
            self.image_panel.canvas.update()
        else:
            self.image_panel.canvas.vol.visible = False

    # Draw Isosurface
    def OnCheck_iso(self, evt):
        evtobj = evt.GetEventObject()
        if evtobj.GetValue():
            self.image_panel.canvas.threshold = self.slider.GetValue()/100
            self.image_panel.draw_iso(redraw=True)
            self.image_panel.canvas.update()
        else:
            self.image_panel.canvas.iso.visible = False
  

    # Change property of an object, (object dependant)
    def OnScroll(self, evt):
        if self.check_vol.GetValue():
            #self.image_panel.canvas.vol.threshold = self.slider.GetValue()/100
            #self.image_panel.canvas.vol.attenuation = self.slider.GetValue()/100
            self.image_panel.canvas.plane_position[1] = self.slider.GetValue()/100
            self.image_panel.canvas.update()
        elif self.check_iso.GetValue():
            self.image_panel.canvas.threshold = self.slider.GetValue()/100
            self.image_panel.draw_iso(redraw=True)
            self.image_panel.canvas.update()
        else:
            self.image_panel.draw_scatter()

    # Change brightness of an object
    def OnScroll_gamma(self, evt):
        if self.check_vol.GetValue():
            self.image_panel.canvas.vol.gamma = self.slider_gamma.GetValue()/10
            self.image_panel.canvas.update()
        elif self.check_iso.GetValue():
            self.image_panel.canvas.alpha = self.slider_gamma.GetValue()/100
            self.image_panel.draw_iso(redraw=True)
            self.image_panel.canvas.update()
        else:
            self.image_panel.draw_scatter()

    # Redraw on vector list change
    def OnVector(self, evt):
        self.image_panel.draw_arrows()
        
    # On dataset select
    def OnChoice(self, evt):
        self.h5_data.get_dataset(self.drop_list.GetStringSelection())
        if self.h5_data.dataset_min<=0:
            self.check_log.SetValue(False)
            self.check_log.Disable()
        else:
            self.check_log.Enable()
            
        if self.check_vol.GetValue():
            self.image_panel.draw_volume(True)
        else:
            self.image_panel.draw_scatter()

    # Redraw on colormap change
    def OnCmap(self, evt):
        self.image_panel.update()


    def InitUI(self):
        # Create File, Tools menu items
        file_menu = wx.Menu()
        file_menu_open_item = file_menu.Append(wx.ID_ANY, 'Open snapshot')
        tools_menu = wx.Menu()
        tools_menu_hist_item = tools_menu.Append(wx.ID_ANY, 'Histogram')
        tools_menu_gl_item = tools_menu.Append(wx.ID_ANY, 'Gl to screen')
        tools_menu_gl_vbo_item = tools_menu.Append(wx.ID_ANY, 'Gl to vbo')
                
        # Create menu bar and add File menu
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, '&File')
        menu_bar.Append(tools_menu, '&Tools')
        
        # Add events
        self.Bind(wx.EVT_MENU, self.on_open_snapshot, source=file_menu_open_item)
        self.Bind(wx.EVT_MENU, self.on_hist, source=tools_menu_hist_item)
        self.Bind(wx.EVT_MENU, self.on_gl, source=tools_menu_gl_item)
        self.Bind(wx.EVT_MENU, self.on_gl_vbo, source=tools_menu_gl_vbo_item)

        self.SetMenuBar(menu_bar)

class FileDialog(wx.FileDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.open_dialog()
        
    def open_dialog(self, event=None):
        dialog = wx.FileDialog(self, 'Open Gadget snapshot:',
                                style=wx.DD_DEFAULT_STYLE,
                                wildcard="HDF5 files (*.hdf5)|*.hdf5")
        #path='/Users/martynas/App/SPHerture/snap_050.hdf5'
        #frame = MyFrame(path=dialog.GetPath())
        #self.InitUI(frame)
        #return
        if dialog.ShowModal() == wx.ID_OK:
            try:
                self.parent.path = dialog.GetPath()
                self.parent.current_snapshot = dialog.GetFilename()
                self.parent.current_dir = dialog.GetDirectory()
                self.get_all()
                
            except Exception as error:
                dlg = wx.MessageDialog(self, type(error).__name__, "No bueno!", wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()

        dialog.Destroy()

    def get_all(self):
        filenames = next(os.walk(self.parent.current_dir), (None, None, []))[2]
        template = self.parent.current_snapshot[0:-8]+'*'+self.parent.current_snapshot[-4:]
        self.parent.snapshots = np.sort(fnmatch.filter(filenames, template))
        self.parent.current_snapshot = np.where(self.parent.snapshots == self.parent.current_snapshot)[0]
        
if __name__ == '__main__':
    app = wx.App(False)
    frame=MyFrame()
    if 'Win' in wx.GetOsDescription():
        frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU))
        frame.Refresh()
    #frame.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU))
    # Uncomment for debug
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
