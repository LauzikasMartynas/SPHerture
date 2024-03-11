import wx
import numpy as np
import math
from vispy import app, gloo, scene, color

class DisplayPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.data = parent

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.on_quit)
        self.Bind(wx.EVT_SHOW, self.on_show)
        
        self.canvas = MyCanvas(parent=self, keys='interactive', show=True, size=(800,500))
        
        self.refresh()
        self.Fit()
        

    def refresh(self):
        pos = self.data.h5_data.get_pos()
        data_set = self.data.drop_list.GetStringSelection()
        data = self.data.h5_data.get_dataset(data_set)
        
        cmap = self.get_cmap(self.data.drop_cmap.GetStringSelection())
        
        if self.data.check_log.GetValue():
            data = np.log10(data)
        
        data -= np.amin(data)
        data = data/np.amax(data)

        self.canvas.scatter.set_data(pos, edge_width=0, face_color=cmap[data], size=0.1)
        self.canvas.update()

    def OnSize(self, event):
        w, h = self.GetSize()
        self.canvas.size = (w,h)
        self.Refresh()

    def on_quit(self, event):
        self.Destroy()

    def on_show(self, event):
        self.canvas.show()
        
    def get_cmap(self, map):
        if map=='HSL':
            cmap =  color.colormap.HSL()
        if map=='SingleHue':
            cmap = color.colormap.SingleHue(hue=20)
        return cmap

class MyCanvas(scene.SceneCanvas):
    def __init__(self, *args, **kwargs):
        scene.SceneCanvas.__init__(self, *args, **kwargs)
        
        self.unfreeze()
        view = self.central_widget.add_view()
        view.camera = 'turntable'  # or try 'arcball'
        
        self.scatter = scene.visuals.Markers(antialias=0, parent=view.scene)

        axis = scene.visuals.XYZAxis(parent=view.scene)
        
        self.measure_fps()
        self.freeze()
