import importlib
import os
from functools import partial
from multiprocessing import Manager, Process
from typing import Dict


def run_module_pipeline(
    module_names: str,
    module_package: str = "module",
    root_dir: str | None = None,
    extra_flags: dict | None = None,
):
    """
    以多进程方式运行 module pipeline。

    每个 module 在一个独立子进程中循环执行其 PU 链。

    Args:
        module_names: 逗号分隔的 Module 名称，如 "PriceMonitorModule,PriceDisplayModule"
        module_package: Module 所在的 Python 包路径，默认为 "module"
        root_dir: 项目根目录，默认为当前工作目录 (os.getcwd())
        extra_flags: 传入 shared_dict['flags'] 的额外参数字典
    """
    from .common_utils import get_module_file_name, load_environment_variable

    if root_dir is None:
        root_dir = os.getcwd()

    def execute_module(module_name: str, shared_dict: Dict):
        assert module_name.endswith('Module')
        load_environment_variable()
        module_file_name = get_module_file_name(module_name)
        module_pkg = importlib.import_module(f'{module_package}.{module_name}.{module_file_name}')
        module_class = getattr(module_pkg, module_name)
        module = module_class(shared_dict)
        while True:
            module.run()

    with Manager() as manager:
        shared_dict = manager.dict()
        shared_dict['flags'] = extra_flags or {}
        shared_dict['root'] = root_dir
        processes = []
        for module_name in module_names.split(','):
            process = Process(target=partial(execute_module, module_name),
                              args=(shared_dict,),
                              daemon=True)
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
