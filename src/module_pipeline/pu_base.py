from .module_base import ModuleBase
from .utils import common_utils


class ProcessUnitBase:

    def __init__(self, module: ModuleBase):
        self.pu_name = self.__class__.__name__
        print(f'[{module.module_name}] Initializing PU: {self.pu_name}')
        self.module = module
        self.flags = module.shared_dict['flags']
        self.producer_input: ProducerInput = ProducerInput(module)
        self.producer_output: ProducerOutput = ProducerOutput(module)
        self.update_producer_input()
        self.update_producer_output()

    def update_producer_input(self):
        pass

    def update_producer_output(self):
        pass

    def process(self):
        raise NotImplementedError

    def log(self, content: str):
        print(
            f'{common_utils.STYLE_BOLD_START}[{self.pu_name}]{common_utils.STYLE_BOLD_START} {content}'
        )

    def log_error(self, content: str):
        print(
            f'{common_utils.STYLE_BOLD_START}[{self.pu_name} - Error]{common_utils.STYLE_BOLD_START} {content}'
        )


class _ProducerBase:
    available_attributes = set()

    def __init__(self, module: ModuleBase):
        object.__setattr__(self, 'module', module)

    def __getattribute__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        available_attributes = object.__getattribute__(self, 'available_attributes')
        if name == 'available_attributes':
            return available_attributes
        assert name in available_attributes, f'{name} is not in available attribute {available_attributes}.'
        return getattr(object.__getattribute__(self, 'module'), name)

    def __setattr__(self, name, value):
        if name == 'available_attributes':
            object.__setattr__(self, 'available_attributes', value)
            return
        self._handle_write(name, value)

    def _handle_write(self, name, value):
        raise NotImplementedError

    def declare(self, *attributes: str):
        for attribute in attributes:
            assert attribute not in self.available_attributes, f'{attribute} is already declared.'
            self.available_attributes.add(attribute)


class ProducerInput(_ProducerBase):

    def _handle_write(self, name, value):
        raise NotImplementedError(f'{name} is not mutable.')


class ProducerOutput(_ProducerBase):

    def _handle_write(self, name, value):
        available_attributes = object.__getattribute__(self, 'available_attributes')
        assert name in available_attributes, f'{name} is not in available output attribute {available_attributes}.'
        setattr(object.__getattribute__(self, 'module'), name, value)
