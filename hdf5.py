import numpy as np
from scipy.spatial.transform import Rotation as R
from numba import njit, prange
import h5py
from sklearn import neighbors
from scipy.spatial import KDTree

from matplotlib.colors import hsv_to_rgb
import multiprocessing as mp
import time
import math

class H5Data():
    def __init__(self, path):
        self.pos = None
        self.xmin = 0
        self.xmax = 0
        self.ymin = 0
        self.ymax = 0
        self.zmin = 0
        self.zmax = 0
        self.zoom = 1.0
        self.origin = 0
        self.log = True
        self.slice = False
        self.hue = None
        self.path = None

        with h5py.File(path, 'r') as file:
            file['PartType0']
            self.path = path

        self.rotate((0,0))

    def switch_log(self):
        self.log = not self.log

    def change_color(self, value):
        self.hue = value/255

    def get_the(self, item):
        with h5py.File(self.path, 'r') as file:
            header = file['Header']
            header.attrs['NumPart_Total']
            return file['PartType0'][item][()]

    def get_pos(self):
        if self.pos is None:
            with h5py.File(self.path, 'r') as file:
                header = file['Header']
                header.attrs['NumPart_Total']
                self.pos = file['PartType0']['Coordinates'][()]
                self.hsml = file['PartType0']['SmoothingLength'][()]
                self.xmin = np.amin(self.pos[:,0])
                self.xmax = np.amax(self.pos[:,0])
                self.ymin = np.amin(self.pos[:,1])
                self.ymax = np.amax(self.pos[:,1])
                self.zmin = np.amin(self.pos[:,2])
                self.zmax = np.amax(self.pos[:,2])
                self.origin = ((self.xmax - self.xmin)/2,
                                (self.ymax - self.ymin)/2,
                                (self.zmax - self.zmin)/2)
                self.pos = self.pos - self.origin
                self.xmin = np.amin(self.pos[:,0])
                self.xmax = np.amax(self.pos[:,0])
                self.ymin = np.amin(self.pos[:,1])
                self.ymax = np.amax(self.pos[:,1])
                self.zmin = np.amin(self.pos[:,2])
                self.zmax = np.amax(self.pos[:,2])
        return self.pos

    
    def get_image(self, im_width, im_height, mode):
        self.get_pos()
        if mode == 'scatter':
            return self.get_scatter(im_width, im_height)
        if mode == 'density':
            return self.get_density(im_width, im_height)
        if mode == 'slice':
            return self.get_slice(im_width, im_height)
    
    def rotate(self, delta):
        r = R.from_euler('yx', (-delta[0]*np.pi, delta[1]*np.pi))
        self.pos = r.apply(self.get_pos())
    
    
    def shift(self, delta):
        xwidth = self.xmax - self.xmin
        yheight = self.ymax - self.ymin
        
        self.xmin += delta[0] * xwidth
        self.xmax += delta[0] * xwidth
        self.ymin += delta[1] * yheight
        self.ymax += delta[1] * yheight

    def center(self, position):
        xwidth = self.xmax - self.xmin
        yheight = self.ymax - self.ymin
        self.pos += [position[0] * xwidth, -position[1] * yheight, 0]

    def change_zoom(self, magnification):
        self.zoom += magnification
        
    def get_scatter(self, im_width, im_height):
        xmin, xmax = self.xmin/self.zoom, self.xmax/self.zoom
        ymin, ymax = self.ymin/self.zoom, self.ymax/self.zoom
        
        image = np.zeros((im_height, im_width, 3))
        image[:,:,1] = self._get_scatter_jit(self.pos, im_width, im_height, xmin, xmax, ymin, ymax)
        
        if self.log:
            image[:,:,1] += 1-np.amin(image[:,:,1])
            image[:,:,1] = np.log(image[:,:,1])
        
        max = np.amax(image[:, :, 1])
        if max:
            image[:,:,0] += self.hue
            image[:,:,1] = 1-image[:,:,1]/max
            image[:,:,2][image[:,:,1]<1] += 1
        image = hsv_to_rgb(image)*255
        
        return image.astype(np.uint8)
    
    @staticmethod
    @njit(parallel = True)
    def _get_scatter_jit(pos, im_width, im_height, xmin, xmax, ymin, ymax):
        xwidth = xmax - xmin
        yheight = ymax - ymin

        bitmap = np.zeros((im_height, im_width), dtype=np.uint16)
        posx = (pos[:,0]-xmin)
        posy = (pos[:,1]-ymin)
        im_size = max(im_width, im_height)
        ix = (posx/xwidth * im_size).astype(np.uint16)
        iy = (posy/yheight * im_size).astype(np.uint16)

        for ind_y, ind_x in zip(iy, ix):
            if ind_y>=im_height or ind_x>=im_width:
                continue
            bitmap[ind_y, ind_x] += 1
        
        return bitmap

    def get_density(self, im_width, im_height):
        xmin, xmax = self.xmin/self.zoom, self.xmax/self.zoom
        ymin, ymax = self.ymin/self.zoom, self.ymax/self.zoom
        xwidth = xmax - xmin
        yheight = ymax - ymin
        
        #init_time = time.perf_counter()
        im_size = max(im_width, im_height)
        X, Y = np.meshgrid(np.linspace(xmin, xmax, im_size),
                                    np.linspace(ymin, ymax, im_size))
        XY = np.vstack((X.ravel(), Y.ravel())).T
        
        Tree = KDTree(self.pos[:,0:2], leafsize=100)
        distance, IND = Tree.query(XY, k=64, workers=-1, distance_upper_bound=np.amax(self.hsml))
        IND[IND>=len(self.hsml)] = -1
        
        Density = np.zeros(im_size*im_size)
        for _, dist, h in zip(range(len(Density)), distance, self.hsml[IND]):
            if dist[0] == np.inf:
                continue
            Density[_] = self._get_kernel_w2(dist, h)
        
        if self.log:
            Density += 1 - np.amin(Density)
            Density = np.log(Density)
            
        Density = Density.reshape(im_size, im_size)
        image = np.zeros((im_height, im_width, 3))
        
        Density = Density[0:im_height, 0:im_width]

        maximum = np.amax(Density)
        if maximum:
            image[:,:,0] += self.hue
            image[:,:,1] = 1-Density/maximum
            image[:,:,2] = (Density/maximum)
            
        image = hsv_to_rgb(image)*255
        
        #print(time.perf_counter()-init_time)
        
        return image.astype(np.uint8)
    
    def get_slice(self, im_width, im_height):
        xmin, xmax = self.xmin/self.zoom, self.xmax/self.zoom
        ymin, ymax = self.ymin/self.zoom, self.ymax/self.zoom
        z_mid = (self.zmax - self.zmin)/2

        xwidth = xmax - xmin
        yheight = ymax - ymin
        
        im_size = max(im_width, im_height)
        X, Y = np.meshgrid(np.linspace(xmin, xmax, im_size),
                                    np.linspace(ymin, ymax, im_size))
        
        XYZ = np.vstack((X.ravel(), Y.ravel(), 0*np.ones_like(X.ravel()))).T
        
        Tree = KDTree(XYZ, leafsize=100)
        IND = Tree.query_ball_point(self.pos, workers=-1, r=self.hsml)
        
        Density = np.zeros(im_size*im_size)
        
        for ind, pos, h in zip(IND, self.pos, self.hsml):
            if len(ind) == 0:
                continue
            dist = np.sqrt(np.sum((XYZ[ind]-pos)**2, axis=1))
            Density[ind] += self._get_kernel_w2_slice(dist, h)
        
        if self.log:
            Density += 1 - np.amin(Density)
            Density = np.log(Density)
        
        Density = Density.reshape(im_size, im_size)
        image = np.zeros((im_height, im_width, 3))
        
        Density = Density[0:im_height, 0:im_width]

        maximum = np.amax(Density)
        if maximum:
            image[:,:,0] += self.hue
            image[:,:,1] = 1-Density/maximum
            image[:,:,2] = (Density/maximum)
            
        image = hsv_to_rgb(image)*255

        return image.astype(np.uint8)
    
    @staticmethod
    @njit(parallel=False)
    def _get_kernel_w2(distance, h):
        q = distance/h
        q[q>1] = 0
        res = np.sum(21/(2*np.pi*h**3)*(1-q)**4 * (4*q+1))
        return res

    @staticmethod
    @njit(parallel=True)
    def _get_kernel_w2_slice(distance, h):
        q = distance/h
        q[q>1] = 0
        res = 21/(2*np.pi*h**3)*(1-q)**4 * (4*q+1)
        return res
