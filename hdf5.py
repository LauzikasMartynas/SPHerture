import numpy as np
from scipy.spatial.transform import Rotation as R
from numba import njit, prange
import h5py

import time

class H5Data():
    def __init__(self, path):
        self.pos = None
        self.path = None
        self.dataset = 'None'
        self.dataset_data = None
        self.cmap = None

        with h5py.File(path, 'r') as file:
            file['PartType0']
            self.path = path
            self.keys = list(file['PartType0'].keys())
            self.keys.remove('Coordinates')
            self.keys.remove('ParticleIDs')
            
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
        return self.pos
        
    def get_dataset(self, dataset):
        with h5py.File(self.path, 'r') as file:
            return file['PartType0'][dataset][()]
