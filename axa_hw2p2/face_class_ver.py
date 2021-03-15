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
from models.mobilenet import *
from models.resnet import *
from hyperoptimization import fit_predict
# from axa_hw2p2.datasets import FaceClassificationDataset, FaceVerificationDataset
# from axa_hw2p2.losses import CenterLoss
# from axa_hw2p2.models.mobilenet import *
# from axa_hw2p2.models.resnet import *
# from axa_hw2p2.hyperoptimization import fit_predict

# Cell
def main(model, batch_size, sample_size=None, max_evals=20):

    # Hyperparameters space
    space = {'model': hp.choice(label='model', options=[model]),
             'in_channels': hp.choice(label='in_channels', options=[3]),
            #  'n_classes': hp.choice(label='n_classes', options=[4000]),
             'batch_size': scope.int(hp.choice(label='batch_size', options=[batch_size])),
             'lr': hp.loguniform(label='lr', low=np.log(5e-2), high=np.log(2e-1)),
             'lr_decay': hp.choice(label='lr_decay', options=[0.96,0.97,0.98,0.99,1]),
             'n_lr_decay_steps': hp.choice(label='n_lr_decay_steps', options=[1,2,4]),
             'center_loss': hp.choice(label='center_loss', options=[True]),
             'lr_cl': hp.choice(label='lr_cl', options=[0.4,0.5,0.6]),
             'alpha_cl': hp.choice(label='alpha_cl', options=[0.01,0.1,1]),
             'n_epochs': hp.choice(label='n_epochs', options=[25]),
             'eval_steps': scope.int(hp.choice(label='eval_steps', options=[4])),}

    if sample_size==None:
        space['n_classes'] = hp.choice(label='n_classes', options=[4000])
    else:
        space['n_classes'] = hp.choice(label='n_classes', options=[sample_size])

    # Hyperparameters search
    trials = Trials()
    fmin_objective = partial(fit_predict, verbose=True, trials=trials, sample_size=sample_size)
    fmin(fmin_objective, space=space,
         algo=tpe.suggest, max_evals=max_evals, trials=trials)

# Cell
if __name__ == "__main__":
    main(model='resnet50', batch_size=256, sample_size=500, max_evals=20)