import logging, json_config, file_handler
from classes import ConfigurationValues, TtkGeometry
from copy import deepcopy
from re import search

logger = logging.getLogger('suport_funcions')


def update_win_size_pos(geometry_str:str, window_name: str, config: ConfigurationValues):
    r'''
    Update window size and position in config object
    '''
    temp_splited_geometry = geometry_str.split('+')
    win_size = temp_splited_geometry[0].split('x')
    win_pos = [temp_splited_geometry[1], temp_splited_geometry[2]]
    main_pos = config.list_geometry[window_name]
    if not win_size[0] == main_pos.width or not win_size[1] == main_pos.height or not win_pos[0] == main_pos.x or not win_pos[1] == main_pos.y:
        logger.debug(f'{win_size[0]} x {win_size[1]} + {win_pos[0]} + {win_pos[1]}')
        main_pos = TtkGeometry(win_size[0], win_size[1], win_pos[0], win_pos[1])
        config.list_geometry[window_name] = main_pos
    return config


def save_config_on_change(config: ConfigurationValues):
    r'''
    Save to configuration file if it has changes
    '''
    try:
        config_value = json_config.load_json_config('directory_monitor_config.json')
        old_config = ConfigurationValues.check_type_insertion(config_value)
        if not config.__eq__(old_config):
            temp_config = deepcopy(config)
            json_config.save_json_config('directory_monitor_config.json', temp_config.to_dict())
    except Exception as error:
        logger.error(f'Could not save configuration values {error}')  


def check_win_pos(config: ConfigurationValues, win_name: str):
    r'''
    Get win position in configuration object
    '''
    win_pos = config.list_geometry[win_name]
    if win_pos.width and win_pos.height:
        geometry_values = f'{win_pos.width}x{win_pos.height}+{win_pos.x}+{win_pos.y}'
        logger.debug(geometry_values)
        return geometry_values


def update_count(config : ConfigurationValues) -> None:
    r'''
    Update files count in each directory in config object
    '''
    for path_value in config.path_list:
        try:
            file_list = file_handler.file_list(path_value.path, path_value.extension)
            if path_value.ignore:
                for file_name in file_list:
                    if reg_ex_ignore(path_value.ignore, file_name):
                        file_list.remove(file_name)
            logger.info(f'<PATH>path_name:{path_value.name},quantity:{len(file_list)}')
        except Exception as error:
            logger.error(f'Update count error {error}')
    return


def reg_ex_ignore(reg_ex: str, search_value: str) -> bool:
    r'''
    Regex search returning boolean
    ----- ------ --------- -------
    
    The ignore must be in the regex format
    See Python RegEx Documentation

    '''
    if search(reg_ex, search_value):
        return True
    return False