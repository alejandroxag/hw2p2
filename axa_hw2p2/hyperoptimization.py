# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/hyper_p_opt.ipynb (unless otherwise specified).

__all__ = ['fit_predict']

# Cell
# imports
import torch
import time
from functools import partial
from hyperopt import fmin, tpe, hp, Trials, STATUS_OK
from hyperopt.pyll.base import scope
import json
from datetime import datetime

# Cell
def fit_predict(mc, verbose, trials=None):

    now = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    print(now)

    start_time = time.time()
    print('='*26)
    print(pd.Series(mc))
    print('='*26+'\n')

    train_dataset = FaceClassificationDataset(mode='train')
    val_dataset = FaceClassificationDataset(mode='val')

    train_loader = DataLoader(train_dataset,
                          shuffle=True,
                          batch_size=mc['batch_size'],
                          num_workers=num_workers,
                          pin_memory=True,
                          drop_last=True)

    val_loader = DataLoader(val_dataset,
                            shuffle=False,
                            batch_size=mc['batch_size'],
                            num_workers=num_workers,
                            pin_memory=True,
                            drop_last=True)

    model = FaceClassificationCNN(n_ch_input=mc['n_ch_input'],
                                  n_classes=mc['n_classes'],
                                  lr=mc['lr'],
                                  lr_decay=float(mc['lr_decay']),
                                  n_lr_decay_steps=int(mc['n_lr_decay_steps']),
                                  n_epochs=mc['n_epochs'],
                                  eval_steps=mc['eval_steps'])

    model.fit(train_loader=train_loader, val_loader=val_loader)

    s = 'hw2p2-s1' + '_' + now
    filename = f'../results/{s}.pth'

    best_model_config = {'loss': model.val_loss,
                         'mc': mc,
                         'run_time': time.time()-start_time,
                         'trajectories': model.trajectories,
                         'status': STATUS_OK}

    best_model_config = json.dumps(best_model_config)
    with open(f'best_model_config_{now}.json', 'w') as bfm:
        bfm.write(best_model_config)
    torch.save(model.model.state_dict(), filename)

    if trials is not None:
        results = {'loss': model.val_loss,
                   'mc': mc,
                   'run_time': time.time()-start_time,
                   'trajectories': model.trajectories,
                   'status': STATUS_OK}
        return results
    else:
        return model