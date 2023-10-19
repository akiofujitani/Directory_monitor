import logging
from dataclasses import dataclass
from os.path import normpath
from collections import namedtuple


logger = logging.getLogger()


TtkGeometry = namedtuple('TtkGeometry', 'width, height, x, y')


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


@dataclass
class ConfigurationValues:
    r'''
    Configuration for path list
    '''
    update_time : int
    list_geometry : dict
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
        values_dict['list_geometry'] = {name : [*value] for name, value in values_dict['list_geometry'].items()}
        values_dict['always_on_top'] = str(values_dict['always_on_top'])
        values_dict['path_list'] = [value.__dict__ for value in values_dict['path_list']]
        return values_dict


    def get_path_details(self, name: str) -> PathDetails:
        for path_value in self.path_list:
            if path_value.name == name:
                return path_value
        return None


    @classmethod
    def check_type_insertion(cls, config_values: dict):
        try:
            update_time = int(config_values['update_time'])
            list_geometry = {name : TtkGeometry(*value) for name, value in config_values['list_geometry'].items()}
            always_on_top = eval(config_values['always_on_top']) if type(config_values['always_on_top']) == str else config_values['always_on_top']
            path_list = [PathDetails.check_type_insertion(path_parameters) for path_parameters in config_values['path_list']]
            return cls(update_time, list_geometry, always_on_top, path_list)
        except Exception as error:
            raise error



