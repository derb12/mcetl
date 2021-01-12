# -*- coding: utf-8 -*-
"""Provides utility functions, classes, and constants.

Useful functions are put here in order to prevent circular importing
within the other files.

The functions contained within this module ease the use of user-interfaces,
selecting options for opening files, and working with Excel.

@author: Donald Erb
Created on Jul 15, 2020

Attributes
----------
PROCEED_COLOR : tuple(str, str)
    The button color for all buttons that proceed to the next window.
    The default is ('white', '#00A949'), where '#00A949' is a bright green.

"""


import importlib
import functools
import operator
from pathlib import Path
import textwrap

import numpy as np
import pandas as pd
import PySimpleGUI as sg


PROCEED_COLOR = ('white', '#00A949')


def check_availability(module):
    """
    Checks whether an optional dependency is available to import.

    Does not check the module version since it is assumed that the
    parent module will do a version check if the module is actually
    usable.

    Parameters
    ----------
    module : str
        The name of the module.

    Returns
    -------
    bool
        True if the module can be imported, False if it cannot.

    Notes
    -----
    It is faster to use importlib to check the availability of the
    module rather than doing a try-except block to try and import
    the module, since importlib does not actually import the module.

    """
    return importlib.util.find_spec(module) is not None


_HAS_XLRD = check_availability('xlrd')


class WindowCloseError(Exception):
    """Custom exception to allow exiting a GUI window to stop the program."""


def safely_close_window(window):
    """
    Closes a PySimpleGUI window and removes the window and its layout.

    Used when exiting a window early by manually closing the window. Ensures
    that the window is properly closed and then raises a
    WindowCloseError exception, which can be used to determine that the window
    was manually closed.

    Parameters
    ----------
    window : sg.Window
        The window that will be closed.

    Raises
    ------
    WindowCloseError
        Custom exception to notify that the window has been closed earlier
        than expected.

    """

    window.close()
    raise WindowCloseError('Window was closed earlier than expected.')


def doc_lru_cache(function=None, **lru_cache_kwargs):
    """
    Decorator that allows keeping a function's docstring when using functools.lru_cache.

    Parameters
    ----------
    function : Callable
        The function to use. If used as a decorator and lru_cache_kwargs
        are specified, then function will be None.
    **lru_cache_kwargs
        Any keyword arguments to pass to functools.lru_cache (maxsize and/or typed,
        as of Python 3.9).

    Examples
    --------
    A basic usage of this decorator would look like:

    >>> @doc_lru_cache(maxsize=200)
        def function(arg, kwarg=1)
            return arg + kwarg

    """

    if function is None:
        function = functools.partial(doc_lru_cache, **lru_cache_kwargs)

    @functools.lru_cache(**lru_cache_kwargs)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return functools.update_wrapper(wrapper, function)


@doc_lru_cache(maxsize=None)
def excel_column_name(index):
    """
    Converts 1-based index to the Excel column name.

    Parameters
    ----------
    index : int
        The column number. Must be 1-based, ie. the first column
        number is 1 rather than 0.

    Returns
    -------
    col_name : str
        The column name for the input index, eg. an index of 1 returns 'A'.

    Raises
    ------
    ValueError
        Raised if the input index is not in the range 1 <= index <= 18278,
        meaning the column name is not within 'A'...'ZZZ'.

    Notes
    -----
    Caches the result so that any repeated index lookups are faster,
    and uses recursion to make better usage of the cache.

    chr(64 + remainder) converts the remainder to a character, where
    64 denotes ord('A') - 1, so if remainder = 1, chr(65) = 'A'.

    """

    if not 1 <= index <= 18278: # ensures column is between 'A' and 'ZZZ'.
        raise ValueError(f'Column index {index} must be between 1 and 18278.')

    col_num, remainder = divmod(index, 26)
    # ensure remainder is between 1 and 26
    if remainder == 0:
        remainder = 26
        col_num -= 1

    if col_num > 0:
        return excel_column_name(col_num) + chr(64 + remainder)
    else:
        return chr(64 + remainder)


def get_min_size(default_size, scale, dimension='both'):
    """
    Returns the minimum size for a GUI element to match the screen size.

    Parameters
    ----------
    default_size : int
        The default number of pixels to use. Needed because sg.Window.get_screen_size()
        can return the total screen size when using multiple screens on some linux
        systems.
    scale : float
        The scale factor to apply to the screen size as reported by
        sg.Window.get_screen_size. For example, if the element size was
        desired to be at most 50% of the minimum screen dimension, then
        the scale factor is 0.5.
    dimension : str
        The screen dimension to compare. Can be either 'width', 'height', or 'both'.

    Returns
    -------
    int
        The minimum pixel count among scale * screen height, scale * screen width,
        and default_size.

    """

    indices = {'width': [0], 'height': [1], 'both': [0, 1]}

    screen_size = sg.Window.get_screen_size()

    return int(min(*(scale * screen_size[index] for index in indices[dimension]), default_size))


def string_to_unicode(input_list):
    r"""
    Converts strings to unicode by replacing '\\' with '\'.

    Necessary because the user input from PySimpleGui's InputText element
    will convert any '\' input by the user to '\\', which will not
    be converted to the desired unicode. If the string already has unicode
    characters, it will be left alone.

    Also converts things like '\\n' and '\\t' to '\n' and '\t', respectively,
    so that inputs are correctly interpreted.

    Parameters
    ----------
    input_list : (list, tuple) or str
        A container of strings or a single string.

    Returns
    -------
    output : (list, tuple) or str
        A container of strings or a single string, depending on the input,
        with the unicode correctly converted.

    Notes
    -----
    Uses raw_unicode_escape encoding to ensure that any existing unicode is
    correctly decoded; otherwise, it would translate incorrectly.

    If using mathtext in matplotlib and want to do something like $\nu$,
    input $\\nu$ in the GUI, which gets converted to $\\\\nu$ by PySimpleGUI,
    and in turn will be converted back to $\\nu$ by this fuction, which matplotlib
    considers equivalent to $\nu$.

    """

    if isinstance(input_list, str):
        input_list = [input_list]
        return_list = False
    else:
        return_list = True

    output = []
    for entry in input_list:
        if '\\' in entry:
            entry = entry.encode('raw_unicode_escape').decode('unicode_escape')
        output.append(entry)

    return output if return_list else output[0]


def stringify_backslash(input_string):
    r"""
    Fixes strings containing backslash, such as '\n', so that they display properly in GUIs.

    Parameters
    ----------
    input_string : str
        The string that potentially contains a backslash character.

    Returns
    -------
    output_string : str
        The string after replacing various backslash characters with their
        double backslash versions.

    Notes
    -----
    It is necessary to replace multiple characters because things like '\n' are
    considered unique characters, so simply replacing the '\\' would not work.

    """

    output_string = input_string
    replacements = (('\\', '\\\\'), ('\n', '\\n'), ('\t', '\\t'), ('\r', '\\r'))
    for replacement in replacements:
        output_string = output_string.replace(*replacement)

    return output_string


def validate_inputs(window_values, integers=None, floats=None,
                    strings=None, user_inputs=None, constraints=None):
    """
    Validates entries from a PySimpleGUI window and converts to the desired type.

    Parameters
    ----------
    window_values : dict
        A dictionary of values from a PySimpleGUI window, generated by using
        window.read().
    integers : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary and whose values should
        be integers.
    floats : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary and whose values should
        be floats.
    strings : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary and whose values should
        be non-empty strings.
    user_inputs : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary and whose values should
        be a certain data type; the values are first determined by
        separating each value using ',' (default) or the last index.
    constraints : list, optional
        A list of lists (see Notes below), with each key corresponding
        to a key in the window_values dictionary and whose values should
        be ints or floats constrained between upper and lower bounds.

    Returns
    -------
    bool
        True if all data in the window_values dictionary is correct.
        False if there is any error with the values in the window_values dictionary.

    Notes
    -----
    Inputs for integers, floats, and strings are
        [[key, display text],].
    For example: [['peak_width', 'peak width']]

    Inputs for user_inputs are
        [[key, display text, data type, allow_empty_input (optional), separator (optional)],],
    where separator is a string, and allow_empty_input is a boolean.
    If no separator is given, it is assumed to be a comma (','), and
    if no allow_empty_input value is given, it is assumed to be False.
    user_inputs can also be used to run the inputs through a function by setting
    the data type to a custom function. Use None as the separator if only a
    single value is wanted.
    For example: [
        ['peak_width', 'peak width', float], # ensures each entry is a float
        ['peak_width_2', 'peak width 2', int, False, ';'], # uses ';' as the separator
        ['peak_width_3', 'peak width 3', function, False, None], # no separator, verify with function
        ['peak_width_4', 'peak width 4', function, True, None] # allows empty input
    ]

    Inputs for constraints are
        [[key, display text, lower bound, upper bound (optional)],],
    where lower and upper bounds are strings with the operator and bound, such
    as "> 10". If lower bound or upper bound is None, then the operator and
    bound is assumed to be >=, -np.inf and <=, np.inf, respectively.
    For example: [
        ['peak_width', 'peak width', '> 10', '< 20'], # 10 < peak_width < 20
        ['peak_width_2', 'peak width 2', None, '<= 5'] # -inf <= peak_width_2 <= 5
        ['peak_width_3', 'peak width 3', '> 1'] # 1 < peak_width_2 <= inf
    ]

    The display text will be the text that is shown to the user if the value
    of window_values[key] fails the validation.

    #TODO eventually collect all errors so they can all be fixed at once.

    """

    if integers is not None:
        for entry in integers:
            try:
                window_values[entry[0]] = int(window_values[entry[0]])
            except:
                sg.popup(f'Need to enter integer in "{entry[1]}".\n', title='Error')
                return False

    if floats is not None:
        for entry in floats:
            try:
                window_values[entry[0]] = float(window_values[entry[0]])
            except:
                sg.popup(f'Need to enter number in "{entry[1]}".\n', title='Error')
                return False

    if strings is not None:
        for entry in strings:
            if not window_values[entry[0]]:
                sg.popup(f'Need to enter information in "{entry[1]}".\n',
                         title='Error')
                return False

    if user_inputs is not None:
        for entry in user_inputs:
            if len(entry) > 4:
                allow_empty_input = entry[3]
                separator = entry[4]
            elif len(entry) > 3:
                allow_empty_input = entry[3]
                separator = ','
            else:
                allow_empty_input = False
                separator = ','

            if separator is None:
                inputs = [window_values[entry[0]]] if window_values[entry[0]] else []
            else:
                inputs = [val.strip() for val in window_values[entry[0]].split(separator) if val.strip()]

            try:
                if inputs:
                    values = [entry[2](inpt) for inpt in inputs]
                    window_values[entry[0]] = values if separator is not None else values[0]
                elif allow_empty_input:
                    window_values[entry[0]] = [] if separator is not None else ''
                else:
                    raise ValueError('Entry must not be empty.')

            except Exception as e:
                sg.popup(
                    f'Need to correct entry for "{entry[1]}".\n\nError:\n    {repr(e)}\n',
                    title='Error')
                return False

    if constraints is not None:
        operators = {'>': operator.gt, '>=': operator.ge,
                     '<': operator.lt, '<=': operator.le}
        for entry in constraints:
            if entry[2] is not None:
                lower_key, lower_bound = entry[2].split(' ')
                lower_bound = float(lower_bound) if '.' in lower_bound else int(lower_bound)
            else:
                lower_key = '>='
                lower_bound = float('-inf')

            if len(entry) > 3 and entry[3] is not None:
                upper_key, upper_bound = entry[3].split(' ')
                upper_bound = float(upper_bound) if '.' in upper_bound else int(upper_bound)
            else:
                upper_key = '<='
                upper_bound = float('inf')

            # to allow for constraining iterative values
            if isinstance(window_values[entry[0]], (int, float)):
                values = [window_values[entry[0]]]
            else:
                values = window_values[entry[0]]

            for value in values:
                if not (operators[lower_key](value, lower_bound)
                        and operators[upper_key](value, upper_bound)):
                    sg.popup(
                        (f'"{entry[1]}" must be {lower_key} {lower_bound} and '
                        f'{upper_key} {upper_bound}.\n'),
                        title='Error'
                    )
                    return False

    return True


def validate_sheet_name(sheet_name):
    r"""
    Ensures that the desired Excel sheet name is valid.

    Parameters
    ----------
    sheet_name : str
        The desired sheet name.

    Returns
    -------
    sheet_name : str
        The input sheet name. Only returned if it is valid.

    Raises
    ------
    ValueError
        Raised if the sheet name is greater than 31 characters or if it
        contains any of the following: \, /, ?, *, [, ], :

    """

    forbidden_characters = ('\\', '/', '?', '*', '[', ']', ':')

    if len(sheet_name) > 31:
        raise ValueError('Sheet name must be less than 32 characters.')
    elif any(char in sheet_name for char in forbidden_characters):
        raise ValueError(
            f'Sheet name cannot have any of the following characters: {forbidden_characters}'
        )

    return sheet_name


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

    original_setting = sg.ENABLE_TREEVIEW_869_PATCH
    # set sg.ENABLE_TREEVIEW_869_PATCH to False because it prints out each
    # time the window is made; will restore value after creating window
    sg.set_options(enable_treeview_869_patch=False)

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
                    header_list = dataframe.columns.tolist()

                tabs[i].append(
                    sg.Table(values=data, headings=header_list, key=f'table_{i}{j}',
                             auto_size_columns=True, vertical_scroll_only=False,
                             num_rows=min(25, len(data)))
                )

        if single_file:
            layout = [tabs[0]]
        else:
            datasets = []
            for i, tab_group in enumerate(tabs):
                datasets.append(
                    [sg.Tab(f'Entry {j + 1}', [[table]],
                            key=f'entry_{i}{j}') for j, table in enumerate(tab_group)]
                )

            if single_dataset:
                layout = [
                    [sg.TabGroup([datasets[0]],
                                 tab_background_color=sg.theme_background_color())]
                ]

            else:
                tab_groups = []
                for i, tab_group in enumerate(datasets):
                    tab_groups.append(
                        [sg.Tab(f'Dataset {i + 1}',
                                [[sg.TabGroup([tab_group],
                                              tab_background_color=sg.theme_background_color())]])]
                    )
                layout = [
                    [sg.TabGroup(tab_groups,
                                 tab_background_color=sg.theme_background_color())]
                ]

        window = sg.Window(title, layout, resizable=True, finalize=True)

    except Exception as e: #TODO do I still need this try-except block?
        sg.popup('Error reading file:\n    ' + repr(e) + '\n', title='Error')
        window = None

    sg.set_options(enable_treeview_869_patch=original_setting)

    return window


def optimize_memory(dataframe, convert_objects=False):
    """
    Optimizes dataframe memory usage by converting data types.

    Optimizes object dtypes by trying to convert to other dtypes,
    if the pandas version is greater than 1.0.0.
    Optimizes numerical dtypes by downcasting to the most appropriate dtype.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The dataframe to optimize.
    convert_objects : bool, optional
        If True, will attempt to convert columns with object dtype
        if the pandas version is >= 1.0.0.

    Returns
    -------
    dataframe : pd.DataFrame
        The memory-optimized dataframe.

    Notes
    -----
    convert_objects is needed because currently, when object columns
    are converted to a dtype of string, the row becomes a StringArray object,
    which does not have the tolist() method curently implemented
    (as of pandas version 1.0.5). openpyxl's dataframe_to_rows method
    uses each series's series.values.tolist() method to convert the dataframe
    into a generator of rows, so having a StringArray row without a tolist
    method causes an exception when using openpyxl's dataframe_to_rows.

    When downcasting the float and integer columns, do one at a time rather
    than using df[columns].apply(to_numeric, ...) so that each column is overwritten
    immediately, rather than making a copy of all the selected columns, reducing
    memory usage.

    """

    # ensure all column names are unique
    original_columns = dataframe.columns.tolist()
    dataframe.columns = range(len(original_columns))

    if convert_objects and int(pd.__version__.split('.')[0]) > 0:
        # attempts to convert object columns to other dtypes
        objects = dataframe.select_dtypes(['object'])
        if len(objects.columns) > 0:
            dataframe[objects.columns] = objects.convert_dtypes(convert_integer=False)

    for column in dataframe.select_dtypes(include=['int', 'int64']).columns:
        dataframe[column] = pd.to_numeric(dataframe[column], downcast='integer', errors='ignore')

    for column in dataframe.select_dtypes(include=['float', 'float64']).columns:
        dataframe[column] = pd.to_numeric(dataframe[column], downcast='float', errors='ignore')

    dataframe.columns = original_columns

    return dataframe


def series_to_numpy(series, dtype=float):
    """
    Tries to convert a pandas Series to a numpy array with the desired dtype.

    If initial conversion does not work, tries to convert series to object first.
    If that is not successful and if the first item is a string, assumes the
    first item is a header, converts it to None, and tries the conversion. If
    that is still unsuccessful, then an array of the series is returned without
    changing the dtype.

    Parameters
    ----------
    series : pd.Series
        The series to convert to numpy with the desired dtype.
    dtype : type, optional
        The dtype to use in the numpy array of the series. Default
        is float.

    Returns
    -------
    output : np.ndarray
        The input series with the specified dtype if conversion was successful.
        Otherwise, the output is an ndarray of the input series without dtype
        conversion.

    Notes
    -----
    This function is needed because pandas's pd.NA and extension arrays do not work
    well with other modules and can be difficult to convert.

    """

    if int(pd.__version__.split('.')[0]) > 0:
        kwargs = {'na_value': np.nan if dtype == float else None}
    else:
        kwargs = {}

    output = None
    try:
        output = np.asarray(series.to_numpy(**kwargs), dtype)
    except (TypeError, ValueError):
        try: # try converting to object before conversion
            output = np.asarray(series.to_numpy(object, **kwargs), dtype)
        except (TypeError, ValueError):
            if isinstance(series[0], str):
                try: # try removing the first item if it's a string, maybe it's a header
                    copy = series.copy()
                    copy[0] = None
                    output = np.asarray(copy.to_numpy(object, **kwargs), dtype)
                except (TypeError, ValueError):
                    pass

    if output is None:
        output = series.to_numpy()

    return output


def raw_data_import(window_values, file, show_popup=True):
    """
    Used to import data from the specified file into pandas DataFrames.

    Also used to show how data will look after using certain import values.

    Parameters
    ----------
    window_values : dict
        A dictionary with keys 'row_start', 'row_end', columns', 'separator',
        and optionally 'sheet'.
    file : str:
        A string containing the path to the file to be imported.
    show_popup : bool
        If True, will display a popup window showing a table of the data.

    Returns
    -------
    dataframes : list or None
        A list of dataframes containing the data after importing if show_popup
        is False, otherwise returns None.

    Notes
    -----
    Optimizes the memory usage of the imported data before returning.

    """

    excel_formats = ['.xlsx', '.xlsm']
    if _HAS_XLRD:
        excel_formats.append('.xls')

    try:
        row_start = window_values['row_start']
        row_end = window_values['row_end']
        column_numbers = window_values['columns']
        if window_values['separator'].lower() not in ('', 'none'):
            separator = window_values['separator']
        else:
            separator = None

        if Path(file).suffix in excel_formats:
            first_col = int(window_values['first_col'].split(' ')[-1])
            last_col = int(window_values['last_col'].split(' ')[-1]) + 1
            columns = list(range(first_col, last_col))
            repeat_unit = window_values['repeat_unit']

            total_dataframe = pd.read_excel(
                file, sheet_name=window_values['sheet'], header=None,
                skiprows=row_start, skipfooter=row_end, convert_float=not show_popup,
                usecols=columns, engine=None if _HAS_XLRD else 'openpyxl'
            )

            column_indices = [num + first_col for num in column_numbers]
            dataframes = []
            for num in range(max(1, len(total_dataframe.columns) // repeat_unit)):
                indices = [(num * repeat_unit) + elem for elem in column_indices]
                dataframes.append(total_dataframe[indices])

        elif window_values['fixed_width_file']:
            dataframes = [
                pd.read_fwf(
                    file, skiprows=row_start, skipfooter=row_end, header=None,
                    delimiter=separator, usecols=column_numbers,
                    widths=window_values['fixed_width_columns']
                )[column_numbers]
            ]
        else:
            dataframes = [
                pd.read_csv(
                    file, skiprows=row_start, skipfooter=row_end, header=None,
                    sep=separator, usecols=column_numbers, engine='python'
                )[column_numbers]
            ]

        if not show_popup:
            for i, dataframe in enumerate(dataframes):
                dataframe.columns = list(range(len(dataframe.columns)))
                dataframes[i] = optimize_memory(dataframe)

        else:
            if Path(file).suffix in excel_formats and len(dataframes) > 1:
                window_0 = show_dataframes(dataframes, 'Imported Datasets')
                window_1 = show_dataframes(total_dataframe, 'Total Raw Data')
            else:
                window_0 = show_dataframes(dataframes[0], 'Imported Dataset')
                window_1 = None

            while any((window_0, window_1)):
                window = sg.read_all_windows()[0]
                if window is window_0:
                    window_0.close()
                    window_0 = None
                else:
                    window_1.close()
                    window_1 = None

            dataframes = None # to clean up memory, dataframe is not needed

        return dataframes

    except Exception as e:
        sg.popup('Error reading file:\n    ' + repr(e) + '\n', title='Error')


def select_file_gui(data_source=None, file=None, previous_inputs=None, assign_columns=False):
    """
    GUI to select a file and input the necessary options to import its data.

    Parameters
    ----------
    data_source : DataSource, optional
        The DataSource object used for opening the file.
    file: str, optional
        A string containing the path to the file to be imported.
    previous_inputs : dict, optional
        A dictionary containing the values from a previous usage of this
        function, that will be used to overwrite the defaults. Note, if
        opening Excel files, the previous_inputs will have no effect.
    assign_columns : bool, optional
        If True, designates that the columns for each unique variable in
        the data source need to be identified. If False (or if data_source
        is None), then will not prompt user to select columns for variables.

    Returns
    -------
    values : dict
        A dictionary containing the items necessary for importing data from
        the selected file.

    """

    excel_formats = ['.xlsx', '.xlsm']
    if _HAS_XLRD:
        excel_formats.append('.xls')

    if data_source is None or not data_source.unique_variables:
        assign_column_indices = False
    else:
        assign_column_indices = assign_columns

    # Default values for if there is no file specified
    default_inputs = {
        'row_start': 0 if data_source is None else data_source.start_row,
        'row_end': 0 if data_source is None else data_source.end_row,
        'separator': '' if data_source is None else stringify_backslash(data_source.separator),
        'columns': '0, 1' if data_source is None else ', '.join([
            str(elem) for elem in data_source.column_numbers
        ]),
        'total_indices': None if data_source is None else data_source.column_numbers,
        'variable_indices': None if data_source is None else dict(
            zip(data_source.unique_variables,
                data_source.unique_variable_indices)
        ),
        'sheets': [],
        'sheet': '',
        'excel_columns': [],
        'first_column': '',
        'last_column': '',
        'repeat_unit': '',
        'fixed_width_file': False,
        'fixed_width_columns': '',
        'same_values': True if None not in (data_source, file) else False,
        'initial_separator': '',
        'initial_columns': '',
        'initial_fixed_width_file': False,
        'initial_fixed_width_columns': '',
        'initial_row_start': '',
        'initial_row_end': '',
        'initial_total_indices': None if data_source is None else [''] * len(data_source.column_numbers),
    }

    if previous_inputs:
        unwanted_keys = ('file', 'sheets', 'sheet', 'excel_columns',
                         'first_column', 'last_column', 'repeat_unit')
        for key in unwanted_keys:
            previous_inputs.pop(key, None)

        previous_inputs['columns'] = ', '.join(str(num) for num in previous_inputs.get('columns', [0, 1]))
        previous_inputs['fixed_width_columns'] = ', '.join(str(num) for num in previous_inputs.get('fixed_width_columns', []))
        default_inputs.update(previous_inputs)

    validations = {
        'integers': [['row_start', 'start row'], ['row_end', 'end row']],
        'user_inputs': [['columns', 'data columns', int]],
        'constraints': [['row_start', 'start row', '>= 0'],
                        ['row_end', 'end row', '>= 0'],
                        ['columns', 'data columns', '>= 0']]
    }
    if default_inputs['fixed_width_file']:
        validations['user_inputs'].append(['fixed_width_columns', 'fixed width columns', int])

    disable_excel = True
    disable_other = True
    disable_bottom = True
    dataframes = None # TODO wil be passed to raw_data_import to prevent opening excel files multiple times

    if file is None:
        file_types = [('All Files', '*.*'), ('CSV', '*.csv'),
                      ('Text Files', '*.txt'), ('Excel Workbook', '*.xlsx'),
                      ('Excel Macro-Enabled Workbook', '*.xlsm')]
        if _HAS_XLRD:
            file_types.append(('Excel 97-2003 Workbook', '*.xls'))

        file_element = [
            sg.Input('Choose a file', key='file', size=(26, 1), disabled=True),
            sg.Input('', key='new_file', enable_events=True, visible=False),
            sg.FileBrowse(key='file_browse', target='new_file', file_types=file_types)
        ]
    else:
        disable_bottom = False
        file_element = [sg.Text(textwrap.fill(f'File::{file}', 40, subsequent_indent='  '))]

        if Path(file).suffix not in excel_formats:
            disable_other = False
        else:
            disable_excel = False
            dataframes = pd.read_excel(
                file, sheet_name=None, header=None, convert_float=False,
                engine=None if _HAS_XLRD else 'openpyxl'
            )

            sheet_names = list(dataframes.keys())
            sheet_0_len = len(dataframes[sheet_names[0]].columns)

            default_inputs.update({
                'sheets': sheet_names,
                'sheet': sheet_names[0],
                'excel_columns': [f'Column {num}' for num in range(sheet_0_len)],
                'first_column': 'Column 0',
                'last_column': f'Column {sheet_0_len - 1}',
                'repeat_unit': sheet_0_len,
                'separator': '',
                'columns': ', '.join(str(num) for num in range(sheet_0_len)),
                'row_start': 0,
                'row_end': 0,
                'same_values': False,
                'total_indices': list(range(sheet_0_len)),
            })
            if (assign_column_indices
                    and any(index >= sheet_0_len for index in default_inputs['variable_indices'].values())):
                default_inputs['variable_indices'] = {key: 0 for key in default_inputs['variable_indices'].keys()}

            validations['integers'].append(
                ['repeat_unit', 'number of columns per dataset']
            )
            validations['constraints'].append(
                ['repeat_unit', 'number of columns per dataset', '> 0']
            )

        default_inputs.update({
            'initial_separator': default_inputs['separator'],
            'initial_fixed_width_file': default_inputs['fixed_width_file'],
            'initial_fixed_width_columns': default_inputs['fixed_width_columns'],
            'initial_columns': default_inputs['columns'],
            'initial_row_start': default_inputs['row_start'],
            'initial_row_end': default_inputs['row_end'],
            'initial_total_indices': default_inputs['total_indices'],
        })

    layout = [
        file_element,
        [
            sg.TabGroup([
                [sg.Tab(
                    'Other',
                    [
                        [sg.Text('Separator (eg. , or ;)', size=(20, 1)),
                        sg.Input(default_inputs['initial_separator'], key='separator',
                                disabled=disable_other, size=(5, 1))],
                        [sg.Check('Fixed-width file', default_inputs['initial_fixed_width_file'],
                                key='fixed_width_file', enable_events=True, pad=(5, (5, 0)),
                                disabled=disable_bottom)],
                        [sg.Text('    Column widths,\n     separated by commas'),
                        sg.Input(default_inputs['initial_fixed_width_columns'], size=(10, 1),
                                key='fixed_width_columns',
                                disabled=not(not disable_other and default_inputs['initial_fixed_width_file']))],
                    ], key='OTHER_TAB'
                )],
                [sg.Tab(
                    'Excel',
                    [
                        [sg.Text('Sheet to use'),
                        sg.Combo(default_inputs['sheets'], size=(17, 4), key='sheet',
                                default_value=default_inputs['sheet'], disabled=disable_excel,
                                readonly=True, enable_events=True)],
                        [sg.Text('First column '),
                        sg.Combo(default_inputs['excel_columns'], size=(17, 4),
                                key='first_col', readonly=True,
                                default_value=default_inputs['first_column'],
                                disabled=disable_excel, enable_events=True)],
                        [sg.Text('Last column '),
                        sg.Combo(default_inputs['excel_columns'], size=(17, 4), key='last_col',
                                readonly=True, default_value=default_inputs['last_column'],
                                disabled=disable_excel, enable_events=True)],
                        [sg.Text('Number of columns per dataset:'),
                        sg.Input(default_inputs['repeat_unit'], key='repeat_unit', size=(3, 1),
                                disabled=disable_excel, enable_events=True)],
                    ], key='EXCEL_TAB', background_color=sg.theme_background_color()
                )]
            ], key='-selected_tab-', tab_background_color=sg.theme_background_color()),
        ],
                [sg.Text('Columns to import,\n separated by commas',
                        tooltip='Starts at 0'),
                sg.Input(default_inputs['initial_columns'], key='columns',
                        do_not_clear=True, tooltip='Starts at 0', size=(12, 1),
                        enable_events=True, disabled=disable_bottom)],
                [sg.Text('Start row', tooltip='Starts at 0', size=(8, 1)),
                sg.Input(default_inputs['initial_row_start'], key='row_start',
                        do_not_clear=True, size=(5, 1), disabled=disable_bottom,
                        tooltip='Starts at 0')],
                [sg.Text('End row', tooltip='Counts up from bottom. Starts at 0',
                        size=(8, 1)),
                sg.Input(default_inputs['initial_row_end'], key='row_end',
                        size=(5, 1), disabled=disable_bottom,
                        tooltip='Counts up from bottom. Starts at 0')]
    ]

    if assign_column_indices:
        variable_elements = []
        for variable, index in default_inputs['variable_indices'].items():
            variable_elements.append([
                sg.Column([[sg.Text(textwrap.fill(variable, 15))]], expand_x=True),
                sg.Column([[
                    sg.Text('  Column #'),
                    sg.Combo(default_inputs['initial_total_indices'],
                            default_inputs['initial_total_indices'][index],
                            size=(3, 1), readonly=True,
                            key=f'index_{variable}', disabled=disable_bottom)
                ]], element_justification='right',)
            ])
        layout.extend([
            [sg.HorizontalSeparator()],
            [sg.Column(variable_elements, scrollable=True, vertical_scroll_only=True, expand_x=True)],
            [sg.HorizontalSeparator()]
        ])

    layout.append([
        sg.Column([[
            sg.Column([
                [sg.Check('Same options\nfor all files', default_inputs['same_values'],
                        key='same_values', disabled=disable_other,
                        visible=file is not None and Path(file).suffix not in excel_formats)]
                ]),
            sg.Column([
                [sg.Button('Test Import'),
                sg.Button('Next', bind_return_key=True, button_color=PROCEED_COLOR)]])
        ]], expand_x=True, element_justification='right', pad=(0, 0))
    ])

    window = sg.Window('Data Import', layout, finalize=True)
    if file is not None and Path(file).suffix in excel_formats:
        window['EXCEL_TAB'].select()

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            safely_close_window(window)

        elif event == 'new_file':
            if not values['new_file'] or values['new_file'] == values['file']:
                continue
            else:
                window['file'].update(values['new_file'])
                values['file'] = values['new_file']

            if Path(values['file']).suffix in excel_formats:
                window['EXCEL_TAB'].select()

                dataframes = pd.read_excel(
                    values['file'], sheet_name=None, header=None,
                    convert_float=False, engine=None if _HAS_XLRD else 'openpyxl'
                )
                sheet_names = list(dataframes.keys())
                sheet_0_len = len(dataframes[sheet_names[0]].columns)

                window['sheet'].update(values=sheet_names, value=sheet_names[0],
                                       readonly=True)
                col_list = [f'Column {num}' for num in range(sheet_0_len)]
                window['first_col'].update(values=col_list, value=col_list[0],
                                           readonly=True)
                window['last_col'].update(values=col_list, value=col_list[-1],
                                          readonly=True)
                window['repeat_unit'].update(value=sheet_0_len, disabled=False)
                window['separator'].update(value='', disabled=True)
                window['columns'].update(
                    value=', '.join(str(num) for num in range(sheet_0_len)),
                    disabled=False
                )
                window['row_start'].update(value='0', disabled=False)
                window['row_end'].update(value='0', disabled=False)
                window['same_values'].update(value=False, disabled=True)
                window['fixed_width_columns'].update(value='', disabled=True)
                window['fixed_width_file'].update(value=False, disabled=True)

                if not any('repeat_unit' in entry for entry in validations['integers']):
                    validations['integers'].append(
                        ['repeat_unit', 'number of columns per dataset']
                    )
                    validations['constraints'].append(
                        ['repeat_unit', 'number of columns per dataset', '> 0']
                    )

                for i, entry in enumerate(validations['user_inputs']):
                    if 'fixed_width_columns' in entry:
                        del validations['user_inputs'][i]
                        break

                if assign_column_indices:
                    _assign_indices(
                        window, list(range(sheet_0_len)), default_inputs['variable_indices']
                    )

            else:
                window['OTHER_TAB'].select()
                window['sheet'].update(values=[], value='', disabled=True)
                window['first_col'].update(values=[], value='', disabled=True)
                window['last_col'].update(values=[], value='', disabled=True)
                window['repeat_unit'].update(value='', disabled=True)
                window['separator'].update(value=default_inputs['separator'],
                                           disabled=False)
                window['columns'].update(value=default_inputs['columns'],
                                         disabled=False)
                window['row_start'].update(value=default_inputs['row_start'],
                                           disabled=False)
                window['row_end'].update(value=default_inputs['row_end'],
                                         disabled=False)
                window['same_values'].update(value=default_inputs['same_values'], disabled=False)
                window['fixed_width_columns'].update(
                    value=default_inputs['fixed_width_columns'],
                    disabled=not default_inputs['fixed_width_file']
                )
                window['fixed_width_file'].update(
                    value=default_inputs['fixed_width_file'], disabled=False
                )
                if default_inputs['fixed_width_file']:
                    if not any('fixed_width_columns' in entry for entry in validations['user_inputs']):
                        validations['user_inputs'].append(
                            ['fixed_width_columns', 'fixed width columns', int]
                        )
                else:
                    for i, entry in enumerate(validations['user_inputs']):
                        if 'fixed_width_columns' in entry:
                            del validations['user_inputs'][i]
                            break

                for i, entry in enumerate(validations['integers']):
                    if 'repeat_unit' in entry:
                        del validations['integers'][i]
                        break
                for i, entry in enumerate(validations['constraints']):
                    if 'repeat_unit' in entry:
                        del validations['constraints'][i]
                        break

                if assign_column_indices:
                    for variable in data_source.unique_variables:
                        window[f'index_{variable}'].update(
                            values=default_inputs['total_indices'], readonly=True,
                            set_to_index=default_inputs['variable_indices'][variable]
                        )

        elif event == 'sheet':
            window['repeat_unit'].update(value=len(dataframes[values['sheet']].columns))
            cols = [f'Column {num}' for num in range(len(dataframes[values['sheet']].columns))]
            window['first_col'].update(values=cols, value=cols[0])
            window['last_col'].update(values=cols, value=cols[-1])
            window['columns'].update(
                value=', '.join(str(i) for i in range(len(dataframes[values['sheet']].columns)))
            )

            if assign_column_indices:
                _assign_indices(
                    window, [num for num in range(len(dataframes[values['sheet']].columns))],
                    default_inputs['variable_indices']
                )

        elif event == 'fixed_width_file':
            if values['fixed_width_file']:
                window['fixed_width_columns'].update(disabled=False)
                if not any('fixed_width_columns' in entry for entry in validations['user_inputs']):
                    validations['user_inputs'].append(
                        ['fixed_width_columns', 'fixed width columns', int]
                    )
            else:
                window['fixed_width_columns'].update(value='', disabled=True)
                for i, entry in enumerate(validations['user_inputs']):
                    if 'fixed_width_columns' in entry:
                        del validations['user_inputs'][i]
                        break

        elif event in ('first_col', 'last_col'):
            first_col = int(values['first_col'].split(' ')[-1])
            last_col = int(values['last_col'].split(' ')[-1]) + 1

            if (values['repeat_unit']
                    and (last_col - first_col) < int(values['repeat_unit'])):

                new_len = last_col - first_col
                window['repeat_unit'].update(value=new_len)
                update_text = [num for num in range(new_len)]
                window['columns'].update(
                    value=', '.join(str(elem) for elem in update_text)
                )

                if assign_column_indices:
                    _assign_indices(window, update_text,
                                    default_inputs['variable_indices'])

        elif event == 'repeat_unit' and values['repeat_unit']:
            try:
                update_text = [num for num in range(int(values['repeat_unit']))]
                window['columns'].update(
                    value=', '.join(str(elem) for elem in update_text)
                )

                if assign_column_indices:
                    _assign_indices(window, update_text,
                                    default_inputs['variable_indices'])
            except ValueError:
                window['repeat_unit'].update('')
                sg.popup('Please enter an integer in "number of columns per dataset"',
                         title='Error')

        elif event == 'columns' and assign_column_indices:
            update_text = [
                entry.strip() for entry in values['columns'].split(',') if entry.strip()
            ]
            _assign_indices(window, update_text,
                            default_inputs['variable_indices'])

        elif event in ('Next', 'Test Import'):
            if file is None and values['file'] == 'Choose a file':
                sg.popup('Please choose a file', title='Error')
                continue

            elif validate_inputs(values, **validations):
                if event == 'Test Import':
                    test_file = file if file is not None else values['file']
                    window.disable()#window.hide()
                    raw_data_import(values, test_file)
                    window.enable()#window.un_hide()
                    window.force_focus()
                else:
                    break

    window.close()
    del window

    if assign_column_indices:
        # converts column numbers back to indices
        for key in data_source.unique_variables:
            values[f'index_{key}'] = values['columns'].index(int(values[f'index_{key}']))

    return values


def _assign_indices(window, columns, variables):
    """
    Updates the indices for each variable based on the column length.

    If there are more variables than available columns, the additional
    variables will all be assigned to the last value in columns.

    Parameters
    ----------
    window : sg.Window
        The PySimpleGUI window to update.
    columns : list or tuple
        A list or tuple of column numbers.
    variables : dict
        A dictionary with variable names as keys and their target indices
        as values.

    Notes
    -----
    The updated element in the window is a sg.Combo element.

    """

    for variable in variables:
        if variables[variable] < len(columns):
            index = variables[variable]
        else:
            index = len(columns) - 1

        window[f'index_{variable}'].update(
            values=columns, set_to_index=index, readonly=True
        )


def _manual_file_selector(d_index, s_index, selected_files=None, frame_title='', **kwargs):
    """
    Creates the layout to select files for a single sample in a dataset.

    Parameters
    ----------
    d_index : int
        The dataset index. Used to create the keys for the elements.
    s_index : int
        The sample index for this sample. Used to create the keys for the elements.
    selected_files : list(str), optional
        The previously selected files for this sample. Should be None or an empty
        list if no files were previously selected.
    frame_title : str, optional
        The title of the frame element.
    **kwargs
        Any additional keyword argmuments to pass to sg.Frame.

    Returns
    -------
    sg.Frame
        The Frame element containing all of the internal elements for selecting
        files for this sample.

    """

    files = selected_files if selected_files is not None else []

    layout = [
        [sg.T(f'Files ({len(files)} total, 0 selected)        ',
              pad=(5, 0), key=f'sample_summary_{d_index}_{s_index}')],
        [
            sg.Column([[
                sg.Listbox(files, select_mode='multiple', pad=(0, 0), size=(40, 5),
                           key=f'listbox_{d_index}_{s_index}', enable_events=True)
            ]], pad=((5, 0), (0, 5))),
            sg.Column([
                [sg.Button('Add Files', key=f'add_files_{d_index}_{s_index}', pad=(0, 0))],
                [sg.Button('Del  Files', key=f'remove_files_{d_index}_{s_index}', pad=(0, 0))]
            ], pad=((0, 5), (0, 5)))
        ]
    ]

    return sg.Frame(frame_title, layout, title_location=sg.TITLE_LOCATION_TOP, **kwargs)


def _manual_file_partial_event_loop(window, event, file_types):
    """
    A partial event loop for manual file selection that updates the file listbox.

    Parameters
    ----------
    window : sg.Window
        The window containing the elements.
    event : str
        The event from the window. Relevant events for this function
        start with 'listbox_', 'add_files_', or 'remove_files_'.
    file_types : tuple(tuple(str, str))
        A tuple of the file types to display in the sg.popup_get_file popup.

    Notes
    -----
    All changes are done to the window inplace.

    """

    index = '_'.join(event.split('_')[-2:])

    if event.startswith('listbox_'):
        selected = len(window[event].get_indexes())
        total = len(window[f'listbox_{index}'].get_list_values())
        window[f'sample_summary_{index}'].update(f'Files ({total} total, {selected} selected)')

    elif event.startswith('add_files_'):
        files = sg.popup_get_file('', multiple_files=True, no_window=True, file_types=file_types)
        if files:
            current_values = window[f'listbox_{index}'].get_list_values()
            current_values.extend(files)
            window[f'listbox_{index}'].update(values=current_values)
            window[f'sample_summary_{index}'].update(
                f'Files ({len(current_values)} total, 0 selected)'
            )

    elif event.startswith('remove_files_'):
        removed_indices = window[f'listbox_{index}'].get_indexes()
        current_values = window[f'listbox_{index}'].get_list_values()
        new_values = [
            value for idx, value in enumerate(current_values) if idx not in removed_indices
        ]
        window[f'listbox_{index}'].update(values=new_values)
        window[f'sample_summary_{index}'].update(f'Files ({len(new_values)} total, 0 selected)')


def open_multiple_files():
    """
    Creates a prompt to open multiple files and add their contents to a dataframe.

    Returns
    -------
    dataframes : list
        A list of dataframes containing the imported data from the selected
        files.

    """

    file_types = [
        ('All Files', '*.*'), ('CSV', '*.csv'),
        ('Text Files', '*.txt'), ('Excel Workbook', '*.xlsx'),
        ('Excel Macro-Enabled Workbook', '*.xlsm')
    ]
    if _HAS_XLRD:
        file_types.append(('Excel 97-2003 Workbook', '*.xls'))

    window = sg.Window(
        'Select Files',
        [[_manual_file_selector(0, 0)],
         [sg.Button('Next', button_color=PROCEED_COLOR, bind_return_key=True)]]
    )
    while True:
        event = window.read()[0]

        if event == sg.WIN_CLOSED:
            safely_close_window(window)

        elif event.startswith(('listbox_', 'add_files_', 'remove_files_')):
            _manual_file_partial_event_loop(window, event, file_types)

        elif event == 'Next':
            files = window['listbox_0_0'].get_list_values()
            if files:
                break
            else:
                sg.popup('Must add at least one file.\n', title='Error')

    window.close()
    del window

    dataframes = []
    import_values = {}
    for file in files:
        try:
            if (not import_values.get('same_values', False)
                    or Path(file).suffix in ('.xlsx', '.xlsm', '.xls')):
                import_values = select_file_gui(file=file, previous_inputs=import_values)
            dataframes.extend(
                raw_data_import(import_values, file, False)
            )
        except WindowCloseError:
            break # exits as soon as user exits

    return dataframes
