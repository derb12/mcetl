# -*- coding: utf-8 -*-
"""Provides GUIs to import data depending on the data source used, process and/or fit the data, and save everything to Excel

@author: Donald Erb
Created on Tue May 5 17:08:53 2020

"""

import os #eventually replace os with pathlib
from pathlib import Path
import json
import time
import itertools
import string
import traceback
import pandas as pd
import numpy as np
import xlwings as xw
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from file_organizer import file_finder, file_mover
from utils import (safely_close_window, WindowCloseError,
                   string_to_unicode, validate_inputs, show_dataframes, PROCEED_COLOR)
import peak_fitting_gui


#the path where this program is located
_HERE = Path(__file__).parent.resolve()


#TODO make self.formats = {'even_num_col: {}, ...} for DataSource for xlsxwriter formats
#keys would be 'even_num_col', 'odd_subheader', etc
#would already have defaults. Then update from user input dictionaries
class DataSource(object):
    """Used to give default settings for importing data and various functions based on the source.

    Attributes
    ----------
    name : string representation of the data source.
    column_names : a list of strings to use as default column headers
    function_list : a list of strings that are associated with various
                    functions or features within this program.
    column_numbers : a list of integers corresponding to which columns in
                     the raw data file will be imported; starts at 0
    default_offset : the default number to offset the y values for each dataset;
                     only used if 'offset' is in the function_list
    start_row : an integer designating the first row in the raw data file
                to import data from; starts at 0
    end_row : an integer designating the last row in the raw data file to
              import data from; counts up from the bottom row of the raw
              data file (so the bottom row is end_row = 0)
    separator : a string designating the separator used in the raw data
                file; examples include ',', ';', '\\t' (tab)
    x_index : the column in the data after importing which corresponds to
              the independant variable
    y_index : the column in the data after importing which corresponds to
              the dependant variable
    x_plot_index : the column in the data after doing calculations which
                   will be used for plotting on the x axis
    y_plot_index : the column in the data after doing calculations which
                   will be used for plotting on the y axis
    file_type : the file extension (csv, txt, etc...) of the raw data files

    """

    def __init__(self, name, column_names=None, function_list=None,
                 column_numbers=None, default_offset=0, start_row=0,
                 end_row=0, separator=None, xy_indices=None,
                 xy_plot_indices=None, file_type=None, num_files=1,
                 blank_columns=0):
        """
        Parameters
        ----------
        name : the string representation of the data source, eg. XRD, FTIR
        column_names : a list of strings to use as default column headers
        function_list : a list of strings that are associated with various
                        functions or features within this program. Currently
                        supported functions include:
                            'offset' : adds an offset to the y values of the
                                       raw data
                            'normalize' : will normalize the y data between
                                          0 and 1; allows selection of 'Normalize'
                                          in the data sources window
                            'derivative' : will compute d(y)/d(x) using central
                                           difference formula where the derivative
                                           at point i is equal to
                                           (y[i+1] – y[i-1]) / (x[i+1] – x[i-1])
                            'negative_derivative' : will compute -d(y)/d(x) using
                                                    central difference formula
                            'max_x' : will only take data up to the maximum x
                                      value; to use when x increases
                                      and then decreases, like for TGA data
                            'fractional_change' : computes (yi – y0) / (yf – y0)
                                                  where y0 and yf are the initial
                                                  and final y values, respectively,
                                                  and yi is the y value at any point
                            'fit_peaks' : allows peak fitting

        column_numbers : a list of integers corresponding to which columns in
                         the raw data file will be imported; starts at 0
        default_offset : the default number to offset the y values for each dataset;
                         only used if 'offset' is in the function_list
        start_row : an integer designating the first row in the raw data file
                    to import data from; starts at 0
        end_row : an integer designating the last row in the raw data file to
                  import data from; counts up from the bottom row of the raw
                  data file (so the bottom row is end_row = 0)
        separator : a string designating the separator used in the raw data
                    file; examples include ',', ';', '\\t' (tab)
        xy_indices : a list of two integers designating which of the imported
                     data columns correspond to the x and y indices, which are
                     used for calculations from the function_list; for example,
                     [0, 1] would mean the first column is the x data and the
                     second column is the y data; the indices refer to the data
                     after importing, so even if the column_numbers used to
                     import from the raw data file were [1, 2], the xy_indices
                     would still start at 0 and the available columns would be 0
                     and 1.
        xy_plot_indices : a list of two integers designating which data columns
                          correspond to the x and y indices when plotting (or
                          for fitting data); similar rules as for xy_indices,
                          i.e. starts at 0 regardless of the column_numbers, but
                          the indices can be higher than the number of columns
                          imported; for example, if the imported data has columns
                          0 and 1 (x and y columns), and an offset calculation
                          is done on column 1, then the xy_plot_indices could be
                          [0, 2] to use the raw x data and the calculated offset y
                          data.
        file_type : the file extension (csv, txt, etc...) of the raw data files
        num_files : int, optional
            The number of files that should be found for each search term.

        """

        column_numbers = column_numbers if column_numbers is not None else [0, 1]
        xy_indices = xy_indices if xy_indices is not None else [0, 1]
        xy_plot_indices = xy_plot_indices if xy_plot_indices is not None else [0, 1]

        self.name = name
        self.column_numbers = column_numbers
        self.column_names = column_names if column_names is not None else ['']*len(column_numbers)
        self.default_offset = default_offset
        self.start_row = start_row
        self.end_row = end_row
        self.separator = separator
        self.normalize = False
        self.file_type = file_type
        self.num_files = num_files
        self.blank_columns = blank_columns

        supported_functions = ('offset', 'normalize', 'derivative',
                               'negative_derivative', 'fit_peaks', 'max_x',
                               'fractional_change')
        #calc_functions are functions that add a calculation column to the data
        calc_functions = ('offset', 'derivative', 'negative_derivative',
                          'fractional_change')

        if function_list is None:
            function_list = []
        elif isinstance(function_list, str):
            function_list = [function_list]
        self.function_list = []
        for function in function_list:
            if function in supported_functions:
                self.function_list.append(function)
            else:
                print(f'Warning: "{function}" is not currently in the list of supported functions.')

        if 'normalize' in function_list and 'offset' not in function_list:
            self.function_list.append('offset')
            self.default_offset = 0

        #ensures there are enough columns for a calculation
        func_cols = len([func for func in self.function_list if func in calc_functions])
        needed_cols = len(self.column_numbers) + func_cols
        if len(self.column_names) < needed_cols:
            filler = [''] * (needed_cols - len(self.column_names))
            self.column_names.extend(filler)
        else:
            self.column_names = self.column_names[0:needed_cols]

        #x and y indices for data processing
        if isinstance(xy_indices, (list, tuple)) and len(xy_indices) >= 2:
            self.x_index = xy_indices[0]
            self.y_index = xy_indices[-1]
        else:
            self.x_index = 0
            self.y_index = 1

        #x and y indices for plotting
        if isinstance(xy_plot_indices, (list, tuple)) and len(xy_plot_indices) >= 2:
            self.x_plot_index = xy_plot_indices[0]
            self.y_plot_index = xy_plot_indices[-1]
        else:
            self.x_plot_index = 0
            self.y_plot_index = 1
            

#TODO split this up; first process excel_formulas, then generate_excel(if saving), then process python_formulas
#pass the entire df list into process excel_formulas, with each formula returning a dataframe
def generate_excel(input_dataframes, sample_names, data_source, subheader_names,
                   excel_writer, sheet_name=None, plot_excel=False, plot_options=None,
                   save_excel=True):
    """Creates an Excel sheet from data within a list of dataframes

    Parameters
    ----------
    input_dataframes : a list of dataframes containing raw data
    sample_names : a list of sample names, one for each dataset in the dataframe
    data_source : the DataSource object
    subheader_names : a list of subheader names that will repeat for each dataset,
                      typically the x and y data titles
    excel_writer : the pandas ExcelWriter object that contains all of the
                   information about the Excel file being created
    sheet_name a string for the Excel sheet name
    plot_excel : if True, will create a simple plot in Excel using the data_source's
                 x_plot_index and y_plot_index
    plot_options : a dictionary of options used to create the Excel plot if plot_excel is True
    save_excel : the data will not be written to the excel_writer object if save_excel
                 is False; just saves a little time.

    Returns
    -------
    dataFrame : the output dataframe containing all of the data within the list of
                input_dataframes, as well as any applied calculations.
    """

    #generator that goes from 'A' to 'ZZ' following Excel's naming format.
    excel_columns = itertools.chain(
        string.ascii_uppercase,
        (''.join(pair) for pair in itertools.product(string.ascii_uppercase, repeat=2))
    )

    x_index = data_source.x_index

    #Writes raw data and formulas to the pandas dataframe
    for i, temp_df in enumerate(input_dataframes):

        column_headers = [f'{name}_{i}' for name in subheader_names]
        #ensures that all column headers are unique for each dataset
        for j, header in enumerate(column_headers):
            num = 0
            if header in column_headers[j+1:]:
                for k, elem in enumerate(column_headers[j+1:]):
                    if header == elem:
                        column_headers[j+1+k] = f'{header}_{num}'
                        num += 1

        temp_df.columns = column_headers[0:len(temp_df.columns)]

        #cuts out all data after the maximum x value
        if 'max_x' in data_source.function_list:
            end_index = temp_df[column_headers[x_index]].idxmax()
            temp_df = temp_df[:end_index+1]

        #TODO how to make this okay if temp_df gets split into multiple entries? Base it on len(temp_df.columns)?
        col_names = [next(excel_columns) for j in range(len(subheader_names))]

        #Writes the formulas as strings to be calculated in Excel, based on
        #the input data source
        #TODO pass the dataframe itself, in case formula cannot be done using strings
        calc_list = excel_formulas(data_source, col_names,
                                   temp_df[column_headers[x_index]].count(), offset[i])

        index = len(data_source.column_numbers)
        for calc in calc_list:
            temp_df[column_headers[index]] = calc
            index += 1

        #fills the rest of the dataframe with blank series to create columns
        if len(temp_df.columns) < len(subheader_names):
            for num in range(len(subheader_names) - len(temp_df.columns)):
                temp_df[f'blank_{i}_{num}'] = pd.Series()

    dataFrame = pd.concat(input_dataframes, axis=1)

    if save_excel:
        
        excel_book = excel_writer.book
        
        if len(excel_book.formats) == 2: # a new writer object
            #Formatting styles for the Excel workbook
            odd_header_format = excel_book.add_format({
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
                'bg_color':'DBEDFF', 'font_size':12, 'bottom': True
            })
            even_header_format = excel_book.add_format({
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
                'bg_color':'FFEAD6', 'font_size':12, 'bottom': True
            })
            odd_colnum_format = excel_book.add_format({
                'num_format': '0.00', 'bg_color':'DBEDFF', 'text_v_align': 2,
                'text_h_align': 2
            })
            even_colnum_format = excel_book.add_format({
                'num_format': '0.00', 'bg_color':'FFEAD6', 'text_v_align': 2,
                'text_h_align': 2
            })
        else:
            odd_header_format, even_header_format, odd_colnum_format, even_colnum_format = excel_book.formats[2:6]
        
        #Ensures that the sheet name is unique so it does not overwrite data
        num = 1
        if sheet_name is not None:
            sheet_base = sheet_name
        else:
            sheet_base = 'Sheet'
            sheet_name = 'Sheet_1'
        while True:
            close_loop = True
            for sheet in excel_writer.sheets:
                if sheet_name.lower() == sheet.lower():
                    num += 1
                    close_loop = False
                    sheet_name = f'{sheet_base}_{num}'
                    break
            if close_loop:
                break
        #TODO look at using pandas Styler to set style, would be independent of
        #excelwriting engine, but seems a lot slower...?
        #write to excel as: dataFrame.style.set_properties(**{properties}).to_excel(writer, sheetname, index, etc...)
        dataFrame.to_excel(excel_writer, sheet_name=sheet_name, index=False,
                           startrow=2, header=False)
        worksheet = excel_writer.sheets[sheet_name]

        #Modifies the formatting to look good in Excel
        for i in range(len(input_dataframes)):
            if i % 2 == 0:
                formats = [even_header_format, even_colnum_format]
            else:
                formats = [odd_header_format, odd_colnum_format]
            worksheet.merge_range(
                0, i * len(subheader_names), 0, (i+1) * len(subheader_names) - 1,
                sample_names[i], formats[0]
            )
            for j, subheader_name in enumerate(subheader_names):
                worksheet.write(
                    1, i * len(subheader_names) + j, subheader_name, formats[0]
                )
            worksheet.set_column(
                i * len(subheader_names), (i + 1) * len(subheader_names) - 1,
                12.5, formats[1]
            )

        #changes row height in Excel
        worksheet.set_row(0, 18)
        worksheet.set_row(1, 44)

        if plot_excel:

            x_col = plot_options['x_plot_index']
            y_col = plot_options['y_plot_index']
            x_min = float(plot_options['x_min']) if plot_options['x_min'] else None
            x_max = float(plot_options['x_max']) if plot_options['x_max'] else None
            y_min = float(plot_options['y_min']) if plot_options['y_min'] else None
            y_max = float(plot_options['y_max']) if plot_options['y_max'] else None
            x_reverse = False
            y_reverse = False
            
            #reverses x or y axes if min > max
            if None not in (x_min, x_max) and x_min > x_max:
                x_reverse = True
                x_min, x_max = x_max, x_min
            
            if None not in (y_min, y_max) and y_min > y_max:
                y_reverse = True
                y_min, y_max = y_max, y_min
                    
            x_crossing = 'max' if x_reverse else None
            y_crossing = 'max' if y_reverse else None

            chart = excel_book.add_chart({'type': 'scatter',
                                          'subtype':'straight'})

            for i in range(len(input_dataframes)):
                df_xcol = dataFrame.columns[i*len(subheader_names) + x_col]

                #categories is the x column and values is the y column
                chart.add_series({
                    'name': [sheet_name, 0, i*len(subheader_names)],
                    'categories':[sheet_name, 2, i*len(subheader_names) + x_col,
                                  dataFrame[df_xcol].count() + 1,
                                  i*len(subheader_names) + x_col],
                    'values':[sheet_name, 2, i*len(subheader_names) + y_col,
                              dataFrame[df_xcol].count() + 1,
                              i*len(subheader_names) + y_col],
                    'line': {'width':2}
                })
            chart.set_x_axis({
                'name': plot_options['x_label'],
                'min': x_min,
                'max': x_max,
                'reverse': x_reverse,
                'crossing': x_crossing
            })

            chart.set_y_axis({
                'name': plot_options['y_label'],
                'min': y_min,
                'max': y_max,
                'reverse': y_reverse,
                'crossing': y_crossing
            })
            worksheet.insert_chart('D8', chart)

    return dataFrame


def raw_data_import(window_values, file, show_popup=True):
    """Used to show how data will look after using certain import values.

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

    """

    try:
        row_start = int(window_values['row_start'])
        row_end = int(window_values['row_end'])
        separator = window_values['separator'] if window_values['separator'] != '' else None
        column_numbers = [int(i) for i in
                          window_values['columns'].replace(' ', '').split(',') if i != '']

        if file.endswith('.xlsx'):

            first_col = int(window_values['first_col'].split(' ')[-1])
            last_col = int(window_values['last_col'].split(' ')[-1]) + 1
            columns = [num for num in range(first_col, last_col)]
            repeat_unit = int(window_values['repeat_unit'])

            #NOTE: Reading the values from Excel formulas does not work if the
            #workbook has never been opened after creating using python
            total_dataframe = pd.read_excel(file, window_values['sheet'],
                                            None, skiprows=row_start,
                                            skipfooter=row_end)[columns]

            column_indices = [num + first_col for num in column_numbers]

            dataframes = []
            for num in range(max(1, len(total_dataframe.columns) // repeat_unit)):
                indices = [(num * repeat_unit) + elem for elem in column_indices]
                dataframe = total_dataframe[indices]
                dataframe.columns = [*range(len(dataframe.columns))]
                dataframes.append(dataframe)

        else:
            dataframes = [pd.read_csv(file, skiprows=row_start, skipfooter=row_end,
                                      sep=separator, usecols=column_numbers,
                                      engine='python', header=None)]

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


def select_file_gui(data_source=None, file=None, disable_blank_col=False):
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
        default_blank_col = data_source.blank_columns

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
                           disabled=disable_bottom)],
            [sg.Text('Number of empty columns\n to put between datasets:'),
             sg.Input(key='blank_cols', default_text=default_blank_col,
                      do_not_clear=True, size=(5, 1),
                      disabled=disable_blank_col)]
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
            if data_source is not None:
                integers.append(['blank_cols', 'number of empty columns'])

            close = validate_inputs(values, integers, None, None, user_inputs)
            if close:
                break

    window.close()
    del window

    return values


def create_plot_python(dataframe, repeat_length, plot_options, sample_names):
    """Creates a plot from a dataframe with multiple datasets. Just a placeholder for now.
    """

    ##Use plot options instead of data_source.x_plot_index

    num_samples = int(len(dataframe.columns) / repeat_length)
    plt.figure()

    for i in range(num_samples):
        x_index = plot_options['x_plot_index'] + i * repeat_length
        y_index = plot_options['y_plot_index'] + i * repeat_length

        x_data = dataframe[dataframe.columns[x_index]].astype(float)
        y_data = dataframe[dataframe.columns[y_index]].astype(float)
        plt.plot(x_data, y_data, label=sample_names[i])
    plt.legend()
    plt.show(block=False)
    plt.pause(0.01)


#TODO split this up into multiple function; maybe allow going back?
def launch_main_gui(data_sources):
    """
    Goes through all of the windows to find files, process/plot/fit data, and save to Excel.

    Parameters
    ----------
    data_sources : list or tuple
        A container (list, tuple) of DataSource objects.

    Returns
    -------
    dataframes : list
        A list lists of dataframes, with each dataframe containing the data imported from a
        raw data file; will be None if the function fails before importing data.

    fit_results : list
        A nested list of lists of lmfit ModelResult objects, with each ModelResult
        pertaining to a single fitting, each list of ModelResults containing all of
        the fits for a single dataset, and east list of lists pertaining the data
        within one processed dataframe; will be None if fitting is not done,
        or only partially filled if the fitting process ends early.
        
    plot_results : list
        A list of lists, with one entry per dataset. Each interior list is composed
        of a matplotlib.Figure object and a dictionary of matplotlib.Axes objects.
        Will be None if plotting is not done, or only partially filled if the plotting
        process ends early.

    Notes
    -----
    The entire function is wrapped in a try-except-finally block. If the user exits the
    program early by exiting out of a GUI, a custom WindowCloseError exception is
    thrown, which is just passed, allowing the program is close without error.
    If other exceptions occur, their traceback is printed.

    """

    dataframes = None
    proc_dataframes = None
    fit_results = None

    try:
        if not isinstance(data_sources, (list, tuple)):
            data_sources = [data_sources]

        default_file_name = 'Choose a filename'
        if _HERE.joinpath('previous_search.json').exists():
            last_search_disabled = False
        else:
            last_search_disabled = True

        #Selection of check boxes
        options_layout = [
            [sg.Text('Data Source', relief='ridge', justification='center',
                     size=(40, 1))],
            [sg.Radio('Multiple Files', 'options_radio', default=True,
                      key='multiple_files', enable_events=True)],
            [sg.Checkbox('Use Previous Search', key='use_last_search',
                         default=False, disabled=last_search_disabled,
                         pad=((40, 0),(1, 0)))],
            [sg.Radio('Single File', 'options_radio', key='single_file',
                      enable_events=True)],
            [sg.Text('Select All Boxes That Apply', relief='ridge',
                     justification='center', size=(40, 1))],
            [sg.Checkbox('Fit Peaks', key='fit_peaks', default=False,
                         enable_events=True)],
            [sg.Checkbox('Plot in Python (not implemented)', key='plot_python',
                         default=False, enable_events=True)],
            [sg.Checkbox('Move File(s)', key='move_files', default=False)],
            [sg.Checkbox('Save Excel File', key='save_excel',
                         default=True, enable_events=True),
             sg.InputCombo(('Create new file', 'Append to existing file'),
                           key='append_file', readonly=True,
                           default_value='Append to existing file', size=(19, 1))],
            [sg.Checkbox('Plot data in Excel', key='plot_data_excel',
                         pad=((40, 0), (1, 0)))],
            [sg.Checkbox('Plot fit results in Excel', key='plot_fit_excel',
                         default=False, disabled=True, pad=((40, 0), (1, 0)))],
            [sg.InputText(default_file_name ,disabled=True, key='file_name',
                          text_color='black', size=(23, 1),
                          pad=((40, 0), (1, 0)), enable_events=True),
             sg.FileSaveAs(key='actual_file_name', target='file_name',
                           file_types=(("Excel Workbook (xlsx)", "*.xlsx"),))]
        ]

        #Selection of data source
        data_sources_radios = [
            [sg.Radio(f'{j + 1}) {source.name}', 'radio', key=f'{source.name}',
                      enable_events=True)] for j, source in enumerate(data_sources)
        ]
        
        data_sources_layout = [
            [sg.Text('Select Data Source:', size=(30, 1))],
            *data_sources_radios,
        ]

        layout = [
            [sg.TabGroup([
                [sg.Tab('Options', options_layout, key='tab1'),
                 sg.Tab('Data Sources', data_sources_layout, key='tab2')]
            ], tab_background_color=sg.theme_background_color(), key='tab')],
            [sg.Button('Next', bind_return_key=True, button_color=PROCEED_COLOR)]
        ]

        window = sg.Window('Main Menu', layout)

        while True:
            event, values = window.Read()

            if event == sg.WIN_CLOSED:
                safely_close_window(window)

            elif event == 'Next':
                if any((values['fit_peaks'], values['plot_python'],
                        values['save_excel'], values['move_files'])):
                    close_window = False
                    for source in data_sources:
                        if values[source.name]:
                            close_window = True
                            break
                    if close_window:
                        if values['save_excel']:
                            if values['file_name'] != 'Choose a filename':
                                break
                            else:
                                sg.Popup('Please select a filename for the output Excel file.',
                                         title='Error')
                        else:
                            break
                    else:
                        sg.Popup('Please select a data source.',
                                 title='Error')

                elif values['move_files']:
                    break

                else:
                    sg.Popup('Please select a data processing option.',
                             title='Error')

            if values['tab'] == 'tab1':
                if event == 'multiple_files':
                    if not last_search_disabled:
                        window['use_last_search'].Update(disabled=False)

                elif event == 'single_file':
                    window['use_last_search'].Update(value=False, disabled=True)

                elif event == 'fit_peaks':
                    if values['fit_peaks']:
                        if values['save_excel']:
                            window['plot_fit_excel'].Update(disabled=False)
                    else:
                        window['plot_fit_excel'].Update(value=False, disabled=True)

                elif event == 'save_excel':
                    if values['save_excel']:
                        window['append_file'].Update(visible=True)
                        window['plot_data_excel'].Update(disabled=False)
                        window['actual_file_name'].Update(disabled=False)
                        window['file_name'].Update(value=default_file_name)
                        if values['fit_peaks']:
                            window['plot_fit_excel'].Update(disabled=False)
                    else:
                        window['append_file'].Update(value='Append to existing file',
                                                     visible=False)
                        window['plot_data_excel'].Update(value=False, disabled=True)
                        window['plot_fit_excel'].Update(value=False, disabled=True)
                        window['actual_file_name'].Update(disabled=True)
                        default_file_name = values['file_name']
                        window['file_name'].Update(value='')

                elif event == 'file_name':
                    #TODO replace this with pathlib, and check endswith rather than using replace immediately
                    window['file_name'].Update(value=os.path.basename(values['file_name']).replace('.xlsx', ''))

        window.close()
        del window

        multiple_files = values['multiple_files']
        save_excel, plot_excel = [values['save_excel'], values['plot_data_excel']]
        plot_python = values['plot_python']
        use_last_search = values['use_last_search'] if 'use_last_search' in values else False
        move_files = values['move_files']
        append_excel_file = values['append_file'] == 'Append to existing file'
        fit_peaks = values['fit_peaks']
        plot_peaks = values['plot_fit_excel']

        if save_excel:

            if values['actual_file_name'].endswith('.xlsx'):
                excel_filename = values['actual_file_name']
            else:
                excel_filename = values['actual_file_name']+'.xlsx'

            if append_excel_file:

                if os.path.exists(excel_filename):
                    final_name = excel_filename
                    excel_filename = Path.cwd().joinpath('temporary_file_to_be_deleted.xlsx')
                else:
                    append_excel_file = False

        else:
            excel_filename = 'default.xlsx'

        #Specifying the selected data source
        data_source = None
        for source in data_sources:
            if values[source.name]:
                data_source = source
                break

        #TODO make everything work with the original output of file_finder, which
        #is a thrice nested list: [[[file1, file2]]] <- one main and secondary keywords, two num_files
        #Selection of raw data files
        if multiple_files:
            if use_last_search:
                with open(_HERE.joinpath('previous_search.json'), 'r') as old_search:
                    files = json.load(old_search)
            else:
                files = file_finder(file_type=data_source.file_type,
                                    num_files=data_source.num_files)

                #Saves the last search to a json file so it can be used again to bypass the search.
                with open(_HERE.joinpath('previous_search.json'), 'w') as output_file:
                    json.dump(files, output_file)

            if any((save_excel, fit_peaks, plot_python)):
                dataframes = [[] for file_list in files]
                import_vals_list = [[] for file_list in files] #TODO probably can get rid of import_vals_list once DataSource is updated

                if files[0][0][0].endswith('.xlsx'):
                    for i, file_list in enumerate(files):
                        for j, file in enumerate(file_list):
                            disable_blank_col = not (i == 0 and j == 0)
                            import_values = select_file_gui(data_source, file[0],
                                                            disable_blank_col)
                            dataframes[i].extend([*raw_data_import(import_values,
                                                                   file[0], False)])
                            import_vals_list[i].append(import_values)

                else:
                    import_values = select_file_gui(data_source, files[0][0][0])

                    for i, file_list in enumerate(files):
                        for file in file_list:
                            dataframes[i].extend([*raw_data_import(import_values,
                                                                   file[0], False)])
                            import_vals_list[i].append(import_values)

        else:
            import_values = select_file_gui(data_source)
            dataframes = [raw_data_import(import_values, import_values['file'],
                                          False)]
            files = [[[import_values['file']]]]
            import_vals_list = [[import_values]]

        if any((save_excel, fit_peaks, plot_python)):

            #Takes the maximum values of blank columns and column length to account
            #for the fact that the user could input different values when
            #importing from multiple Excel files.
            blank_cols_list = [int(iv['blank_cols']) for iv_list in import_vals_list
                               for iv in iv_list]
            max_col = max([len(df.columns) for df_list in dataframes for df in df_list])
            data_cols = [int(i) for i in range(max_col)]

            for index, value in enumerate(data_cols):
                if value == int(import_values['x_index']):
                    data_source.x_index = index
                elif value == int(import_values['y_index']):
                    data_source.y_index = index

            original_cols = len(data_source.column_numbers)
            data_source.column_numbers = data_cols
            extra_cols = len(dataframes[0][0].columns) - original_cols
            blank_cols = max(blank_cols_list)
            total_cols = (data_source.column_names[0:original_cols] + ['']*extra_cols +
                          data_source.column_names[original_cols:] + ['']*blank_cols)

            #Formatting for excel sheets
            sheet_names = []
            sample_names = []
            data_headers = [] #TODO rename data_headers to like column_headers
            plot_options = [] if (plot_python or plot_excel) else [None]*len(files)

            for i, dataframe_list in enumerate(dataframes):

                sample_names_inputs = [
                    [sg.Text(f'    Sample {j+1}:', size=(11, 1)),
                     sg.Input(key=f'sample_name_{j}', default_text='', do_not_clear=True,
                              size=(20, 1))]
                    for j in range(len(dataframe_list))
                ]

                if len(sample_names_inputs) > 4:
                    sample_names_inputs = [[sg.Column(sample_names_inputs, scrollable=True,
                                                      vertical_scroll_only=True,
                                                      size=(380, 150))]]
                else:
                    height = len(sample_names_inputs) * 35
                    sample_names_inputs = [[sg.Column(sample_names_inputs, scrollable=False,
                                                      vertical_scroll_only=True,
                                                      size=(404, height))]]

                default_headers = data_headers[-1] if data_headers else total_cols

                data_header_inputs = [[sg.Text(f'    Column {j}:', size=(11, 1)),
                                       sg.Input(key=f'data_header_{j}', default_text=default_headers[j],
                                                do_not_clear=True,
                                                size=(20, 1))] for j in range(len(total_cols))]
                if len(data_header_inputs) > 4:
                    data_header_inputs = [[sg.Column(data_header_inputs, scrollable=True,
                                                     vertical_scroll_only=True,
                                                     size=(380, 150))]]
                else:
                    height = len(data_header_inputs) * 35
                    data_header_inputs = [[sg.Column(data_header_inputs, scrollable=False,
                                                     vertical_scroll_only=True,
                                                     size=(404, height))]]
                if save_excel:
                    header = 'Sheet Name:'
                    header_visible = True
                else:
                    header = f'Dataset {i+1}'
                    header_visible = False

                excel_layout = [
                    [sg.Text(header),
                     sg.Input(key='sheet_name', default_text=f'Sheet {i+1}',
                              do_not_clear=True, size=(15, 1),
                              visible=header_visible)],
                    [sg.Frame('Sample names (eg. 10Ti-800, 20Ti-800)',
                              sample_names_inputs)],
                    [sg.Frame('Column headers (eg. Intensity (counts))',
                              data_header_inputs)],
                ]

                #Plotting options
                if (plot_excel or plot_python):

                    plot_keys = ['x_plot_index', 'y_plot_index', 'x_label', 'y_label',
                                 'x_min', 'x_max', 'y_min', 'y_max']

                    if plot_options:
                        default_x_index = plot_options[-1]['x_plot_index']
                        default_y_index = plot_options[-1]['y_plot_index']
                        default_x_min = plot_options[-1]['x_min']
                        default_x_max = plot_options[-1]['x_max']
                        default_y_min = plot_options[-1]['y_min']
                        default_y_max = plot_options[-1]['y_max']
                        default_x_label = plot_options[-1]['x_label']
                        default_y_label = plot_options[-1]['y_label']
                    else:
                        default_x_index = f'{data_source.x_plot_index}'
                        default_y_index = f'{data_source.y_plot_index}'
                        default_x_min = ''
                        default_x_max = ''
                        default_y_min = ''
                        default_y_max = ''
                        default_x_label = data_source.column_names[data_source.x_plot_index]
                        default_y_label = data_source.column_names[data_source.y_plot_index]

                    plot_layout = [
                        [sg.Text('Column of x data for plotting:'),
                         sg.InputCombo([f'{col}' for col in range(len(total_cols))],
                                       key='x_plot_index', readonly=True, size=(3, 1),
                                       default_value=default_x_index)],
                        [sg.Text('Column of y data for plotting:'),
                         sg.InputCombo([f'{col}' for col in range(len(total_cols))],
                                        key='y_plot_index', readonly=True, size=(3, 1),
                                        default_value=default_y_index)],
                        [sg.Text('X axis label:'),
                         sg.Input(key='x_label', default_text=default_x_label,
                                  do_not_clear=True, size=(20, 1))],
                        [sg.Text('Y axis label:'),
                         sg.Input(key='y_label', default_text=default_y_label,
                                  do_not_clear=True, size=(20, 1))],
                        [sg.Text("Min and max values to show on the plot \n"\
                                 "(Leave blank to use Excel's default):")],
                        [sg.Text('    X min:', size=(8, 1)),
                         sg.Input(key='x_min', default_text=default_x_min,
                                  do_not_clear=True, size=(5, 1))],
                        [sg.Text('    X max:', size=(8, 1)),
                         sg.Input(key='x_max', default_text=default_x_max,
                                  do_not_clear=True, size=(5, 1))],
                        [sg.Text('    Y min:', size=(8, 1)),
                         sg.Input(key='y_min', default_text=default_y_min,
                                  do_not_clear=True, size=(5, 1))],
                        [sg.Text('    Y max:', size=(8, 1)),
                         sg.Input(key='y_max', default_text=default_y_max,
                                  do_not_clear=True, size=(5, 1))]
                    ]

                    layout = [
                        [sg.TabGroup([
                            [sg.Tab('Formatting', excel_layout, key='tab1'),
                             sg.Tab('Excel Plot Options', plot_layout, key='tab2')]],
                            key='tab', tab_background_color=sg.theme_background_color())],
                        [sg.Button('Unicode Help'),
                         sg.Button('Next', bind_return_key=True,
                                   button_color=PROCEED_COLOR)]
                    ]

                else:
                    layout = [
                        *excel_layout,
                        [sg.Button('Unicode Help'),
                         sg.Button('Next', button_color=PROCEED_COLOR,
                                   bind_return_key=True)]
                    ]

                window = sg.Window('Data Labels', layout)

                while True:
                    event, values = window.Read()
                    if event == 'Unicode Help':
                        sg.Popup(
                            '"\\u00B2": \u00B2 \n"\\u03B8": \u03B8 \n"\\u00B0": \u00B0'\
                            '\nFor example, Acceleration (m/s\\u00B2) creates Acceleration (m/s\u00B2)',
                            title='Common Unicode'
                        )
                    elif event == sg.WIN_CLOSED:
                        safely_close_window(window)
                    elif event == 'Next':
                        break

                window.close()
                del window

                sheet_names.append(values['sheet_name'])
                data_headers.append([values[f'data_header_{j}'] for j in range(len(total_cols))])
                sample_names.append([values[f'sample_name_{j}']for j in range(len(dataframe_list))])

                if (plot_excel or plot_python):

                    plot_dict = {}
                    for entry in plot_keys:
                        plot_dict[entry] = values.pop(entry)
                    plot_options.append(plot_dict)

            #Converts any '\\' in the input strings to '\' to make the unicode work correctly
            sheet_names = string_to_unicode(sheet_names)
            data_headers = [string_to_unicode(input_list) for input_list in data_headers]
            sample_names = [string_to_unicode(input_list) for input_list in sample_names]
            for entry in plot_options:
                if entry is not None:
                    entry['x_label'] = string_to_unicode(entry['x_label'])
                    entry['y_label'] = string_to_unicode(entry['y_label'])
                    entry['x_plot_index'] = int(entry['x_plot_index'])
                    entry['y_plot_index'] = int(entry['y_plot_index'])
                    data_source.x_plot_index = entry['x_plot_index']
                    data_source.y_plot_index = entry['y_plot_index']

        #Collects each set of data into a single dataframe and applies formulas according
        #to the selected data source
        #proc_dataframes denotes processed dataframes
        proc_dataframes = []
        if any((save_excel, fit_peaks, plot_python)):
            writer = pd.ExcelWriter(excel_filename, engine='xlsxwriter')
            
            for i, df_list in enumerate(dataframes):
                df = generate_excel(
                    df_list, sample_names[i], data_source, data_headers[i], writer,
                    sheet_names[i], plot_excel, offsets[i], plot_options[i], save_excel
                )

                proc_dataframes.append(df)
                proc_dataframes[i] = python_formulas(df_list, proc_dataframes[i],
                                                     data_source, data_headers[i],
                                                     offsets[i])

        #renames dataframe columns if there are repeated terms,
        #since it causes issues for plotting and fitting
        if any((plot_python, fit_peaks)):

            for k, dataframe in enumerate(proc_dataframes):
                header_list = dataframe.columns.tolist()
                for i, header in enumerate(header_list):
                    num = 1
                    if header in header_list[i+1:]:
                        for j, elem in enumerate(header_list[i+1:]):
                            if header == elem:
                                header_list[i+1+j] = f'{header}_{num}'
                                num += 1
                proc_dataframes[k].columns = header_list

        #Handles plotting in python
        if plot_python: #TODO move this after peak fitting and saving to excel

            #allows an exception to occur during plotting while still moving
            #on to save the Excel file
            try:
                for i, dataframe in enumerate(proc_dataframes):
                    create_plot_python(dataframe, len(data_headers[i]),
                                       plot_options[i], sample_names[i])
            except WindowCloseError:
                print('\nPlotting manually ended early.\nMoving on with program.')

            except Exception:
                print('\nException occured during plotting:\n')
                print(traceback.format_exc())
                print('Moving on with program.')

            except KeyboardInterrupt:
                print('\nPlotting manually ended early.\nMoving on with program.')

        #Handles peak fitting
        fit_results = [[] for _ in range(len(proc_dataframes))]
        if fit_peaks:

            if 'fit_peaks' in data_source.function_list:

                #allows exiting from the peak fitting GUI early, if desired or because of
                #an exception, while still writing the data to Excel
                try:

                    default_inputs = {
                        'x_fit_index': data_source.x_plot_index,
                        'y_fit_index': data_source.y_plot_index,
                        'x_label': data_source.column_names[data_source.x_plot_index],
                        'y_label': data_source.column_names[data_source.y_plot_index],
                    }

                    for i, dataframe in enumerate(proc_dataframes):

                        peak_dfs = []
                        params_dfs = []
                        descriptors_dfs = []

                        for num in range(max(1, len(dataframe.columns) // len(total_cols))):

                            default_inputs['sample_name'] = f'{sample_names[i][num]}_fit'
                            indices = [num*len(total_cols), (1+num)*(len(total_cols))]
                            col_names = dataframe.columns[indices[0]:indices[1]]

                            fit_output = peak_fitting_gui.fit_dataframe(
                                dataframe[col_names], default_inputs)

                            fit_results[i].append(fit_output[0])
                            peak_dfs.append(fit_output[1])
                            params_dfs.append(fit_output[2])
                            descriptors_dfs.append(fit_output[3])
                            default_inputs = fit_output[4]

                            if save_excel:
                                peak_fitting_gui.fit_to_excel(
                                    peak_dfs[-1], params_dfs[-1], descriptors_dfs[-1],
                                    writer, default_inputs['sample_name'],
                                    plot_peaks
                                )

                except WindowCloseError:
                    print('\nPeak fitting manually ended early.\nMoving on with program.')

                except Exception:
                    print('\nException occured during peak fitting:\n')
                    print(traceback.format_exc())
                    print('Moving on with program.')

                except KeyboardInterrupt:
                    print('\nPeak fitting manually ended early.\nMoving on with program.')

            else:
                sg.Popup(f"Peak fitting is not allowed for {data_source.name}.\n\n"\
                         "If desired, please put 'fit_peaks' into \nthe function_list"\
                         f" for {data_source.name}.\n", title='Error')

        #Handles moving files
        if move_files:

            text_layout = [[sg.Text(f'Dataset {i+1}')] for i in range(len(files))]
            files_layout = [[sg.InputText('', key=f'folder_{i}', enable_events=True,
                                          disabled=True),
                             sg.FolderBrowse(target=f'folder_{i}',
                                             key=f'button_{i}')] for i in range(len(files))]
            tot_layout = [i for j in zip(text_layout, files_layout) for i in j]
            if len(files) > 2:
                column = sg.Column(tot_layout, scrollable=True,
                                   vertical_scroll_only=True, size=(600, 200))
            else:
                column = sg.Column(tot_layout, scrollable=False,
                                   vertical_scroll_only=True)
            layout = [
                      [sg.Text('Choose the folder(s) to move files to:', size=(30, 1))],
                      [sg.Frame('', [[column]])],
                      [sg.Button('Submit', bind_return_key=True,
                                 button_color=PROCEED_COLOR),
                       sg.Checkbox('All Same Folder', key='same_folder',
                                   enable_events=True, disabled=len(files) == 1)]
                     ]

            window = sg.Window('Move Files', layout)

            while True:
                event, values = window.Read()

                if event == sg.WIN_CLOSED:
                    safely_close_window(window)

                elif 'folder_' in event:
                    if values['same_folder']:
                        folder = values['folder_0']
                        for i in range(1, len(files)):
                            window[f'folder_{i}'].Update(value=folder)

                elif event == 'same_folder':
                    if values['same_folder']:
                        folder = values['folder_0']
                        for i in range(1, len(files)):
                            window[f'folder_{i}'].Update(value=folder)
                            window[f'button_{i}'].Update(disabled=True)
                    else:
                        for i in range(1, len(files)):
                            window[f'button_{i}'].Update(disabled=False)

                elif event == 'Submit':
                    close = True
                    for i in range(len(files)):
                        if values[f'folder_{i}'] == '':
                            close = False
                            sg.Popup('Please enter folders for all datasets',
                                     title='Error')
                            break
                    if close:
                        break

            window.close()
            del window

            if (values is not None) and (None not in values.values()):
                folders = [values[f'folder_{i}'] for i in range(len(files))]

                for i, file_list in enumerate(files):
                    #Will automatically rename files if there is already a file with
                    #the same name in the destination folder.
                    file_mover(file_list, new_folder=folders[i],
                               skip_same_files=False)

        #Handles saving the Excel file and transferring sheets if appending to an existing file
        if save_excel:

            tries = 0
            while True:
                if tries < 10:
                    try:
                        if os.path.exists(excel_filename):
                            #os.rename will throw an exception if the file is open
                            os.rename(excel_filename, excel_filename)
                        writer.save()

                        if append_excel_file:
                            print('\nSaved temporary file...')
                        else:
                            print('\nSaved Excel file.')
                        break

                    except PermissionError:
                        print('\nTrying to overwrite Excel file. Please close the file.')
                        tries += 1
                        time.sleep(6)
                else:
                    print('\nThe saving process took too long and was abandoned.')
                    break

            if append_excel_file and (tries < 10):
                if os.name == 'nt': #will only do this in Windows (os.name=='nt' for windows)
                    try:
                        #checks if the file is open; raises PermissionError if so
                        os.rename(final_name, final_name)

                        app = xw.App(visible=False)
                        app.screen_updating = False
                        workbook_1 = xw.Book(excel_filename)
                        workbook_2 = xw.Book(final_name)

                        close_file = True

                    except PermissionError:
                        app = xw.apps.active
                        app.screen_updating = False
                        workbook_1 = xw.Book(excel_filename)

                        #cycles through Excel instances
                        for open_app in xw.apps:
                            #cycles through open Excel workbooks to find the right file
                            for book in open_app.books:
                                if os.path.basename(final_name) == book.name:
                                    workbook_2 = book
                                    break

                        close_file = False

                    finally:
                        #use another try-except here because xlwings/win32com is error prone
                        try:
                            #creates a temporary sheet at the end of the workbook
                            #will put all copied worksheets before this sheet because
                            #using after does not work with Copy (creates new workbook rather than copying)
                            workbook_2.sheets.add('temp_sheet_unique_name',
                                                  after=workbook_2.sheets[-1])
                            temp_sheet = workbook_2.sheets[-1]
                            #copies all sheets from workbook_1 to workbook_2
                            for sheet in workbook_1.sheets:
                                sheet.api.Copy(Before=temp_sheet.api)

                            print('Appended Excel file and saved.')
                            workbook_1.close()
                            os.remove(excel_filename) #TODO Path(excel_filename).unlink(True)

                        except Exception as e:
                            print(repr(e))
                            print('\nAppending sheets potentially failed. Check the '\
                                  'Excel file, and potentially copy the sheets from '\
                                  f'"{excel_filename}" if it exists.')

                        finally:

                            for sheet in workbook_2.sheets:
                                if 'temp_sheet_unique_name' in sheet.name:
                                    sheet.delete()

                            app.screen_updating = True
                            workbook_2.app.screen_updating = True
                            workbook_2.save()

                            if close_file:
                                workbook_2.close()
                                app.kill()
                else:
                    print('\nAppending not supported for this os system. Please manually '\
                          f'copy the sheets from "{excel_filename}"')

    except WindowCloseError:
        pass

    except Exception:
        print(traceback.format_exc())

    except KeyboardInterrupt:
        pass

    finally:
        return dataframes, proc_dataframes, fit_results


if __name__ == '__main__':

    #Definitions for each data source
    xrd = DataSource(name='XRD', column_names=['2\u03B8 (\u00B0)',
                                    'Intensity (Counts)', 'Offset Intensity (a.u.)'],
                                    function_list=['offset', 'fit_peaks'],
                                    column_numbers=[1, 2],
                                    default_offset=1000, start_row=1, end_row=0,
                                    separator=',', xy_indices=[0, 1],
                                    xy_plot_indices=[0, 2], file_type='csv',
                                    num_files=1)
    ftir = DataSource('FTIR', ['Wavenumber (1/cm)','Absorbance (a.u.)',
                                     'Offset Absorbance (a.u.)'],
                                     ['offset', 'normalize', 'fit_peaks'], [0, 1],
                                     1, 0, 0, ',', [0, 1], [0, 2], 'csv')
    raman = DataSource('Raman', ['Raman Shift (1/cm)','Intensity (a.u.)',
                                      'Offset Intensity (a.u.)'],
                                      ['offset', 'normalize', 'fit_peaks'], [0, 1],
                                      1, 0, 0, '\\t', [0, 1], [0, 2], 'txt')
    tga = DataSource('TGA', ['Temperature (\u00B0C)', 'Time (min)',
                                    'Mass (%)', 'Mass Loss Rate (%/\u00B0C)',
                                    'Fraction Mass Lost'],
                                    ['negative_derivative', 'max_x', 'fit_peaks',
                                     'fractional_change'],
                                    [0, 1, 2], None, 34, 0, ';', [0, 2], [0, 2], 'txt')
    other = DataSource('Other')

    #Put all DataSource objects in this tuple in order to use them
    data_sources = (xrd, ftir, raman, tga, other)

    #call the main function with data_sources as the input
    dataframes, proc_dataframes, fit_results = launch_main_gui(data_sources)