# module_pipeline

一个轻量级的 Module-PU 多进程管道框架。通过 YAML 配置串联多个 PU (Processing Unit)，每个 Module 在独立进程中运行。

## 安装

```bash
pip install -e .
```

或直接通过 PYTHONPATH 使用：

```bash
export PYTHONPATH=src:$PYTHONPATH
```

## 核心概念

- **Module** — 独立进程，通过 `pu_config.yaml` 定义 PU 执行链
- **PU (Processing Unit)** — 最小执行单元，负责具体逻辑
- **ProducerInput / ProducerOutput** — 同一 Module 内 PU 之间通过 Module 属性共享数据

## 快速开始

### 1. 创建新 Module

```python
from module_pipeline.generator import create_module

create_module("MyMonitorModule")
```

这会生成三个文件：Module 类、PU 类、`pu_config.yaml`。

### 2. 实现 PU 逻辑

在生成的 PU 文件中填充 `process()` 方法：

```python
from module_pipeline.pu_base import ProcessUnitBase

class MyMonitorUnit(ProcessUnitBase):

    def process(self):
        # 写入共享数据
        self.producer_output.price = 123.45
```

### 3. 运行管道

```python
from module_pipeline.utils.runner import run_module_pipeline

run_module_pipeline(
    module_names="MyMonitorModule",
    module_package="myproject.modules",
)
```

## 依赖

- PyYAML
- IPython
- pandas
- python-dotenv
