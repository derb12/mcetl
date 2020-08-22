# -*- coding: utf-8 -*-
"""Provides GUIs to import data depending on the data source used, process and/or fit the data, and save everything to Excel

@author: Donald Erb
Created on Tue May 5 17:08:53 2020

"""

import os #eventually replace os with pathlib
from pathlib import Path
import json
import time
import traceback
import pandas as pd
import xlwings as xw
import PySimpleGUI as sg
from . import utils
from .file_organizer import file_finder, file_mover
from .datasource import DataSource
from .peak_fitting_gui import fit_dataframe, fit_to_excel
from .plotting_gui import configure_plots


#the path where this program is located
_HERE = Path(__file__).parent.resolve()


def generate_excel(dataframe, sample_names, data_source, subheader_names,
                   excel_writer, plot_options, sheet_name=None, plot_excel=False):
    """Creates an Excel sheet from data within a list of dataframes

    Parameters
    ----------
    dataframe : pd.DataFrame
        The dataframe containing all the raw data to put on one sheet in Excel.
    sample_names : list
        A list of sample names, one for each sample in the dataframe.
    data_source : DataSource
        The selected DataSource.
    subheader_names : list
        A list of subheader names that will repeat for each dataset,
        typically the x and y data titles.
    excel_writer : pd.ExcelWriter
        The pandas ExcelWriter object that contains all of the
        information about the Excel file being created.
    plot_options : dict
        A dictionary of options used to create the Excel plot if plot_excel is True.
    sheet_name: str, optional
        The Excel sheet name.
    plot_excel : bool, optional
        If True, will create a simple plot in Excel using the data_source's
        x_plot_index and y_plot_index.

    """

    excel_book = excel_writer.book
    first_row = data_source.excel_row_offset
    first_col = data_source.excel_column_offset
    
    if len(excel_book.formats) == 2: # a new writer object
        #Formatting styles for the Excel workbook
        for excel_format in data_source.excel_formats:
            excel_book.add_format(excel_format)
    
    (odd_header_format, even_header_format, odd_colnum_format,
     even_colnum_format) = excel_book.formats[2:6]
    
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
    dataframe.to_excel(
        excel_writer, sheet_name=sheet_name, index=False, startrow=2 + first_row,
        startcol=first_col, header=False
    )
    worksheet = excel_writer.sheets[sheet_name]

    #Modifies the formatting to look good in Excel
    for i in range(len(input_dataframes)):
        if i % 2 == 0:
            formats = [even_header_format, even_colnum_format]
        else:
            formats = [odd_header_format, odd_colnum_format]
        worksheet.merge_range(
            first_row, i * len(subheader_names), first_row, (i+1) * len(subheader_names) - 1,
            sample_names[i], formats[0]
        )
        for j, subheader_name in enumerate(subheader_names):
            worksheet.write(
                first_row + 1, i * len(subheader_names) + j, subheader_name, formats[0]
            )
        worksheet.set_column(
            i * len(subheader_names), (i + 1) * len(subheader_names) - 1,
            12.5, formats[1]
        )

    #changes row height in Excel
    worksheet.set_row(first_row, 18)
    worksheet.set_row(first_row + 1, 44)

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
            df_xcol = dataframe.columns[i*len(subheader_names) + x_col]

            #categories is the x column and values is the y column
            chart.add_series({
                'name': [sheet_name, first_row, i*len(subheader_names)],
                'categories':[
                    sheet_name, first_row + 2, i*len(subheader_names) + x_col,
                    dataframe[df_xcol].count() + 1, i*len(subheader_names) + x_col
                ],
                'values':[
                    sheet_name, first_row + 2, i*len(subheader_names) + y_col,
                    dataframe[df_xcol].count() + 1, i*len(subheader_names) + y_col
                ],
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
    fit_results = None
    plot_results = None

    try:
        if not isinstance(data_sources, (list, tuple)):
            data_sources = [data_sources]
        if any(not isinstance(data_source, DataSource) for data_source in data_sources):
            raise TypeError("Only DataSource objects can be used.")

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
            [sg.Button('Next', bind_return_key=True, button_color=utils.PROCEED_COLOR)]
        ]

        window = sg.Window('Main Menu', layout)

        while True:
            event, values = window.Read()

            if event == sg.WIN_CLOSED:
                utils.safely_close_window(window)

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
                                sg.popup('Please select a filename for the output Excel file.',
                                         title='Error')
                        else:
                            break
                    else:
                        sg.popup('Please select a data source.',
                                 title='Error')

                elif values['move_files']:
                    break

                else:
                    sg.popup('Please select a data processing option.',
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
                import_vals = [[] for file_list in files]

                if files[0][0][0].endswith('.xlsx'):
                    for i, file_list in enumerate(files):
                        for j, file in enumerate(file_list):
                            disable_blank_col = not (i == 0 and j == 0)
                            import_values = utils.select_file_gui(
                                data_source, file[0], disable_blank_col
                            )
                            dataframes[i].extend(
                                [*utils.raw_data_import(import_values, file[0], False)]
                            )
                            import_vals[i].append(import_values)

                else:
                    import_values = utils.select_file_gui(data_source, files[0][0][0])

                    for i, file_list in enumerate(files):
                        for file in file_list:
                            dataframes[i].extend(
                                [*utils.raw_data_import(import_values, file[0], False)]
                            )
                            import_vals[i].append(import_values)

        else:
            import_values = utils.select_file_gui(data_source)
            dataframes = [utils.raw_data_import(import_values, import_values['file'],
                                                False)]
            files = [[[import_values['file']]]]
            import_vals = [[import_values]]

        if any((save_excel, fit_peaks, plot_python)):

            #Takes the maximum values of blank columns and column length to account
            #for the fact that the user could input different values when
            #importing from multiple Excel files.
            blank_cols_list = [
                int(iv['blank_cols']) for iv_list in import_vals for iv in iv_list
            ]
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
                                   button_color=utils.PROCEED_COLOR)]
                    ]

                else:
                    layout = [
                        *excel_layout,
                        [sg.Button('Unicode Help'),
                         sg.Button('Next', button_color=utils.PROCEED_COLOR,
                                   bind_return_key=True)]
                    ]

                window = sg.Window('Data Labels', layout)

                while True:
                    event, values = window.Read()
                    if event == 'Unicode Help':
                        sg.popup(
                            '"\\u00B2": \u00B2 \n"\\u03B8": \u03B8 \n"\\u00B0": \u00B0'\
                            '\nFor example, Acceleration (m/s\\u00B2) creates Acceleration (m/s\u00B2)',
                            title='Common Unicode'
                        )
                    elif event == sg.WIN_CLOSED:
                        utils.safely_close_window(window)
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
            sheet_names = utils.string_to_unicode(sheet_names)
            data_headers = [
                utils.string_to_unicode(input_list) for input_list in data_headers
            ]
            sample_names = [
                utils.string_to_unicode(input_list) for input_list in sample_names
            ]
            for entry in plot_options:
                if entry is not None:
                    entry['x_label'] = utils.string_to_unicode(entry['x_label'])
                    entry['y_label'] = utils.string_to_unicode(entry['y_label'])
                    entry['x_plot_index'] = int(entry['x_plot_index'])
                    entry['y_plot_index'] = int(entry['y_plot_index'])
                    data_source.x_plot_index = entry['x_plot_index']
                    data_source.y_plot_index = entry['y_plot_index']

        #Collects each set of data into a single dataframe and applies formulas according
        #to the selected data source
        if any((save_excel, fit_peaks, plot_python)):
            writer = pd.ExcelWriter(excel_filename, engine='xlsxwriter')
            
            #perform separation calcs
            data_source.separate_data(dataframes, import_vals)
            #assign reference indices for all relevant columns
            data_source.set_references(dataframes, import_vals)
            
            #merge dfs for each dataset
            merged_dataframes = data_source.merge_datasets(dataframes)
            dataframes = None #frees up memory
            
            if save_excel: #and process_data
            
                data_source.do_excel_functions(merged_dataframes)
            
                for i, df_list in enumerate(merged_dataframes):
                    generate_excel(
                        df_list, sample_names[i], data_source, data_headers[i], writer,
                        sheet_names[i], plot_excel, plot_options[i], save_excel
                    )

            #if process_data:
            data_source.do_python_functions(merged_dataframes)
    
            #split data back into individual dataframes
            dataframes = data_source.split_into_measurements(merged_dataframes)
            del merged_dataframes
        
        """
        save this for later to put into the DataSource
        #renames dataframe columns if there are repeated terms,
        #since it causes issues for plotting and fitting
        if any((plot_python, fit_peaks)):

            for k, dataframe in enumerate(dataframes):
                header_list = dataframe.columns.tolist()
                for i, header in enumerate(header_list):
                    num = 1
                    if header in header_list[i+1:]:
                        for j, elem in enumerate(header_list[i+1:]):
                            if header == elem:
                                header_list[i+1+j] = f'{header}_{num}'
                                num += 1
                dataframes[k].columns = header_list
        """

        #Handles plotting in python
        if plot_python: #TODO move this after peak fitting and saving to excel

            #allows an exception to occur during plotting while still moving
            #on to save the Excel file
            try:
                configure_plots(dataframes, data_source.figure_kwargs)
            
            except utils.WindowCloseError:
                print('\nPlotting manually ended early.\nMoving on with program.')

            except Exception:
                print('\nException occured during plotting:\n')
                print(traceback.format_exc())
                print('Moving on with program.')

            except KeyboardInterrupt:
                print('\nPlotting manually ended early.\nMoving on with program.')

        #Handles peak fitting
        fit_results = [[[] for sample in dataset] for dataset in dataframes]
        if fit_peaks:

            #allows exiting from the peak fitting GUI early, if desired or because of
            #an exception, while still writing the data to Excel
            try:

                default_inputs = {
                    'x_fit_index': data_source.x_plot_index,
                    'y_fit_index': data_source.y_plot_index,
                    'x_label': data_source.column_names[data_source.x_plot_index],
                    'y_label': data_source.column_names[data_source.y_plot_index],
                }

                for i, dataset in enumerate(dataframes):
                    for j, sample in enumerate(dataset):
                        for measurement in sample:
            
                            default_inputs['sample_name'] = f'{sample_names[i]}_fit'
    
                            fit_output = fit_dataframe(measurement, default_inputs)
    
                            fit_results[i][j].append(fit_output[0])
                            peak_df = fit_output[1]
                            params_df = fit_output[2]
                            descriptors_df = fit_output[3]
                            default_inputs = fit_output[4]
    
                            if save_excel:
                                fit_to_excel(
                                    peak_df, params_df, descriptors_df,
                                    writer, default_inputs['sample_name'],
                                    plot_peaks
                                )

            except utils.WindowCloseError:
                print('\nPeak fitting manually ended early.\nMoving on with program.')

            except Exception:
                print('\nException occured during peak fitting:\n')
                print(traceback.format_exc())
                print('Moving on with program.')

            except KeyboardInterrupt:
                print('\nPeak fitting manually ended early.\nMoving on with program.')

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
                           button_color=utils.PROCEED_COLOR),
                 sg.Checkbox('All Same Folder', key='same_folder',
                             enable_events=True, disabled=len(files) == 1)]
            ]

            window = sg.Window('Move Files', layout)

            while True:
                event, values = window.Read()

                if event == sg.WIN_CLOSED:
                    utils.safely_close_window(window)

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
                            sg.popup('Please enter folders for all datasets',
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

    except utils.WindowCloseError:
        pass
    except Exception:
        print(traceback.format_exc())
    except KeyboardInterrupt:
        pass

    finally:
        return dataframes, fit_results, plot_results
