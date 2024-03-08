import numpy as np
from numba import njit, prange
from matplotlib.colors import hsv_to_rgb

class JuliaSet():
    def __init__(self):
        # Image width and height; parameters for the plot
        self.c_x = -0.7
        self.c_y = 0.38
        self.zabs_max = 4
        self.nit_max = 100
        self.zoom = 1.0
        self.xmin, self.xmax = -1.5, 1.5
        self.ymin, self.ymax = -1, 1

    def set_zoom(self, zoom):
        self.zoom /= zoom
        
    def set_rot(self, angle):
        theta = np.arctan2(self.c_y, self.c_x)
        theta += angle
        r = np.sqrt(self.c_x*self.c_x+self.c_y*self.c_y)
        self.c_x = r * np.cos(theta)
        self.c_y = r * np.sin(theta)
        

    def shift(self, delta, im_size):
        ratiox = -delta[0]/im_size[0]
        ratioy = -delta[1]/im_size[1]
        
        xwidth = self.xmax - self.xmin
        yheight = self.ymax - self.ymin
        
        self.xmin += ratiox * xwidth
        self.xmax += ratiox * xwidth
        self.ymin += ratioy * yheight
        self.ymax += ratioy * yheight

    def get_julia_jit(self, im_width, im_height):
        xmin, xmax = self.xmin*self.zoom, self.xmax*self.zoom
        ymin, ymax = self.ymin*self.zoom, self.ymax*self.zoom
        
        julia = self._calc_julia_jit(im_width, im_height, self.c_x,
                                    self.c_y, self.zabs_max, self.nit_max,
                                    xmin, xmax, ymin, ymax)

        julia = self.hsv_to_rgb(julia, im_width, im_height)
        
        #julia = hsv_to_rgb(julia)*255

        return julia.astype(np.uint8)

    @staticmethod
    @njit(parallel=True)
    def _calc_julia_jit(im_width, im_height, c_x, c_y, zabs_max, nit_max,
                        xmin, xmax, ymin, ymax):
        xwidth = xmax - xmin
        yheight = ymax - ymin
        
        julia = np.zeros((im_height, im_width, 3))
        for iy in prange(im_height):
            for ix in prange(im_width):
                # Map pixel position to a point in the complex plane
                zx = ix / im_width * xwidth + xmin
                zy = iy / im_height * yheight + ymin
                nit=0
                while nit < nit_max:
                    zxzx = zx*zx
                    zyzy = zy*zy
                    tmp = zxzx - zyzy + c_x
                    zy = 2*zx*zy + c_y
                    zx = tmp
                    nit += 1
                    if zxzx+zyzy >= zabs_max:
                        break
                julia[iy,ix, 0] = nit / nit_max
                julia[iy,ix, 1] = 1.0
                julia[iy,ix, 2] = (nit < nit_max)
        return julia
    
    @staticmethod
    @njit(parallel=True)
    def hsv_to_rgb(julia, im_width, im_height):
        for iy in prange(im_height):
            for ix in prange(im_width):
                if julia[iy,ix,1]:
                    if julia[iy,ix,0] == 1.0: julia[iy,ix,0] = 0.0
                    
                    i = int(julia[iy,ix,0]*6.0)
                    f = julia[iy,ix,0]*6.0 - i
                    
                    w = int(255*( julia[iy,ix,0] * (1.0 - julia[iy,ix,1]) ))
                    q = int(255*( julia[iy,ix,0] * (1.0 - julia[iy,ix,1] * f) ))
                    t = int(255*( julia[iy,ix,0] * (1.0 - julia[iy,ix,1] * (1.0 - f)) ))
                    v = int(255*julia[iy,ix,0])
                    
                    if i==0:
                        julia[iy,ix,0]=v
                        julia[iy,ix,1]=t
                        julia[iy,ix,2]=w
                    if i==1:
                        julia[iy,ix,0]=q
                        julia[iy,ix,1]=v
                        julia[iy,ix,2]=w
                    if i==2:
                        julia[iy,ix,0]=w
                        julia[iy,ix,1]=v
                        julia[iy,ix,2]=t
                    if i==3:
                        julia[iy,ix,0]=w
                        julia[iy,ix,1]=q
                        julia[iy,ix,2]=v
                    if i==4:
                        julia[iy,ix,0]=t
                        julia[iy,ix,1]=w
                        julia[iy,ix,2]=v
                    if i==5:
                        julia[iy,ix,0]=v
                        julia[iy,ix,1]=w
                        julia[iy,ix,2]=q
                else:
                    v = int(255*julia[iy,ix,0])
                    julia[iy,ix,0]=v
                    julia[iy,ix,1]=v
                    julia[iy,ix,2]=v
        return julia
