import os

from .utils.common_utils import get_module_file_name, get_pu_file_name


DEFAULT_MODULE_FILE_CONTENT = '''
from typing import Dict

from module_pipeline.module_base import ModuleBase


class ${MODULE_NAME}(ModuleBase):
    ITERATION_INTERVAL = 1

    def __init__(self, shared_dict: Dict):
        super().__init__(shared_dict, self.ITERATION_INTERVAL)

'''

DEFAULT_PU_CONFIG_CONTENT = '''
- ${PU_NAME}:
    param: ~
'''

DEFAULT_PU_FILE_CONTENT = '''
from module_pipeline.pu_base import ProcessUnitBase
from module_pipeline.module_base import ModuleBase


class ${PU_NAME}(ProcessUnitBase):

    def __init__(self, module: ModuleBase, param: str):
        self.param = param
        super().__init__(module)

    def update_producer_input(self):
        self.producer_input.available_attributs = {}

    def update_producer_output(self):
        self.producer_output.available_attributs = {}

    def process(self):
        pass

'''


def create_module(
    module_name: str,
    project_root: str | None = None,
    module_dir: str = "module",
    pu_dir: str = "pu",
):
    """
    生成一个新的 Module 及其默认 PU 文件骨架。

    参数:
        module_name: Module 名称，如 "RequestBasedXPostScraperModule"
        project_root: 项目根目录，默认为 cwd
        module_dir: Module 文件存放目录，默认为 "module"
        pu_dir: PU 文件存放目录，默认为 "pu"
    """
    if project_root is None:
        project_root = os.getcwd()

    assert module_name.endswith('Module')

    # Create module directory and files
    new_module_dir = os.path.join(project_root, module_dir, module_name)
    os.makedirs(new_module_dir, exist_ok=True)

    new_module_file_name = get_module_file_name(module_name) + '.py'
    new_module_file_path = os.path.join(new_module_dir, new_module_file_name)
    if not os.path.exists(new_module_file_path):
        with open(new_module_file_path, 'w') as f:
            f.write(DEFAULT_MODULE_FILE_CONTENT.replace('${MODULE_NAME}', module_name))

    # Create pu_config.yaml
    new_module_config_path = os.path.join(new_module_dir, 'pu_config.yaml')
    pu_name = module_name[:-len('Module')] + 'Unit'
    if not os.path.exists(new_module_config_path):
        with open(new_module_config_path, 'w') as f:
            f.write(DEFAULT_PU_CONFIG_CONTENT.replace('${PU_NAME}', pu_name))

    # Create PU file
    new_pu_file_name = get_pu_file_name(pu_name) + '.py'
    new_pu_dir = os.path.join(project_root, pu_dir)
    os.makedirs(new_pu_dir, exist_ok=True)
    new_pu_file_path = os.path.join(new_pu_dir, new_pu_file_name)
    if not os.path.exists(new_pu_file_path):
        with open(new_pu_file_path, 'w') as f:
            f.write(DEFAULT_PU_FILE_CONTENT.replace('${PU_NAME}', pu_name))

    print(f'Created module: {module_name}')
    print(f'  Module file: {new_module_file_path}')
    print(f'  Config file: {new_module_config_path}')
    print(f'  PU file:     {new_pu_file_path}')
