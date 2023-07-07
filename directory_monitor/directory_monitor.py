import logging, log_builder, file_handler, tkinter, json_config
from classes import ConfigurationValues, PathDetails
from gui_builder import Config_Window, About
from queue import Queue
from threading import Event, Thread
from tkinter import messagebox
from tkinter import ttk
from PIL import Image
from re import search
from time import sleep
from copy import deepcopy

logger = logging.getLogger('directory_monitor')


configuration_template = '''
{
    "update_time" : "10",
    "width" : "",
    "height" : "",
    "x" : "0",
    "y" : "0",
    "always_on_top" : "False",
    "path_list" : [
        {
            "name" : "Template",
            "path" : "./",
            "extension" : "",
            "ignore" : ""
        }
    ]
}
'''


class MainApp(tkinter.Tk):
    def __init__(self, title: str, log_queue: Queue, config: ConfigurationValues, *args, **kwargs) -> None:
        tkinter.Tk.__init__(self, *args, **kwargs)
        self.title(title)
        self.config_values = config
        self.log_queue = log_queue

        # If config has window size and position, set it in app
        if config.width and config.height:
            geometry_values = f'{config.width}x{config.height}+{config.x}+{config.y}'
            logger.debug(geometry_values)
            self.geometry(geometry_values)

        # Icon load hard coded, but it doesn't matter
        try:
            self.icon_path = file_handler.resource_path('./Icon/tiger.ico')
            self.icon_image = Image.open(self.icon_path)
        except Exception as error:
            logger.error(f'Could not load icon {error}')
        
        # Configure grid columns weight (follow resize)
        self.grid_columnconfigure(0, weight=1, minsize=200)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_rowconfigure(0, weight=1)

        # Menu bar creation
        menu_bar = tkinter.Menu(self)
        file_menu = tkinter.Menu(menu_bar, tearoff=0)
        help_menu = tkinter.Menu(menu_bar, tearoff=0)
        edit_menu = tkinter.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label='Update    ', command=self.__update)
        file_menu.add_command(label='Exit     ', command=self.__quit_window)
        edit_menu.add_command(label='Settings', command=self.__configuration)
        help_menu.add_command(label='About     ', command=self.__about_command)
        menu_bar.add_cascade(label='File     ', menu=file_menu)
        menu_bar.add_cascade(label='Edit     ', menu=edit_menu)
        menu_bar.add_cascade(label='Help     ', menu=help_menu)
        self.config(menu=menu_bar)

        # treeview
        column_list = ('path_name', 'quantity')
        width_list = (150, 80)
        self.column_descr = ('Path Name' , 'Quantity')
        self.path_tree_view = ttk.Treeview(self, columns=column_list, show='headings')
        self.path_tree_view.column('# 2', anchor=tkinter.CENTER)

        # treeview style
        style = ttk.Style()
        style.configure('Treeview.Heading', rowheight=30, font=(None, 10, 'bold'))
        style.configure('Treeview', rowheight=30, font=(None, 12))

        for i in range(len(column_list)):
            self.path_tree_view.heading(column_list[i], text=self.column_descr[i])
            self.path_tree_view.column(column_list[i], minwidth=20, width=width_list[i])
        self.path_tree_view.grid(column=0, row=0, columnspan=3, sticky='nesw', padx=(5, 0), pady=(5, 0))

        # Treeview Insert
        for i in range(len(self.config_values.path_list)):
            path_values = self.config_values.path_list[i]
            self.path_tree_view.insert('', tkinter.END, values=(path_values.name, path_values.path))      

        # Treeview Scrollbar configuration
        y_scrollbar = ttk.Scrollbar(self, orient=tkinter.VERTICAL, command=self.path_tree_view.yview)
        self.path_tree_view.configure(yscroll=y_scrollbar.set)
        y_scrollbar.grid(row=0, column=4, sticky='ns', padx=(0, 5), pady=(5, 0))

        # Treeview configure
        self.path_tree_view.columnconfigure(0, weight=1)
        self.path_tree_view.rowconfigure(0, weight=1)

        # For later development, will open a window with the files list
        self.path_tree_view.bind('<Double-1>', self.__tree_item_view)
        self.path_tree_view.bind('<Return>', self.__tree_item_view)

        # Button configuration
        button_frame = tkinter.Frame(self)
        button_frame.grid(column=0, row=1, columnspan=5, padx=(3), pady=(3), sticky='nesw')
        for i in range(5):
            button_frame.columnconfigure(i, minsize=43)
        button_frame.columnconfigure(1, weight=1)
        button_frame.rowconfigure(0, minsize=20)

        button_update = tkinter.Button(button_frame, text='Update', command=self.__update, width=10)
        button_update.grid(column=2, row=1, padx=(3, 0), pady=(3), sticky='nw')
        button_config = tkinter.Button(button_frame, text='Settings', command=self.__configuration, width=10)
        button_config.grid(column=3, row=1, padx=(0), pady=(3), sticky='nw')

        # Check button configuration
        self.entry = tkinter.IntVar()
        self.entry.set(self.config_values.always_on_top)
        self.__always_on_top()
        always_on_top = tkinter.Checkbutton(button_frame, text='Always on top', variable=self.entry, onvalue=1, offvalue=0, command=self.__always_on_top)
        always_on_top.grid(column=0, row=1, padx=(3), pady=(3), sticky='ne')

        # Button close top right
        self.protocol('WM_DELETE_WINDOW', self.__on_window_close)
        self.after(100, self.__pull_log_queue)


    # Log handler
    def __pull_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get(block=False)
            self.__display(message)
        self.after(100, self.__pull_log_queue)


    def __display(self, message: str):
        if '<PATH>' in message:
            path_dict = {}
            path_values = message.split('<PATH>')[1].split(',')
            for path in path_values:
                path_split = path.split(':')
                path_dict[path_split[0]] = path_split[1]
            logger.debug(path_dict)
            for child in self.path_tree_view.get_children():
                values = self.path_tree_view.item(child)['values']
                if str(values[0]) == str(path_dict['path_name']):
                    self.path_tree_view.item(child, values=(path_dict['path_name'], path_dict['quantity']))


    def __always_on_top(self):
        r'''
        Set window do always on top
        '''
        logger.info(f'Always on top {self.entry.get()}')
        self.attributes('-topmost', self.entry.get())
        self.config_values.always_on_top = self.entry.get()
        self.__save_config_on_change()

    def __update(self):
        r'''
        Update values from treeview
        '''
        logger.info('Update clicked')
        self.update_count(self.config_values)


    def __configuration(self):
        logger.debug('Config button clicked')
        self.config_window = Config_Window(self.config_values, (400, 300), 'directory_monitor_config.json', self.icon_path)
        logger.debug(f'Config {self.grab_status}')
        logger.debug(self.winfo_children)


    def __on_window_close(self):
        self.__quit_window()


    def __quit_window(self):
        if messagebox.askokcancel('Quit', 'Do you want to quit?'):
            event.set()
            self.__update_win_size_pos(self.config_values)
            self.__save_config_on_change()
            logger.info('Forcing kill thread if it is open')
            self.after(150, self.deiconify)
            self.destroy()


    def __tree_item_view(self):
        try:
            self.path_tree_view.selection()[0]
        except:
            messagebox.showerror('Selection error', 'No row is selected')
        logger.debug('Treeview double click, return')


    def __about_command(self):
        logger.info('About clicked')
        self.about = About('About', '''
        Application name: Directory Monitor
        Version: 0.10.00
        Developed by: Akio Fujitani
        e-mail: akiofujitani@gmail.com
        ''', file_handler.resource_path('./Icon/Bedo.jpg'), self.icon_path)


    def __update_win_size_pos(self, config: ConfigurationValues):
        r'''
        Update window size and position in config object
        '''
        geometry_str = self.geometry()
        temp_splited_geometry = geometry_str.split('+')
        win_size = temp_splited_geometry[0].split('x')
        win_pos = [temp_splited_geometry[1], temp_splited_geometry[2]]
        if not win_size[0] == config.width or not win_size[1] == config.width or not win_pos[0] == config.x or not win_pos[1] == config.y:
            logger.debug(f'{win_size[0]} x {win_size[1]} + {win_pos[0]} + {win_pos[1]}')
            config.width = win_size[0]
            config.height = win_size[1]
            config.x = win_pos[0]
            config.y = win_pos[1]
        return


    def __save_config_on_change(self):
        try:
            config_value = json_config.load_json_config('directory_monitor_config.json')
            old_config = ConfigurationValues.check_type_insertion(config_value)
            if not self.config_values.__eq__(old_config):
                temp_config = deepcopy(self.config_values)
                json_config.save_json_config('directory_monitor_config.json', temp_config.to_dict())
        except Exception as error:
            logger.error(f'Could not save configuration values {error}')                


    @staticmethod
    def update_count(config: ConfigurationValues) -> None:
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


def main(event: Event, config: ConfigurationValues):
    while True:
        MainApp.update_count(config)
        if event.set():
            return
        sleep(config.update_time)


# def __update_count(config: ConfigurationValues) -> None:
#     for path_value in config.path_list:
#         try:
#             file_list = file_handler.file_list(path_value.path, path_value.extension)
#             if path_value.ignore:
#                 for file_name in file_list:
#                     if reg_ex_ignore(path_value.ignore, file_name):
#                         file_list.remove(file_name)
#             logger.info(f'<PATH>path_name:{path_value.name},quantity:{len(file_list)}')
#         except Exception as error:
#             logger.error(f'Update count error {error}')
#     return


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


if __name__ == '__main__':
    log_queue = Queue()
    logger = logging.getLogger()
    log_builder.logger_setup(logger, log_queue)

    event = Event()

    try:
        config_values = json_config.load_json_config('directory_monitor_config.json', configuration_template)
        config = ConfigurationValues.check_type_insertion(config_values)
    except Exception as error:
        logger.critical(f'Configuration error {error}')
        exit()

    
    main_thread = Thread(target=main, args=(event, config, ), daemon=True, name='Directory Monitor')
    main_thread.start()

    main_app = MainApp('Directoru Monitor', log_queue, config)
    main_app.mainloop()

