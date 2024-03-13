import numpy as np
from scipy.spatial.transform import Rotation as R
from numba import njit, prange
import h5py

from scipy.spatial import KDTree

import time

class H5Data():
    def __init__(self, path):
        self.pos = None
        self.volume = None
        self.path = None
        self.dataset = 'None'
        self.dataset_data = None

        with h5py.File(path, 'r') as file:
            file['PartType0']
            self.path = path
            
            self.keys = ['None']
            self.vector_keys = ['None']
            for key in file['PartType0'].keys():
                if key in ('Coordinates', 'HydroAcceleration'):
                    continue
                if isinstance(file['PartType0'][key][0], (list, tuple, np.ndarray)):
                    self.vector_keys.append(key)
                self.keys.append(key)
            
            
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
                self.pos = self.pos + [self.xmin, self.ymin, self.zmin]
                self.xmin = np.amin(self.pos[:,0])
                self.xmax = np.amax(self.pos[:,0])
                self.ymin = np.amin(self.pos[:,1])
                self.ymax = np.amax(self.pos[:,1])
                self.zmin = np.amin(self.pos[:,2])
                self.zmax = np.amax(self.pos[:,2])
                
                # Prebuild Tree
                rot_pos = np.empty_like(self.pos)
                rot_pos[:,0] = self.pos[:,1] *1.1
                rot_pos[:,1] = self.pos[:,2] *1.1
                rot_pos[:,2] = self.pos[:,0] *1.1
                self.Tree = KDTree(rot_pos, leafsize=100)
        return self.pos
        
    def get_dataset(self, dataset):
        with h5py.File(self.path, 'r') as file:
            return file['PartType0'][dataset][()]
   
    def get_volume(self, dataset, res):
        X, Y, Z = np.meshgrid(np.linspace(self.xmin, self.xmax, res, endpoint=False),
                              np.linspace(self.ymin, self.ymax, res, endpoint=False),
                             np.linspace(self.zmin, self.zmax, res, endpoint=False))
        self.XYZ = np.vstack((X.ravel(), Y.ravel(), Z.ravel())).T
        
        _, IND = self.Tree.query(self.XYZ, k=16, workers=-1)
        
        grid = np.mean(self.get_dataset(dataset)[IND], axis=1)
        if dataset in self.vector_keys:
            self.volume = grid.reshape(res, res, res, 3)
        else:
            self.volume = grid.reshape(res, res, res)
        return self.volume
