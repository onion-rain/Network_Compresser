# 该文件通常用来加载.pth.tar文件以供debug

import torch

from utils import print_flops_params

import warnings
warnings.filterwarnings(action="ignore", category=UserWarning)

import models

def dump_model(model_name=None,
                cfg=None,
                checkpoint_path=None,
                num_classes=10,
                save_path=None,
                dataset='cifar10'):
    """
    从.pth.tar中取出state.dict并连同模型保存为.pth
    """
    checkpoint = torch.load(checkpoint_path)
    if cfg is None:
        if 'cfg' in checkpoint:
            cfg = checkpoint['cfg']
    model = models.__dict__[model_name](cfg=cfg, num_classes=num_classes)
    model.load_state_dict(checkpoint['model_state_dict'])

    for key in checkpoint:
        if key != 'model_state_dict' and key != 'optimizer_state_dict':
            print("{}: {}".format(key, checkpoint[key]))

        
    print_flops_params(model, dataset)

    if save_path is not None:
        torch.save(model, save_path)

        # exit(0)

if __name__ == "__main__":
    dump_model(
        model_name='resnet110_cs', 
        cfg=None,
        checkpoint_path='checkpoints/no_sparsity/cifar10_resnet110_cs_best.pth.tar',
        # num_classes=10,
        # save_path='VGG19BN_slimmed0.7_10.0.pth'
        dataset="cifar10"
    )