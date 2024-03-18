from vispy import app, gloo, visuals, scene, use
import numpy as np
from vispy.util.transforms import perspective, translate, rotate

# full gl+ context is required for instanced rendering
use(gl='gl+')

VERT_SHADER = """
//precision highp float;

// Program inputs
attribute vec2  a_position;
attribute vec3  a_color;
attribute float a_hsml;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

// Internal variables
varying vec4 v_fg_color;
varying float hsml;

// Main
void main (void) {
    v_fg_color  = vec4(a_color, 1.0);
    hsml = a_hsml;
    gl_Position =  u_projection * u_view * u_model* vec4(a_position, 0.0, 1.0);
    gl_PointSize = 2.0 * hsml;
}
"""

FRAG_SHADER = """
#version 120
//precision highp float;

// Internal variables
varying vec4 v_fg_color;
varying float hsml;

void main()
{
    // PointCoord [0...1]
    float q = length(gl_PointCoord.xy - vec2(0.5, 0.5)) * 2;
    if( q > 1.0 )
        discard;
    else
        {
        float alpha = 21 / (2*3.14*hsml*hsml*hsml) * (1-q)*(1-q)*(1-q)*(1-q) * (4*q+1);
        gl_FragColor = vec4(v_fg_color.rgb, clamp(alpha, 0, 1));
        }
}
"""


class Canvas(app.Canvas):

    def __init__(self):
        app.Canvas.__init__(self, keys='interactive')
        ps = self.pixel_scale

        # Create vertices
        n = 1000000
        v_position = 0.25 * np.random.randn(n, 2).astype(np.float32)
        v_color = np.random.uniform(0, 1, (n, 3)).astype(np.float32)
        v_size = np.random.uniform(2*ps, 12*ps, (n, 1)).astype(np.float32)

        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        
        # Set uniform and attribute
        print("Min:", np.amin(v_color), "Min:", np.amax(v_color), print(np.shape(v_color)))
        self.program['a_color'] = gloo.VertexBuffer(v_color)
        print("Min:", np.amin(v_position), "Min:", np.amax(v_position), print(np.shape(v_position)))
        self.program['a_position'] = gloo.VertexBuffer(v_position)
        print("Min:", np.amin(v_size), "Min:", np.amax(v_size), print(np.shape(v_size)))
        self.program['a_size'] = gloo.VertexBuffer(v_size)
        gloo.set_state(clear_color='black', blend=True, preset='additive')

        self.show()

    def on_draw(self, event):
        gloo.clear(color=True, depth=True)
        self.program.draw('points')


#Canvas()


class Canvas2(app.Canvas):

    def __init__(self, data):
        app.Canvas.__init__(self, keys='interactive', size=(500,500))
        ps = self.pixel_scale

        # GL position on screen [-1...1]
        v_position = data.pos[:,0:2]
        max = np.amax(v_position)
        ratio = self.physical_size[1]/max
        v_position = (v_position/max - 0.5)
        
        v_color = np.zeros_like(data.pos)
        v_color[:,0] += 1
        
        # Object size is in physical pixels
        v_size = data.hsml[:, np.newaxis]
        v_size = v_size*2*ratio
        #print("Min:", np.amin(v_size), "Max:", np.amax(v_size), print(np.shape(v_size)))

        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        
        # Set uniform and attribute
        self.program['a_color'] = gloo.VertexBuffer(v_color)
        self.program['a_position'] = gloo.VertexBuffer(v_position)
        self.program['a_hsml'] = gloo.VertexBuffer(v_size)
        gloo.set_state(clear_color='black', blend=True, preset='additive')

        self.translate = 2
        self.view = translate((0, 0, -self.translate), dtype=np.float32)
        self.model = np.eye(4, dtype=np.float32)

        self.projection = perspective(45.0, self.size[0] /
                                      float(self.size[1]), 1.0, 1000.0)
        self.program['u_projection'] = self.projection

        self.program['u_model'] = self.model
        self.program['u_view'] = self.view
        
        self.theta = 0
        self.phi = 0

        self.timer = app.Timer('auto', connect=self.on_timer, start=False)

        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.gl.glDepthMask(False)

        self.show()

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *self.physical_size)
        self.projection = perspective(45.0, event.size[0] /
                                      float(event.size[1]), 1.0, 1000.0)
        self.program['u_projection'] = self.projection

    def on_mouse_wheel(self, event):
        self.translate += event.delta[1]
        self.translate = max(1, self.translate)
        self.view = translate((0, 0, -self.translate))
        self.program['u_view'] = self.view
        self.update()

    def on_draw(self, event):
        gloo.clear(color=True, depth=True)
        self.program.draw('points')

    def on_timer(self, event):
        self.theta += .5
        self.phi += .5
        self.model = np.dot(rotate(self.theta, (0, 0, 1)),
                            rotate(self.phi, (0, 1, 0)))
        self.program['u_model'] = self.model
        self.update()

    def on_key_press(self, event):
        if event.text == ' ':
            if self.timer.running:
                self.timer.stop()
            else:
                self.timer.start()
#Canvas()


# Volume
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
