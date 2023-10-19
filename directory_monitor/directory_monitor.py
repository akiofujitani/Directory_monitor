import logging, log_builder, file_handler, tkinter, json_config, support_funcions
from classes import ConfigurationValues
from gui_builder import Config_Window, About, ListView
from queue import Queue
from threading import Event, Thread
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
from time import sleep

logger = logging.getLogger('directory_monitor')


configuration_template = '''
{
    "update_time" : "10",
    "list_geometry" : {
        "main" : [
            "", 
            "", 
            0, 
            0
        ],
        "settings" : [
            "", 
            "", 
            0, 
            0
        ],
        "edit" : [
            "", 
            "", 
            0, 
            0
        ],
        "list_view" : [
            "", 
            "", 
            0, 
            0
        ]
    },
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
    def __init__(self, title: str, log_queue: Queue, main_thread : Thread, config: ConfigurationValues, *args, **kwargs) -> None:
        tkinter.Tk.__init__(self, *args, **kwargs)
        self.title(title)
        self.config_values = config
        self.log_queue = log_queue
        self.main_thread = main_thread

        # If config has window size and position, set it in app
        win_pos = support_funcions.check_win_pos(self.config_values, 'main')
        if win_pos:
            self.geometry(win_pos)

        # Icon load hard coded, but it doesn't matter
        try:
            self.icon_path = file_handler.resource_path('./Icon/walrus.png')
            icon = Image.open(self.icon_path)
            icon.resize((96, 96), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(icon)
            self.wm_iconphoto(True, photo)
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
        self.style = ttk.Style()
        self.style.configure('Treeview.Heading', rowheight=30, font=(None, 10, 'bold'))
        self.style.configure('Treeview', rowheight=30, font=(None, 12))

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
        y_scrollbar.grid(row=0, column=4, sticky='ns', padx=(0, 5), pady=(5, 0))
        self.path_tree_view.configure(yscroll=y_scrollbar.set)

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
        if '<UPDATE>' in message:
            event.set()
            self.main_thread.join()
            logger.debug('Thread finalized')
            try:
                config_values = json_config.load_json_config('directory_monitor_config.json', configuration_template)
                config = ConfigurationValues.check_type_insertion(config_values)
                self.config_values = config
                self.__update_gui()
            except Exception as error:
                logger.critical(f'Configuration error {error}')
                exit()
            event.clear()
            self.main_thread = Thread(target=main, args=(event, self.config_values, ), daemon=True, name='Directory Monitor')
            self.main_thread.start()


    def __update_gui(self):
        self.path_tree_view.delete(*self.path_tree_view.get_children())
        for i in range(len(self.config_values.path_list)):
            path_values = self.config_values.path_list[i]
            self.path_tree_view.insert('', tkinter.END, values=(path_values.name, path_values.path))
        self.__update()          


    def __always_on_top(self):
        r'''
        Set window do always on top
        '''
        logger.info(f'Always on top {self.entry.get()}')
        self.attributes('-topmost', self.entry.get())
        self.config_values.always_on_top = self.entry.get()
        support_funcions.save_config_on_change(self.config_values)


    def __update(self):
        r'''
        Update values from treeview
        '''
        logger.info('Update clicked')
        support_funcions.update_count(self.config_values)


    def __configuration(self):
        logger.debug('Config button clicked')
        self.config_window = Config_Window(self, self.config_values, (400, 300), 'directory_monitor_config.json')


    def __on_window_close(self):
        self.__quit_window()


    def __quit_window(self):
        if messagebox.askokcancel('Quit', 'Do you want to quit?'):
            event.set()
            support_funcions.save_config_on_change(support_funcions.update_win_size_pos(self.geometry(), 'main', self.config_values))
            logger.info('Forcing kill thread if it is open')
            self.after(150, self.deiconify)
            self.destroy()


    def __tree_item_view(self, event=None):
        try:
            item_id = self.path_tree_view.selection()[0]
            selected_item = self.path_tree_view.item(item_id)['values']
            self.list_view = ListView(self, self.config_values.get_path_details(selected_item[0]), self.config_values, (500, 500))
        except:
            messagebox.showerror('Selection error', 'No row is selected')
        logger.debug('Treeview double click, return')


    def __about_command(self):
        logger.info('About clicked')
        self.about = About(self, self.config_values.always_on_top,
            'About', '''
            Application name: Directory Monitor
            Version: 0.10.00
            Developed by: Akio Fujitani
            e-mail: akiofujitani@gmail.com
        ''', file_handler.resource_path('./Icon/Bedo.jpg'))              


def main(event: Event, config: ConfigurationValues):
    while True:
        support_funcions.update_count(config)
        if event.is_set():
            return
        sleep(config.update_time)


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

    main_app = MainApp('Directory Monitor', log_queue, main_thread, config)
    main_app.mainloop()

