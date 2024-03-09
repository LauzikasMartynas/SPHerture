import wx
import numpy as np
from scipy.spatial.transform import Rotation as R

import threading

from hdf5 import H5Data

class DisplayPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetSize((600, 600))
        
        size = self.GetSize()
        self.x = (int(size[0]/20),0,0)
        self.y = (0,-int(size[0]/20),0)
        self.z = (0,0,int(size[0]/20))
        
        self.mode = 'scatter'
        self.h5_data = parent.h5_data

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MAGNIFY, self.OnMagnify)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDclick)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)

    def OnSize(self, event):
        self.mode = 'scatter'

    def OnMagnify(self, event):
        self.mode = 'scatter'
        self.h5_data.change_zoom(event.GetMagnification())
        self.Refresh()

    def OnLeftDown(self, event):
        self.mode = 'scatter'
        self.mouse_pos_init = event.GetPosition()

    def OnRightDown(self, event):
        self.mode = 'scatter'
        self.mouse_pos_init = event.GetPosition()

    def OnLeftDclick(self, event):
        delta = self.GetSize()/2 - event.GetPosition()
        self.h5_data.center(self.get_ratio((delta[0], -delta[1])))
        self.Refresh()

    def OnLeftUp(self, event):
        self.mouse_pos_final = event.GetPosition()

    def OnMouseMove(self, event):
        self.mouse_pos_current = event.GetPosition()
        if event.LeftIsDown():
            delta = self.mouse_pos_init - self.mouse_pos_current
            self.h5_data.shift(self.get_ratio(delta))
            self.mouse_pos_init = self.mouse_pos_current
        if event.RightIsDown():
            delta = self.mouse_pos_current - self.mouse_pos_init
            size = self.GetSize()
            self.h5_data.rotate((delta[0]/size[1], delta[1]/size[1]))
            self.xyz_rotate((delta[0]/size[1], delta[1]/size[1]))
            self.mouse_pos_init = self.mouse_pos_current
        self.Refresh()
                
    def OnChange(self, evt=None):
        t=threading.Thread(target=self.OnPaint())
        t.start()
        #mp.Process(self.OnPaint())
        
    def OnPaint(self, evt=None):
        width, height = self.GetSize()
        dc = wx.PaintDC(self)
        size = self.Size
        data = self.h5_data.get_image(size[0], size[1], self.mode)
        bitmap = wx.Bitmap.FromBuffer(size[0], size[1], data)
        try:
            dc.DrawBitmap(bitmap, 0, 0)
        except ValueError:
            pass
        
        # Draw coord axes
        dc.SetPen(wx.RED_PEN)
        lines = ((10, height-10, 10+int(self.x[0]), height-10+int(self.x[1])),
                    (10, height-10, 10+int(self.y[0]), height-10+int(self.y[1])),
                    (10, height-10, 10+int(self.z[0]), height-10+int(self.z[1])))
        dc.DrawLineList(lines)
        
    def get_ratio(self, delta):
        size = self.GetSize()
        return (delta[0]/size[0], delta[1]/size[1])

    def xyz_rotate(self, delta):
        r = R.from_euler('yx', (-delta[0]*np.pi, delta[1]*np.pi))
        self.x = r.apply(self.x)
        self.y = r.apply(self.y)
        self.z = r.apply(self.z)
