# pytorch-slimming

论文地址：[Learning Efficient Convolutional Networks Through Network Slimming](https://arxiv.org/abs/1708.06519v1) (ICCV2017)

参考代码：https://github.com/foolwood/pytorch-slimming

参考代码：https://github.com/Eric-mingjie/network-slimming

usage: ```trainer.py [-h] [--arch ARCH] [--dataset DATASET] [--workers N]
                  [--batch-size N] [--epochs N] [--lr LR] [--weight-decay W]
                  [--gpu GPU] [--deterministic] [--momentum M] [--valuate]
                  [--resume PATH] [--refine] [--sparsity-regularization]
                  [--srl SR_LAMBDA] [--visdom] [--vis-env ENV]
                  [--vis-legend LEGEND] [--vis-interval N]```

usage: ```slimmer.py [-h] [--arch ARCH] [--dataset DATASET] [--workers N]
                  [--gpu gpu_idx] [--resume PATH] [--refine]
                  [--slim-percent N]```

## 实验（基于CIFAR10数据集）：

### vgg19_bn_cifar

sparsity training: ```python trainer.py --arch vgg19_bn_cifar --epochs 150 --gpu 4 --valuate -sr --visdom --srl 1e-4```

slimming: ```python slimmer.py --arch vgg19_bn_cifar --gpu 4 --resume checkpoints/sparsity/cifar10_vgg19_bn_cifar_sr_best.pth.tar --slim 0.7```

fine-tune: ```python trainer.py --arch vgg19_bn_cifar --epochs 10 --gpu 4 --valuate --resume checkpoints/slimmed_ratio0.7_cifar10_vgg19_bn_cifar_checkpoint.pth.tar --refine```

|  vgg19_bn_cifar  | Baseline | Trained with sparsity (lambda=1e-4) | slimmed (ratio=0.7) | Fine-tuned (10epochs) |
| :--------------: | :------: | :---------------------------------: | :-----------------: | :-------------------: |
| Top1 Accuracy(%) |  93.26   |                94.02                |        10.00        |         92.64         |
|  Parameters(M)   |  20.04   |                20.04                |        2.49         |         2.49          |
|   FLOPs(GMac)    |   0.4    |                 0.4                 |        0.22         |         0.22          |

|             Pruned Ratio             |     0      |     0.1     |     0.2     |    0.3    |    0.4     |    0.5     |    0.6     |    0.7     |
| :----------------------------------: | :--------: | :---------: | :---------: | :-------: | :--------: | :--------: | :--------: | :--------: |
| Top1 Accuracy (%) without Fine-tuned |   93.26    |    93.93    |    93.96    |   93.95   |   94.01    |   94.03    |   94.05    |   93.01    |
|      Parameters(M)/ FLOPs(GMac)      | 20.04/ 0.4 | 15.93/ 0.35 | 12.36/ 0.31 | 9.4/ 0.28 | 6.82/ 0.25 | 4.62/ 0.24 | 3.25/ 0.23 | 2.49/ 0.22 |

| Slimmed Ratio |                         architecture                         |
| :-----------: | :----------------------------------------------------------: |
|       0       | [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512] |
|      0.1      | [62, 64, 'M', 128, 128, 'M', 256, 256, 253, 248, 'M', 444, 420, 421, 460, 'M', 468, 477, 461, 407] |
|      0.2      | [61, 64, 'M', 128, 128, 'M', 256, 256, 251, 242, 'M', 376, 325, 346, 403, 'M', 419, 433, 414, 301] |
|      0.3      | [59, 64, 'M', 128, 128, 'M', 256, 256, 249, 234, 'M', 289, 239, 265, 349, 'M', 372, 387, 358, 219] |
|      0.4      | [56, 64, 'M', 128, 128, 'M', 256, 256, 249, 227, 'M', 224, 144, 183, 297, 'M', 316, 344, 302, 128] |
|      0.5      | [54, 64, 'M', 128, 128, 'M', 256, 256, 249, 226, 'M', 202, 118, 141, 238, 'M', 188, 214, 198, 91] |
|      0.6      | [51, 64, 'M', 128, 128, 'M', 256, 256, 249, 224, 'M', 190, 95, 115, 136, 'M', 71, 63, 84, 91] |
|      0.7      | [49, 64, 'M', 128, 128, 'M', 256, 256, 249, 208, 'M', 116, 38, 18, 8, 'M', 14, 9, 16, 94] |

### resnet20_cs ('cs' means channel sellection)

sparsity training: ```python trainer.py --arch resnet20_cs --epochs 100 --gpu 5 --valuate -sr --visdom --srl 1e-5```

slimming: ```python slimmer.py --arch resnet20_cs --gpu 5 --resume checkpoints/sparsity/cifar10_resnet20_cs_sr_best.pth.tar --slim 0.5```

fine-tune: ```python trainer.py --arch resnet20_cs --epochs 40 --gpu 5 --valuate --resume checkpoints/slimmed_ratio0.5_cifar10_resnet20_cs_checkpoint.pth.tar --refine```

|   resnet20_cs    | Baseline | Trained with sparsity (lambda=1e-5) | slimmed (ratio=0.5) | Fine-tuned (40epochs) |
| :--------------: | :------: | :---------------------------------: | :-----------------: | :-------------------: |
| Top1 Accuracy(%) |  92.54   |                92.30                |        10.00        |         89.22         |
|  Parameters(K)   |  683.85  |               683.85                |       620.35        |        620.35         |
|   FLOPs(GMac)    |   0.1    |                 0.1                 |        0.07         |         0.07          |

### resnet56_cs ('cs' means channel sellection)

sparsity training: ```python trainer.py --arch resnet56_cs --epochs 100 --gpu 6 --valuate -sr --visdom --srl 1e-5```

slimming: ```python slimmer.py --arch resnet56_cs --gpu 6 --resume checkpoints/sparsity/cifar10_resnet56_cs_sr_best.pth.tar --slim 0.6```

fine-tune: ```python trainer.py --arch resnet56_cs --epochs 40 --gpu 6 --valuate --resume checkpoints/slimmed_ratio0.6_cifar10_resnet56_cs_checkpoint.pth.tar --refine```

|   resnet56_cs    | Baseline | Trained with sparsity (lambda=1e-5) | slimmed (ratio=0.6) | Fine-tuned (40epochs) |
| :--------------: | :------: | :---------------------------------: | :-----------------: | :-------------------: |
| Top1 Accuracy(%) |  93.33   |                93.70                |        11.72        |         90.99         |
|  Parameters(M)   |   1.98   |                1.98                 |        1.81         |         1.81          |
|   FLOPs(GMac)    |   0.29   |                0.29                 |        0.25         |         0.25          |

### resnet110_cs ('cs' means channel sellection)

sparsity training: ```python trainer.py --arch resnet110_cs --epochs 100 --gpu 7 --valuate -sr --visdom --srl 1e-5```

slimming: ```python slimmer.py --arch resnet110_cs --gpu 7 --resume checkpoints/sparsity/cifar10_resnet110_cs_sr_best.pth.tar --slim 0.6```

fine-tune: ```python trainer.py --arch resnet110_cs --epochs 20 --gpu 7 --valuate --resume checkpoints/slimmed_ratio0.6_cifar10_resnet110_cs_checkpoint.pth.tar --refine```

|   resnet110_cs   | Baseline | Trained with sparsity (lambda=1e-5) | slimmed (ratio=0.6) | Fine-tuned (20epochs) |
| :--------------: | :------: | :---------------------------------: | :-----------------: | :-------------------: |
| Top1 Accuracy(%) |  93.88   |                93.58                |        10.00        |         90.66         |
|  Parameters(M)   |   3.93   |                3.93                 |        3.54         |         3.54          |
|   FLOPs(GMac)    |   0.58   |                0.58                 |        0.53         |         0.53          |

## 稀疏/正常训练过程（From Scratch）：

### test_loss(交叉熵):

![test_loss](imgs/slimming/test_loss.jpg)

### test_top1:

![test_top1](imgs/slimming/test_top1.jpg)