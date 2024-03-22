from vispy import app, gloo, visuals, scene, use, util, plot
import numpy as np
from vispy.util.transforms import ortho, perspective, translate, rotate

import matplotlib.pyplot as plt

# full gl+ context is required for instanced rendering
#use(gl='gl+')

VERT_SHADER = """
precision highp float;

// Program inputs
attribute vec3  a_position;
attribute vec3  a_color;
attribute float a_size;

// Global shared variables
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_pixel_scale; // 1 for most OS
uniform float u_scaling; // Enlarges the hsml on "zoom in"

// Local variables
varying vec4 v_fg_color;
varying float hsml;

// Main
void main (void) {
    v_fg_color  = vec4(a_color, 1.0);
    hsml = a_size / 2.0 * u_scaling * u_pixel_scale;
    gl_Position =  u_projection * u_view * u_model * vec4(a_position, 1.0);
    gl_PointSize = a_size * u_scaling * u_pixel_scale;
}
"""

FRAG_SHADER = """
//#version 120
precision highp float;

varying vec4 v_fg_color;
varying float hsml;

void main()
{
    float q = length(gl_PointCoord.xy - vec2(0.5, 0.5)) * 2;
    if( q > 1 )
        discard;
    else
        {
        float alpha = 7 / (3.14159*hsml*hsml) * (1-q)*(1-q)*(1-q)*(1-q) * (4*q+1);
        gl_FragColor = vec4(v_fg_color.r, 0, 0, alpha);
        }
}
"""

class GL_screen(app.Canvas):
    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        data=kwargs['parent'].parent.h5_data
        ps = self.pixel_scale
        self.theta = 0
        self.phi = 0
        self.aspect_ratio = self.size[0]/self.size[1]
        
        # GL position on screen [-1...1]
        v_position = data.pos#[::1000,:]
        max = np.amax(v_position)
        self.cur_size = self.size[1]
        ratio = self.cur_size/max
        v_position = (v_position/max - 0.5)*2
        
        v_color = np.zeros_like(v_position)
        v_color[:,0] += 1
        
        # Object (2*hsml) size is in physical pixels
        v_size = data.hsml[:, np.newaxis]#[::1000,:]
        v_size = v_size*2*ratio

        # Create shade rprogram
        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        
        # Send data to shader
        self.program['a_color'] = gloo.VertexBuffer(v_color)
        self.program['a_position'] = gloo.VertexBuffer(v_position)
        self.program['a_size'] = gloo.VertexBuffer(v_size)

        # Make transformation matrices
        self.translate = [0,0,0]
        self.view = translate(self.translate, dtype=np.float32)
        self.model = np.eye(4, dtype=np.float32)
        self.range = 1.0
        self.projection = ortho(-self.range, self.range, -self.range/self.aspect_ratio, self.range/self.aspect_ratio, 10.0, -10.0)
        #print('Projection:', self.projection)
        self.program['u_projection'] = self.projection
        self.program['u_model'] = self.model
        self.program['u_view'] = self.view
        self.scaling = 1
        self.program['u_scaling'] = self.scaling
        self.program['u_pixel_scale'] = ps
        
        self.set_current()
        gloo.set_state(clear_color='black', preset='additive')
        gloo.set_viewport(0, 0, *self.size)
        self.show()
        
    def on_draw(self, event):
        gloo.clear(color=True, depth=False)
        self.program.draw('points')

    def on_resize(self, event):
        self.aspect_ratio = self.size[0]/self.size[1]
        ratio = self.size[1]/self.cur_size
        gloo.set_viewport(0, 0, *self.size)
        self.projection = ortho(-self.range, self.range, -self.range/self.aspect_ratio, self.range/self.aspect_ratio, 10.0, -10.0)
        self.program['u_projection'] = self.projection
        self.scaling *= ratio
        self.program['u_scaling'] = self.scaling/self.range
        self.cur_size = self.size[1]
        self.update()

    def on_mouse_wheel(self, event):
        self.range = self.range - self.range * event.delta[1]/50
        self.range = max(0.1, self.range)
        self.range = min(1, self.range)
        self.projection = ortho(-self.range, self.range, -self.range/self.aspect_ratio, self.range/self.aspect_ratio, 10.0, -10.0)
        self.program['u_projection'] = self.projection
        self.program['u_scaling'] = self.scaling/self.range
        self.update()

    def on_mouse_press(self, event):
        self.old_pos = event.pos

    def on_mouse_move(self, event):
        if event.button == 1 and event.is_dragging:
            self.translate[0] -= (self.old_pos[0] - event.pos[0])/1000
            self.translate[1] += (self.old_pos[1] - event.pos[1])/1000
            self.view = translate(self.translate)
            self.program['u_view'] = self.view
            self.old_pos = event.pos
            self.update()
        if event.button == 2 and event.is_dragging:
            self.phi -= (self.old_pos[0] - event.pos[0])/10
            self.theta -= (self.old_pos[1] - event.pos[1])/10
            self.model = np.dot(rotate(self.theta, (1, 0, 0)),
                                rotate(self.phi, (0, 1, 0)))
            self.program['u_model'] = self.model
            self.old_pos = event.pos
            self.update()

class GL_vbo(app.Canvas):
    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        data=kwargs['parent'].parent.h5_data
        ps = self.pixel_scale
        self.theta = 0
        self.phi = 0
        self.im = None
        
        # GL position on screen [-1...1]
        v_position = data.pos
        max = np.amax(v_position)
        ratio = self.physical_size[1]/max
        v_position = (v_position/max - 0.5)*2
        
        v_color = np.zeros_like(data.pos)
        v_color[:,0] += 1
        
        # Object (2*hsml) size is in physical pixels
        v_size = data.hsml[:, np.newaxis]
        v_size = v_size*2*ratio
        # Create shade rprogram
        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        
        # Send data to shader
        self.program['a_color'] = gloo.VertexBuffer(v_color)
        self.program['a_position'] = gloo.VertexBuffer(v_position)
        self.program['a_size'] = gloo.VertexBuffer(v_size)

        # Make transformation matrices
        self.translate = [0,0,0]
        self.view = translate(self.translate, dtype=np.float32)
        self.model = np.eye(4, dtype=np.float32)
        self.range = 1.0
        self.projection = ortho(-self.range, self.range, -self.range, self.range, 10.0, -10.0)
        self.program['u_projection'] = self.projection
        self.program['u_model'] = self.model
        self.program['u_view'] = self.view
        self.scaling = 1
        self.program['u_scaling'] = self.scaling
        self.program['u_pixel_scale'] = ps
        
        self.set_current()
        gloo.set_state(clear_color='black', blend=True, preset='additive')
        
        # Offscreen rendering (returns float)
        self._rendertex = gloo.Texture2D(shape=self.physical_size[::-1]+(4,), internalformat='rgba32f')
        self._fbo = gloo.FrameBuffer(self._rendertex, gloo.RenderBuffer(self.physical_size[::-1]))
        
        # Var 2
        #self.set_current()
        #size = self.physical_size
        #self._fbo = gloo.FrameBuffer(color=gloo.RenderBuffer(size[::-1]),
        #                  depth=gloo.RenderBuffer(size[::-1]))
        #try:
        #    self._fbo.activate()
        #    self.events.draw()
        #    self.im2 = self._fbo.read()
        #finally:
        #    self._fbo.deactivate()
        
        self.on_update()
        self.show(False)
        
    def on_update(self):
       with self._fbo:
            gloo.clear('black')
            gloo.set_viewport(0,0,*self.size)
            self.program.draw('points')
            self.im = gloo.util.read_pixels((0,0,self.physical_size[0], self.physical_size[1]), out_type='float')
