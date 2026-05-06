import os
import signal
import time
from typing import Dict

import yaml
from IPython import get_ipython

from . import pu_signal
from .utils.common_utils import get_class_by_name


class ModuleBase:
    pus = []

    def __init__(self, shared_dict: Dict, iteration_interval: float = 1.0,
                 module_dir: str = 'module', pu_search_root: str = 'pu'):
        self.module_name = self.__class__.__name__
        print(f'Initializing Module: {self.module_name}')
        self.shared_dict = shared_dict
        self.iteration_interval = iteration_interval
        config_path = os.path.join(module_dir, self.module_name, 'pu_config.yaml')
        with open(config_path) as pu_config:
            pu_config = yaml.safe_load(pu_config)
            for pu_setting_dict in pu_config:
                assert len(pu_setting_dict) == 1
                pu_name, kwargs = tuple(pu_setting_dict.items())[0]
                pu_class = get_class_by_name(pu_name, root=pu_search_root)
                self.pus.append(pu_class(self, **kwargs))

    def run(self):
        ipython = get_ipython()
        for pu in self.pus:
            pu_status = pu.process()
            if pu_status == pu_signal.SKIP_ITERATION_SIGNAL:
                print(f'[{self.module_name}] {pu.pu_name}: {pu_status}')
                break
            elif pu_status == pu_signal.STOP_SIGNAL:
                if ipython is None:
                    exit()
                os.kill(os.getpid(), signal.SIGKILL)

        time.sleep(self.iteration_interval)
