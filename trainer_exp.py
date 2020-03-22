# import ssl
# #全局取消证书验证
# ssl._create_default_https_context = ssl._create_unverified_context

import torch
from utils.visualize import Visualizer
from tqdm import tqdm
from torch.nn import functional as F
# import torchvision as tv
import numpy as np
import time
import os
import random
import datetime
import argparse

from utils import *
import models
from train import *
from tester import Tester

import warnings
warnings.filterwarnings(action="ignore", category=UserWarning)

# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "0, 1, 2, 3, 4, 5, 6, 7"
# fuser -v /dev/nvidia* |awk '{for(i=1;i<=NF;i++)print "kill -9 " $i;}' | sh

class TrainerExp(object):
    """
    TODO 待大量测试
    """
    def __init__(self, config_dic=None, **kwargs):

        print("| ----------------- Initializing Trainer ----------------- |")

        self.config = Configuration()
        self.config.update_config(kwargs) # 解析参数更新默认配置
        if self.config.check_config(): raise # 检测路径、设备是否存在
        print('{:<30}  {:<8}'.format('==> num_workers: ', self.config.num_workers))
        print('{:<30}  {:<8}'.format('==> batch_size: ', self.config.batch_size))
        print('{:<30}  {:<8}'.format('==> max_epoch: ', self.config.max_epoch))
        print('{:<30}  {:<8}'.format('==> lr_scheduler milestones: ', str([self.config.max_epoch*0.5, self.config.max_epoch*0.75])))

        self.suffix = get_suffix(self.config)
        print('{:<30}  {:<8}'.format('==> suffix: ', self.suffix))

        # 更新一些默认标志
        self.start_epoch = 0
        self.best_acc1 = 0
        self.checkpoint = None
        vis_clear = True

        # device
        if len(self.config.gpu_idx_list) > 0:
            self.device = torch.device('cuda:{}'.format(min(self.config.gpu_idx_list))) # 起始gpu序号
            print('{:<30}  {:<8}'.format('==> chosen GPU index: ', self.config.gpu_idx))
        else:
            self.device = torch.device('cpu')
            print('{:<30}  {:<8}'.format('==> device: ', 'CPU'))

        # Random Seed 
        # (其实pytorch只保证在同版本并且没有多线程的情况下相同的seed可以得到相同的结果，而加载数据一般没有不用多线程的，这就有点尴尬了)
        if self.config.deterministic:
            if self.config.num_workers > 1:
                print("ERROR: Setting --deterministic requires setting --workers to 0 or 1")
            random.seed(0)
            torch.manual_seed(0)
            np.random.seed(self.config.random_seed)
            torch.backends.cudnn.deterministic = True
        else: 
            torch.backends.cudnn.benchmark = True # 让程序在开始时花费一点额外时间，为整个网络的每个卷积层搜索最适合它的卷积实现算法，进而实现网络的加速

        # step1: data
        # self.train_dataloader, self.val_dataloader, self.num_classes = get_dataloader(self.config)
        self.train_dataloader, self.val_dataloader, self.num_classes = dataloader_div_init(self.config, val_num=50)

        # step2: model
        print('{:<30}  {:<8}'.format('==> creating arch: ', self.config.arch))
        self.cfg = None
        checkpoint = None
        if self.config.resume_path != '': # 断点续练hhh
            checkpoint = torch.load(self.config.resume_path, map_location=self.device)
            print('{:<30}  {:<8}'.format('==> resuming from: ', self.config.resume_path))
            if self.config.refine: # 根据cfg加载剪枝后的模型结构
                self.cfg=checkpoint['cfg']
                print(self.cfg)
        if self.cfg is not None:
            self.model = models.__dict__[self.config.arch](cfg=cfg, num_classes=self.num_classes)
        else:
            self.model = models.__dict__[self.config.arch](num_classes=self.num_classes)
        self.model.to(self.device) # 模型转移到设备上
        if len(self.config.gpu_idx_list) > 1:
            self.model = torch.nn.DataParallel(self.model, device_ids=self.config.gpu_idx_list)
            # torch.distributed.init_process_group(backend='nccl', init_method='tcp://localhost:65535', rank=0, world_size=1)
            # self.model = torch.nn.parallel.DistributedDataParallel(self.model, find_unused_parameters=True)
        if checkpoint is not None:
            if 'epoch' in checkpoint.keys():
                self.start_epoch = checkpoint['epoch'] + 1 # 保存的是已经训练完的epoch，因此start_epoch要+1
                print("{:<30}  {:<8}".format('==> checkpoint trained epoch: ', checkpoint['epoch']))
                if checkpoint['epoch'] > -1:
                    vis_clear = False # 不清空visdom已有visdom env里的内容
            if 'best_acc1' in checkpoint.keys():
                self.best_acc1 = checkpoint['best_acc1']
                print("{:<30}  {:<8}".format('==> checkpoint best acc1: ', checkpoint['best_acc1']))
            self.model.load_state_dict(checkpoint['model_state_dict'])
            
        # exit(0)
        
        # step3: criterion and optimizer
        self.optimizer = torch.optim.SGD(
            params=self.model.parameters(),
            lr=self.config.lr,
            momentum=self.config.momentum,
            weight_decay=self.config.weight_decay,
        )
        if checkpoint is not None:
            if 'optimizer_state_dict' in checkpoint.keys():
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        self.criterion = torch.nn.CrossEntropyLoss()

        self.lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(
            optimizer=self.optimizer,
            milestones=[self.config.max_epoch*0.5, self.config.max_epoch*0.75], 
            gamma=0.1,
            last_epoch=self.start_epoch-1, # 我的训练epoch从1开始，而pytorch要通过当前epoch是否等于0判断是不是resume
        )
        
        # step5: visdom
        self.vis = None
        self.vis_interval = None
        if self.config.visdom:
            if self.config.vis_env == '':
                self.config.vis_env = self.config.dataset + '_' + self.config.arch + self.suffix
            if self.config.vis_legend == '':
                self.config.vis_legend = self.config.arch + self.suffix
            self.vis = Visualizer(self.config.vis_env, self.config.vis_legend, clear=vis_clear) 
            self.vis_interval = self.config.vis_interval

        if self.config.sr:
            self.sr = self.config.sr
        
        if self.config.sr:
            self.trainer = SlimmerTrainer(
                self.model, 
                self.train_dataloader, 
                self.criterion, 
                self.optimizer, 
                self.device, 
                self.sr_lambda, 
                self.vis, 
                self.vis_interval,
                self.lr_scheduler,
            )
        else:
            self.trainer = Trainer(
                self.model, 
                self.train_dataloader, 
                self.criterion, 
                self.optimizer, 
                self.device, 
                self.vis, 
                self.vis_interval,
                self.lr_scheduler,
            )

        # step6: valuator
        self.valuator = None
        if self.config.valuate is True:
            val_config_dic = {
                'model': self.model,
                'dataloader': self.val_dataloader,
                'device': self.device,
                'vis': self.vis,
                'seed': self.config.random_seed,
                'criterion': self.criterion,
            }
            self.valuator = Tester(val_config_dic)
        
    
    def print_bar(self, start_time, arch, dataset):
        """calculate duration time"""
        interval = datetime.datetime.now() - start_time
        print("--------  model: {model}  --  dataset: {dataset}  --  duration: {dh:2}h:{dm:02d}.{ds:02d}  --------".
            format(
                model=arch,
                dataset=dataset,
                dh=interval.seconds//3600,
                dm=interval.seconds%3600//60,
                ds=interval.seconds%60,
            )
        )

    def run(self):

        print("")
        start_time = datetime.datetime.now()
        name = (self.config.dataset + "_" + self.config.arch + self.suffix)
        print_flops_params(model=self.model)

        # initial test
        if self.valuator is not None:
            self.valuator.test(self.model, epoch=self.start_epoch-1)
        self.print_bar(start_time, self.config.arch, self.config.dataset)
        print("")
        for epoch in range(self.start_epoch, self.config.max_epoch):
            # train & valuate
            self.trainer.train(epoch=epoch)
            if self.valuator is not None:
                self.valuator.test(self.model, epoch=epoch)
            self.print_bar(start_time, self.config.arch, self.config.dataset)
            print("")
            
            # save checkpoint
            if self.valuator is not None:
                is_best = self.valuator.top1_acc.avg > self.best_acc1
                self.best_acc1 = max(self.valuator.top1_acc.avg, self.best_acc1)
            else:
                is_best = self.top1_acc.avg > self.best_acc1
                self.best_acc1 = max(self.top1_acc.avg, self.best_acc1)
            if len(self.config.gpu_idx_list) > 1:
                state_dict = self.model.module.state_dict()
            else: state_dict = self.model.state_dict()
            save_dict = {
                'model': self.config.arch,
                'epoch': epoch,
                'model_state_dict': state_dict,
                'best_acc1': self.best_acc1,
                'optimizer_state_dict': self.optimizer.state_dict(),
            }
            if self.cfg is not None:
                save_dict['cfg'] = self.cfg
            save_checkpoint(save_dict, is_best=is_best, epoch=None, file_root='checkpoints/', file_name=name)
        print("{}{}".format("best_acc1: ", self.best_acc1))



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='network trainer')
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
    parser.add_argument('--lr', dest='lr', type=float, default=1e-1, 
                        metavar='LR', help='initial learning rate (default: 1e-1)')
    parser.add_argument('--weight-decay', '-wd', dest='weight_decay', type=float,
                        default=1e-4, metavar='W', help='weight decay (default: 1e-4)')
    parser.add_argument('--gpu', type=str, default='0',
                        help='training GPU index(default:"0",which means use GPU0')
    parser.add_argument('--deterministic', '--det', action='store_true',
                    help='Ensure deterministic execution for re-producible results.')
    parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                        help='SGD momentum (default: 0.9)')
    parser.add_argument('--valuate', action='store_true',
                        help='valuate each training epoch')
    parser.add_argument('--resume', dest='resume_path', type=str, default='',
                        metavar='PATH', help='path to latest checkpoint (default: none)')
    parser.add_argument('--refine', action='store_true',
                        help='refine from pruned model, use construction to build the model')
    parser.add_argument('--usr-suffix', type=str, default='',
                        help='usr_suffix(default:"", means nothing')

    parser.add_argument('--sparsity-regularization', '-sr', dest='sr', action='store_true',
                        help='train with channel sparsity regularization')
    parser.add_argument('--srl', dest='sr_lambda', type=float, default=1e-4,
                        help='scale sparse rate (default: 1e-4), suggest 1e-4 for vgg, 1e-5 for resnet/densenet')

    parser.add_argument('--visdom', dest='visdom', action='store_true',
                        help='visualize the training process using visdom')
    parser.add_argument('--vis-env', type=str, default='', metavar='ENV',
                        help='visdom environment (default: "", which means env is automatically set to args.dataset + "_" + args.arch)')
    parser.add_argument('--vis-legend', type=str, default='', metavar='LEGEND',
                        help='refine from pruned model (default: "", which means env is automatically set to args.arch)')
    parser.add_argument('--vis-interval', type=int, default=50, metavar='N',
                        help='visdom plot interval batchs (default: 50)')
    # parser.add_argument('--nclear', dest='nclear', action='store_true',
    #                     help='if set this true, the wisdom env will not be cleared before training.')
    args = parser.parse_args()

    # debug用
    # args.workers = 0


    trainer_exp = TrainerExp(
        arch=args.arch,
        dataset=args.dataset,
        num_workers = args.workers, # 使用多进程加载数据
        batch_size=args.batch_size,
        max_epoch=args.epochs,
        lr=args.lr,
        gpu_idx = args.gpu, # choose gpu
        weight_decay=args.weight_decay,
        momentum=args.momentum,
        deterministic=args.deterministic,
        valuate=args.valuate,
        resume_path=args.resume_path,
        refine=args.refine,
        usr_suffix=args.usr_suffix,

        sr=args.sr,
        sr_lambda=args.sr_lambda,

        visdom = args.visdom, # 使用visdom可视化训练过程
        vis_env=args.vis_env,
        vis_legend=args.vis_legend,
        vis_interval=args.vis_interval,
    )
    trainer_exp.run()
    print("end")

