# 该文件通常用来加载.pth.tar文件以供debug

import torch
import torchvision as tv

from utils import *

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
    return

def get_features_hook(self, input, output):# self 代表类模块本身
    print(output.size())
    print(output)

def get_features_hook1(self, input, output):# self 代表类模块本身
    print(output.size())
    print(output[0][0])
    print(output[0][1])
    print(output[0][2])
    print(output[0][3])
    # print(output[0][4])
    # print(output[0][5])

if __name__ == "__main__":

    train_transform = tv.transforms.Compose([
        # tv.transforms.CenterCrop(32),
        tv.transforms.ToTensor(), 
        tv.transforms.Normalize(
            # mean=[0.5, 0.5, 0.5], 
            # std =[0.5, 0.5, 0.5],
            mean=[0.4914, 0.4822, 0.4465], 
            std=[0.2023, 0.1994, 0.2010],
        ) # 标准化的过程为(input-mean)/std
    ])

    train_dataset = tv.datasets.CIFAR10(
        root='/home/xueruini/onion_rain/pytorch/dataset/', 
        train=True, 
        download=False,
        transform=train_transform,)

    # train_dataloader = torch.utils.data.DataLoader(
    #     dataset=train_dataset, 
    #     batch_size=1,
    #     shuffle=False,
    #     num_workers=1,
    #     pin_memory=True,
    # )

    input, _ = train_dataset.__getitem__(0)
    input = input.unsqueeze(0)

    checkpoint_simple = torch.load('checkpoints/cifar10_test_simple_prune0.5_state_dict_best.pth.tar')
    # print(checkpoint_simple['model_state_dict'])
    simple_pruned_model = models.__dict__['test']
    simple_pruned_model = simple_pruned_model(num_classes=10)
    simple_pruned_model.load_state_dict(checkpoint_simple['model_state_dict'])

    idx = 0
    for name, m in simple_pruned_model.named_modules():
        # if isinstance(m, torch.nn.Conv2d):
        if isinstance(m, torch.nn.BatchNorm2d):
        # if isinstance(m, torch.nn.ReLU):
            idx += 1
            if idx == 1:
                m.register_forward_hook(get_features_hook1)
                break
    print("simple")
    simple_output = simple_pruned_model(input)
    # simple_feature = simple_pruned_model.feature_map
    # print(simple_feature)

    checkpoint_filter = torch.load('checkpoints/cifar10_test_filter_prune0.5_state_dict_best.pth.tar')
    # print(checkpoint_filter['model_state_dict'])
    pruned_model = models.__dict__['test']
    pruned_model = pruned_model(cfg=checkpoint_filter['cfg'], num_classes=10)
    pruned_model.load_state_dict(checkpoint_filter['model_state_dict'])
    
    idx = 0
    for name, m in pruned_model.named_modules():
        # if isinstance(m, torch.nn.Conv2d):
        if isinstance(m, torch.nn.BatchNorm2d):
        # if isinstance(m, torch.nn.ReLU):
            idx += 1
            if idx == 1:
                m.register_forward_hook(get_features_hook)
                break

    print("pruned")
    pruned_output = pruned_model(input)
    # pruned_feature = pruned_model.feature_map
    # print(pruned_feature)

    print()