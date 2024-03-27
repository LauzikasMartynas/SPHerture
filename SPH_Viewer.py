import wx
from wx.lib.agw.floatspin import FloatSpin, EVT_FLOATSPIN

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
        super().__init__(None, title='SPHerture')
        # Create menu items and open dialog
        self.InitUI()
        
        self.path = None
        self.file_dialog = FileDialog(self)
        
        # Cant close with Destroy thus using Exit
        if self.path is None:
            self.Destroy()
            wx.Exit()
        
        self.h5_data = H5Data(self.path)
        
        # Sizers for image and controls
        self.root_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.layer_sizer = wx.BoxSizer(wx.VERTICAL)
        self.control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Setup control menu
        self.InitControls()
        
        # Preload default data
        self.h5_data.get_dataset(self.drop_list.GetStringSelection())
        
        # Update statistics
        self.set_statistics()
        
        # Create main panel and add sizers
        self.image_panel = DisplayPanel(self)
        
        self.root_sizer.Add(self.top_sizer, 1, wx.EXPAND)
        self.top_sizer.Add(self.image_panel, 1, wx.EXPAND)
        self.top_sizer.Add(self.layer_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.root_sizer.Add(self.control_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # Bind events
        self.slider_left.Bind(wx.EVT_SCROLL, self.OnScroll_left)
        self.slider_right.Bind(wx.EVT_SCROLL, self.OnScroll_right)
        self.drop_list.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.drop_cmap.Bind(wx.EVT_CHOICE, self.OnCmap)
        self.check_vol.Bind(wx.EVT_CHECKBOX, self.OnCheck_vol)
        self.check_log.Bind(wx.EVT_CHECKBOX, self.OnCheck_log)
        self.check_scatter.Bind(wx.EVT_CHECKBOX, self.OnCheck_scatter)
        self.check_iso.Bind(wx.EVT_CHECKBOX, self.OnCheck_iso)
        self.drop_vectors.Bind(wx.EVT_CHOICE, self.OnVector)
        self.spin_min.Bind(EVT_FLOATSPIN, self.OnSpin)
        self.spin_max.Bind(EVT_FLOATSPIN, self.OnSpin)
        self.prev_button.Bind(wx.EVT_BUTTON, self.On_Button)
        self.next_button.Bind(wx.EVT_BUTTON, self.On_Button)
        self.add_button.Bind(wx.EVT_BUTTON, self.On_Add_Button)
        self.remove_button.Bind(wx.EVT_BUTTON, self.On_Remove_Button)
        
        # Remove in future
        self.draw_gl = False
        
       # Setup window properties
        #self.root_sizer.SetSizeHints(self)
        self.SetSizerAndFit(self.root_sizer)
        
        self.Show()

    def InitControls(self):
        # Right panel
        self.layer_sizer.Add(wx.StaticText(self, label='Layers'), 0, wx.ALIGN_LEFT)
        self.layer_list_items = []
        self.layer_list = wx.ListBox(self, choices=self.layer_list_items , style=wx.LB_MULTIPLE)
        self.layer_sizer.Add(self.layer_list, 0, wx.EXPAND)
        self.layer_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_button = wx.Button(self, label='+')
        self.remove_button = wx.Button(self, label='-')
        self.layer_button_sizer.Add(self.add_button, 0, wx.ALIGN_CENTER)
        self.layer_button_sizer.Add(self.remove_button, 0, wx.ALIGN_CENTER)
        self.layer_sizer.Add(self.layer_button_sizer, wx.ALIGN_TOP)
        
        # Statistics pane
        self.layer_sizer.AddStretchSpacer(1)
        self.layer_sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        self.label_stat = wx.StaticText(self, label='Statistics:')
        self.label_min = wx.StaticText(self, label='Min: -')
        self.label_max = wx.StaticText(self, label='Max: -')
        self.layer_sizer.Add(self.label_stat, 0, flag=wx.ALIGN_LEFT)
        self.layer_sizer.Add(self.label_min, 0, flag=wx.ALIGN_LEFT)
        self.layer_sizer.Add(self.label_max, 0, flag=wx.ALIGN_LEFT)
        self.layer_sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        self.layer_sizer.AddSpacer(10)

        # Spinners        
        spin_size = self.add_button.GetSize()[0]*2
        self.digit = 3
        self.layer_sizer.Add(wx.StaticText(self, label='Set min:'), 0, wx.ALIGN_LEFT)
        self.spin_min = FloatSpin(self, digits=self.digit, size=(spin_size,-1))
        self.spin_min.SetFormat('%e')
        self.layer_sizer.Add(self.spin_min, wx.ALIGN_TOP)
        
        self.layer_sizer.Add(wx.StaticText(self, label='Set max:'), 0, wx.ALIGN_LEFT)
        self.spin_max = FloatSpin(self, digits=self.digit, size=(spin_size,-1))
        self.spin_max.SetFormat('%e')
        self.layer_sizer.Add(self.spin_max, wx.ALIGN_TOP)
        self.layer_sizer.AddSpacer(20)
                
        # Snapshot buttons
        self.layer_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        self.layer_sizer.Add(wx.StaticText(self, label='Snapshot:'), 0, wx.ALIGN_LEFT)
        self.layer_button_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.prev_button = wx.Button(self, label='<')
        self.next_button = wx.Button(self, label='>')
        if len(self.snapshots)<= 1:
            self.prev_button.Disable()
            self.next_button.Disable()
        self.layer_button_sizer2.Add(self.prev_button, 0, wx.ALIGN_CENTER)
        self.layer_button_sizer2.Add(self.next_button, 0, wx.ALIGN_CENTER)
        self.layer_sizer.Add(self.layer_button_sizer2, wx.ALIGN_TOP)
        self.label_snap = wx.StaticText(self, label='Snap: -')
        self.layer_sizer.Add(self.label_snap, 0, flag=wx.ALIGN_LEFT)
        self.layer_sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        self.layer_sizer.AddSpacer(10)
        
        # Available data list
        self.available_data = self.h5_data.keys
        self.drop_list = wx.Choice(self, choices=self.available_data)
        self.drop_list.SetStringSelection('Density')
        self.control_sizer.Add(self.drop_list, 0, wx.ALIGN_CENTER)
        
        # Left slider
        self.slider_left = wx.Slider(self, value=20, minValue=0, maxValue=100)
        self.control_sizer.AddSpacer(10)
        #self.control_sizer.Add(wx.StaticText(self, label='Hue:'), 0, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.slider_left, 0, wx.ALIGN_CENTER)
        
        # Colormap list
        self.available_cmaps = ['HSL', 'Viridis', 'Inferno', 'Heat', 'BlueRed', 'Copper', 'SingleHue', 'Gray']
        self.drop_cmap = wx.Choice(self, choices=self.available_cmaps)
        self.drop_cmap.SetStringSelection('HSL')
        self.control_sizer.AddSpacer(10)
        self.control_sizer.Add(self.drop_cmap, 0, wx.ALIGN_CENTER)
        
        # Right slider
        self.slider_right = wx.Slider(self, value=100, minValue=1, maxValue=100)
        self.control_sizer.AddSpacer(10)
        #self.control_sizer.Add(wx.StaticText(self, label='Hue:'), 0, wx.ALIGN_CENTER)
        self.control_sizer.Add(self.slider_right, 0, wx.ALIGN_CENTER)
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

    def set_statistics(self):
        self.label_snap.SetLabel(f'Snap: {self.snapshots[self.current_snapshot][0]}')
        self.label_min.SetLabel(f'Min: {self.h5_data.dataset_min:.3e}')
        self.label_max.SetLabel(f'Max: {self.h5_data.dataset_max:.3e}')
        self.spin_min.SetDigits(50)
        self.spin_max.SetDigits(50)
        self.spin_min.SetValue(self.h5_data.dataset_min)
        self.spin_max.SetValue(self.h5_data.dataset_max)
        
        if self.h5_data.dataset_min != 0:
            self.spin_min.SetIncrement(abs(self.spin_min.GetValue()/10))
        
        if self.h5_data.dataset_max != 0:
            self.spin_max.SetIncrement(abs(self.spin_max.GetValue()/10))
        
        self.spin_min.SetDigits(self.digit)
        self.spin_max.SetDigits(self.digit)
        
        #self.slider_left.SetValue(100)
        
        #value = (self.h5_data.dataset_max-self.h5_data.dataset_min)/50 + self.h5_data.dataset_min
        #self.slider_right.SetValue(int(value))
        

    def OnSpin(self, evt):
        evtobj = evt.GetEventObject()
        evtobj.SetDigits(50)
        evtobj.SetIncrement(abs(evtobj.GetValue()/10))
        evtobj.SetDigits(self.digit)
        self.image_panel.update()

    def On_Remove_Button(self, event):
        selection = self.layer_list.GetSelections()
        for item in selection:
            self.layer_list.Delete(item)
            self.image_panel.canvas.iso.pop()
        #if self.layer_list.GetCount()>1 and len(selection) > 0:
        #    self.layer_list.Delete(selection[-1])

    def On_Add_Button(self, event):
        if self.check_iso.GetValue():
            self.image_panel.update(redraw=True, append=True)
            self.layer_list.Append(str(self.image_panel.canvas.iso[-1]))

    def On_Button(self, event):
        if event.GetEventObject().GetLabel() == '<':
            if self.current_snapshot > 0:
                self.current_snapshot -= 1
        if event.GetEventObject().GetLabel() == '>':
            if self.current_snapshot < len(self.snapshots)-1:
                self.current_snapshot += 1
        
        path = os.path.join(self.current_dir, str(*self.snapshots[self.current_snapshot]))
        self.h5_data = H5Data(path)
        self.OnChoice(None)
        
    def open_dialog(self, event=None):
        FileDialog(self)
    
    def on_hist(self, evt):
        hist(self)
    
    def on_gl(self, evt):
        self.image_panel.canvas.show(self.draw_gl)
        self.draw_gl = not self.draw_gl
        self.image_panel.canvas2.show(self.draw_gl)
        
    def on_gl_vbo(self, evt):
        self.image_panel.draw_image_vbo()
        
    def OnExit(self, evt=None):
        self.image_panel.Destroy()
        self.Destroy()

    def preload_data(self):
        self.OnChoice(None)

    # Redraw on log
    def OnCheck_log(self, evt):
        self.image_panel.update(redraw=True)

    def OnCheck_scatter(self, evt):
        self.image_panel.update()
            
    # Draw Volume
    def OnCheck_vol(self, evt):
        self.image_panel.update(redraw=True)

    # Draw Isosurface
    def OnCheck_iso(self, evt):
        self.image_panel.update(redraw=True)

    # Change property of an object, (object dependant)
    def OnScroll_left(self, evt):
        self.image_panel.update(redraw=False)

    # Change brightness of an object
    def OnScroll_right(self, evt):
        self.image_panel.update(redraw=False)

    # Redraw on vector list change
    def OnVector(self, evt):
        self.image_panel.update()
        
    # On dataset select
    def OnChoice(self, evt):
        self.h5_data.get_dataset(self.drop_list.GetStringSelection())
        self.set_statistics()
        
        if self.h5_data.dataset_min<=0:
            self.check_log.SetValue(False)
            self.check_log.Disable()
        else:
            self.check_log.Enable()
            self.check_log.SetValue(True)
    
        self.image_panel.update(True)

    # Redraw on colormap change
    def OnCmap(self, evt):
        self.image_panel.update(True)


    def InitUI(self):
        # Create File, Tools menu items
        file_menu = wx.Menu()
        file_menu_open_item = file_menu.Append(wx.ID_OPEN, '&Open snapshot')
        file_menu.AppendSeparator()
        file_menu_exit = file_menu.Append(wx.ID_EXIT, '&Quit')
        tools_menu = wx.Menu()
        tools_menu_hist_item = tools_menu.Append(wx.ID_ANY, 'Histogram')
        tools_menu_gl_item = tools_menu.Append(wx.ID_ANY, 'Gl to screen')
        tools_menu_gl_vbo_item = tools_menu.Append(wx.ID_ANY, 'Gl to vbo')
                
        # Create menu bar and add File menu
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, '&File')
        menu_bar.Append(tools_menu, '&Tools')

        self.SetMenuBar(menu_bar)
        
        # Add events
        self.Bind(wx.EVT_MENU, self.open_dialog, file_menu_open_item)
        self.Bind(wx.EVT_MENU, self.OnExit, file_menu_exit)
        self.Bind(wx.EVT_MENU, self.on_hist, tools_menu_hist_item)
        self.Bind(wx.EVT_MENU, self.on_gl, tools_menu_gl_item)
        self.Bind(wx.EVT_MENU, self.on_gl_vbo, tools_menu_gl_vbo_item)
        
        a_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('Q'), wx.ID_EXIT)])
        self.SetAcceleratorTable(a_tbl)

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
        #self.parent.path = path
        #self.parent.current_snapshot = dialog.GetFilename()
        #self.parent.current_dir = dialog.GetDirectory()
        #self.get_all()
        #return
        #wx.TopLevelWindow.RequestUserAttention(self)
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

    def get_all(self):
        filenames = next(os.walk(self.parent.current_dir), (None, None, []))[2]
        template = self.parent.current_snapshot[0:-8]+'*'+self.parent.current_snapshot[-4:]
        self.parent.snapshots = np.sort(fnmatch.filter(filenames, template))
        self.parent.current_snapshot = np.where(self.parent.snapshots == self.parent.current_snapshot)[0]
        
if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame()
    if 'Win' in wx.GetOsDescription():
        frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU))
        frame.Refresh()
    
    # Uncomment for debug
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()
