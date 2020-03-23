import torch
from utils.visualize import Visualizer
from tqdm import tqdm
import torchvision as tv
import numpy as np
import time
import random
import argparse

import models
from utils import *
from traintest import *

class TesterExp(object):
    """
    TODO 由于trainer类大改，本类某些函数可能个已过期
    """
    def __init__(self, **kwargs):

        print("| ----------------- Initializing Tester ------------------ |")
        
        self.config = Configuration()
        self.config.update_config(kwargs) # 解析参数更新默认配置
        if self.config.check_config(): raise # 检测路径、设备是否存在
        print('{:<30}  {:<8}'.format('==> num_workers: ', self.config.num_workers))

        # visdom
        self.vis = None
        if self.config.visdom:
            self.vis = Visualizer(self.config.vis_env, self.config.vis_legend) # 初始化visdom

        # device
        if len(self.config.gpu_idx_list) > 0:
            self.device = torch.device('cuda:{}'.format(min(self.config.gpu_idx_list))) # 起始gpu序号
            print('{:<30}  {:<8}'.format('==> chosen GPU index: ', self.config.gpu_idx))
        else:
            self.device = torch.device('cpu')
            print('{:<30}  {:<8}'.format('==> device: ', 'CPU'))

        # Random Seed
        random.seed(0)
        torch.manual_seed(0)
        np.random.seed(self.config.random_seed)
        torch.backends.cudnn.deterministic = True

        # step1: data
        _, self.test_dataloader, self.num_classes = get_dataloader(self.config)

        # model
        self.model, self.cfg, checkpoint = model_init(self.config, self.device, self.num_classes)
        if 'epoch' in checkpoint.keys():
            self.start_epoch = checkpoint['epoch'] + 1 # 保存的是已经训练完的epoch，因此start_epoch要+1
            print("{:<30}  {:<8}".format('==> checkpoint trained epoch: ', checkpoint['epoch']))
            if checkpoint['epoch'] > -1:
                vis_clear = False # 不清空visdom已有visdom env里的内容
        if 'best_acc1' in checkpoint.keys():
            self.best_acc1 = checkpoint['best_acc1']
            print("{:<30}  {:<8}".format('==> checkpoint best acc1: ', checkpoint['best_acc1']))
        if 'best_acc1' in checkpoint.keys():
            self.best_acc1 = checkpoint['best_acc1']
            print("{:<30}  {:<8}".format('==> checkpoint best acc1: ', checkpoint['best_acc1']))


        # step3: criterion
        self.criterion = torch.nn.CrossEntropyLoss()

        self.tester = Tester(
            dataloader=self.val_dataloader,
            device=self.device,
            criterion=self.criterion,
            vis=self.vis,
        )
        
    def run(self):
        print_model_param_flops(model=self.model, input_res=32, device=self.device)
        print_model_param_nums(model=self.model)
        print_flops_params(model=self.model)
        self.tester.test(self.model, epoch=self.start_epoch)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='network tester')
    parser.add_argument('--arch', '-a', type=str, metavar='ARCH', default='vgg19_bn_cifar',
                        choices=models.ALL_MODEL_NAMES,
                        help='model architecture: ' +
                        ' | '.join(name for name in models.ALL_MODEL_NAMES) +
                        ' (default: resnet18)')
    parser.add_argument('--dataset', type=str, default='cifar10',
                        help='training dataset (default: cifar10)')
    parser.add_argument('--workers', type=int, default=10, metavar='N',
                        help='number of data loading workers (default: 10)')
    parser.add_argument('--batch-size', type=int, default=100, metavar='N',
                        help='input batch size for training (default: 100)')
    # parser.add_argument('--test-batch-size', type=int, default=1000, metavar='N',
    #                     help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=150, metavar='N',
                        help='number of epochs to train (default: 150)')
    parser.add_argument('--learning-rate', '-lr', dest='lr', type=float, default=1e-1, 
                        metavar='LR', help='initial learning rate (default: 1e-1)')
    parser.add_argument('--weight-decay', '-wd', dest='weight_decay', type=float,
                        default=1e-4, metavar='W', help='weight decay (default: 1e-4)')
    parser.add_argument('--gpu', type=str, default='0',
                        help='training GPU index(default:"0",which means use GPU0')
    parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                        help='SGD momentum (default: 0.9)')
    parser.add_argument('--valuate', action='store_true',
                        help='valuate each training epoch')
    parser.add_argument('--resume-path', '-rp', dest='resume_path', type=str, default='',
                        metavar='PATH', help='path to latest checkpoint (default: none)')
    parser.add_argument('--refine', action='store_true',
                        help='refine from pruned model, use construction to build the model')
    args = parser.parse_args()


    if args.resume_path != '':
        tester = Tester(
            arch=args.arch,
            dataset=args.dataset,
            num_workers = args.workers, # 使用多进程加载数据
            batch_size=args.batch_size,
            max_epoch=args.epochs,
            lr=args.lr,
            gpu_idx = args.gpu, # choose gpu
            weight_decay=args.weight_decay,
            momentum=args.momentum,
            valuate=args.valuate,
            resume_path=args.resume_path,
            refine=args.refine,
        )
    else:
        tester = Tester(
            batch_size=1000,
            arch='vgg19_bn_cifar',
            dataset="cifar10",
            gpu_idx = "4", # choose gpu
            resume_path='checkpoints/cifar10_vgg19_bn_cifar_sr_refine_best.pth.tar',
            refine=True,
            # num_workers = 10, # 使用多进程加载数据
        )
    tester.run()
    print("end")