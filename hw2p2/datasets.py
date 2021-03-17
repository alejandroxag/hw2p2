# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/datasets.ipynb (unless otherwise specified).

__all__ = ['FaceClassificationDataset', 'FaceVerificationDataset']

# Cell
# imports
import os
import numpy as np
import torch
from torch.utils.data import Dataset
import torchvision
from torchvision import transforms
from PIL import Image

# Cell
class FaceClassificationDataset(Dataset):
    """
    """
    def __init__(self,
                 sample=None,
                 mode='train'):

        # Assertions to avoid wrong inputs
        assert mode in ['train', 'val', 'test']
        assert mode == 'test' and sample == None or \
            mode != 'test'
        if sample is not None:
            assert isinstance(sample, (list, np.ndarray))

        self.mode = mode

        # Directory setup
        if mode == 'train':
            self.data_dir = './data/s1/train_data'
        elif mode == 'val':
            self.data_dir = './data/s1/val_data'
        else:
            self.data_dir = './data/s1/test_data'

        # Labels
        if (mode == 'train' or mode == 'val'):
            if sample is not None:
                sample = np.array(sample)
                assert sample.min() >= 0
                self.labels = np.array(sample)
                self.labels.sort(axis=0)
            else:
               self.labels = [int(d) for d in os.listdir(self.data_dir)]
               self.labels = np.array(self.labels)
               self.labels.sort(axis=0)
        else:
            self.labels = os.listdir(self.data_dir)
            self.labels = np.array([int(f.split('.')[0]) for f in self.labels])
            self.labels.sort(axis=0)

        if mode != 'test':
            self.map_files = []
            for l in self.labels:
                temp_ls = [(l, f) for f in \
                    os.listdir(os.path.join(self.data_dir, str(l)))]
                temp_ls = [(t[0], t[1]) for t in temp_ls]
                self.map_files.append(temp_ls)

            self.map_files = [t for sl in self.map_files for t in sl]
            self.labels = [t[0] for t in self.map_files]
            self.X = [t[1] for t in self.map_files]
        else:
            self.X = [str(s) + '.jpg' for s in self.labels]
            self.labels = ['' for s in self.labels]

    def __len__(self): return len(self.X)

    def __getitem__(self, idx):

        if self.mode == 'train':
            trans_list = [transforms.Resize(80),
                          transforms.RandomCrop(64),
                          transforms.RandomHorizontalFlip(),
                          transforms.ToTensor(),
                          transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                               std=[0.229, 0.224, 0.225])]
        else:
            trans_list = [transforms.ToTensor(),
                          transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                               std=[0.229, 0.224, 0.225])]

        preprocess = transforms.Compose(trans_list)

        image_path = os.path.join(self.data_dir,
                                  str(self.labels[idx]),
                                  self.X[idx])
        image_tensor = Image.open(image_path)
        image_tensor = preprocess(image_tensor)

        if self.mode == 'test': return image_tensor
        else: return image_tensor, self.labels[idx]

# Cell
class FaceVerificationDataset(Dataset):
    """
    """
    def __init__(self,
                 sample=None,
                 mode='val'):

        # Assertions to avoid wrong inputs
        assert mode in ['val', 'test']
        assert mode == 'test' and sample == None or \
            mode != 'test'
        if sample is not None:
            assert isinstance(sample, (list, np.ndarray))

        self.mode = mode
        self.data_dir = './data/s2/'

        # Directory setup
        if mode == 'val':
            self.pairs_file = \
                './data/s2/verification_pairs_val.txt'
        else:
            self.pairs_file = \
                './data/s2/verification_pairs_test.txt'

        with open(self.pairs_file) as f:
            self.pairs = [l.rstrip().split() for l in f]

        if sample is not None:
            sample = np.array(sample)
            sample.sort(axis=0)
            self.pairs = [self.pairs[i] for i in sample]

    def __len__(self): return len(self.pairs)

    def __getitem__(self, idx):

        trans_list = [transforms.ToTensor(),
                          transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                               std=[0.229, 0.224, 0.225])]

        preprocess = transforms.Compose(trans_list)

        image_tensor_0 = Image.open(os.path.join(self.data_dir,self.pairs[idx][0]))
        image_tensor_1 = Image.open(os.path.join(self.data_dir,self.pairs[idx][1]))
        image_tensor_0 = preprocess(image_tensor_0)
        image_tensor_1 = preprocess(image_tensor_1)
        if self.mode == 'test':
            return image_tensor_0, image_tensor_1
        else:
            return image_tensor_0, image_tensor_1, int(self.pairs[idx][2])