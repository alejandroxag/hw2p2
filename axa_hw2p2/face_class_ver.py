# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/face_class_ver.ipynb (unless otherwise specified).

__all__ = ['main']

# Cell
# imports
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision
from PIL import Image
from torch.nn.functional import cosine_similarity, adaptive_avg_pool2d
from torch.optim import Adam
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
from models import _BottleNeck, _MobileNetV2, MobileNetV2
from hyperoptimization import fit_predict
# from axa_hw2p2.datasets import FaceClassificationDataset, FaceVerificationDataset
# from axa_hw2p2.losses import CenterLoss
# from axa_hw2p2.models import _BottleNeck, _MobileNetV2, MobileNetV2
# from axa_hw2p2.hyperoptimization import fit_predict

# Cell
def main():

    # Hyperparameters space

    # space = {'n_in_ch_bn': hp.choice(label='n_in_ch_bn', options=[3]),
    #          'ls_out_ch_bn': hp.choice(label='ls_out_ch_bn',
    #                                    options=[[16, 24, 32, 64, 96, 160, 320]]),
    #          'ls_n_rep_bn': hp.choice(label='ls_n_rep_bn',
    #                                    options=[[1, 2, 3, 4, 3, 3, 1]]),
    #          'ls_stride_bn': hp.choice(label='ls_stride_bn',
    #                                    options=[[1, 2, 2, 2, 1, 2, 1]]),
    #          'ls_exp_fct_t_bn': hp.choice(label='ls_exp_fct_t_bn',
    #                                       options=[[1, 6, 6, 6, 6, 6, 6]]),
    #          'n_embeddings': hp.choice(label='n_embeddings', options=[1280]),
    #          'n_classes': hp.choice(label='n_classes', options=[6]),
    #          'batch_size': scope.int(hp.choice(label='batch_size', options=[64])),
    #          'lr': hp.loguniform(label='lr', low=np.log(5e-4), high=np.log(0.03)),
    #          'lr_decay': hp.choice(label='lr_decay', options=[0.9,0.92,0.94,
    #                                                           0.96,0.98,1]),
    #          'n_lr_decay_steps': hp.choice(label='n_lr_decay_steps', options=[1,2,4]),
    #          'lr_cl': hp.choice(label='lr_cl', options=[0.4,0.5,0.6]),
    #          'alpha_cl': hp.choice(label='alpha_cl', options=[0.001,0.01,0.1]),
    #          'n_epochs': hp.choice(label='n_epochs', options=[16]),
    #          'eval_steps': scope.int(hp.choice(label='eval_steps', options=[4])),}

    space = {'n_in_ch_bn': hp.choice(label='n_in_ch_bn', options=[3]),
             'ls_out_ch_bn': hp.choice(label='ls_out_ch_bn',
                                       options=[[16, 24, 32, 64, 96, 160, 320]]),
             'ls_n_rep_bn': hp.choice(label='ls_n_rep_bn',
                                       options=[[1, 2, 3, 4, 3, 3, 1]]),
             'ls_stride_bn': hp.choice(label='ls_stride_bn',
                                       options=[[1, 2, 2, 2, 1, 2, 1]]),
             'ls_exp_fct_t_bn': hp.choice(label='ls_exp_fct_t_bn',
                                          options=[[1, 6, 6, 6, 6, 6, 6]]),
             'n_embeddings': hp.choice(label='n_embeddings', options=[1280]),
             'n_classes': hp.choice(label='n_classes', options=[4000]),
             'batch_size': scope.int(hp.choice(label='batch_size', options=[512])),
             'lr': hp.loguniform(label='lr', low=np.log(5e-4), high=np.log(0.03)),
             'lr_decay': hp.choice(label='lr_decay', options=[0.9,0.92,0.94,
                                                              0.96,0.98,1]),
             'n_lr_decay_steps': hp.choice(label='n_lr_decay_steps', options=[1,2,4]),
             'lr_cl': hp.choice(label='lr_cl', options=[0.4,0.5,0.6]),
             'alpha_cl': hp.choice(label='alpha_cl', options=[0.001,0.01,0.1]),
             'n_epochs': hp.choice(label='n_epochs', options=[100]),
             'eval_steps': scope.int(hp.choice(label='eval_steps', options=[4])),}

    # Hyperparameters search
    trials = Trials()
    fmin_objective = partial(fit_predict, trials=trials, verbose=True)
    fmin(fmin_objective, space=space,
         algo=tpe.suggest, max_evals=20, trials=trials)

# Cell
if __name__ == "__main__":
    # os.chdir('nbs')
    main()