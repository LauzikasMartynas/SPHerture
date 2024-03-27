import numpy as np
import h5py

from scipy.spatial import KDTree

import time

class H5Data():
    def __init__(self, path):
        self.path = None
        self.keys = []
        self.vector_keys = ['None']
        
        self.data = {}
        
        self.pos = None
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        self.zmin = None
        self.zmax = None
        
        self.iso_volume = None
        self.volume = None
        
        # Dataset properties
        self.dataset_name = ''
        self.dataset_data = None
        self.dataset_min = None
        self.dataset_max = None
        
        self.dataset_name_vec = ''
        self.dataset_data_vec = None

        with h5py.File(path, 'r') as file:
            self.path = path
            
            for root_key in file.keys():
                continue
                self.data[root_key] = {}
                self.data[root_key]['keys'] = list(file[root_key].keys())
                for attrib in file[root_key].attrs.keys():
                    self.data[root_key][attrib] = file[root_key].attrs[attrib]
            
            for key in file['PartType0'].keys():
                if key in ('Coordinates', 'HydroAcceleration'):
                    continue
                if isinstance(file['PartType0'][key][0], (list, tuple, np.ndarray)):
                    self.vector_keys.append(key)
                self.keys.append(key)
        
        self.get_pos()
            
    def get_pos(self):
        if self.pos is None:
            with h5py.File(self.path, 'r') as file:
                # Load and center
                self.pos = file['PartType0']['Coordinates'][()]
                self.hsml = file['PartType0']['SmoothingLength'][()]
                self.xmin = np.amin(self.pos[:,0])
                self.xmax = np.amax(self.pos[:,0])
                self.ymin = np.amin(self.pos[:,1])
                self.ymax = np.amax(self.pos[:,1])
                self.zmin = np.amin(self.pos[:,2])
                self.zmax = np.amax(self.pos[:,2])
        return self.pos
        
    def get_dataset(self, dataset):
        self.dataset_name = dataset
        with h5py.File(self.path, 'r') as file:
            self.dataset_name = dataset
            self.dataset_data = file['PartType0'][dataset][()]
            if isinstance(self.dataset_data[0], (list, tuple, np.ndarray)):
                self.dataset_data = np.linalg.norm(self.dataset_data, axis=1)

            self.dataset_min = np.amin(self.dataset_data)
            self.dataset_max = np.amax(self.dataset_data)
            return self.dataset_data

    def get_dataset_vec(self, dataset):
        if dataset not in self.vector_keys:
            return
        self.dataset_name_vec = dataset
        with h5py.File(self.path, 'r') as file:
            self.dataset_data_vec = file['PartType0'][self.dataset_name_vec][()]
            return self.dataset_data_vec

    def prebuild_volume(self):
        self.Tree = KDTree(self.pos[:,[1,0,2]], leafsize=100)
        
    def get_iso_volume(self, dataset, res):
        self.prebuild_volume()
        X, Y, Z = np.meshgrid(np.linspace(self.xmin, self.xmax, res, endpoint=True),
                              np.linspace(self.ymin, self.ymax, res, endpoint=True),
                             np.linspace(self.zmin, self.zmax, res, endpoint=True))
        self.XYZ = np.vstack((X.ravel(), Y.ravel(), Z.ravel())).T
        
        _, IND = self.Tree.query(self.XYZ, k=8, workers=-1)
        
        grid = np.mean(self.get_dataset(dataset)[IND], axis=1)
        
        #if dataset in self.vector_keys:
        #    self.volume = grid.reshape(res, res, res, 3)
        #else:
        self.iso_volume = grid.reshape(res, res, res)
        
        return self.iso_volume
    
    def get_volume(self, dataset, res):
        Tree = KDTree(self.pos[:,[1,2,0]], leafsize=100)
        
        X, Y, Z = np.meshgrid(np.linspace(self.xmin, self.xmax, res, endpoint=True),
                              np.linspace(self.ymin, self.ymax, res, endpoint=True),
                             np.linspace(self.zmin, self.zmax, res, endpoint=True))
        XYZ = np.vstack((X.ravel(), Y.ravel(), Z.ravel())).T
        
        _, IND = Tree.query(XYZ, k=8, workers=-1)
        
        grid = np.mean(self.get_dataset(dataset)[IND], axis=1)
        
        if dataset in self.vector_keys:
            self.volume = grid.reshape(res, res, res, 3)
        else:
            self.volume = grid.reshape(res, res, res)
        
        return self.volume
