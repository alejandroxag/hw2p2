# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/models_resnet.ipynb (unless otherwise specified).

__all__ = ['Conv2dAuto', 'conv3x3', 'conv3x3', 'conv', 'ResidualBlock', 'ResNetResidualBlock', 'conv_bn',
           'ResNetBasicBlock', 'ResNetBottleNeckBlock', 'ResNetLayer', 'ResNetEncoder', 'ResnetDecoder', 'resnet18',
           'resnet34', 'resnet50', 'ResNetN']

# Cell
#imports
import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam, SGD
from torch.optim.lr_scheduler import StepLR
from torch.nn.functional import cosine_similarity, adaptive_avg_pool2d, softmax
from sklearn.metrics import roc_auc_score
from functools import partial
# from losses import CenterLoss
from ..losses import CenterLoss

# Cell
class Conv2dAuto(nn.Conv2d):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.padding =  (self.kernel_size[0] // 2,
                         self.kernel_size[1] // 2) # dynamic add padding based on the kernel_size

conv3x3 = partial(Conv2dAuto, kernel_size=3, bias=False)

# Cell
conv3x3 = partial(Conv2dAuto, kernel_size=3, bias=False)
conv = conv3x3(in_channels=32, out_channels=64)


# Cell
class ResidualBlock(nn.Module):
    def __init__(self,
                 in_channels: int,
                 out_channels: int):
        super().__init__()
        self.in_channels, self.out_channels =  in_channels, out_channels
        self.blocks = nn.Identity()
        self.activation_f = nn.ReLU(inplace=True)
        self.shortcut = nn.Identity()

    def forward(self, x):
        residual = x
        if self.should_apply_shortcut: residual = self.shortcut(x)
        x = self.blocks(x)
        x += residual
        return x

    @property
    def should_apply_shortcut(self):
        return self.in_channels != self.out_channels

# Cell
class ResNetResidualBlock(ResidualBlock):
    def __init__(self,
                 in_channels: int,
                 out_channels: int,
                 expansion=1,
                 downsampling=1,
                 conv=conv3x3,
                 *args,
                 **kwargs):
        super().__init__(in_channels=in_channels,
                         out_channels=out_channels,
                         *args,
                         **kwargs)
        self.expansion = expansion
        self.downsampling = downsampling
        self.conv = conv

        if self.should_apply_shortcut:
            self.shortcut = nn.Sequential(nn.Conv2d(self.in_channels,
                                                    self.expanded_channels,
                                                    kernel_size=1,
                                                    stride=self.downsampling,
                                                    bias=False),
                                          nn.BatchNorm2d(self.expanded_channels))
        else: None

    @property
    def expanded_channels(self):
        return self.out_channels * self.expansion

    @property
    def should_apply_shortcut(self):
        return self.in_channels != self.expanded_channels

# Cell
def conv_bn(in_channels:int,
            out_channels: int,
            conv,
            *args,
            **kwargs):

    return nn.Sequential(conv(in_channels, out_channels, *args, **kwargs), nn.BatchNorm2d(out_channels))


# Cell
class ResNetBasicBlock(ResNetResidualBlock):
    """
    Basic ResNet block composed by two layers of 3x3conv/batchnorm/activation
    """
    expansion = 1
    def __init__(self,
                 in_channels: int,
                 out_channels: int,
                 *args,
                 **kwargs):
        super().__init__(in_channels=in_channels,
                         out_channels=out_channels,
                         *args,
                         **kwargs)

        self.blocks = nn.Sequential(
            conv_bn(in_channels=self.in_channels,
                    out_channels=self.out_channels,
                    conv=self.conv,
                    bias=False,
                    stride=self.downsampling),
            self.activation_f,
            conv_bn(in_channels=self.out_channels,
                    out_channels=self.expanded_channels,
                    conv=self.conv,
                    bias=False),
        )

# Cell
class ResNetBottleNeckBlock(ResNetResidualBlock):
    expansion = 4
    def __init__(self,
                 in_channels: int,
                 out_channels: int,
                 *args,
                 **kwargs):
        super().__init__(in_channels=in_channels,
                         out_channels=out_channels,
                         expansion=4,
                         *args,
                         **kwargs)
        self.blocks = nn.Sequential(
           conv_bn(in_channels=self.in_channels,
                   out_channels=self.out_channels,
                   conv=self.conv,
                   kernel_size=1),
           self.activation_f,
           conv_bn(in_channels=self.out_channels,
                   out_channels=self.out_channels,
                   conv=self.conv,
                   kernel_size=3,
                   stride=self.downsampling),
           self.activation_f,
           conv_bn(in_channels=self.out_channels,
                   out_channels=self.expanded_channels,
                   conv=self.conv,
                   kernel_size=1),
        )

# Cell
class ResNetLayer(nn.Module):
    """
    A ResNet layer composed by `n` blocks stacked one after the other
    """
    def __init__(self,
                 in_channels: int,
                 out_channels: int,
                 block=ResNetBasicBlock,
                 n_blocks=1,
                 *args,
                 **kwargs):
        super().__init__()
        # 'We perform downsampling directly by convolutional layers that have a stride of 2.'
        if in_channels != out_channels: downsampling = 2
        else: downsampling = 1

        self.blocks = nn.Sequential(
            block(in_channels=in_channels ,
                  out_channels=out_channels,
                  *args,
                  **kwargs,
                  downsampling=downsampling),
            *[block(in_channels=out_channels * block.expansion,
                    out_channels=out_channels,
                    downsampling=1,
                    *args,
                    **kwargs) for _ in range(n_blocks - 1)]
        )

    def forward(self, x):
        x = self.blocks(x)
        return x

# Cell
class ResNetEncoder(nn.Module):
    """
    ResNet encoder composed by layers with increasing features.
    """
    def __init__(self,
                 in_channels=3,
                 blocks_sizes=[64, 128, 256, 512],
                 deepths=[2,2,2,2],
                 block=ResNetBasicBlock,
                 *args,
                 **kwargs):
        super().__init__()

        self.blocks_sizes = blocks_sizes

        self.gate = nn.Sequential(
            nn.Conv2d(in_channels=in_channels,
                      out_channels=self.blocks_sizes[0],
                      kernel_size=7,
                      stride=2,
                      padding=3,
                      bias=False),
            nn.BatchNorm2d(self.blocks_sizes[0]),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3,
                         stride=2,
                         padding=1)
        )

        self.in_out_block_sizes = list(zip(blocks_sizes, blocks_sizes[1:]))

        self.blocks = nn.ModuleList([
            ResNetLayer(in_channels=blocks_sizes[0],
                        out_channels=blocks_sizes[0],
                        n_blocks=deepths[0],
                        block=block,
                        *args,
                        **kwargs),
            *[ResNetLayer(in_channels=in_channels * block.expansion,
                          out_channels=out_channels,
                          n_blocks=n,
                          block=block,
                          *args,
                          **kwargs)
              for (in_channels, out_channels), n in zip(self.in_out_block_sizes, deepths[1:])]
        ])


    def forward(self, x):
        x = self.gate(x)
        for block in self.blocks:
            x = block(x)
        return x

# Cell
class ResnetDecoder(nn.Module):
    """
    This class represents the tail of ResNet. It performs a global pooling and maps the output to the
    correct class by using a fully connected layer.
    """
    def __init__(self,
                 in_features: int,
                 n_classes: int):
        super().__init__()
        self.avg = nn.AdaptiveAvgPool2d((1, 1))
        self.decoder = nn.Linear(in_features=in_features,
                                 out_features=n_classes)

    def forward(self, x):
        x = self.avg(x)
        embeddings = x.view(x.size(0), -1)
        x = self.decoder(embeddings)
        return embeddings, x

# Cell
class _ResNet(nn.Module):

    def __init__(self,
                 in_channels: int,
                 n_classes: int,
                 *args,
                 **kwargs):
        super().__init__()
        self.encoder = ResNetEncoder(in_channels=in_channels,
                                     *args,
                                     **kwargs)

        n_features = self.encoder.blocks[-1].blocks[-1].expanded_channels
        self.decoder = ResnetDecoder(in_features=n_features,
                                     n_classes=n_classes)

    def forward(self, x):
        x = self.encoder(x)
        embeddings, x = self.decoder(x)
        return embeddings, x

# Cell
def resnet18(in_channels: int,
             n_classes: int,
             block=ResNetBasicBlock,
             *args,
             **kwargs):

    return _ResNet(in_channels=in_channels,
                   n_classes=n_classes,
                   block=block,
                   deepths=[2, 2, 2, 2],
                   *args,
                   **kwargs)

# Cell
def resnet34(in_channels: int,
             n_classes: int,
             block=ResNetBasicBlock,
             *args,
             **kwargs):

    return _ResNet(in_channels=in_channels,
                   n_classes=n_classes,
                   block=block,
                   deepths=[3, 4, 6, 3],
                   *args,
                   **kwargs)

# Cell
def resnet50(in_channels: int,
             n_classes: int,
             block=ResNetBottleNeckBlock,
             *args,
             **kwargs):

    return _ResNet(in_channels=in_channels,
                   n_classes=n_classes,
                   block=block,
                   deepths=[3, 4, 6, 3],
                   *args,
                   **kwargs)

# Cell
class ResNetN():
    """
    """
    def __init__(self,
                 res_net_deepth,
                 in_channels: int,
                 n_classes: int,
                 lr: float,
                 lr_decay: float,
                 n_lr_decay_steps: int,
                 center_loss: bool,
                 lr_cl: float,
                 alpha_cl: float,
                 n_epochs: int,
                 eval_steps: int):

        assert res_net_deepth in [18, 34, 50]

        # Architecture parameters
        self.in_channels = in_channels
        self.n_classes = n_classes
        self.center_loss = center_loss
        if res_net_deepth == 50: self.n_embeddings = 2048
        else: self.n_embeddings = 512

        # Optimization parameters
        self.lr = lr
        self.lr_decay = lr_decay
        self.n_lr_decay_steps = n_lr_decay_steps
        self.lr_cl = lr_cl
        self.alpha_cl = alpha_cl
        self.n_epochs = n_epochs
        self.eval_steps = eval_steps

        if res_net_deepth == 18: self.model = resnet18
        if res_net_deepth == 34: self.model = resnet34
        if res_net_deepth == 50: self.model = resnet50

        self.model = self.model(in_channels=in_channels,
                                n_classes=n_classes)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.train_loss = -1
        self.val_c_loss = -1
        self.train_c_acc = 0
        self.val_c_acc = 0
        self.val_v_acc = 0
        self.trajectories = {'epoch': [],
                             'train_loss': [],
                             'train_c_acc': [],
                             'val_c_loss': [],
                             'val_c_acc': [],
                             'val_v_acc':[]}

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

        break_flag = False

        for epoch in range(self.n_epochs):

            if break_flag: continue

            train_loss = 0
            train_correct_predictions = 0
            train_total_predictions = 0

            for batch_idx, (img, label) in enumerate(train_loader):
                img = img.to(self.device)
                label = label.to(self.device)

                embeddings, cl_output = self.model(img)

                if self.center_loss == True:
                    loss = self.alpha_cl * center_loss_f(embeddings, label) + \
                       cross_entroypy_loss_f(cl_output, label)

                else:
                    loss = cross_entroypy_loss_f(cl_output, label)

                predicted = torch.argmax(cl_output.data, 1)
                train_correct_predictions += (predicted == label).sum().item()
                train_total_predictions += len(label)

                optimizer.zero_grad()

                if self.center_loss == True:
                    optimizer_centerloss.zero_grad()

                loss.backward()

                if self.center_loss == True:
                    for p in center_loss_f.parameters():
                        p.grad.data *= (1./self.alpha_cl)


                if np.isnan(float(loss)):
                    print('muerte y destruccion')
                    break
                    break_flag = True

                nn.utils.clip_grad_norm_(self.model.parameters(), 10)
                optimizer.step()

                if self.center_loss == True:
                    optimizer_centerloss.step()

                scheduler.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)
            train_c_acc = train_correct_predictions/train_total_predictions

            if epoch % self.eval_steps == 0:
                val_c_loss, val_c_acc, val_v_acc = \
                    self.evaluate_performance(val_c_loader,
                                              val_v_loader)

                self.trajectories['epoch'].append(epoch)
                self.trajectories['train_loss'].append(train_loss)
                self.trajectories['train_c_acc'].append(train_c_acc)
                self.trajectories['val_c_loss'].append(val_c_loss)
                self.trajectories['val_c_acc'].append(val_c_acc)
                self.trajectories['val_v_acc'].append(val_v_acc)

                display_str = f'epoch: {epoch} '
                display_str += f'train_loss: {np.round(train_loss,4)} '
                display_str += f'train_c_acc: {np.round(train_c_acc,4):.2%} '
                display_str += f'val_c_loss: {np.round(val_c_loss,4)} '
                display_str += f'val_c_acc: {np.round(val_c_acc,4):.2%} '
                display_str += f'val_v_acc: {np.round(val_v_acc,4):.2%} '
                print(display_str)

                if self.val_c_loss > val_c_loss: self.val_c_loss = val_c_loss
                if self.train_loss > train_loss: self.train_loss = train_loss
                if self.train_c_acc < train_c_acc: self.train_c_acc = train_c_acc
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

                predicted = torch.argmax(cl_output.data, 1)
                total_predictions += len(label)
                correct_predictions += (predicted == label).sum().item()

        val_c_loss /= len(val_c_loader)
        val_c_acc = correct_predictions/total_predictions

        similarity = np.array([])
        ver_bool = np.array([])

        with torch.no_grad():
            for batch_idx, (img_0, img_1, target) in enumerate(val_v_loader):
                img_0 = img_0.to(self.device)
                img_1 = img_1.to(self.device)

                emb_0 = self.model(img_0)[0]
                emb_1 = self.model(img_1)[0]

                sim_score = cosine_similarity(emb_0, emb_1)
                similarity = np.append(similarity, sim_score.cpu().numpy().reshape(-1))
                ver_bool = np.append(ver_bool, target)

        try:
            val_v_acc = roc_auc_score(ver_bool, similarity)
        except:
            print('ROC calculation error')
            print(similarity)
            print(ver_bool)
            print(emb_0)
            print(emb_1)
            val_v_acc = -1


        return val_c_loss, val_c_acc, val_v_acc
