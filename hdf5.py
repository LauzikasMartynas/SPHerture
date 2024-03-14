import numpy as np
import h5py

from scipy.spatial import KDTree

import time

class H5Data():
    def __init__(self, path):
        self.path = None
        self.pos = None
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        self.zmin = None
        self.zmax = None
        
        self.volume = None
        
        # Dataset properties
        self.dataset_name = ''
        self.dataset_data = None
        self.dataset_min = None
        self.dataset_max = None

        with h5py.File(path, 'r') as file:
            file['PartType0']
            self.path = path
            
            # Get available datasets
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
                # Load and center
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
                
                if header.attrs['NumPart_Total'][5]:
                    self.pos = self.pos - file['PartType5']['Coordinates'][0]
                else:
                    self.pos = self.pos - [self.xmax/2, self.ymax/2, self.zmax/2]
                    self.xmin = np.amin(self.pos[:,0])
                    self.xmax = np.amax(self.pos[:,0])
                    self.ymin = np.amin(self.pos[:,1])
                    self.ymax = np.amax(self.pos[:,1])
                    self.zmin = np.amin(self.pos[:,2])
                    self.zmax = np.amax(self.pos[:,2])
                
                # Prebuild Tree for Volume grid
                rot_pos = np.empty_like(self.pos)
                rot_pos[:,0] = self.pos[:,1] *1.1
                rot_pos[:,1] = self.pos[:,2] *1.1
                rot_pos[:,2] = self.pos[:,0] *1.1
                self.Tree = KDTree(rot_pos, leafsize=100)
        return self.pos
        
    def get_dataset(self, dataset):
        self.dataset_name = dataset
        with h5py.File(self.path, 'r') as file:
            self.dataset_data = file['PartType0'][dataset][()]
            self.dataset_min = np.amin(self.dataset_data)
            self.dataset_max = np.amax(self.dataset_data)
            return self.dataset_data
   
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
