# import ssl
# #全局取消证书验证
# ssl._create_default_https_context = ssl._create_unverified_context

import torch
import datetime
import copy

from slimmer import Slimmer
from tester import Tester
from config import Configuration
class Slimmer_tester(object):

    def __init__(self, **kwargs):

        self.start_time = datetime.datetime.now()
        config = Configuration()
        config.update_config(kwargs) # 解析参数更新默认配置
        if config.check_config(): raise # 检测路径、设备是否存在

        self.slimmer = Slimmer(config=config)
        self.slimmer1 = Slimmer(config=config)
        self.slimmer2 = Slimmer(config=config)
        self.tester = Tester(config=config)

    def run(self):

        print("")
        print("| -------------------- original model -------------------- |")
        self.tester.model = copy.deepcopy(self.slimmer.model)
        self.tester.print_flops_params()
        self.tester.test()

        print("")
        print("| ----------------------- slim model --------------------- |")
        self.slimmer.slim()
        self.tester.model = self.slimmer.slimmed_model
        self.tester.print_flops_params()
        self.tester.test()

        # print("")
        # print("| ----------------------- slim model --------------------- |")
        # self.slimmer1.slim()
        # # self.tester.model = self.slimmer.slimmed_model
        # # self.tester.print_flops_params()
        # # self.tester.test()
        # # print(self.slimmer1.slimmed_model.state_dict())

        # print("")
        # print("| ----------------------- slim model --------------------- |")
        # self.slimmer2.slim()
        # # print(self.slimmer2.slimmed_model.state_dict())

        # # self.tester.model = self.slimmer.slimmed_model
        # # self.tester.print_flops_params()
        # # self.tester.test()


        # self.tester.model = self.slimmer1.slimmed_model
        # self.tester.print_flops_params()
        # self.tester.test()

        # self.tester.model = self.slimmer1.slimmed_model
        # self.tester.print_flops_params()
        # self.tester.test()


        # self.tester.model = self.slimmer2.slimmed_model
        # self.tester.print_flops_params()
        # self.tester.test()


        # print("")
        # print("| ------------------- simple slim model ------------------ |")
        # self.slimmer.simple_slim()
        # self.tester.model = self.slimmer.simple_slimmed_model
        # self.tester.print_flops_params()
        # self.tester.test()

        # print("")
        # print("| -------------------- original model -------------------- |")
        # self.tester.model = self.slimmer.model
        # self.tester.print_flops_params()
        # self.tester.test()

        # print("")
        # print("| ----------------------- slim model --------------------- |")
        # self.slimmer.slim()
        # self.tester.model = self.slimmer.slimmed_model
        # self.tester.print_flops_params()
        # self.tester.test()

        # print("")
        # print("| ------------------- simple slim model ------------------ |")
        # self.slimmer.simple_slim()
        # self.tester.model = self.slimmer.simple_slimmed_model
        # self.tester.print_flops_params()
        # self.tester.test()

        # print("")
        
        # # save slimmed model
        # if self.slimmer.config.save_model_path is None:
        #     self.slimmer.config.save_model_path = "slimmed_checkpoints/" + self.slimmer.config.dataset + "_" + self.slimmer.config.model + "_acc{acc:.2f}.pth".format(acc=self.tester.top1_acc.avg)
        # torch.save(self.slimmer.model.state_dict(), self.slimmer.config.save_model_path)

if __name__ == "__main__":
    slimmer_tester = Slimmer_tester(
        model='vgg16_bn',
        dataset="cifar10",
        gpu_idx = "5", # choose gpu
        random_seed=2,
        load_model_path="checkpoints/cifar10_vgg16_bn_epoch150_acc91.90.pth",
        # num_workers = 5, # 使用多进程加载数据
        slim_percent=0.3,
    )
    slimmer_tester.run()
    print("end")

