import tkinter, logging, json_config, file_handler, support_funcions
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
from copy import deepcopy
from classes import ConfigurationValues, PathDetails
from PIL import Image, ImageTk
from os.path import normpath, exists, getmtime, join
from os import startfile
from datetime import datetime
logger = logging.getLogger('gui_classes')


'''
=============================================================================================================================

        List View Window        List View Window        List View Window        List View Window        List View Window                        

=============================================================================================================================
'''

class ListView(tkinter.Toplevel):
    r'''
    List View Window
    ----------------

    PathDetail
    name : str
    path: str
    extension: str
    ignore: str    
    '''
    def __init__(self, master_win: tkinter.Tk, path_detail: PathDetails, config: ConfigurationValues, min_size: tuple, *args, **kwargs):
        tkinter.Toplevel.__init__(self, *args, **kwargs)
        self.config_values = config
        self.last_grab = self.grab_current()
        self.grab_set()
        self.path_detail = path_detail
        self.title(f'List View for {self.path_detail.name}')
        self.minsize(width=min_size[0], height=min_size[1])
        self.master_win = master_win
        if self.config_values.always_on_top == True:
            self.master_win.attributes('-topmost', False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        win_pos = support_funcions.check_win_pos(self.config_values, 'list_view')
        if win_pos:
            self.geometry(win_pos)

        # Treeview Frame
        frame_treeview = tkinter.Frame(self)
        frame_treeview.grid(column=0, row=0, columnspan=5, sticky='nesw', padx=(5), pady=(5))
        frame_treeview.columnconfigure(0, weight=1)
        frame_treeview.rowconfigure(0, minsize=35)
        frame_treeview.rowconfigure(1, weight=1)

        # Filter
        tkinter.Label(frame_treeview, text='Filter ').grid(column=2, row=0, sticky='nesw', padx=(5), pady=(5))
        call_back_reg = (frame_treeview.register(self.__validate_text),'%P')        # register a callback function in Frame
        self.filter_entry = tkinter.Entry(frame_treeview, width=40, justify=tkinter.CENTER, validate='key', validatecommand=call_back_reg) # Entry with verification
        self.filter_entry.grid(column=3, row=0, columnspan=2, sticky='nesw', padx=(5), pady=(5))

        # Treeview
        heading_dict = {'file_name' : 'File Name', 'modified_date' :'Modified Date'}
        column_size = (250, 250)
        anchor = (tkinter.W, tkinter.CENTER)
        self.treeview_list = ttk.Treeview(frame_treeview, columns=('file_name', 'modified_date'), show='headings')
        for i, (key, value) in enumerate(heading_dict.items()):
            self.treeview_list.heading(key, text=value)
            self.treeview_list.column(i, anchor=anchor[i], minwidth=30, width=column_size[i])
        self.treeview_list.grid(column=0, row=1, columnspan=4, sticky='nesw')
        self.treeview_list.columnconfigure(0, weight=1)
        self.treeview_list.rowconfigure(0, weight=1)
        scroll_bar = ttk.Scrollbar(frame_treeview, orient=tkinter.VERTICAL, command=self.treeview_list.yview)
        scroll_bar.grid(column=4, row=1, sticky='ns', padx=(0, 5))
        self.treeview_list.configure(yscrollcommand=scroll_bar.set)
        self.file_list = self.create_treeview_list()
        self.tree_view_insert(self.file_list)
        self.treeview_list.bind('<Double-1>', self.__tree_item_view)
        self.treeview_list.bind('<Return>', self.__tree_item_view)

        # Button Frame
        frame_button = tkinter.Frame(self)
        frame_button.grid(column=0, row=1, columnspan=5, sticky='nesw', padx=(5), pady=(5))

        # Button
        self.button_close = tkinter.Button(frame_button, text='Close', command=self.__on_window_close, width=15)
    

    def __tree_item_view(self, event=None):
        try:
            item_id = self.treeview_list.selection()[0]
            selected_item = self.treeview_list.item(item_id)['values']
            startfile(join(self.path_detail.path, selected_item[0]))
        except:
            messagebox.showerror('Selection error', 'No row is selected')
        logger.debug('Treeview double click, return')


    
    def __validate_text(self, input: any):
        r'''
        Entry validation
        Rebuild de treeview using the input as filter
        '''
        logger.debug(input)
        self.tree_view_insert(self.file_list, input)
        return True
        

    def tree_view_insert(self, name_date_list: list, filter: str | None=None):
        self.treeview_list.delete(*self.treeview_list.get_children())
        if filter:
            name_date_list = [name_date for name_date in name_date_list if filter in name_date[0]]
        for name_date in name_date_list:
            self.treeview_list.insert('', tkinter.END, values=tuple(name_date))


    def create_treeview_list(self):
        try:
            file_list = file_handler.file_list(self.path_detail.path, self.path_detail.extension)
            if len(file_list) > 0:
                name_date_list = [[file, datetime.strftime(datetime.fromtimestamp(getmtime(join(self.path_detail.path, file))), '%d/%m/%Y %H:%M:%S')] for file in file_list]
                return name_date_list
        except Exception as error:
            logger.debug(error)
            messagebox.showerror('File List Error', f'Could not load file list due {error}')            


    def __on_window_close(self):
        logger.debug('On close click')
        self.destroy()


    # destroy override
    def destroy(self) -> None:
        if self.last_grab:
            self.last_grab.grab_set()
        self.master_win.attributes('-topmost', self.config_values.always_on_top)
        support_funcions.save_config_on_change(support_funcions.update_win_size_pos(self.geometry(), 'list_view', self.config_values))
        return super().destroy()


'''
=============================================================================================================================

        Configuration Window        Configuration Window        Configuration Window        Configuration Window        

=============================================================================================================================
'''


class Config_Window(tkinter.Toplevel):
    r'''
    Configuration Window
    --------------------
    
    update_time : int
    width: int
    height: int
    x : int
    y : int
    always_on_top: bool
    path_list: list        
    
    name : str
    path: str
    extension: str
    ignore: str

    ''' 
    def __init__(self, master_win: tkinter.Tk, config: ConfigurationValues, 
                min_size: tuple,
                config_path: str,
                *args, **kwargs) -> None:
        tkinter.Toplevel.__init__(self, *args, **kwargs)
        self.last_grab = self.grab_current()
        self.grab_set()
        self.config_values = config
        self.config_path = config_path
        self.title('Configuration')
        self.minsize(width=min_size[0], height=min_size[1])
        self.master_win = master_win
        if self.config_values.always_on_top == True:
            self.master_win.attributes('-topmost', False)
        win_pos = support_funcions.check_win_pos(self.config_values, 'settings')
        if win_pos:
            self.geometry(win_pos)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Configuration Frame
        config_main = tkinter.Frame(self)
        config_main.grid(column=0, row=0, columnspan=5, sticky='nesw', padx=(5), pady=(5))  
        config_main.columnconfigure(0, weight=1)

        # Label and values
        tkinter.Label(config_main, text='Update time', justify='left').grid(column=2, row=0, sticky='nesw', padx=(5), pady=(5))
        self.time_entry = tkinter.Entry(config_main, justify='center')
        self.time_entry.grid(column=3, row=0, sticky='nesw', columnspan=2, padx=(5), pady=(5))
        self.time_entry.insert(tkinter.END, self.config_values.update_time)

        # Treeview Frame
        config_treeview = tkinter.Frame(self)
        config_treeview.grid(column=0, row=1, columnspan=5, sticky='nesw', padx=(5), pady=(5))
        config_treeview.columnconfigure(0, weight=1)
        config_treeview.rowconfigure(0, weight=1)

        # Treeview
        headings_dict = {'name' : 'Display name', 'path' : 'Path', 'extension' : 'Extension','ignore' : 'Ignore'}
        column_size = (100, 150, 70, 100)
        self.path_treeview = ttk.Treeview(config_treeview, columns=('name', 'path', 'extension', 'ignore'), show='headings')
        for i, (key, value) in enumerate(headings_dict.items()):
            self.path_treeview.heading(key, text=value)
            self.path_treeview.column(i, minwidth=20, width=column_size[i])
        for path_value in self.config_values.path_list:
            self.path_treeview.insert('', tkinter.END, values=(path_value.name, path_value.path, path_value.extension, path_value.ignore))
        self.path_treeview.grid(column=0, row=0, columnspan=4, sticky='nesw')
        scroll_bar = ttk.Scrollbar(config_treeview, orient=tkinter.VERTICAL, command=self.path_treeview.yview)
        scroll_bar.grid(column=4, row=0, sticky='ns', padx=(0, 5))
        self.path_treeview.configure(yscrollcommand=scroll_bar.set)

        self.path_treeview.bind('<Double-1>', self.__treeview_edit)
        self.path_treeview.bind('<Return>', self.__treeview_edit)

        # Treeview Buttons
        treeview_button_frame = tkinter.Frame(config_treeview)
        treeview_button_frame.grid(column=0, row=1, columnspan=5, sticky='nesw')
        treeview_button_frame.columnconfigure(0, weight=1)

        treeview_edit = tkinter.Button(treeview_button_frame, text='Edit ', command=self.__treeview_edit, width=12)
        treeview_delete = tkinter.Button(treeview_button_frame, text='Delete', command=self.__treeview_delete, width=12)
        treeview_add = tkinter.Button(treeview_button_frame, text='Add ', command=self.__treeview_add, width=12)
        treeview_edit.grid(column=2, row=1, sticky='nesw')
        treeview_delete.grid(column=3, row=1, sticky='nesw')
        treeview_add.grid(column=4, row=1, sticky='nesw', padx=(0, 10))

        # Buttons
        button_frame = tkinter.Frame(self)
        button_frame.grid(column=0, row=2, columnspan=5, padx=(5), pady=(5), sticky='nesw')
        button_frame.columnconfigure(0, weight=1)

        cancel_button = tkinter.Button(button_frame, text='Cancel', command=self.__click_button_cancel, width=15)
        cancel_button.grid(column=4, row=1, padx=(0), pady=(0, 5))    
        save_button = tkinter.Button(button_frame, text='Save', command=self.__click_button_save, width=15)
        save_button.grid(column=5, row=1, padx=(0), pady=(0, 5))

        self.protocol('WM_DELETE_WINDOW', self.__on_window_close)


    def __treeview_edit(self, event=None):
        r'''
        Edit the selected treeview
        --------------------------
        name : str
        path: str
        extension: str
        ignore: str
        '''
        logger.debug('Treeview edit')
        try:
            # Code here
            self.path_treeview.selection()[0]
            label_list = ('Display name', 'Path', 'Extension', 'Ignore')
            type_list = ('str', 'path', 'str', 'str')
            self.path_treeview_edit = Edit_Values(self.path_treeview, self.config_values, label_list, type_list, 'Edit directory values')
        except Exception as error:
            logger.debug(error)
            messagebox.showerror('Edit error', 'No row is selected')


    def __treeview_delete(self):
        '''
        Delete selected row from treeview
        '''
        logger.debug('Treeview delete')
        try:
            selected_item = self.path_treeview.selection()[0]
            logger.debug(selected_item)
            if messagebox.askquestion('Delete', f'Do you really want to delete the item {selected_item}?') == 'yes':
                self.path_treeview.delete(selected_item)
        except:
            messagebox.showerror('Delete error', 'No row is selected')
    

    def __treeview_add(self):
        '''
        Add row to treeview
        '''
        logger.debug('Treeview add')
        empty_values = ['' for _ in range(4)]
        self.path_treeview.insert('', tkinter.END, values=(tuple(empty_values)))
        children_list = self.path_treeview.get_children()
        self.path_treeview.selection_set(children_list[-1])
        self.__treeview_edit(None)


    def __click_button_cancel(self):
        logger.debug('Cancel click')
        self.__on_window_close()


    def __click_button_save(self):
        r'''
        update_time : int
        width: int
        height: int
        x : int
        y : int
        always_on_top: bool
        path_list: list        
        
        name : str
        path: str
        extension: str
        ignore: str
        '''
        logger.debug('Save clicked')

        new_config = deepcopy(self.config_values)
        new_config.update_time = int(self.time_entry.get())
        new_config.path_list = [PathDetails(*self.path_treeview.item(value)['values']) for value in self.path_treeview.get_children()]
        if not self.config_values.__eq__(new_config):
            logger.debug('Configuration objects are different')
            self.config_values = deepcopy(new_config)
            json_config.save_json_config(self.config_path, new_config.to_dict())
            logger.info('<UPDATE> Configuration values updated')
        self.destroy()


    def __on_window_close(self):
        logger.debug('On close click')
        self.destroy()


    # destroy override
    def destroy(self) -> None:
        if self.last_grab:
            self.last_grab.grab_set()
        self.master_win.attributes('-topmost', self.config_values.always_on_top)            
        config_updated = support_funcions.update_win_size_pos(self.geometry(), 'settings', self.config_values)
        support_funcions.save_config_on_change(config_updated)
        return super().destroy()

'''
=============================================================================================================================

        Edit_Values     Edit_Values     Edit_Values     Edit_Values     Edit_Values     Edit_Values     Edit_Values     

=============================================================================================================================
'''

class Edit_Values(tkinter.Toplevel):
    def __init__(self, 
                    parent=ttk.Treeview, 
                    config= ConfigurationValues,
                    key_list=tuple, 
                    type_list=tuple,
                    edit_title=str,
                    values_disabled=None, 
                    focus_force=None, 
                    drop_down_list=None,
                    *args, **kwargs) -> None:
        tkinter.Toplevel.__init__(self, *args, **kwargs)
        self.config_values = config
        self.last_grab = self.grab_current()
        self.grab_set()
        self.parent = parent
        self.title(edit_title)
        self.transient()
        win_pos = support_funcions.check_win_pos(self.config_values, 'edit')
        if win_pos:
            self.geometry(win_pos)
        self.selected_item = self.parent.selection()[0]
        self.record_value = [str(value) for value in self.parent.item(self.selected_item)['values']]
        self.type_list = type_list
        self.entry_dict = {}
        self.button_dict = {}
        for key_index in range(len(key_list)):
            ttk.Label(self, text=key_list[key_index], justify='left').grid(column=0, row=key_index, padx=(5), pady=(5, 0))
            match type_list[key_index]:
                case 'str' | 'int' :
                    entry = ttk.Entry(self, width=50, justify='center')
                    entry.grid(column=1, row=key_index, sticky='nesw', columnspan=3, padx=(5), pady=(5, 0))
                    entry.insert(tkinter.END, str(self.record_value[key_index]))
                case 'path':
                    entry = ttk.Entry(self, width=50, justify='center')
                    entry.grid(column=1, row=key_index, sticky='nesw', columnspan=2, padx=(5, 0), pady=(5, 0))
                    browse_button = tkinter.Button(self, text='...', width=3)
                    browse_button.grid(column=3, row=key_index, padx=(0, 5), pady=(5, 0))
                    self.button_dict[f'{key_list[key_index]}'] = browse_button
                    self.button_dict[f'{key_list[key_index]}'].configure(command= lambda info=key_list[key_index]: self.__browse_files(info))
                    entry.insert(tkinter.END, str(self.record_value[key_index]))
                case 'boolean':
                    entry = tkinter.BooleanVar()
                    entry.set(self.record_value[key_index] if not self.record_value[key_index] == '' else False)
                    boolean_name = ('True', 'False')
                    radio_bool_button = {}
                    for i in range(len(boolean_name)):
                        radio_bool_button[i] = tkinter.ttk.Radiobutton(self, text=boolean_name[i], value=eval(boolean_name[i]), variable=entry, command=lambda variable=entry: self.__click_radio_bool(variable))
                        radio_bool_button[i].grid(column=1 + i, row=key_index)
                case 'combo_box':
                    entry = ttk.Combobox(self, width=50, justify='center')
                    entry['values'] = drop_down_list[key_list[key_index]]
                    entry.set(str(self.record_value[key_index]) if not str(self.record_value[key_index]) == '' else 'Daily')
                    entry.grid(column=1, row=key_index, sticky='nesw', columnspan=3, padx=(5), pady=(5, 0))
                case _:
                    entry = ttk.Entry(self, width=50, justify='center')
                    entry.grid(column=1, row=key_index, sticky='nesw', columnspan=2, padx=(5), pady=(5, 0))
                    entry.insert(tkinter.END, str(self.record_value[key_index]))
            if not values_disabled == None:
                if key_list[key_index] in values_disabled:
                    entry.configure(state='disabled')
            self.entry_dict[key_list[key_index]] = entry
        if focus_force:
            self.entry_dict[focus_force].focus_force()
            self.entry_dict[focus_force].select_clear()
            self.entry_dict[focus_force].select_range(0, tkinter.END)
        self.bind("<Return>", self.__click_button_save)
        self.bind("<Escape>", lambda *ignore: self.destroy())

        cancel_button = tkinter.Button(self, text='Cancel', command=self.__click_button_cancel, width=15)
        cancel_button.grid(column=1, row=key_index + 1, padx=(5), pady=(5))    
        save_button = tkinter.Button(self, text='Save', command=self.__click_button_save, width=15)
        save_button.grid(column=2, row=key_index + 1, padx=(5), pady=(5))       


    def __click_radio_bool(self, variable):
        logger.debug(variable.get())


    def __click_button_cancel(self):
        logger.debug('Button cancel')
        if self.__compare_to_empty(''):
            self.parent.delete(self.selected_item)
        self.destroy()
    

    def __compare_to_empty(self, compare_value=str):
        for value in self.record_value:
            if not value == compare_value:
                return False
        return True


    def __click_button_save(self, event=None):
        logger.debug('Button save')
        new_record = []
        diff_found = False        
        entry_dict_keys = list(self.entry_dict.keys())
        for index in range(len(entry_dict_keys)):
            match self.type_list[index]:
                case 'str' | 'int':
                    if self.type_list[index] == 'int':
                        try:
                            value = int(self.entry_dict[entry_dict_keys[index]].get())
                        except:
                            messagebox.showerror('Save error', f'Value must be an integer')
                            self.lift()
                            self.focus_force()
                            self.entry_dict[entry_dict_keys[index]].focus_force()
                            return
                    else:
                        value = str(self.entry_dict[entry_dict_keys[index]].get())
                case 'path':
                    try:
                        if not exists(self.entry_dict[entry_dict_keys[index]].get()):
                            raise Exception('Path error')
                        value = normpath(self.entry_dict[entry_dict_keys[index]].get())
                    except:
                        messagebox.showerror('Save error', f'Invalid or inexistent path')
                        self.lift()
                        self.focus_force()
                        self.entry_dict[entry_dict_keys[index]].focus_force()
                        return
                case 'boolean':
                    value = self.entry_dict[entry_dict_keys[index]].get()
                case 'combo_box':
                    value = self.entry_dict[entry_dict_keys[index]].get()
            new_record.append(value)
            if not self.record_value[index] == value:
                diff_found = True
        if diff_found == True:
            self.parent.item(self.selected_item, values=new_record)
        logger.debug(f'Button save done')
        self.destroy()


    def __browse_files(self, button_id=str):
        logger.debug('Browser files')
        logger.debug(button_id)
        file_path = filedialog.askdirectory(initialdir='/', title='Select the file path')
        if file_path:
            self.entry_dict[button_id].delete(0, tkinter.END)
            self.entry_dict[button_id].insert(tkinter.END, str(normpath(file_path)))
        self.lift()
        logger.debug(f'File path {file_path}')


    # destroy override
    def destroy(self) -> None:
        if self.last_grab:
            self.last_grab.grab_set()
        support_funcions.save_config_on_change(support_funcions.update_win_size_pos(self.geometry(), 'edit', self.config_values))
        return super().destroy()


# Basic About class
class About(tkinter.Toplevel):
    def __init__(self, master_win: tkinter.Tk, master_always_on_top: bool, title=str, label_values=str, image_file=str, *args, **kwargs) -> None:
        r'''
        About Window
        ------------

        Meant to store development information
        '''
        tkinter.Toplevel.__init__(self, *args, **kwargs)
        self.last_grab = self.grab_current()
        self.grab_set()
        self.geometry('450x400')
        self.master_win = master_win
        self.always_on_top = master_always_on_top
        if self.always_on_top == True:
            self.master_win.attributes('-topmost', False)
        self.title(title)
        self.resizable(width=False, height=False)
        image = Image.open(image_file)
        image_tk = ImageTk.PhotoImage(image=image)
        image_label = tkinter.Label(self, image=image_tk, justify='center')
        image_label.image = image_tk
        image_label.grid(column=0, row=0, columnspan=2, padx=(10), pady=(5, 0))

        text_label = tkinter.Label(self, text=label_values, justify='left')
        text_label.grid(column=0, row=1, rowspan=2, sticky='nw', padx=(5), pady=(5, 0))

        ok_button = tkinter.Button(self, text='Ok', width=15, command=self.__pressed_ok_button)
        ok_button.grid(column=1, row=2, sticky='se', padx=(10), pady=(5, 10))

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=2)
        self.protocol('WM_DELETE_WINDOW', self.__on_window_close)    
    

    def destroy(self) -> None:
        if self.last_grab:
            self.last_grab.grab_set()
        self.master_win.attributes('-topmost', self.always_on_top)
        return super().destroy()


    def __pressed_ok_button(self):
        self.__on_window_close()
    

    def __on_window_close(self):
        self.destroy()