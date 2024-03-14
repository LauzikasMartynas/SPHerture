import wx
import numpy as np
from vispy import app, scene, color
from vispy.visuals.transforms import STTransform
from itertools import cycle

class DisplayPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.data = parent
        self.old_dataset = ''
        
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_CLOSE, self.on_quit)
        
        self.canvas = MyCanvas(app='wx', parent=self, keys='interactive', size=(800,500))
        self.draw_scatter()
        
    def set_log_state(self, min):
        if min<=0:
            self.data.check_log.SetValue(False)
            self.data.check_log.Disable()
        else:
            self.data.check_log.Enable()

    def draw_scatter(self):
        pos = self.data.h5_data.get_pos()
        data_set = self.data.drop_list.GetStringSelection()
        vector_set = self.data.drop_vectors.GetStringSelection()

        # Show hide scene elements
        if self.data.drop_vectors.GetStringSelection()!='None':
            vector_data = self.data.h5_data.get_dataset(vector_set)
            self.draw_arrows(pos, vector_data)
            self.canvas.arrows.visible = True
        else:
            #self.canvas.arrows.parent = None
            self.canvas.arrows.visible = False
        
        if self.data.drop_list.GetStringSelection()=='None':
            self.canvas.scatter.visible = False
            return

        # Get dataset
        data = self.data.h5_data.get_dataset(data_set)
        if isinstance(data[0], (list, tuple, np.ndarray)):
            data = np.linalg.norm(data, axis=1)
        
        # Set log state
        self.set_log_state(np.amin(data))
        #Select colormap and normalise data to [0, 1]
        cmap = self.get_cmap(self.data.drop_cmap.GetStringSelection())
        if self.data.check_log.GetValue():
            data = np.log10(data)
        data -= np.amin(data)
        data = data/np.amax(data)

        # Scatter
        self.canvas.scatter.set_data(pos, edge_width=0, face_color=cmap[data], size=0.1)
        #self.canvas.view.camera.set_range((self.data.h5_data.xmin,self.data.h5_data.xmax), (-self.data.h5_data.ymin,self.data.h5_data.ymax), (-self.data.h5_data.zmin,self.data.h5_data.zmax))
        self.canvas.scatter.visible = True
        self.canvas.update()

    def draw_arrows(self, pos, data):
        # Get pos with stride
        data = data[::50, :]
        pos = pos[::50, :]
        
        # Normalise and make start-end array
        data_norm = np.linalg.norm(data, axis=1)
        data = data/np.amax(data_norm)
        #arrows = np.hstack((pos, pos+data))
        pos = np.repeat(pos, 2, axis=0)
        pos[::2] -= data * np.log10(data_norm[:, np.newaxis])
        
        # Draw vectors
        self.canvas.arrows.set_data(pos=pos, color=(1,1,1,0.5), connect='segments', width=1)
        self.canvas.update()
    
    def draw_volume(self, redraw=False):
        # If no dataset selected return
        data_set = self.data.drop_list.GetStringSelection()
        if data_set=='None':
            self.canvas.vol.visible = False
            return
        
        # Hide other items
        self.canvas.scatter.visible = False
        self.canvas.arrows.visible = False
        
        # Prevent repeated loading of the same dataset
        if self.old_dataset != data_set:
            self.current_data = self.data.h5_data.get_volume(data_set, 128)
            self.old_dataset = data_set
            if isinstance(self.current_data[0,0,0], (list, tuple, np.ndarray)):
                self.current_data = np.linalg.norm(self.current_data, axis=3)
            # Set log tick-box
            self.set_log_state(np.amin(self.current_data))

        # Draw if empty update otherwise
        if self.canvas.vol is None or redraw:
            cmap = self.get_cmap(self.data.drop_cmap.GetStringSelection())
            
            # Normalise to [0...1]
            if self.data.check_log.GetValue():
                data = np.log10(self.current_data)
            else:
                data = np.copy(self.current_data)
            data -= np.amin(data)
            data = data/np.amax(data)
            
            self.canvas.unfreeze()
            if self.canvas.vol is not None:
                self.canvas.vol.visible = False
            self.canvas.vol = scene.visuals.Volume(data,
                            parent=self.canvas.view.scene,
                            cmap=cmap,
                            interpolation=self.canvas.interpolation,
                            raycasting_mode=self.canvas.raycasting_mode,
                            plane_normal=self.canvas.plane_normal,
                            plane_position=self.canvas.plane_position,
                            plane_thickness=self.canvas.plane_thickness)
            self.canvas.update()
        else:
            self.canvas.update()
            
        #self.canvas.vol.opacity = 0.25
        self.canvas.vol.visible = True
    
    # Resize canvas with window resize
    def on_size(self, event):
        w, h = self.GetSize()
        self.canvas.size = (w,h)
        self.Refresh()

    def on_quit(self, event):
        self.Destroy()

    def on_show(self, event):
        self.canvas.show()
    
    # Get colormaps
    def get_cmap(self, map):
        if map=='HSL':
            cmap = color.colormap.HSL()
        if map=='SingleHue':
            hue = self.data.slider.GetValue()
            cmap = color.colormap.SingleHue(hue=hue)
        if map=='Inferno':
            cmap = color.colormap.MatplotlibColormap('inferno')
        if map=='Viridis':
            cmap = color.colormap.MatplotlibColormap('viridis')
        if map=='Heat':
            cmap = color.colormap.MatplotlibColormap('gist_heat')
        if map=='Copper':
            cmap = color.colormap.MatplotlibColormap('copper')
        if map=='BlueRed':
            cmap = color.colormap.MatplotlibColormap('bwr')
        if map=='Gray':
            cmap = color.colormap.MatplotlibColormap('gray')
        return cmap

class MyCanvas(scene.SceneCanvas):
    def __init__(self, *args, **kwargs):
        scene.SceneCanvas.__init__(self, *args, **kwargs)
        self.unfreeze()
        
        # Iterators for scene properties
        self.vol_iter = cycle(('mip', 'attenuated_mip', 'minip', 'translucent', 'additive', 'iso', 'average'))
        self.interp_iter = cycle(('linear', 'spline16'))
        self.camera_iter = cycle(('turntable', 'fly'))
        
        # Setup view and camera
        self.view = self.central_widget.add_view()
        #cam = scene.cameras.TurntableCamera(parent=self.view.scene)
        #self.view.camera = cam
        self.view.camera = next(self.camera_iter)
        self.view.camera.center = [0, 0, 0]
        self.view.camera.fov = 0
        self.view.camera.elevation = 0
        #self.view.camera.roll = 0
        self.view.camera.azimuth = 0
        
        # Add scatter
        self.scatter = scene.visuals.Markers(antialias=0, parent=self.view.scene)
        
        # Add vectors
        self.arrows = scene.visuals.Arrow(parent=self.view.scene)
        
        self.text = scene.visuals.Text(str(self.view.camera), parent=self.view, pos=(self.size[0], self.size[1]),
                                    anchor_x='right',
                                    anchor_y='top',
                                    color='white', font_size=7)
        #self.text.pos = self.size[0] // 2, self.size[1] // 3
        
        # Add volume
        self.vol = None
        self.interpolation='linear'
        self.raycasting_mode='volume'
        self.plane_normal=[0,1,0]
        self.plane_position=[50, 50, 50]
        self.plane_thickness=1
        
        # Add XYZ widget
        self.make_xyz()
        
        # Show fps in console
        #self.measure_fps()
        self.show()

    # Capture key events
    def on_key_press(self, event):
        if event.text in ['m', 'M']:
            self.vol.method = next(self.vol_iter)
            self.update()
        if event.text in ['n', 'N']:
            self.vol.interpolation = next(self.interp_iter)
            self.update()
        if event.text in ['p', 'P']:
            self.vol.raycasting_mode = 'plane'
            self.update()
        if event.text in ['v', 'V']:
            self.vol.raycasting_mode = 'volume'
            self.update()
        if event.text in ['k', 'K']:
            self.view.camera = next(self.camera_iter)
            if self.view.camera=='fly':
                self.axis.visible = False
            else:
                self.axis.visible = True
            self.update()
    
    def make_xyz(self):
        self.xyz_size = self.size[1]/10
        self.axis = scene.visuals.XYZAxis(parent=self.view)
        s = STTransform(translate=(self.xyz_size, self.xyz_size),
            scale=(self.xyz_size, self.xyz_size, self.xyz_size, 1))
        affine = s.as_matrix()
        self.axis.transform = affine
    
    # Rotate XYZ on mouse move
    def on_mouse_move(self, event):
        if self.view.camera!='fly' and event.button == 1 and event.is_dragging:
            self.axis.transform.reset()
            self.xyz_size = self.size[1]/10
            self.axis.transform.rotate(self.view.camera.roll, (0, 0, 1))
            self.axis.transform.rotate(self.view.camera.elevation, (1, 0, 0))
            self.axis.transform.rotate(self.view.camera.azimuth, (0, 1, 0))
            self.axis.transform.scale((self.xyz_size, self.xyz_size, 0.001))
            self.axis.transform.translate((self.xyz_size, self.xyz_size))
            self.axis.update()
