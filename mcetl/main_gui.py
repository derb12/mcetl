# -*- coding: utf-8 -*-
"""Provides GUIs to import data depending on the data source used, process and/or fit the data, and save everything to Excel

@author: Donald Erb
Created on Tue May 5 17:08:53 2020

"""


import itertools
import json
import os
from pathlib import Path
import traceback

import pandas as pd
import PySimpleGUI as sg
if os.name == 'nt':
    import xlwings as xw

from . import utils
from .file_organizer import file_finder, file_mover
from .datasource import DataSource
from .peak_fitting_gui import launch_peak_fitting_gui
from .plotting_gui import launch_plotting_gui


def _generate_excel(dataframe, sample_names, data_source, subheader_names,
                    excel_writer, plot_options, sheet_name, plot_excel):
    """
    Creates an Excel sheet from data within a list of dataframes.

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
    sheet_name: str
        The Excel sheet name.
    plot_excel : bool
        If True, will create a simple plot in Excel using the data_source's
        x_plot_index and y_plot_index.

    """

    excel_book = excel_writer.book
    first_row = data_source.excel_row_offset
    first_col = data_source.excel_column_offset

    (odd_header_format, even_header_format, odd_colnum_format,
     even_colnum_format) = excel_book.formats[2:6]

    # Ensures that the sheet name is unique so it does not overwrite data
    num = 1
    sheet_base = sheet_name
    while True:
        close_loop = True
        for sheet in excel_writer.sheets:
            if sheet_name.lower() == sheet.lower():
                sheet_name = f'{sheet_base}_{num}'
                num += 1
                close_loop = False
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

    # Modifies the formatting to look good in Excel
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

    # changes row height in Excel
    worksheet.set_row(first_row, 18)
    worksheet.set_row(first_row + 1, 44)

    if plot_excel:

        x_col = plot_options['x_plot_index']
        y_col = plot_options['y_plot_index']
        x_min = plot_options['x_min']
        x_max = plot_options['x_max']
        y_min = plot_options['y_min']
        y_max = plot_options['y_max']

        x_reverse = False
        y_reverse = False
        # reverses x or y axes if min > max
        if None not in (x_min, x_max) and x_min > x_max:
            x_reverse = True
            x_min, x_max = x_max, x_min

        if None not in (y_min, y_max) and y_min > y_max:
            y_reverse = True
            y_min, y_max = y_max, y_min

        x_crossing = 'max' if x_reverse else None
        y_crossing = 'max' if y_reverse else None

        chart = excel_book.add_chart(
            {'type': 'scatter', 'subtype':'straight'}
        )
        #TODO plot every measurement for each sample, but skip summary sections
        for i in range(len(input_dataframes)):
            df_xcol = dataframe.columns[i*len(subheader_names) + x_col]

            # categories is the x column and values is the y column
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


def _select_processing_options(data_sources):
    """
    Launches a window to select the processing options.

    Parameters
    ----------
    data_sources : list or tuple
        A container (list, tuple) of DataSource objects.

    Returns
    -------
    values : dict
        A dictionary containing the processing options.

    """

    if Path(__file__).parent.resolve().joinpath('previous_search.json').exists():
        last_search_disabled = False
    else:
        last_search_disabled = True

    #Selection of check boxes
    options_layout = [
        [sg.Text('Select Input', relief='ridge', justification='center',
                 size=(40, 1))],
        [sg.Radio('Multiple Files', 'options_radio', default=True,
                  key='multiple_files', enable_events=True)],
        [sg.Check('Use Previous Search', key='use_last_search',
                  disabled=last_search_disabled, pad=((40, 0),(1, 0)))],
        [sg.Radio('Single File', 'options_radio', key='single_file',
                  enable_events=True)],
        [sg.Text('Select All Boxes That Apply', relief='ridge',
                 justification='center', size=(40, 1))],
        [sg.Check('Process Data', key='process_data', default=True,
                  enable_events=True)],
        [sg.Check('Fit Peaks', key='fit_peaks', enable_events=True)],
        [sg.Check('Save to Excel', key='save_fitting', pad=((40, 0), (1, 0)),
                  enable_events=True, disabled=True)],
        [sg.Check('Plot in Python', key='plot_python')],
        [sg.Check('Move File(s)', key='move_files', default=False)],
        [sg.Check('Save Excel File', key='save_excel',
                  default=True, enable_events=True),
         sg.Combo(('Create new file', 'Append to existing file'),
                  key='append_file', readonly=True,
                  default_value='Append to existing file', size=(19, 1))],
        [sg.Check('Plot Data in Excel', key='plot_data_excel',
                  pad=((40, 0), (1, 0)))],
        [sg.Check('Plot Fit Results in Excel', key='plot_fit_excel',
                  disabled=True, pad=((40, 0), (1, 0)))],
        [sg.Input('', key='file_name', visible=False),
         sg.Input('', key='save_as', visible=False,
                  enable_events=True, do_not_clear=False),
         sg.SaveAs(file_types=(("Excel Workbook (xlsx)", "*.xlsx"),),
                   key='file_save_as', target='save_as',
                   pad=((40, 0), 5))],
    ]

    data_sources_radios = [
        [sg.Radio(f'{j + 1}) {source.name}', 'radio', key=f'source_{source.name}',
                  enable_events=True)] for j, source in enumerate(data_sources)
    ]

    layout = [
        [sg.TabGroup([
            [sg.Tab('Options', options_layout, key='tab1'),
             sg.Tab('Data Sources', [
                [sg.Text('Select Data Source:', relief='ridge',
                         justification='center', size=(40, 1))],
                *data_sources_radios,
             ], key='tab2')]
        ], tab_background_color=sg.theme_background_color(), key='tab')],
        [sg.Button('Next', bind_return_key=True,
                   button_color=utils.PROCEED_COLOR)]
    ]

    window = sg.Window('Main Menu', layout)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            utils.safely_close_window(window)

        elif event == 'Next':
            if any((values['fit_peaks'], values['plot_python'],
                    values['save_excel'], values['move_files'],
                    values['process_data'])):

                close_window = False
                for source in data_sources:
                    if values[f'source_{source.name}']:
                        close_window = True
                        break
                if close_window:
                    if not values['save_excel'] or values['file_name']:
                        break
                    else:
                        sg.popup(
                            'Please select a filename for the output Excel file.',
                            title='Error'
                        )
                else:
                    sg.popup('Please select a data source.',
                             title='Error')

            elif values['move_files']:
                break

            else:
                sg.popup('Please select a data processing option.',
                         title='Error')

        if event == 'multiple_files':
            if not last_search_disabled:
                window['use_last_search'].update(disabled=False)

        elif event == 'single_file':
            window['use_last_search'].update(value=False, disabled=True)

        elif event == 'fit_peaks':
            if values['fit_peaks'] and values['save_excel']:
                window['save_fitting'].update(value=True, disabled=False)
                window['plot_fit_excel'].update(disabled=False)
            else:
                window['save_fitting'].update(value=False, disabled=True)
                window['plot_fit_excel'].update(value=False, disabled=True)

        elif event == 'save_fitting':
            if values['save_fitting']:
                window['plot_fit_excel'].update(disabled=False)
            else:
                window['plot_fit_excel'].update(value=False, disabled=True)

        elif event == 'save_excel':
            if values['save_excel']:
                window['append_file'].update(readonly=True)
                window['plot_data_excel'].update(disabled=False)

                if values['fit_peaks']:
                    window['save_fitting'].update(value=True, disabled=False)
                    window['plot_fit_excel'].update(disabled=False)
            else:
                window['append_file'].update(
                    value='Append to existing file', disabled=True
                )
                window['plot_data_excel'].update(value=False, disabled=True)
                window['plot_fit_excel'].update(value=False, disabled=True)
                window['save_fitting'].update(value=False, disabled=True)

        elif event == 'save_as' and values['save_as']:
            file_path = Path(values['save_as'])
            file_extension = file_path.suffix.lower()
            if not file_extension or file_extension != '.xlsx':
                file_path = Path(file_path.parent, file_path.stem + '.xlsx')
            window['file_name'].update(value=str(file_path))

    window.close()
    del window

    values['append_file'] = values['append_file'] == 'Append to existing file'

    # removes unneeded keys
    for key in ('file_save_as', 'save_as', 'single_file', 'tab'):
        del values[key]

    return values


def _create_column_labels_window(
        dataset, data_source, processing_options, index,
        gui_inputs, location, last_index):
    """
    Creates the window to specify the sample and column labels.

    Parameters
    ----------
    dataset : list
        The list of lists of dataframes for one dataset.
    data_source : DataSource
        The DataSource object for the data.
    processing_options : dict
        The dictionary that contains information about which
        processing steps will be conducted.
    index : int
        The index of the dataset within the total list of datasets.
    gui_inputs : dict
        A dictionary of values to overwrite the default gui values, used
        when displaying a previous window.
    location : tuple
        The window location.
    last_index : bool
        If True, designates that it is the last index.

    Returns
    -------
    validations : dict
        A dictionary with the validations needed for the created window.
    sg.Window
        The created window to select the labels.

    """

    validations = {'user_inputs': []}
    default_inputs = {
        'x_plot_index': f'{data_source.x_plot_index}',
        'y_plot_index': f'{data_source.y_plot_index}',
        'x_min': '',
        'x_max': '',
        'y_min': '',
        'y_max': '',
        'x_label': data_source.column_labels[data_source.x_plot_index],
        'y_label': data_source.column_labels[data_source.y_plot_index]
    }

    for i in range(len(dataset)):
        default_inputs.update({f'sample_name_{i}': ''})
        validations['user_inputs'].append([
            f'sample_name_{i}', f'sample name {i + 1}',
            utils.string_to_unicode, True, None
        ])

    if processing_options['process_data'] and data_source.dataset_summary_functions:
        i += 1
        default_inputs.update({f'sample_name_{i}': 'Summary'})
        validations['user_inputs'].append([
            f'sample_name_{i}', f'sample name {i + 1}',
            utils.string_to_unicode, True, None
        ])

    labels = data_source.create_needed_labels(
        max(len(df.columns) for sample in dataset for df in sample)
    )

    keys = ('data_label', 'calculation_label',
            'sample_summary_label', 'dataset_summary_label')

    for i, label_list in enumerate(labels):
        default_inputs.update(
            {f'{keys[i]}_{j}': label for j, label in enumerate(label_list)}
        )

    default_inputs.update(gui_inputs)
    default_inputs.update({'sheet_name': f'Sheet {index + 1}'})

    if processing_options['save_excel']:
        header = 'Sheet Name: '
        header_visible = True
        validations['user_inputs'].append([
            'sheet_name', 'sheet name', utils.string_to_unicode, False, None
        ])
    else:
        header = f'Dataset {index + 1}'
        header_visible = False

    column_width = 32
    labels_layout = [
        [sg.Text(header, visible=header_visible),
         sg.Input(default_inputs['sheet_name'], key='sheet_name',
                  do_not_clear=True, size=(15, 1),
                  visible=header_visible)],
        [sg.Text('Sample Names', size=(column_width, 1),
                 justification='center', relief='ridge', pad=(5, 10))]
    ]

    for i in range(len(dataset)):
        labels_layout.append(
            [sg.Text(f'    Sample {i + 1}'),
             sg.Input(default_inputs[f'sample_name_{i}'] ,size=(20, 1),
                      key=f'sample_name_{i}', do_not_clear=True)]
        )

    if processing_options['process_data'] and data_source.dataset_summary_functions:
        i += 1
        labels_layout.append(
            [sg.Text(f'    Summary'),
             sg.Input(default_inputs[f'sample_name_{i}'] ,size=(20, 1),
                      key=f'sample_name_{i}', do_not_clear=True)]
        )

    labels_layout.extend([
        [sg.Text('Column Labels', size=(column_width, 1),
                 justification='center', relief='ridge', pad=(5, 10))],
        [sg.Text('Imported Data Labels:')]
    ])

    for i in range(len(labels[0])):
        validations['user_inputs'].append([
            f'{keys[0]}_{i}', f'raw data label {i}',
            utils.string_to_unicode, True, None
        ])
        labels_layout.append(
            [sg.Text(f'    Column {i}'),
             sg.Input(default_inputs[f'{keys[0]}_{i}'], size=(20, 1),
                      key=f'{keys[0]}_{i}', do_not_clear=True)]
        )

    if processing_options['process_data']:
        calc_labels = ('Calculation', 'Sample Summary', 'Dataset Summary')

        for j, label_list in enumerate(labels[1:]):
            if label_list:
                labels_layout.append([sg.Text(f'{calc_labels[j]} Labels:')])
                for k in range(len(label_list)):
                    col_num = i + 1 + k if j == 0 else k # continue column numbering for Calculations
                    labels_layout.append(
                        [sg.Text(f'    Column {col_num}'),
                         sg.Input(default_inputs[f'{keys[j + 1]}_{k}'], size=(20, 1),
                                  key=f'{keys[j + 1]}_{k}', do_not_clear=True)]
                    )
                    validations['user_inputs'].append([
                        f'{keys[j + 1]}_{k}', f'{calc_labels[j].lower()} label {col_num}',
                        utils.string_to_unicode, True, None
                    ])

    labels_column = [
        sg.Column(labels_layout, scrollable=True,
                  vertical_scroll_only=True, size=(404, 400))
    ]

    if not processing_options['plot_data_excel']:
        main_section = labels_column
    else:
        validations['user_inputs'].extend([
            ['x_min', 'x min', float , True, None],
            ['x_max', 'x max', float , True, None],
            ['y_min', 'y min', float , True, None],
            ['y_max', 'y max', float , True, None],
            ['x_label', 'x axis label', utils.string_to_unicode, False, None],
            ['y_label', 'y axis label', utils.string_to_unicode, False, None],
        ])

        available_cols = labels[0] + labels[1] if processing_options['process_data'] else labels[0]
        plot_layout = [
            [sg.Text('')],
            [sg.Text('Column of x data for plotting:'),
             sg.Combo([f'{col}' for col in range(len(available_cols))],
                      key='x_plot_index', readonly=True, size=(3, 1),
                      default_value=default_inputs['x_plot_index'])],
            [sg.Text('Column of y data for plotting:'),
             sg.Combo([f'{col}' for col in range(len(available_cols))],
                      key='y_plot_index', readonly=True, size=(3, 1),
                      default_value=default_inputs['y_plot_index'])],
            [sg.Text('X axis label:'),
             sg.Input(default_inputs['x_label'], key='x_label',
                      do_not_clear=True, size=(20, 1))],
            [sg.Text('Y axis label:'),
             sg.Input(default_inputs['y_label'], key='y_label',
                      do_not_clear=True, size=(20, 1))],
            [sg.Text(("Min and max values to show on the plot\n"
                     "(leave blank to use Excel's default):"))],
            [sg.Text('    X min:', size=(8, 1)),
             sg.Input(default_inputs['x_min'], key='x_min',
                      do_not_clear=True, size=(5, 1)),
             sg.Text('    X max:', size=(8, 1)),
             sg.Input(default_inputs['x_max'], key='x_max',
                      do_not_clear=True, size=(5, 1))],
            [sg.Text('    Y min:', size=(8, 1)),
             sg.Input(default_inputs['y_min'], key='y_min',
                      do_not_clear=True, size=(5, 1)),
             sg.Text('    Y max:', size=(8, 1)),
             sg.Input(default_inputs['y_max'], key='y_max',
                      do_not_clear=True, size=(5, 1))]
        ]

        main_section = [
            sg.TabGroup([
                [sg.Tab('Labels', [labels_column], key='tab1'),
                 sg.Tab('Excel Plot', plot_layout, key='tab2')]
            ], key='tab', tab_background_color=sg.theme_background_color())
        ]

    layout = [
        [sg.Menu([['&Help', ['&Unicode Help']]], key='-menu-',
                 background_color=sg.theme_background_color())],
        main_section,
        [sg.Button('Back', disabled=index == 0),
         sg.Button('Finish' if last_index else 'Next', bind_return_key=True,
                   button_color=utils.PROCEED_COLOR)]
    ]

    return validations, sg.Window(f'Dataset {index + 1} Options',
                                  layout, location=location)


def _select_column_labels(dataframes, data_source, processing_options):
    """
    Handles the event loop for the window to select the sample and column labels.

    Parameters
    ----------
    dataframes : list
        A list of lists of lists of pd.DataFrame objects, containing the all
        the data to process.
    data_source : DataSource
        The DataSource object for the data.
    processing_options : dict
        The dictionary that contains information about which
        processing steps will be conducted.

    Returns
    -------
    label_values : list
        A list of dictionaries containing all of the sample and column
        labels, as well as the Excel plot options, if plotting in Excel.
        Each entry in the list corresponds to one dataset.

    """

    label_values = [{} for _ in dataframes]
    location = (None, None)

    for i, dataset in enumerate(dataframes):
        j = i

        validations, window = _create_column_labels_window(
            dataset, data_source, processing_options, i, label_values[i],
            location, i==len(dataframes) - 1
        )

        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                utils.safely_close_window(window)

            elif event == 'Unicode Help':
                sg.popup(
                    ('"\\u00B2": \u00B2 \n"\\u03B8": \u03B8 \n"'
                     '\\u00B0": \u00B0\n\nFor example, Acceleration'
                     ' (m/s\\u00B2) creates Acceleration (m/s\u00B2)\n'),
                    title='Common Unicode'
                )

            elif event in ('Back', 'Next', 'Finish'):
                if utils.validate_inputs(values, **validations):
                    label_values[j].update(values)
                    location = window.current_location()
                    window.close()

                    if event == 'Back':
                        j -= 1
                    else:
                        j += 1

                    if j <= i:
                        validations, window = _create_column_labels_window(
                            dataframes[j], data_source, processing_options, j,
                            label_values[j], location, j==len(dataframes) - 1
                        )
                    else:
                        if i < len(dataframes) - 1:
                            label_values[i + 1].update(values)
                        break

        window.close()
        window = None

    return label_values


def _fit_data(datasets, data_source, sample_names, column_headers,
              excel_writer, options):
    """
    Handles peak fitting and any exceptions that occur during peak fitting.

    Parameters
    ----------
    dataframes : list
        A nested list of lists of lists of dataframes.
    data_source : DataSource
        The selected DataSource.
    sample_names : list
        A nested list of lists of strings for the sample names.
    column_headers : list
        A nested list of lists of strings for the sample names.
    options : dict
        A dictionary containing the relevent keys 'save_fitting' and
        'plot_fit_excel' which determine whether the fit results
        will be saved to Excel and whether the results will be plotted,
        respectively.

    Returns
    -------
    results : list
        A nested list of lists of lists, one entry for each entry in each sample
        in each dataset in datasets. If fitting was not done for the entry,
        the value will be None.

    """

    # changes some defaults for the plot formatting to look nice
    mpl_changes = { #TODO maybe allow this to be an input into the main gui function
        'font.serif': 'Times New Roman',
        'font.family': 'serif',
        'font.size': 12,
        'mathtext.default': 'regular',
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.minor.visible': True,
        'ytick.minor.visible': True,
        'xtick.major.size': 5,
        'xtick.major.width': 0.6,
        'xtick.minor.size': 2.5,
        'xtick.minor.width': 0.6,
        'ytick.major.size': 5,
        'ytick.major.width': 0.6,
        'ytick.minor.size': 2.5,
        'ytick.minor.width': 0.6,
        'lines.linewidth': 2,
        'lines.markersize': 5,
        'axes.linewidth': 0.6,
        'legend.frameon': False,
        'figure.dpi': 150,
        'figure.figsize': (6, 4.5)
    }

    results = [[[] for sample in dataset] for dataset in datasets]

    # allows exiting from the peak fitting GUI early, if desired or because of
    # an exception, while still continuing with the program
    try:

        default_inputs = {
            'x_fit_index': data_source.x_plot_index,
            'y_fit_index': data_source.y_plot_index
        }

        for i, dataset in enumerate(datasets):
            default_inputs.update({
                'x_label': column_headers[i][data_source.x_plot_index],
                'y_label': column_headers[i][data_source.y_plot_index]
            })

            for j, sample in enumerate(dataset):
                for k, entry in enumerate(sample):
                    default_inputs.update({
                        'sample_name': f'{sample_names[i][j]}_{k}_fit'
                    })

                    fit_output, default_inputs, proceed = launch_peak_fitting_gui(
                        entry, default_inputs, excel_writer,
                        options['save_fitting'], options['plot_fit_excel'],
                        mpl_changes, False)

                    results[i][j].extend(fit_output)

                    if not proceed:
                        raise utils.WindowCloseError

    except (utils.WindowCloseError, KeyboardInterrupt):
        print('\nPeak fitting manually ended early.\nMoving on with program.')

    except Exception:
        print('\nException occured during peak fitting:\n')
        print(traceback.format_exc())
        print('Moving on with program.')

    return results


def _plot_data(datasets, data_source):
    """
    Handles plotting and any exceptions that occur during plotting.

    Parameters
    ----------
    dataframes : list
        A nested list of lists of lists of dataframes.
    data_source : DataSource
        The DataSource object whose figure_rcParams attribute will be used
        to set matplotlib's rcParams.

    Returns
    -------
    list
        A nested list of lists, with one entry per dataset in datasets.
        Each entry contains the matplotlib Figure, and a dictionary
        containing the Axes. If plotting was exited before plotting all
        datasets in dataframes, then [None, None] will be the entry instead.

    """

    plot_datasets = []
    for dataset in datasets: # flattens the dataset to a single list per dataset
        plot_datasets.append([*itertools.chain(*dataset)])

    return launch_plotting_gui(plot_datasets, data_source.figure_rcParams)


def _move_files(files):
    """
    Launches a window to select the new folder destinations for the files.

    Parameters
    ----------
    files : list
        A nested list of lists of lists of strings corresponding
        to file paths.

    """

    text_layout = [[sg.Text(f'Dataset {i + 1}')] for i in range(len(files))]
    files_layout = [
        [sg.Input('', key=f'folder_{i}', enable_events=True,
                  disabled=True),
         sg.FolderBrowse(target=f'folder_{i}', key=f'button_{i}')]
        for i in range(len(files))
    ]
    tot_layout = [i for j in zip(text_layout, files_layout) for i in j]

    if len(files) > 2:
        scrollable = True
        size = (600, 200)
    else:
        scrollable = False
        size = (None, None)

    layout = [
        [sg.Text('Choose the folder(s) to move files to:', size=(30, 1))],
        [sg.Frame('', [[sg.Column(tot_layout, scrollable=scrollable,
                                  vertical_scroll_only=True, size=size)]])],
        [sg.Button('Submit', bind_return_key=True,
                   button_color=utils.PROCEED_COLOR),
         sg.Check('All Same Folder', key='same_folder',
                  enable_events=True, disabled=len(files) == 1)]
    ]

    try:
        window = sg.Window('Move Files', layout)
        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                utils.safely_close_window(window)

            elif event.startswith('folder_') and values['same_folder']:
                for i in range(1, len(files)):
                    window[f'folder_{i}'].update(value=values['folder_0'])

            elif event == 'same_folder':
                if values['same_folder']:
                    for i in range(1, len(files)):
                        window[f'folder_{i}'].update(value=values['folder_0'])
                        window[f'button_{i}'].update(disabled=True)
                else:
                    for i in range(1, len(files)):
                        window[f'button_{i}'].update(disabled=False)

            elif event == 'Submit':
                if any(not values[key] for key in values if key.startswith('folder_')):
                    sg.popup('Please enter folders for all datasets', title='Error')
                else:
                    break

        window.close()
        del window

    except (utils.WindowCloseError, KeyboardInterrupt):
        print('\nMoving files manually ended early.\nMoving on with program.')

    else:
        try:
            folders = [values[f'folder_{i}'] for i in range(len(files))]
            for i, file_list in enumerate(files):
                # Will automatically rename files if there is already a file with
                # the same name in the destination folder.
                file_mover(file_list, new_folder=folders[i],
                           skip_same_files=False)
        except Exception:
            print('\nException occured during moving files:\n')
            print(traceback.format_exc())
            print('Moving on with program.')


def _save_excel_file(append_file, excel_writer, file_name, alternate_name=None):
    """
    Handles saving the Excel file and the various exceptions that can occur.

    Parameters
    ----------
    append_file : bool
        If True, will save a temporary file and then append the sheets to the
        destination file.
    excel_writer : pd.ExcelWriter
        The pandas ExcelWriter object that contains all of the
        information about the Excel file being created.
    file_name : str
        The string of the file path for the file to save with
        the input excel_writer. If append_file is True, this
        will correspond to a temporary file that will be deleted.
    alternate_name : str, optional
        If append_file is True, this is the file path string
        for the actual file. The default is None.

    """

    #ensures that the folder destinations exist
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)
    if alternate_name is not None:
        Path(alternate_name).parent.mkdir(parents=True, exist_ok=True)

    try_to_save = True
    while try_to_save:
        try:
            excel_writer.save() # raises PermissionError if file is open

            if append_file:
                print('\nSaved temporary file...')
            else:
                print('\nSaved Excel file.')
            break

        except PermissionError:
            try_to_save = sg.popup_ok(
                '\nTrying to overwrite Excel file. Please close the file.\n'
            )

    if append_file and try_to_save:
        if os.name != 'nt': # will only do this in Windows (os.name=='nt' for windows)
            print((
                '\nAppending not supported for this os system. Please manually '
                f'copy the sheets from "{file_name}"'
            ))
        else:
            close_file = True
            try:
                #checks if the file is open; raises PermissionError if so
                Path(alternate_name).rename(alternate_name)

                app = xw.App(visible=False)
                app.screen_updating = False
                workbook_1 = xw.Book(file_name)
                workbook_2 = xw.Book(alternate_name)

            except PermissionError:
                close_file = False
                app = xw.apps.active
                app.screen_updating = False
                workbook_1 = xw.Book(file_name)

                #cycles through Excel instances
                for open_app in xw.apps:
                    #cycles through open Excel workbooks to find the right file
                    for book in open_app.books:
                        if Path(alternate_name).name == book.name:
                            workbook_2 = book
                            break

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
                    Path(file_name).unlink(True)

                except Exception as e:
                    print(repr(e))
                    print('\nAppending sheets potentially failed. Check the '\
                          'Excel file, and potentially copy the sheets from '\
                          f'"{file_name}" if it exists.')

                finally:
                    for sheet in workbook_2.sheets:
                        if 'temp_sheet_unique_name' in sheet.name:
                            sheet.delete()
                            break

                    app.screen_updating = True
                    workbook_2.app.screen_updating = True
                    workbook_2.save()

                    if close_file:
                        workbook_2.close()
                        app.kill()


def launch_main_gui(data_sources):
    """
    Goes through all of the windows to find files, process/plot/fit data, and save to Excel.

    Parameters
    ----------
    data_sources : list/tuple or DataSource
        A container (list, tuple) of mcetl.DataSource objects, or a single
        DataSource object.

    Returns
    -------
    dataframes : list
        A list of lists of dataframes, with each dataframe containing the data imported from a
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
            raise TypeError("Only DataSource objects can be used in the main gui.")

        processing_options = _select_processing_options(data_sources)

        # Specifying the selected data source
        data_source = None
        for source in data_sources:
            if processing_options[f'source_{source.name}']:
                data_source = source
                break

        if not processing_options['save_excel']:
            writer = None
        else:
            excel_filename = processing_options['file_name']

            if processing_options['append_file'] and Path(excel_filename).exists():
                final_name = excel_filename
                excel_filename = str(
                    Path.cwd().joinpath('temporary_file_to_be_deleted.xlsx')
                )
            else:
                processing_options['append_file'] = False
                final_name = None

            writer = pd.ExcelWriter(excel_filename, engine='xlsxwriter') #TODO later add mode here to be either 'a' or 'w' after switching to openpyxl
            # Formatting styles for the Excel workbook
            for excel_format in data_source.excel_formats:
                writer.book.add_format(data_source.excel_formats[excel_format])

        # Selection of raw data files
        if processing_options['multiple_files']:
            if processing_options['use_last_search']:
                with open(Path(__file__).parent.resolve().joinpath(
                        'previous_search.json'), 'r') as old_search:
                    files = json.load(old_search)
            else:
                files = file_finder(file_type=data_source.file_type,
                                    num_files=data_source.num_files)

                # Saves the last search to a json file so it can be used again to bypass the search.
                with open(Path(__file__).parent.resolve().joinpath(
                        'previous_search.json'), 'w') as output_file:
                    json.dump(files, output_file)

            # Imports the raw data from the files
            if any((processing_options['process_data'],
                    processing_options['save_excel'],
                    processing_options['fit_peaks'],
                    processing_options['plot_python'])):

                dataframes = [[[] for sample in dataset] for dataset in files]
                import_vals = [[[] for sample in dataset] for dataset in files]
                if files[0][0][0].endswith('.xlsx'):
                    for i, dataset in enumerate(files):
                        for j, sample in enumerate(dataset):
                            for entry in sample:
                                #disable_blank_col = not (i == 0 and j == 0) #TODO use this later to lock out changing the number of columns
                                import_values = utils.select_file_gui(
                                    data_source, sample
                                )
                                added_dataframes = utils.raw_data_import(
                                    import_values, sample, False
                                )
                                dataframes[i][j].extend(added_dataframes)
                                import_vals[i][j].extend(
                                    [import_values] * len(added_dataframes)
                                )

                else:
                    import_values = utils.select_file_gui(data_source, files[0][0][0])
                    for i, dataset in enumerate(files):
                        for j, sample in enumerate(dataset):
                            for entry in sample:
                                dataframes[i][j].extend(
                                    utils.raw_data_import(import_values, entry, False)
                                )
                                import_vals[i][j].append(import_values)

        else:
            import_values = utils.select_file_gui(data_source)
            dataframes = [[
                utils.raw_data_import(import_values, import_values['file'], False)
            ]]
            files = [[[import_values['file']]]]
            import_vals = [[[import_values] * len(dataframes[0][0])]]

        # Specifies column names
        if any((processing_options['process_data'],
                processing_options['save_excel'],
                processing_options['fit_peaks'],
                processing_options['plot_python'])):

            # Formatting for excel sheets
            sheet_names = []
            sample_names = []
            column_headers = []
            plot_options = []

            labels = _select_column_labels(
                dataframes, data_source, processing_options
            )

            for values in labels:

                sheet_names.append(utils.string_to_unicode(values['sheet_name']))
                sample_names.append(
                    utils.string_to_unicode([
                        values[key] for key in values if key.startswith('sample_name')
                    ])
                )
                column_headers.append(
                    utils.string_to_unicode([
                        values[key] for key in values if key.startswith('data_label')
                    ])
                )

                if processing_options['process_data']:
                    for prefix in ('calculation_label', 'sample_summary_label',
                                   'dataset_summary_label'):
                        column_headers[-1].extend(
                            utils.string_to_unicode([
                                values[key] for key in values if key.startswith(prefix)
                            ])
                        )

                if not processing_options['plot_data_excel']:
                    plot_options.append(None)
                else:
                    plot_options.append({
                        'x_label': utils.string_to_unicode(values['x_label']),
                        'y_label': utils.string_to_unicode(values['y_label']),
                        'x_plot_index': int(values['x_plot_index']),
                        'y_plot_index': int(values['y_plot_index']),
                        'x_min':  float(values['x_min']) if values['x_min'] else None,
                        'x_max':  float(values['x_max']) if values['x_max'] else None,
                        'y_min':  float(values['y_min']) if values['y_min'] else None,
                        'y_max':  float(values['y_max']) if values['y_max'] else None
                    })

        # Collects each set of data into a single dataframe and applies formulas according
        # to the selected data source
        if processing_options['save_excel'] or processing_options['process_data']:

            if processing_options['process_data']:
                # perform separation functions
                dataframes, import_vals = data_source.do_separation_functions(
                    dataframes, import_vals
                )
                # assign reference indices for all relevant columns
                data_source.set_references(dataframes, import_vals)

            # merge dataframes for each dataset
            merged_dataframes = data_source.merge_datasets(dataframes)
            dataframes = None # frees up memory

            if processing_options['save_excel'] and processing_options['process_data']:
                merged_dataframes = data_source.do_excel_functions(merged_dataframes)

            if processing_options['save_excel']:
                for i, df_list in enumerate(merged_dataframes):
                    _generate_excel(
                        df_list, sample_names[i], data_source,
                        column_headers[i], writer, sheet_names[i],
                        processing_options['plot_data_excel'], plot_options[i]
                    )

            if processing_options['process_data']:
                merged_dataframes = data_source.do_python_functions(merged_dataframes)

            # split data back into individual dataframes
            dataframes = data_source.split_into_entries(merged_dataframes)
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

        # Handles peak fitting
        if processing_options['fit_peaks']:
            fit_results = _fit_data(
                dataframes, data_source, sample_names, column_headers,
                writer, processing_options
            )

        # Handles saving the Excel file and transferring sheets if appending to an existing file
        if processing_options['save_excel']:
            _save_excel_file(
                processing_options['append_file'], writer, excel_filename, final_name
            )

        # Handles moving files
        if processing_options['move_files']:
            _move_files(files)

        # Handles plotting in python
        if processing_options['plot_python']:
            plot_results = _plot_data(dataframes, data_source)

    except (utils.WindowCloseError, KeyboardInterrupt):
        pass
    except Exception:
        print(traceback.format_exc())

    return dataframes, fit_results, plot_results
