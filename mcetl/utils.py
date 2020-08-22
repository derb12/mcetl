# -*- coding: utf-8 -*-
"""Provides utility functions, classes, and constants.

Useful functions are put here in order to prevent circular importing
within the other files.

@author: Donald Erb
Created on Wed Jul 15 14:26:59 2020

"""


import pandas as pd
import PySimpleGUI as sg


#the button color for buttons that proceed to the next window.
PROCEED_COLOR = ('white', '#00A949')
                 

class WindowCloseError(Exception):
    """Custom exception to allow exiting a GUI window to stop the program."""


def safely_close_window(window):
    """
    Closes a PySimpleGUI window and removes the window and its layout.

    Used when exiting a window early by manually closing the window. Ensures
    that the window is properly garbage collected, and then raises a
    WindowCloseError exception, which can be used to determine that the window
    was manually closed.

    Parameters
    ----------
    window : sg.Window
        The window that was closed.
        
    Raises
    ------
    WindowCloseError
        Custom exception to notify that the window has been closed earlier
        than expected.

    """

    window.close()
    del window

    raise WindowCloseError


def string_to_unicode(input_list):
    """
    Takes a list of strings and replaces the '\\(you)' in the strings with '\(you)', where (you) is u'.

    Necessary because the user input from PySimpleGui's InputText element
    will convert any '\' input by the user to '\\', which will not
    be converted to the desired unicode. If the string already has unicode
    characters, it will be left alone.

    Parameters
    ----------
    input_list : (list, tuple) or str
        A container of strings or a single string.

    Returns
    -------
    new_list : (list, tuple) or str
        A container of strings or a single string, depending on the input,
        with the unicode correctly converted.

    """

    if isinstance(input_list, str):
        input_list = [input_list]
        return_list = False
    else:
        return_list = True

    new_list = [[] for i in range(len(input_list))]

    for i, entry in enumerate(input_list):
        if '\\u' in entry:
            #replace "\\\\u" with "\\u" in case user used \\ instead of \
            new_list[i] = entry.replace('\\\\u', '\\u').encode('utf-8').decode('unicode_escape')
        else:
            new_list[i] = entry

    if return_list:
        return new_list
    else:
        return new_list[0]


def validate_inputs(window_values, integers=None, floats=None, strings=None,
                    user_inputs=None):
    """
    Validates entries from a PySimpleGUI window.

    Parameters
    ----------
    window_values : dict
        A dictionary of values from a PySimpleGUI window, generated by using
        window.read().
    integers : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary, whose values should
        be integers.
    floats : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary, whose values should
        be floats.
    strings : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary, whose values should
        be non-empty strings.
    user_inputs : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary, whose values should
        be a certain datatype; the values are first determined by
        separating each value using ',' (maybe later add the separator
        as an additional input).

    Returns
    -------
    bool
        True if all data in the window_values dictionary is correct.
        False if there is any error with the values in the window_values dictionary.

    Notes
    -----
    Inputs for integers, floats, and strings are [[key, display text],].
    For example: [['peak_width', 'peak width']].
    
    Inputs for user_inputs are [[key, display text, data type],].
    For example: [['peak_width', 'peak_width', float]].

    The display text will be the text that is shown to the user if the value
    of window_values[key] is not the correct data type.

    """

    if integers is not None:
        integers = integers if isinstance(integers, (list, tuple)) else [integers]
        for entry in integers:
            try:
                int(window_values[entry[0]])
            except:
                sg.Popup(f'Need to enter integer in "{entry[1]}".\n', title='Error')
                return False

    if floats is not None:
        floats = floats if isinstance(floats, (list, tuple)) else [floats]
        for entry in floats:
            if entry == 'inf':
                continue
            elif entry == '-inf':
                continue
            else:
                try:
                    float(window_values[entry[0]])
                except:
                    sg.Popup(f'Need to enter number in "{entry[1]}".\n', title='Error')
                    return False

    if strings is not None:
        strings = strings if isinstance(strings, (list, tuple)) else [strings]
        for entry in strings:
            try:
                if not window_values[entry[0]]:
                    raise ValueError
            except:
                sg.Popup(f'Need to enter information in "{entry[1]}".\n', title='Error')
                return False

    if user_inputs is not None:
        user_inputs = user_inputs if isinstance(user_inputs, (list, tuple)) else [user_inputs]
        for entry in user_inputs:
            try:
                inputs = [ent for ent in window_values[entry[0]].replace(' ', '').split(',') if ent]
                [entry[2](inpt) for inpt in inputs]

            except:
                sg.Popup(f'Need to correct entry for "{entry[1]}".\n', title='Error')
                return False

    return True


def show_dataframes(dataframes, title='Raw Data'):
    """
    Used to show data to help select the right columns or datasets from the data.

    Parameters
    ----------
    dataframes : list or pd.DataFrame
        Either (1) a pandas DataFrame, (2) a list of DataFrames, or (3) a list
        of lists of DataFrames. The layout of the window will depend on the
        input type.
    title : str, optional
        The title for the popup window.

    Returns
    -------
    window : sg.Window or None
        If no exceptions occur, a PySimpleGUI window will be returned; otherwise,
        None will be returned.

    """

    try:

        if isinstance(dataframes, pd.DataFrame):
            single_file = True
            dataframes = [[dataframes]]
        else:
            single_file = False

            if isinstance(dataframes[0], pd.DataFrame):
                single_dataset = True
                dataframes = [dataframes]
            else:
                single_dataset = False

        tabs = [[] for df_collection in dataframes]
        for i, df_collection in enumerate(dataframes):
            for j, dataframe in enumerate(df_collection):

                data = dataframe.values.tolist()
                if any(not isinstance(col, str) for col in dataframe.columns):
                    header_list = [f'Column {num}' for num in range(len(data[0]))]
                else:
                    header_list = dataframe.columns

                tabs[i] += [
                    sg.Table(values=data, headings=header_list, key=f'table_{i}{j}',
                             auto_size_columns=True, vertical_scroll_only=False,
                             num_rows=min(25, len(data)))
                ]

        if single_file:
            layout = [tabs[0]]
        else:
            datasets = []
            for i, tab_group in enumerate(tabs):
                datasets += [
                    [sg.Tab(f'Sample {j + 1}', [[table]],
                            key=f'set_{i}{j}') for j, table in enumerate(tab_group)]
                ]

            if single_dataset:
                layout = [
                    [sg.TabGroup([datasets[0]],
                                 tab_background_color=sg.theme_background_color())]
                ]

            else:
                tab_groups = []
                for i, tab_group in enumerate(datasets):
                    tab_groups += [
                        [sg.Tab(f'Dataset {i + 1}',
                                [[sg.TabGroup([tab_group],
                                              tab_background_color=sg.theme_background_color())]])]
                    ]
                layout = [[sg.TabGroup(tab_groups,
                                       tab_background_color=sg.theme_background_color())]]

        window = sg.Window(title, layout, resizable=True)

    except Exception as e:
        sg.Popup('Error reading file:\n    ' + repr(e) + '\n', title='Error')
        window = None

    finally:
        return window


def optimize_memory(dataframe):
    """
    Optimizes dataframe memory usage by converting data types.
    
    Optimizes object dtypes by trying to convert to other dtypes.
    Optimizes numerical dtypes by downcasting to the most appropriate dtype.
    
    All changes are done inplace, so no new dataframe is created.
    
    Parameters
    ----------
    dataframe : pd.DataFrame
        The dataframe to optimize.
    
    """

    df = dataframe.copy()
    #attempts to convert object columns to other dtypes
    objects = dataframe.select_dtypes(['object'])
    if len(objects.columns) > 0:
        df[objects.columns] = objects.convert_dtypes(convert_integer=False)

    ints = dataframe.select_dtypes(include=['int'])
    if len(ints.columns) > 0:
        df[ints.columns] = ints.apply(pd.to_numeric, downcast='integer',
                                      errors='ignore')

    floats = dataframe.select_dtypes(include=['float'])
    if len(floats.columns) > 0:
        df[floats.columns] = floats.apply(pd.to_numeric, downcast='float',
                                          errors='ignore')
        
    return df


def raw_data_import(window_values, file, show_popup=True):
    """
    Used to import data from the specified file into pandas DataFrames.
    
    Also used to show how data will look after using certain import values.

    Parameters
    ----------
    window_values : dict
        A dictionary with keys 'row_start', 'row_end', columns', 'separator',
        and optionally 'sheet'
    file : str:
        A string containing the path to the file to be imported.
    show_popup : bool
        If True, will display a popup window showing a table of the data.

    Returns
    -------
    dataframes : list
        A list of dataframes containing the data after importing.

    Notes
    -----
    Optimizes the memory usage of the imported data before returning.

    """

    try:
        row_start = int(window_values['row_start'])
        row_end = int(window_values['row_end'])
        separator = window_values['separator'] if window_values['separator'] != '' else None
        column_numbers = [
            int(i) for i in window_values['columns'].replace(' ', '').split(',') if i != ''
        ]

        if file.endswith('.xlsx'):

            first_col = int(window_values['first_col'].split(' ')[-1])
            last_col = int(window_values['last_col'].split(' ')[-1]) + 1
            columns = [num for num in range(first_col, last_col)]
            repeat_unit = int(window_values['repeat_unit'])

            total_dataframe = pd.read_excel(
                file, window_values['sheet'], None, skiprows=row_start,
                skipfooter=row_end, usecols=columns
            )

            column_indices = [num + first_col for num in column_numbers]

            dataframes = []
            for num in range(max(1, len(total_dataframe.columns) // repeat_unit)):
                indices = [(num * repeat_unit) + elem for elem in column_indices]
                dataframe = total_dataframe[indices]
                dataframe.columns = [*range(len(dataframe.columns))]
                dataframes.append(dataframe)

        else:
            dataframes = [
                pd.read_csv(
                    file, skiprows=row_start, skipfooter=row_end, header=None,
                    sep=separator, usecols=column_numbers, engine='python'
                )
            ]

        for i, dataframe in enumerate(dataframes):
            dataframes[i] = optimize_memory(dataframe)

        if show_popup:

            window_1_open = False
            if file.endswith('.xlsx') and len(dataframes) > 1:
                window_1_open = True
                window_1 = show_dataframes(total_dataframe, 'Total Raw Data')
                window_0 = show_dataframes(dataframes, 'Imported Datasets')
            else:
                window_0 = show_dataframes(dataframes[0], 'Imported Dataset')

            if window_0:
                window_0_open = True
                while window_0_open or window_1_open:

                    if window_1_open:
                        event_1 = window_1.Read(100)[0]
                        if event_1 == sg.WIN_CLOSED:
                            window_1.close()
                            window_1_open = False

                    event = window_0.Read(100)[0]
                    if event == sg.WIN_CLOSED:
                        window_0.close()
                        window_0_open = False

            del window_0
            if file.endswith('.xlsx') and len(dataframes) > 1:
                del window_1

        return dataframes

    except Exception as e:
        sg.Popup('Error reading file:\n    ' + repr(e) + '\n', title='Error')


def select_file_gui(data_source=None, file=None):
    """
    GUI to select a file and input the necessary options to import its data.

    Parameters
    ----------
    data_source : DataSource
        The DataSource object used for opening the file.
    file: str
        A string containing the path to the file to be imported.

    Returns
    -------
    values : dict
        A dictionary containing the items necessary for importing data.
    """

    #TODO put all of these default variables into a single dictionary
    if data_source is not None:
        default_row_start = data_source.start_row
        default_row_end = data_source.end_row
        default_separator = data_source.separator if data_source.separator is not None else ''
        default_columns = ', '.join([str(elem) for elem in data_source.column_numbers])
        default_indices = data_source.column_numbers
        default_x_index = data_source.x_index
        default_y_index = data_source.y_index

    else:
        default_row_start = 0
        default_row_end = 0
        default_separator = ''
        default_columns = '0, 1'

    if file is None:
        disable_excel = True
        disable_other = True
        disable_bottom = True
        default_sheets = []
        default_sheet = ''
        default_column_list = []
        default_first_col = ''
        default_last_col = ''
        default_repeat_unit = ''
        initial_separator = ''
        initial_columns = ''
        initial_row_start = ''
        initial_row_end = ''
        initial_indices = []
        initial_x_index = ''
        initial_y_index = ''

    else:
        disable_bottom = False

        if file.endswith('.xlsx'):
            disable_excel = False
            disable_other = True

            dataframes = pd.read_excel(file, None, None)
            sheet_names = [*dataframes.keys()]
            sheet_0_len = len(dataframes[sheet_names[0]].columns)

            default_sheets = [*dataframes.keys()]
            default_sheet = default_sheets[0]
            sheet_0_len = len(dataframes[default_sheet].columns)
            default_column_list = [f'Column {num}' for num in range(sheet_0_len)]
            default_first_col = default_column_list[0]
            default_last_col = default_column_list[-1]
            default_repeat_unit = sheet_0_len
            default_columns = ', '.join(str(num) for num in range(sheet_0_len))
            default_separator = ''
            default_row_start = 0
            default_row_end = 0
            default_indices = [num for num in range(sheet_0_len)]
            default_x_index = 0
            default_y_index = 1

        else:
            disable_excel = True
            disable_other = False
            default_sheets = []
            default_sheet = ''
            default_column_list = []
            default_first_col = ''
            default_last_col = ''
            default_repeat_unit = ''

        initial_separator = default_separator
        initial_columns = default_columns
        initial_row_start = default_row_start
        initial_row_end = default_row_end
        initial_indices = default_indices
        initial_x_index = default_indices[default_x_index]
        initial_y_index = default_indices[default_y_index]

    file_layout = [
        [sg.Text('Excel Workbook Options', relief='ridge', size=(38,1),
                 justification='center', pad=(0,(15, 10)))],
        [sg.Text('Sheet to use:'),
         sg.InputCombo(default_sheets, size=(17, 4), key='sheet',
                       default_value=default_sheet, disabled=disable_excel,
                       readonly=True, enable_events=True)],
        [sg.Text('First Column:'),
         sg.InputCombo(default_column_list, size=(17, 4),
                       key='first_col', readonly=True,
                       default_value=default_first_col,
                       disabled=disable_excel, enable_events=True)],
        [sg.Text('Last Column:'),
         sg.InputCombo(default_column_list, size=(17, 4), key='last_col',
                       readonly=True, default_value=default_last_col,
                       disabled=disable_excel, enable_events=True)],
        [sg.Text('Number of columns per dataset:'),
         sg.Input(key='repeat_unit', default_text=default_repeat_unit,
                  do_not_clear=True, disabled=disable_excel,
                  size=(3, 1), enable_events=True)],
        [sg.Text('Other Filetype Options', relief='ridge', size=(38 ,1),
                 justification='center', pad=(5,(25, 10)))],
        [sg.Text('Separator (eg. , or ;)', size=(20, 1)),
         sg.Input(key='separator', default_text=initial_separator,
                  disabled=disable_other, do_not_clear=True, size=(5, 1))],
        [sg.Text('=' * 34, pad=(5, (10, 10)))],
        [sg.Text('Enter data columns,\n separated by commas:',
                 tooltip='Starts at 0'),
         sg.Input(key='columns', default_text=initial_columns,
                  do_not_clear=True, tooltip='Starts at 0', size=(10, 1),
                  enable_events=True, disabled=disable_bottom)],
        [sg.Text('Start row:', tooltip='Starts at 0', size=(8, 1)),
         sg.Input(key='row_start', default_text=initial_row_start,
                  do_not_clear=True, size=(5, 1), disabled=disable_bottom,
                  tooltip='Starts at 0')],
        [sg.Text('End row: ', tooltip='Counts up from bottom. Starts at 0',
                 size=(8, 1)),
         sg.Input(key='row_end', default_text=initial_row_end,
                  do_not_clear=True, size=(5, 1), disabled=disable_bottom,
                  tooltip='Counts up from bottom. Starts at 0')]
    ]

    if file is None:
        file_layout.insert(0, 
            [sg.InputText('Choose a file', key='file', enable_events=True,
                          disabled=True, size=(28, 1), pad=(5, (10, 5))),
             sg.FileBrowse(key='file_browse', target='file', pad=(5, (10, 5)),
                           file_types=(("All Files", "*.*"),
                                       ("Excel Workbook", "*.xlsx"),
                                       ("CSV", "*.csv"),
                                       ("Text Files", "*.txt")))]
        )
    if data_source is not None: #TODO change this for when DataSource can have more than two unique variables
        file_layout.extend([
            [sg.Text('Column of x data:'),
             sg.InputCombo(initial_indices, default_value=initial_x_index,
                           key='x_index', readonly=True, size=(3, 1),
                           disabled=disable_bottom)],
            [sg.Text('Column of y data:'),
             sg.InputCombo(initial_indices, default_value=initial_y_index,
                           key='y_index', readonly=True, size=(3, 1),
                           disabled=disable_bottom)]
        ])

    file_layout.extend([
        [sg.Button('Next', bind_return_key=True, pad=(5, (15, 5)),
                   button_color=PROCEED_COLOR),
         sg.Button('Test Import', pad=(5, (15, 5)))]
    ])

    window = sg.Window('Data Import', file_layout)
    #TODO add validations before trying importing
    while True:
        event, values = window.Read()

        if event == sg.WIN_CLOSED:
            safely_close_window(window)

        elif event == 'file':
            if values['file'] == 'Choose a file':
                continue

            elif values['file'].endswith('xlsx'):

                dataframes = pd.read_excel(values['file'], None, None)
                sheet_names = [*dataframes.keys()]
                sheet_0_len = len(dataframes[sheet_names[0]].columns)

                window['sheet'].Update(values=sheet_names, value=sheet_names[0],
                                       disabled=False)
                col_list = [f'Column {num}' for num in range(sheet_0_len)]
                window['first_col'].Update(values=col_list, value=col_list[0],
                                           disabled=False)
                window['last_col'].Update(values=col_list, value=col_list[-1],
                                          disabled=False)
                window['repeat_unit'].Update(value=sheet_0_len, disabled=False)
                window['separator'].Update(value='', disabled=True)
                window['columns'].Update(value=', '.join(str(num) for num in range(sheet_0_len)),
                                         disabled=False)
                window['row_start'].Update(value='0', disabled=False)
                window['row_end'].Update(value='0', disabled=False)
                if data_source is not None:
                    indices = [num for num in range(sheet_0_len)]
                    window['x_index'].Update(values=indices, set_to_index=0,
                                             disabled=False)
                    window['y_index'].Update(values=indices, set_to_index=1,
                                             disabled=False)

            else:
                window['sheet'].Update(values=[], value='', disabled=True)
                window['first_col'].Update(values=[], value='', disabled=True)
                window['last_col'].Update(values=[], value='', disabled=True)
                window['repeat_unit'].Update(value='', disabled=True)
                window['separator'].Update(value=default_separator, disabled=False)
                window['columns'].Update(value=default_columns, disabled=False)
                window['row_start'].Update(value=default_row_start, disabled=False)
                window['row_end'].Update(value=default_row_end, disabled=False)
                if data_source is not None:
                    window['x_index'].Update(values=default_indices,
                                             set_to_index=default_x_index,
                                             disabled=False)
                    window['y_index'].Update(values=default_indices,
                                             set_to_index=default_y_index,
                                             disabled=False)

        elif event == 'sheet':
            dataframe = dataframes[values['sheet']]
            window['repeat_unit'].Update(value=len(dataframe.columns))
            cols = [f'Column {num}' for num in range(len(dataframe.columns))]
            window['first_col'].Update(values=cols, value=cols[0])
            window['last_col'].Update(values=cols, value=cols[-1])
            window['columns'].Update(value=', '.join(str(i) for i in range(len(dataframe.columns))))
            if data_source is not None:
                indices = [num for num in range(len(dataframe.columns))]
                window['x_index'].Update(values=indices, set_to_index=0)
                window['y_index'].Update(values=indices, set_to_index=1)

        elif event in ('first_col', 'last_col'):
            first_col = int(values['first_col'].split(' ')[-1])
            last_col = int(values['last_col'].split(' ')[-1]) + 1

            if (last_col - first_col) < int(values['repeat_unit']):
                new_len = last_col - first_col
                window['repeat_unit'].Update(value=new_len)
                update_text = [num for num in range(new_len)]
                window['columns'].Update(value=', '.join(str(elem) for elem in update_text))
                if data_source is not None:
                    window['x_index'].Update(values=update_text, set_to_index=0)
                    window['y_index'].Update(values=update_text, set_to_index=1)

        elif event == 'repeat_unit':
            try:
                if values['repeat_unit'] != '':
                    update_text = [num for num in range(int(values['repeat_unit']))]
                    window['columns'].Update(value=', '.join(str(elem) for elem in update_text))
                    if data_source is not None:
                        window['x_index'].Update(values=update_text, set_to_index=0)
                        window['y_index'].Update(values=update_text, set_to_index=1)
            except:
                sg.Popup('Please enter an integer in "number of columns per dataset"',
                         title='Error')

        elif event == 'columns':
            if data_source is not None:
                update_text = [entry for entry in values['columns'].replace(' ', '').split(',') if entry]
                window['x_index'].Update(values=update_text, set_to_index=0)
                window['y_index'].Update(values=update_text, set_to_index=1)

        elif event == 'Test Import':
            test_file = file if file is not None else values['file']
            raw_data_import(values, test_file)

        elif event == 'Next':
            if (file is None) and (values['file'] == 'Choose a file'):
                sg.Popup('Please choose a file', title='Error')
                continue
            integers = [['row_start', 'start row'], ['row_end', 'end row']]
            user_inputs = [['columns', 'data columns', int]]
            import_file = file if file is not None else values['file']

            if import_file.endswith('xlsx'):
                integers.append(['repeat_unit', 'number of columns per dataset'])

            close = validate_inputs(values, integers, None, None, user_inputs)
            if close:
                break

    window.close()
    del window

    return values
