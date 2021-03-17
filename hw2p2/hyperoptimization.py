# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/hyper_p_opt.ipynb (unless otherwise specified).

__all__ = ['fit_predict']

# Cell
# imports
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision
from PIL import Image
from torch.nn.functional import cosine_similarity, adaptive_avg_pool2d
from torch.optim import Adam, SGD
from torch.optim.lr_scheduler import StepLR
from sklearn.metrics import roc_auc_score
import pandas as pd
from functools import partial
from hyperopt import fmin, tpe, hp, Trials, STATUS_OK
from hyperopt.pyll.base import scope
import json
from datetime import datetime
import os
import time

# from datasets import FaceClassificationDataset, FaceVerificationDataset
# from losses import CenterLoss
# from models.mobilenet import *
# from models.resnet import *
from .datasets import FaceClassificationDataset, FaceVerificationDataset
from .losses import CenterLoss
from .models.mobilenet import *
from .models.resnet import *

# Cell
def fit_predict(mc, verbose, trials=None, sample_size=None):

    assert mc['model'] in ['resnet18', 'resnet34', 'resnet50', 'mobilenet']

    print(f'\nCurrent directory: {os.getcwd()}\n')
    now = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    print(now)

    start_time = time.time()
    print('='*26)
    print(pd.Series(mc))
    print('='*26+'\n')

    num_workers = 8 if torch.cuda.is_available() else 0

    if sample_size == None:
        train_dataset = FaceClassificationDataset(mode='train')
        val_c_dataset = FaceClassificationDataset(mode='val')
        val_v_dataset = FaceVerificationDataset(mode='val')
    else:
        sample = np.array(range(sample_size))
        train_dataset = FaceClassificationDataset(sample, mode='train')
        val_c_dataset = FaceClassificationDataset(sample, mode='val')
        val_v_dataset = FaceVerificationDataset(sample, mode='val')

    print(f'train_dataset_len: {len(train_dataset)}, val_c_dataset_len: {len(val_c_dataset)}, val_v_dataset_len: {len(val_v_dataset)}')

    train_loader = DataLoader(train_dataset,
                              shuffle=True,
                              batch_size=mc['batch_size'],
                              num_workers=num_workers,
                              pin_memory=torch.cuda.is_available(),
                              drop_last=True)
    val_c_loader = DataLoader(val_c_dataset,
                              shuffle=False,
                              batch_size=mc['batch_size'],
                              num_workers=num_workers,
                              pin_memory=torch.cuda.is_available(),
                              drop_last=True)
    val_v_loader = DataLoader(val_v_dataset,
                              shuffle=False,
                              batch_size=mc['batch_size'],
                              num_workers=num_workers,
                              pin_memory=torch.cuda.is_available(),
                              drop_last=True)

    assert len(train_loader) > 0
    assert len(val_c_loader) > 0
    assert len(val_v_loader) > 0

    if mc['model'] == 'mobilenet':
        model = MobileNetV2(n_in_ch_bn=mc['in_channels'],
                            ls_out_ch_bn=[16, 24, 32, 64, 96, 160, 320],
                            ls_n_rep_bn=[1, 2, 3, 4, 3, 3, 1],
                            ls_stride_bn=[1, 2, 2, 2, 1, 2, 1],
                            ls_exp_fct_t_bn=[1, 6, 6, 6, 6, 6, 6],
                            n_embeddings=1280,
                            n_classes=mc['n_classes'],
                            lr=mc['lr'],
                            lr_decay=mc['lr_decay'],
                            n_lr_decay_steps=mc['n_lr_decay_steps'],
                            center_loss=mc['center_loss'],
                            lr_cl=mc['lr_cl'],
                            alpha_cl=mc['alpha_cl'],
                            n_epochs=mc['n_epochs'],
                            eval_steps=mc['eval_steps'])
    else:
        if  mc['model'] == 'resnet18': resnet_n_layers = 18
        if  mc['model'] == 'resnet34': resnet_n_layers = 34
        if  mc['model'] == 'resnet50': resnet_n_layers = 50

        model = ResNetN(resnet_n_layers,
                        in_channels=mc['in_channels'],
                        n_classes=mc['n_classes'],
                        lr=mc['lr'],
                        lr_decay=mc['lr_decay'],
                        n_lr_decay_steps=mc['n_lr_decay_steps'],
                        center_loss = mc['center_loss'],
                        lr_cl=mc['lr_cl'],
                        alpha_cl=mc['alpha_cl'],
                        n_epochs=mc['n_epochs'],
                        eval_steps=mc['eval_steps'])


    model.fit(train_loader=train_loader,
              val_c_loader=val_c_loader,
              val_v_loader=val_v_loader)

    if trials is not None:
        results = {'loss': model.train_loss,
                   'val_c_loss': model.val_c_loss,
                   'train_c_acc': model.train_c_acc,
                   'val_c_acc': model.val_c_acc,
                   'val_v_acc': model.val_v_acc,
                   'mc': mc,
                   'run_time': time.time()-start_time,
                   'trajectories': model.trajectories,
                   'model': model,
                   'time_stamp': now,
                   'status': STATUS_OK}
        return results
    else:
        return model