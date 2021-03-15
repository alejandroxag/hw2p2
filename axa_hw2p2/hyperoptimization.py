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

from datasets import FaceClassificationDataset, FaceVerificationDataset
from losses import CenterLoss
from models.mobilenet import _BottleNeck, _MobileNetV2, MobileNetV2
# from models.resnet import
# from axa_hw2p2.datasets import FaceClassificationDataset, FaceVerificationDataset
# from axa_hw2p2.losses import CenterLoss
# from axa_hw2p2.models import _BottleNeck, _MobileNetV2, MobileNetV2

# Cell
def fit_predict(mc, verbose, trials=None, sample_size=None):
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
        assert mc['batch_size'] < 2*sample_size
        sample = np.array(range(sample_size))
        train_dataset = FaceClassificationDataset(sample, mode='train')
        val_c_dataset = FaceClassificationDataset(sample, mode='val')
        val_v_dataset = FaceVerificationDataset(sample, mode='val')

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

    model = MobileNetV2(n_in_ch_bn=mc['n_in_ch_bn'],
                        ls_out_ch_bn=mc['ls_out_ch_bn'],
                        ls_n_rep_bn=mc['ls_n_rep_bn'],
                        ls_stride_bn=mc['ls_stride_bn'],
                        ls_exp_fct_t_bn=mc['ls_exp_fct_t_bn'],
                        n_embeddings=mc['n_embeddings'],
                        n_classes=mc['n_classes'],
                        lr=mc['lr'],
                        lr_decay=mc['lr_decay'],
                        n_lr_decay_steps=mc['n_lr_decay_steps'],
                        center_loss=mc['center_loss'],
                        lr_cl=mc['lr_cl'],
                        alpha_cl=mc['alpha_cl'],
                        n_epochs=mc['n_epochs'],
                        eval_steps=mc['eval_steps'])

    model.fit(train_loader=train_loader,
              val_c_loader=val_c_loader,
              val_v_loader=val_v_loader)

    this_mc = {'loss': model.val_c_loss,
                'val_c_acc': model.val_c_acc,
                'val_v_acc': model.val_v_acc,
                'mc': mc,
                'run_time': time.time()-start_time,
                'trajectories': model.trajectories}

    this_mc = json.dumps(this_mc)

    s = 'hw2p2' + '_' + now
    filename = f'./results/{s}.pth'

    torch.save(model.model.state_dict(), filename)

    with open(f'./results/mc_{now}.json', 'w') as bfm:
        bfm.write(this_mc)

    if trials is not None:
        results = {'loss': model.val_c_loss,
                   'val_c_acc': model.val_c_acc,
                   'val_v_acc': model.val_v_acc,
                   'mc': mc,
                   'run_time': time.time()-start_time,
                   'trajectories': model.trajectories,
                   'status': STATUS_OK}
        return results
    else:
        return model