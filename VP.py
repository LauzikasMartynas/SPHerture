import wx
import numpy as np
from vispy import app, scene, color, gloo, use, visuals
from vispy.visuals.transforms import STTransform
from vispy.util.transforms import ortho, perspective, translate, rotate
from itertools import cycle
from vispy.gloo import gl
from gl import GL_vbo, GL_screen, VERT_SHADER, FRAG_SHADER
import matplotlib.pyplot as plt

class DisplayPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.old_dataset = ''
        
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        
        self.canvas = MyCanvas(app='wx', parent=self, keys='interactive')
        self.draw_scatter()
        self.canvas.view.camera.set_range()
        self.canvas.view.camera.set_default_state()

    def on_exit(self, evt):
        self.canvas.close()
        self.Destroy()

    def update(self):
        self.draw_scatter()
        self.draw_arrows()
        self.draw_iso()
        self.draw_volume()

    def draw_scatter(self):
        data_set = self.parent.drop_list.GetStringSelection()
        
        if self.parent.check_scatter.GetValue():
            self.canvas.scatter.visible = True
        else:
            self.canvas.scatter.visible = False
            return

        # Get dataset
        data = np.copy(self.parent.h5_data.dataset_data)
        
        #Select colormap and normalise data to [0, 1]
        cmap = self.get_cmap(self.parent.drop_cmap.GetStringSelection())
        if self.parent.check_log.GetValue():
            data = np.log10(data)
        data -= np.amin(data)
        data = data/np.amax(data)

        # Scatter
        self.canvas.scatter.set_data(self.parent.h5_data.pos, edge_width=0, face_color=cmap[data], size=0.1)
        #self.canvas.view.camera.set_range((self.parent.h5_data.xmin,self.parent.h5_data.xmax), (self.parent.h5_data.ymin,self.parent.h5_data.ymax), (self.parent.h5_data.zmin,self.parent.h5_data.zmax))

        self.canvas.update()

    def draw_arrows(self):
        dataset = self.parent.drop_vectors.GetStringSelection()
        if dataset != 'None':
            self.canvas.arrows.visible = True
            vector_data = self.parent.h5_data.get_dataset_vec(dataset)
        else:
            self.canvas.arrows.visible = False
            return
        
        # Get pos with stride
        data = vector_data[::50, :]
        pos = self.parent.h5_data.pos[::50, :]
        
        # Normalise and make start-end array
        data_norm = np.linalg.norm(data, axis=1)
        data = data/np.amax(data_norm)
        #arrows = np.hstack((pos, pos+data))
        pos = np.repeat(pos, 2, axis=0)
        pos[::2] -= data * np.log10(data_norm[:, np.newaxis])
        
        # Draw vectors
        self.canvas.arrows.set_data(pos=pos, color=(1,1,1,0.5), connect='segments', width=1)

        self.canvas.update()
    
    def draw_iso(self, redraw=False):
        # If no dataset selected return
        data_set = self.parent.drop_list.GetStringSelection()
        if  not self.parent.check_iso.GetValue():
            self.canvas.iso.visible = False
            return
        
        # Prevent repeated loading of the same dataset
        if self.old_dataset != data_set:
            self.current_data = self.parent.h5_data.get_volume(data_set, 128)
            self.old_dataset = data_set
            if isinstance(self.current_data[0,0,0], (list, tuple, np.ndarray)):
                self.current_data = np.linalg.norm(self.current_data, axis=3)
        
        if isinstance(self.current_data[0,0,0], (list, tuple, np.ndarray)):
            self.current_data = np.linalg.norm(self.current_data, axis=3)
        
        # Draw if empty update otherwise
        if self.canvas.iso is None or redraw:
            cmap = self.get_cmap(self.parent.drop_cmap.GetStringSelection())
            
            # Normalise to [0...1]
            if self.parent.check_log.GetValue():
                data = np.log10(self.current_data)
            else:
                data = np.copy(self.current_data)
            data -= np.amin(data)
            data = data/np.amax(data)
            
            self.canvas.unfreeze()
            if self.canvas.iso is not None:
                self.canvas.iso.visible = False
            self.canvas.iso = scene.visuals.Isosurface(data,
                            color=(0.5, 0.0, 0.0, self.canvas.alpha),
                            parent=self.canvas.view.scene,
                            level=self.canvas.threshold, shading='smooth')
            self.canvas.update()
        else:
            self.canvas.update()
        
        self.canvas.iso.visible = True
        self.canvas.update()

# Volume
    def draw_volume(self, redraw=False):
        # If no dataset selected return
        data_set = self.parent.drop_list.GetStringSelection()
        if data_set=='None':
            self.canvas.vol.visible = False
            return
        
        # Prevent repeated loading of the same dataset
        if self.old_dataset != data_set:
            self.current_data = self.parent.h5_data.get_volume(data_set, 128)
            self.old_dataset = data_set
            if isinstance(self.current_data[0,0,0], (list, tuple, np.ndarray)):
                self.current_data = np.linalg.norm(self.current_data, axis=3)

        # Draw if empty update otherwise
        if self.canvas.vol is None or redraw:
            cmap = self.get_cmap(self.parent.drop_cmap.GetStringSelection())
            
            # Normalise to [0...1]
            if self.parent.check_log.GetValue():
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
                            plane_thickness=self.canvas.plane_thickness,
                            texture_format='r32f', relative_step_size=1.0)
                            #clipping_planes_coord_system='documnent')
            self.canvas.update()
        else:
            self.canvas.update()
  
    def draw_image(self):
        vbo = GL_vbo(data = self.parent.h5_data)
        print(self.canvas.scene.describe_tree())
        #imager = np.copy(vbo.im[:,:,0])
        #imager[imager<=0] = 1e-5
        #plt.imshow(np.log10(imager), vmin=-1, vmax=2)
        #plt.show()

        self.canvas.unfreeze()
        scene.visuals.Image(data=vbo.im, parent=self.canvas.view.scene, cmap=self.get_cmap('Viridis'))
        self.canvas.view.camera = scene.PanZoomCamera(aspect=1)
        # flip y-axis to have correct aligment
        self.canvas.view.camera.flip = (0, 1, 0)
        self.canvas.view.camera.set_range()
        self.canvas.update()
            
        #self.canvas.vol.opacity = 0.25
        self.canvas.vol.visible = True

    def draw_image_vbo(self):
        vbo = GL_vbo(data = self.parent.h5_data)
        #print(self.canvas.scene.describe_tree())
        #imager = np.copy(vbo.im[:,:,0])
        #imager[imager<=0] = 1e-5
        #plt.imshow(np.log10(imager), vmin=-1, vmax=2)
        #plt.show()

        self.canvas.unfreeze()
        scene.visuals.Image(data=np.log10(vbo.im[:,:,0]), parent=self.canvas.view.scene, cmap=self.get_cmap('Viridis'))
        self.canvas.view.camera = scene.PanZoomCamera(aspect=1)
        # flip y-axis to have correct aligment
        self.canvas.view.camera.flip = (0, 1, 0)
        self.canvas.view.camera.set_range()
        self.canvas.update()

    # Resize canvas with window resize
    def on_size(self, event):
        w, h = self.GetSize()
        self.canvas.size = (w,h)
        self.Refresh()

    def on_show(self, event):
        self.canvas.show()
    
    # Get colormaps
    def get_cmap(self, map):
        if map=='HSL':
            cmap = color.colormap.HSL()
        if map=='SingleHue':
            hue = self.parent.slider.GetValue()
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
        self._backend._vispy_set_current()
        self.unfreeze()
        
        # Iterators for scene properties
        self.vol_iter = cycle(('additive', 'iso'))
        self.interp_iter = cycle(('linear', 'spline16'))
        self.camera_iter = cycle(('turntable', 'fly'))
        self.mode_iter = cycle(('volume', 'plane'))
        
        # Setup view and camera
        self.view = self.central_widget.add_view()
        self.view.camera = next(self.camera_iter)
        self.reset_camera()
        
        # Add scatter
        self.scatter = scene.visuals.Markers(antialias=0, parent=self.view.scene)
        
        # Add vectors
        self.arrows = scene.visuals.Arrow(parent=self.view.scene)
        
        # Add image
        self.image = None
        
        # Add program
        self.program = visuals.shaders.program.ModularProgram(VERT_SHADER, FRAG_SHADER)
        
        # Add text
        #self.text = scene.visuals.Text(str(self.view.camera), parent=self.view, pos=(self.size[0], self.size[1]), anchor_x='right',anchor_y='top', color='white', font_size=7)
        #self.text.pos = self.size[0] // 2, self.size[1] // 3
        
        # Add volume placeholder
        self.vol = None
        self.interpolation = next(self.interp_iter)
        self.raycasting_mode = next(self.mode_iter)
        self.plane_normal=[0,1,0]
        self.plane_position=[50, 50, 50]
        self.plane_thickness=1
        
        # Add isosurface placeholder
        self.iso = None
        self.threshold = None
        self.alpha = None
        #Enables isosurface opacity
        gloo.set_state('translucent')
        
        # Add XYZ widget
        self.make_xyz()
        
        # Show fps in console
        #self.measure_fps()
        
        self.show()

    # Capture key events
    def on_key_press(self, event):
        if self.vol is not None:
            if event.text in ['m', 'M']:
                self.vol.method = next(self.vol_iter)
            if event.text in ['n', 'N']:
                self.vol.interpolation = next(self.interp_iter)
            if event.text in ['v', 'V']:
                self.vol.raycasting_mode = next(self.mode_iter)
        if event.text in ['r', 'R']:
            self.view.camera.reset()
            self.reset_camera()
            self.view.camera.set_range()
        if event.text in ['k', 'K']:
            self.view.camera = next(self.camera_iter)
            if 'Fly' in str(self.view.camera):
                self.axis.visible = False
                #self.view.camera._update_from_mouse = True
                self.view.camera._auto_roll = False
                self.view.camera.reset()
            else:
                self.reset_camera()
                self.axis.transform.reset()
                self.axis.update()
                self.axis.visible = True
    
    # reset turntable camera
    def reset_camera(self):
        self.view.camera.fov = 0
        self.view.camera.elevation = 0
        self.view.camera.roll = 0
        self.view.camera.azimuth = 0
    
    # Make XYZ widget
    def make_xyz(self):
        self.xyz_size = self.size[1]/10
        self.axis = scene.visuals.XYZAxis(parent=self.view)
        s = STTransform(translate=(self.xyz_size, self.xyz_size),
            scale=(self.xyz_size, self.xyz_size, self.xyz_size, 1))
        affine = s.as_matrix()
        self.axis.transform = affine
    
    # Rotate XYZ on mouse move
    def on_mouse_move(self, event):
        if 'Fly' not in str(self.view.camera) and event.button == 1 and event.is_dragging:
            self.axis.transform.reset()
            self.xyz_size = self.size[1]/10
            self.axis.transform.rotate(self.view.camera.roll, (0, 0, 1))
            self.axis.transform.rotate(self.view.camera.elevation, (1, 0, 0))
            self.axis.transform.rotate(self.view.camera.azimuth, (0, 1, 0))
            self.axis.transform.scale((self.xyz_size, self.xyz_size, 0.001))
            self.axis.transform.translate((self.xyz_size, self.xyz_size))
            self.axis.update()
    
    def on_close(self, event):
        self.close()
