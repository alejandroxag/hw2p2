# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/models.ipynb (unless otherwise specified).

__all__ = ['MobileNetV2']

# Cell
#imports
import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam, SGD
from torch.optim.lr_scheduler import StepLR
from torch.nn.functional import cosine_similarity, adaptive_avg_pool2d
from sklearn.metrics import roc_auc_score
from losses import CenterLoss
# from axa_hw2p2.losses import CenterLoss

# Cell
class _BottleNeck(nn.Module):
    """
    """
    def __init__(self,
                 n_input_ch: int,
                 n_output_ch: int,
                 stride: int,
                 exp_fct_t: int):
        """
        """
        super(_BottleNeck, self).__init__()
        self.n_input_ch = n_input_ch
        self.n_output_ch = n_output_ch
        self.stride = stride

        # Expansion block:
        # (batch_size, height, width, n_input_ch) ->
        # (batch_size, height, width, exp_fct_t*n_input_ch)
        # kernel size: 1, stride: 1, padding: 0, groups: 1.
        exp_block = []
        exp_block.append(nn.Conv2d(in_channels=n_input_ch,
                                   out_channels=exp_fct_t*n_input_ch,
                                   kernel_size=1,
                                   stride=1,
                                   padding=0,
                                   groups=1,
                                   bias=False))
        exp_block.append(nn.BatchNorm2d(num_features=exp_fct_t*n_input_ch))
        exp_block.append(nn.ReLU6())

        # Depthwise convolutional block:
        # (batch_size, height, width, exp_fct_t*n_input_ch) ->
        # (batch_size, height/stride, width/stride, exp_fct_t*n_input_ch)
        # kernel size: 3, stride: stride,
        # padding: 1, groups: exp_fct_t*n_input_ch.
        dw_conv_block = []
        dw_conv_block.append(nn.Conv2d(in_channels=exp_fct_t*n_input_ch,
                                       out_channels=exp_fct_t*n_input_ch,
                                       kernel_size=3,
                                       stride=stride,
                                       padding=1,
                                       groups=exp_fct_t*n_input_ch,
                                       bias=False))
        dw_conv_block.append(nn.BatchNorm2d(num_features=exp_fct_t*n_input_ch))
        dw_conv_block.append(nn.ReLU6())

        # Depthwise convolutional block:
        # (batch_size, height, width, exp_fct_t*n_input_ch) ->
        # (batch_size, height/stride, width/stride, n_output_ch)
        # kernel size: 1, stride: 1, padding: 0, groups: 1.
        proj_block = []
        proj_block.append(nn.Conv2d(in_channels=exp_fct_t*n_input_ch,
                                    out_channels=n_output_ch,
                                    kernel_size=1,
                                    stride=1,
                                    padding=0,
                                    groups=1,
                                    bias=False))
        proj_block.append(nn.BatchNorm2d(num_features=n_output_ch))

        self.block = exp_block + dw_conv_block + proj_block
        self.block = nn.Sequential(*self.block)

    def forward(self, x):
        """
        """
        if self.stride == 1 and self.n_input_ch == self.n_output_ch:
            return x + self.block(x)
        else:
            return self.block(x)




# Cell
class _MobileNetV2(nn.Module):
    """
    """
    def __init__(self,
                 n_in_ch_bn: int,
                 ls_out_ch_bn: list,
                 ls_n_rep_bn: list,
                 ls_stride_bn: list,
                 ls_exp_fct_t_bn: list,
                 n_embeddings: int,
                 n_classes: int):

        super(_MobileNetV2, self).__init__()

        assert len(ls_out_ch_bn) == len(ls_n_rep_bn)
        assert len(ls_n_rep_bn) == len(ls_stride_bn)
        assert len(ls_stride_bn) == len(ls_exp_fct_t_bn)

        # Initial fully convolution block
        # (batch_size, 64, 64, 3) ->
        # (batch_size, 64, 64, n_in_ch_bn)
        # kernel size: 1, stride: 1, padding: 0, groups: 1.
        # (stride is 1 instead of two because images are small (64x64))
        block1 = []
        block1.append(nn.Conv2d(in_channels=3,
                                out_channels=n_in_ch_bn,
                                kernel_size=3,
                                stride=1,
                                padding=0,
                                groups=1,
                                bias=False))
        block1.append(nn.BatchNorm2d(n_in_ch_bn))
        block1.append(nn.ReLU6())

        # Bottlenecks
        bottlenecks = []
        n_input_ch = n_in_ch_bn

        for i in range(len(ls_out_ch_bn)):

            c = ls_out_ch_bn[i]
            n = ls_n_rep_bn[i]
            s = ls_stride_bn[i]
            t = ls_exp_fct_t_bn[i]

            for j in range(n):

                if j == 0: stride = 1
                else: stride = s
                bottlenecks.append(_BottleNeck(n_input_ch=n_input_ch,
                                               n_output_ch=c,
                                               stride=stride,
                                               exp_fct_t=t))
                n_input_ch = c

        # Last 1x1 convolution block
        blockn = []
        blockn.append(nn.Conv2d(in_channels=n_input_ch,
                                out_channels=n_embeddings,
                                kernel_size=1,
                                stride=1,
                                padding=0,
                                groups=1,
                                bias=False))
        blockn.append(nn.BatchNorm2d(n_embeddings))
        blockn.append(nn.ReLU6())

        self.net = block1 + bottlenecks + blockn
        self.net = nn.Sequential(*self.net)
        self.classifier = nn.Linear(in_features=n_embeddings,
                                    out_features=n_classes)

    def forward(self, x):
        """
        """
        x = self.net(x)
        x = adaptive_avg_pool2d(x, 1).reshape(x.shape[0], -1)
        embeddings = x
        cl_output = self.classifier(x)

        return embeddings, cl_output






# Cell
class MobileNetV2():
    """
    """
    def __init__(self,
                 n_in_ch_bn: int,
                 ls_out_ch_bn: list,
                 ls_n_rep_bn: list,
                 ls_stride_bn: list,
                 ls_exp_fct_t_bn: list,
                 n_embeddings: int,
                 n_classes: int,
                 lr: float,
                 lr_decay: float,
                 n_lr_decay_steps: int,
                 center_loss: bool,
                 lr_cl: float,
                 alpha_cl: float,
                 n_epochs: int,
                 eval_steps: int):

        # Architecture parameters
        self.n_in_ch_bn = n_in_ch_bn
        self.ls_out_ch_bn = ls_out_ch_bn
        self.ls_n_rep_bn = ls_n_rep_bn
        self.ls_stride_bn = ls_stride_bn
        self.ls_exp_fct_t_bn = ls_exp_fct_t_bn
        self.n_embeddings = n_embeddings
        self.n_classes = n_classes
        self.center_loss = center_loss

        # Optimization parameters
        self.lr = lr
        self.lr_decay = lr_decay
        self.n_lr_decay_steps = n_lr_decay_steps
        self.lr_cl = lr_cl
        self.alpha_cl = alpha_cl
        self.n_epochs = n_epochs
        self.eval_steps = eval_steps

        self.model = _MobileNetV2(n_in_ch_bn=n_in_ch_bn,
                                  ls_out_ch_bn=ls_out_ch_bn,
                                  ls_n_rep_bn=ls_n_rep_bn,
                                  ls_stride_bn=ls_stride_bn,
                                  ls_exp_fct_t_bn=ls_exp_fct_t_bn,
                                  n_embeddings=n_embeddings,
                                  n_classes=n_classes)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def fit(self, train_loader, val_c_loader, val_v_loader):

        print("="*30 + 'Start Fitting' + "="*30)
        self.model.to(self.device)
        self.model.train()

        cross_entroypy_loss_f = nn.CrossEntropyLoss()
        center_loss_f = CenterLoss(num_classes=self.n_classes,
                                   feat_dim=self.n_embeddings,
                                   use_gpu=torch.cuda.is_available())

        # optimizer = Adam(self.model.parameters(),
        #                  lr=self.lr,
        #                  weight_decay=0.00004)

        # optimizer_centerloss = Adam(center_loss_f.parameters(),
        #                             lr=self.lr_cl)

        optimizer = SGD(self.model.parameters(),
                        lr=self.lr,
                        weight_decay=0.00004,
                        momentum=0.9)

        optimizer_centerloss = SGD(center_loss_f.parameters(),
                                   lr=self.lr_cl)

        scheduler = StepLR(optimizer=optimizer,
                           step_size=self.n_epochs//self.n_lr_decay_steps,
                           gamma=self.lr_decay)

        self.train_loss = -1
        self.val_c_loss = -1
        self.val_c_acc = 0
        self.val_v_acc = 0
        self.trajectories = {'epoch': [],
                             'train_loss': [],
                             'val_c_loss': [],
                             'val_c_acc': [],
                             'val_v_acc':[]}

        for epoch in range(self.n_epochs):

            train_loss = 0

            for batch_idx, (img, label) in enumerate(train_loader):
                # print(f'Train. epoch: {epoch}, batch_idx: {batch_idx}')
                img = img.to(self.device)
                label = label.to(self.device)

                embeddings, cl_output = self.model(img)

                if self.center_loss == True:
                    loss = self.alpha_cl * center_loss_f(embeddings, label) + \
                       cross_entroypy_loss_f(cl_output, label)

                else:
                    loss = cross_entroypy_loss_f(cl_output, label)

                optimizer.zero_grad()

                if self.center_loss == True:
                    optimizer_centerloss.zero_grad()

                loss.backward()

                if self.center_loss == True:
                    for p in center_loss_f.parameters():
                        p.grad.data *= (1./self.alpha_cl)


                optimizer.step()

                if self.center_loss == True:
                    optimizer_centerloss.step()

                scheduler.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            if epoch % self.eval_steps == 0:
                val_c_loss, val_c_acc, val_v_acc = \
                    self.evaluate_performance(val_c_loader,
                                              val_v_loader)

                self.trajectories['epoch'].append(epoch)
                self.trajectories['train_loss'].append(train_loss)
                self.trajectories['val_c_loss'].append(val_c_loss)
                self.trajectories['val_c_acc'].append(val_c_acc)
                self.trajectories['val_v_acc'].append(val_v_acc)

                display_str = f'epoch: {epoch} '
                display_str += f'train_loss: {np.round(train_loss,4)} '
                display_str += f'val_c_loss: {np.round(val_c_loss,4)} '
                display_str += f'val_c_acc: {np.round(val_c_acc,4):.2%} '
                display_str += f'val_v_acc: {np.round(val_v_acc,4):.2%} '
                print(display_str)

                if self.val_c_loss > val_c_loss: self.val_c_loss = val_c_loss
                if self.train_loss > train_loss: self.train_loss = train_loss
                if self.val_c_acc < val_c_acc: self.val_c_acc = val_c_acc
                if self.val_v_acc < val_v_acc: self.val_v_acc = val_v_acc

        print("="*72+"\n")


    def evaluate_performance(self, val_c_loader, val_v_loader):

        cross_entroypy_loss_f = nn.CrossEntropyLoss()
        center_loss_f = CenterLoss(num_classes=self.n_classes,
                                   feat_dim=self.n_embeddings,
                                   use_gpu=torch.cuda.is_available())

        self.model.to(self.device)
        self.model.eval()

        val_c_loss = 0.0
        total_predictions = 0.0
        correct_predictions = 0.0

        with torch.no_grad():
            for batch_idx, (img, label) in enumerate(val_c_loader):
                # print(f'Val class. batch_idx: {batch_idx}')
                img = img.to(self.device)
                label = label.to(self.device)

                embeddings, cl_output = self.model(img)

                if self.center_loss == True:
                    loss = self.alpha_cl * center_loss_f(embeddings, label) + \
                       cross_entroypy_loss_f(cl_output, label)

                else:
                    loss = cross_entroypy_loss_f(cl_output, label)

                loss = loss.detach()
                val_c_loss += loss.item()

                # predicted = torch.argmax(cl_output.data, 1)
                predicted = torch.max(F.softmax(cl_output, dim=1), 1).view(-1)
                total_predictions += len(label)
                # correct_predictions += (predicted == label).sum().item()
                correct_predictions += torch.sum(torch.eq(predicted, label)).item()

        val_c_loss /= len(val_c_loader)
        val_c_acc = correct_predictions/total_predictions

        similarity = np.array([])
        ver_bool = np.array([])

        with torch.no_grad():
            for batch_idx, (img_0, img_1, target) in enumerate(val_v_loader):
                # print(f'Val ver. batch_idx: {batch_idx}')
                img_0 = img_0.to(self.device)
                img_1 = img_1.to(self.device)

                emb_0 = self.model(img_0)[0]
                emb_1 = self.model(img_1)[0]

                sim_score = cosine_similarity(emb_0, emb_1)
                similarity = np.append(similarity, sim_score.cpu().numpy().reshape(-1))
                ver_bool = np.append(ver_bool, target)

        val_v_acc = roc_auc_score(ver_bool, similarity)

        return val_c_loss, val_c_acc, val_v_acc
