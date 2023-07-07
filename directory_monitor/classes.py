import logging, log_builder
from dataclasses import dataclass
from os.path import normpath
from collections import namedtuple


logger = logging.getLogger()


TtkGeometry = namedtuple('TtkGeometry', 'width, height, x, y')

@dataclass
class ConfigurationValues:
    r'''
    Configuration for path list
    '''
    update_time : int
    width: int
    height: int
    x : int
    y : int
    always_on_top: bool
    path_list: list


    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        else:
            self_values = self.__dict__
            for key in self_values.keys():
                if not getattr(self, key) == getattr(other, key):
                    return False
            return True


    def to_dict(self):
        values_dict = self.__dict__
        values_dict['always_on_top'] = str(values_dict['always_on_top'])
        values_dict['path_list'] = [value.__dict__ for value in values_dict['path_list']]
        return values_dict


    @classmethod
    def check_type_insertion(cls, config_values: dict):
        try:
            update_time = int(config_values['update_time'])
            width = int(config_values['width']) if config_values['width'] else ''
            height = int(config_values['height']) if config_values['height'] else ''
            x = int(config_values['x']) if config_values['x'] else ''
            y = int(config_values['y']) if config_values['y'] else ''
            always_on_top = eval(config_values['always_on_top']) if type(config_values['always_on_top']) == str else config_values['always_on_top']
            path_list = [PathDetails.check_type_insertion(path_parameters) for path_parameters in config_values['path_list']]
            return cls(update_time, width, height, x, y, always_on_top, path_list)
        except Exception as error:
            raise error



@dataclass
class PathDetails:
    r'''
    Path details with path, file extension, and ignore pattern
    '''
    name : str
    path: str
    extension: str
    ignore: str


    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        else:
            self_values = self.__dict__
            for key in self_values.keys():
                if not getattr(self, key) == getattr(other, key):
                    return False
            return True
    

    @classmethod
    def check_type_insertion(cls, config_values: dict):
        try:
            name = config_values['name']
            path =  normpath(config_values['path'])
            extension = config_values['extension']
            ignore = config_values['ignore']
            return cls(name, path, extension, ignore)
        except Exception as error:
            raise error