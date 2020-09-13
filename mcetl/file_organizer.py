# -*- coding: utf-8 -*-
"""Provides GUIs to find files containing combinations of keywords and move files.

#TODO add an option to select each file individually

@author: Donald Erb
Created on Mon Sep  2 22:08:12 2019

"""


import itertools
from pathlib import Path
import shutil

import PySimpleGUI as sg

from .utils import safely_close_window, validate_inputs, PROCEED_COLOR


__all__ = ['file_finder', 'file_mover']

_HELP_TEXT = (
    'For example, consider the following files:\n\n'
    '    Ti-10Ni-700, Ti-20Ni-700, Ti-10Ni-800, Ti-20Ni-800,\n'
    '    Ti-10Fe-700, Ti-20Fe-700, Ti-10Fe-800, Ti-20Fe-800,\n'
    '    Co-10Ni-700, Co-20Ni-700, Co-10Ni-800, Co-20Ni-800,\n'
    '    Co-10Fe-700, Co-20Fe-700, Co-10Fe-800, Co-20Fe-800\n\n'
    'If only the files for the 700 samples were wanted, then one possible search could be \n'
    'two main keywords ("Ti, 700" and "Co, 700") and four secondary \n'
    'keywords ("10Ni", "20Ni", "10Fe", "20Fe").\n\nLeave all entries blank to find all '
    'files with the given file extension under the specified folder.\n'
)


def _prepare_for_search(input_str):
    """
    Ensures that no consecutive stars ('*') are in the search term to work with Path.rglob.

    Parameters
    ----------
    input_str : str
        A string that will be used for file searching.

    Returns
    -------
    output_str : str
        The input string containing no consecutive stars ('*').

    """

    output_list = [input_str[0]]
    output_list.extend(
        [letter for i, letter in enumerate(input_str[1:]) if letter != '*' or input_str[i] != '*']
    )
    output_str = ''.join(output_list)

    return output_str


def _generate_num_keyword_window(
        file_directory=None, keyword_1=None, keyword_2=None, file_type=None,
        num_files=None, previous_inputs=None, location=(None, None)):
    """
    Creates a Window to select the number of keywords and other file search parameters.

    Parameters
    ----------
    file_directory : str
        String for the topmost folder under which all files are searched.
    keyword_1 : str, tuple, or list
        String or list of strings for the main keyword.
    keyword_2 : str, tuple, or list
        String or list of strings for the secondary keyword.
    file_type : str
        The file extension that is being searched, eg. csv, txt, pdf.
    num_files: int
        The maximum number of files to find for each search term.
    previous_inputs : dict
        A dictionary containing the values from a previous run of this function,
        used to regenerate the layout.
    location : tuple
        The location to place the window.

    Returns
    -------
    sg.Window
        The PySimpleGUI window for the selection of the number of keywords,
        the file type, and the search directory.

    """

    default_inputs = {
        'num_keyword_1': len(keyword_1) if keyword_1 is not None else '',
        'num_keyword_2': len(keyword_2) if keyword_2 is not None else '',
        'file_type': file_type.replace('.', '') if file_type is not None else '',
        'num_files': num_files if num_files is not None else 1,
        'folder' : file_directory if file_directory is not None else '',
        'folder_initial': file_directory
    }

    previous_inputs = previous_inputs if previous_inputs is not None else {}
    default_inputs.update(previous_inputs)

    layout = [
        [sg.Text('Choose the topmost folder for searching:', size=(35, 1))],
        [sg.Input(default_inputs['folder'], key='folder', disabled=True, 
                  size=(26, 1)),
         sg.FolderBrowse(key='search', target='folder',
                         initial_folder=default_inputs['folder_initial'])],
        [sg.Text('')],            
        [sg.Text('Number of main keywords:', size=(28, 1)),
         sg.Input(key='num_keyword_1', do_not_clear=True, size=(5, 1), focus=True,
                  default_text=default_inputs['num_keyword_1'])],
        [sg.Text('Number of secondary keywords:', size=(28, 1)),
         sg.Input(key='num_keyword_2', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['num_keyword_2'])],
        [sg.Text('')],
        [sg.Text('File extension (eg. csv or txt):', size=(28, 1)),
         sg.Input(key='file_type', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['file_type'])],
        [sg.Text('Maximum number of files\nper search term:', size=(28, 2)),
         sg.Input(key='num_files', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['num_files'])],
        [sg.Text('')],
        [sg.Button('Help'),
         sg.Button('Next', bind_return_key=True, button_color=PROCEED_COLOR)]
    ]

    return sg.Window('Search Criteria', layout, location=location)


def _get_num_keywords(
        file_directory=None, keyword_1=None, keyword_2=None, file_type=None,
        num_files=None, previous_inputs=None, location=(None, None)):
    """
    Launches a GUI to get the number of keywords and other file search parameters.

    Parameters
    ----------
    file_directory : str
        String for the topmost folder under which all files are searched.
    keyword_1 : str, tuple, or list
        String or list of strings for the main keyword.
    keyword_2 : str, tuple, or list
        String or list of strings for the secondary keyword.
    file_type : str
        The file extension that is being searched, eg. csv, txt, pdf.
    num_files: int
        The maximum number of files to find for each search term.
    previous_inputs : dict
        A dictionary containing the values from a previous run of this function,
        used to regenerate the layout.
    location : tuple
        The location to place the window.

    Returns
    -------
    file_directory : Path
        The Path for the topmost folder for searching.
    num_keyword_1 : int
        The number of keywords for keyword_1.
    num_keyword_2 : int
        The number of keywords for keyword_2.
    file_type : str
        The file extension to search for.
    values : dict
        The values needed to regenerate the layout with the final selected fields.

    """

    window = _generate_num_keyword_window(
        file_directory, keyword_1, keyword_2, file_type,
        num_files, previous_inputs, location
    )

    validations = {
        'strings': [
            ['folder', 'topmost folder'],
            ['file_type', 'file extension']
        ],
        'integers': [
            ['num_keyword_1', 'number of main keywords'],
            ['num_keyword_2', 'number of secondary keywords'],
            ['num_files', 'maximum number of files per search term']
        ]
    }

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            safely_close_window(window)

        elif event == 'Help':
            sg.popup(_HELP_TEXT, title='Help')

        elif event == 'Next':
            if validate_inputs(values, **validations):
                if int(values['num_keyword_1']) > 0 and int(values['num_keyword_2']) > 0:
                    if int(values['num_files']) > 0:
                        break
                    else:
                        sg.popup('Maximum number of files must be > 0.\n',
                                 title='Error')
                else:
                    sg.popup('Number of keywords must be > 0.\n', title='Error')

    window.close()
    del window

    num_keyword_1 = int(values['num_keyword_1'])
    num_keyword_2 = int(values['num_keyword_2'])

    return num_keyword_1, num_keyword_2, values


def _generate_keyword_window(
        num_keyword_1, num_keyword_2, keyword_1=None, keyword_2=None,
        previous_inputs=None, location=(None, None)):
    """
    Creates a Window to enter the terms for each keyword.

    Parameters
    ----------
    num_keyword_1 : int
        The number of keywords for keyword_1.
    num_keyword_2 : int
        The number of keywords for keyword_2.
    keyword_1 : tuple or list
        Tuple or list of strings for the main keyword.
    keyword_2 : tuple or list
        Tuple or list of strings for the secondary keyword.
    previous_inputs : dict
        A dictionary containing the values from a previous run of this function,
        used to regenerate the layout.
    location : tuple
        The location to place the window.

    Returns
    -------
    sg.Window
        The PySimpleGUI window for the selection of the keyword terms.

    """

    # default values for keywords
    if keyword_1 is None:
        if num_keyword_1 == 0:
            default_keyword_1 = ['']
        else:
            default_keyword_1 = [''] * num_keyword_1
    else:
        default_keyword_1 = [keyword for keyword in keyword_1]
        # in case num_keyword_1 is greater than the number of user inputs for keyword 1
        default_keyword_1.extend(['' for i in range(num_keyword_1 - len(keyword_1))])

    if keyword_2 is None:
        if num_keyword_2 == 0:
            default_keyword_2 = ['']
        else:
            default_keyword_2 = [''] * num_keyword_2
    else:
        default_keyword_2 = [keyword for keyword in keyword_2]
        default_keyword_2.extend(
            ['' for i in range(num_keyword_2 - len(keyword_2))]
        )

    default_options = {f'keyword_1_{i}': kw for i, kw in enumerate(default_keyword_1)}
    default_options.update({
        f'keyword_2_{i}': kw for i, kw in enumerate(default_keyword_2)
    })

    previous_inputs = previous_inputs if previous_inputs is not None else {}
    default_inputs = dict(default_options, **previous_inputs)

    keyword_1_inputs = [
        [sg.Text(f'    entry {i+1}'),
         sg.Input(default_inputs[f'keyword_1_{i}'], key=f'keyword_1_{i}',
                  do_not_clear=True, size=(20, 1))]
        for i in range(num_keyword_1)]
    keyword_2_inputs = [
        [sg.Text(f'    entry {i+1}'),
         sg.Input(default_inputs[f'keyword_2_{i}'], key=f'keyword_2_{i}',
                  do_not_clear=True, size=(20, 1))]
        for i in range(num_keyword_2)]

    layout = [
        [sg.Text(('Entries for main keywords, separated\nby commas if'
                  ' using more than one term:'))],
        *keyword_1_inputs,
        [sg.Text(('\nEntries for secondary keywords, separated\nby'
                  ' commas if using more than one term:'))],
        *keyword_2_inputs,
        [sg.Text("")],
        [sg.Button('Back'),
         sg.Button('Help'),
         sg.Button('Submit', bind_return_key=True, button_color=PROCEED_COLOR)]
    ]

    return sg.Window('Keyword Selection', layout, location=location)


def _get_keywords(
        num_keyword_1, num_keyword_2, keyword_1=None,
        keyword_2=None, num_kw_values=None):
    """Launches the GUI to enter the terms for each keyword.

    Parameters
    ----------
    num_keyword_1 : int
        The number of keywords for keyword_1.
    num_keyword_2 : int
        The number of keywords for keyword_2.
    keyword_1 : tuple or list
        Tuple or list of strings for the main keyword.
    keyword_2 : tuple or list
        Tuple or list of strings for the secondary keyword.
    num_kw_values : dict
        A dictionary containing the values to recreate the layout for the
        number of keywords window through _generate_num_keyword_window.

    Returns
    -------
    file_directory : str
        String for the topmost folder under which all files are searched.
    keyword_1 : str, tuple, or list
        String or list of strings for the main keyword.
    keyword_2 : str, tuple, or list
        String or list of strings for the secondary keyword.
    file_type : str
        The file extension that is being searched, eg. csv, txt, pdf.
    num_files: int
        The maximum number of files to find for each search term.

    """

    window = _generate_keyword_window(num_keyword_1, num_keyword_2,
                                      keyword_1, keyword_2)
    location = (None, None)
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            safely_close_window(window)

        elif event == 'Help':
            sg.popup(_HELP_TEXT, title='Help')

        elif event == 'Back':
            location = window.current_location()
            window.close()
            window = None
            num_keyword_1, num_keyword_2, num_kw_values = _get_num_keywords(
                previous_inputs=num_kw_values, location=location
            )
            window = _generate_keyword_window(
                num_keyword_1, num_keyword_2, keyword_1, keyword_2,
                values, location
            )

        else:
            break

    window.close()
    del window

    kw_1_tmp = [values[f'keyword_1_{i}'].split(',') for i in range(num_keyword_1)]
    kw_2_tmp = [values[f'keyword_2_{i}'].split(',') for i in range(num_keyword_2)]
    # deletes repeated entries to reduce the permutations and search time
    keyword_1 = [
        set(entry.strip() for entry in kw_entries if entry) for kw_entries in kw_1_tmp
    ]
    keyword_2 = [
        set(entry.strip() for entry in kw_entries if entry) for kw_entries in kw_2_tmp
    ]

    file_directory = Path(num_kw_values['folder'])
    # in case the extension is given as something like .csv instead of csv
    file_type = num_kw_values['file_type'].replace('.', '')
    num_files = int(num_kw_values['num_files'])

    return file_directory, keyword_1, keyword_2, file_type, num_files


def file_finder(file_directory=None, keyword_1=None, keyword_2=None,
                file_type=None, num_files=None):
    """
    Finds files that match the given keywords and file type using a GUI.

    Parameters
    ----------
    file_directory : str
        String for the topmost folder under which all files are searched.
    keyword_1 : str, tuple, or list
        String or list of strings for the main keyword.
    keyword_2 : str, tuple, or list
        String or list of strings for the secondary keyword.
    file_type : str
        The file extension that is being searched, eg. csv, txt, pdf.
    num_files : int
        The maximum number of files to be associated with each search term.

    Returns
    -------
    output_list : list
        A nested list of lists containing the file locations as strings
        for the files that matched the search term. len(output_list)
        is equal to the number of main keywords (len(keyword_1)),
        len(output_list[0]) is equal to the number of secondary keywords
        (len(keyword_2)), and len(outupt_list[0][0]) is equal to the num_files.

    Notes
    -----
    Leaving a blank string for all keywords will search for all files with
    the given file extension under the parent folder.

    If using more than one term for a keyword, input the terms together as
    one string, separated by a comma. For example, if terms for keyword_1
    are [['a', 'b'], ['c']], where ['a', 'b'] is one keyword and ['c'] is the other,
    then input ['a, b', 'c'] for keyword_1.

    """

    # Ensures the keywords are input as lists
    if keyword_1 is not None and not isinstance(keyword_1, (list, tuple)):
        keyword_1 = [keyword_1]
    if keyword_2 is not None and not isinstance(keyword_2, (list, tuple)):
        keyword_2 = [keyword_2]

    num_keyword_1, num_keyword_2, num_kw_values = _get_num_keywords(
        file_directory, keyword_1, keyword_2, file_type, num_files
    )
    
    file_directory, keyword_1, keyword_2, file_type, num_files = _get_keywords(
        num_keyword_1, num_keyword_2, keyword_1, keyword_2, num_kw_values
    )

    # File finding
    found_files = [[[] for j in range(len(keyword_2))] for i in range(len(keyword_1))]
    window_location = (None, None)
    for j, keyword1 in enumerate(keyword_1):
        for k, keyword2 in enumerate(keyword_2):
            # Tries each variation of (keyword1, keyword2) and collects all files that fit
            keywords = [*keyword1, *keyword2]
            permutations = ['*'.join(p) for p in itertools.permutations(keywords) if p]
            for permutation in permutations:
                search_term = _prepare_for_search(f'*{permutation}*.{file_type}')
                found_files[j][k].extend(file_directory.rglob(search_term))

            # Relaxes the search criteria and tries to find the file using only
            # one keyword if not enough files were found using the original two keywords
            if len(found_files[j][k]) < num_files:

                keywords = [*keyword1]
                permutations = ['*'.join(p) for p in itertools.permutations(keywords)]

                for permutation in permutations:
                    search_term = _prepare_for_search(f'*{permutation}*.{file_type}')
                    found_files[j][k].extend(file_directory.rglob(search_term))

                keywords = [*keyword2]
                permutations = ['*'.join(p) for p in itertools.permutations(keywords)]

                for permutation in permutations:
                    search_term = _prepare_for_search(f'*{permutation}*.{file_type}')
                    found_files[j][k].extend(file_directory.rglob(search_term))

                # Relaxes the search criteria to match any of the keywords
                if len(found_files[j][k]) < num_files:
                    for keyword in [*keyword1, *keyword2]:
                        search_term = _prepare_for_search(f'*{keyword}*.{file_type}')
                        found_files[j][k].extend(file_directory.rglob(search_term))

                    # Relaxes the search criteria to just include the file extension
                    # if not enough files have been found yet
                    if len(found_files[j][k]) < num_files:
                        found_files[j][k].extend(file_directory.rglob(f'*.{file_type}'))

                        # Relaxes the search criteria completely and includes all files in the folder
                        if len(found_files[j][k]) < num_files:
                            found_files[j][k].extend(file_directory.rglob('*.*'))

            # Converts the list to a set to remove duplicates and then converts back using sorted
            found_files[j][k] = [str(file) for file in sorted(set(found_files[j][k]))]

            if len(found_files[j][k]) <= num_files:
                continue
            else:
                files = [
                    file.replace(str(file_directory), '') for file in found_files[j][k]
                ]
                kw1_keywords = ', '.join(kw for kw in keyword1)
                kw2_keywords = ', '.join(kw for kw in keyword2)
                layout = [
                    [sg.Text('Select the file(s).')],
                    [sg.Text((f'Current keywords:\n    Main keyword: {kw1_keywords}'
                              f'\n    Secondary keyword: {kw2_keywords}'))],
                    [sg.Listbox(key='listbox', values=files,
                                size=(max(len(str(file)) for file in files) + 3, 8),
                                select_mode='multiple', bind_return_key=True)],
                    [sg.Button('Submit', button_color=PROCEED_COLOR)]
                ]

                window = sg.Window('Found Files', layout, location=window_location)
                while True:
                    event, values = window.read()
                    if event == sg.WIN_CLOSED:
                        safely_close_window(window)

                    elif not values['listbox']:
                        sg.popup('Please select a file.')

                    elif len(values['listbox']) != num_files:
                        sg.popup(f'Please select {num_files} file(s).')

                    else:
                        window_location = window.current_location()
                        break

                window.close()
                window = None

                found_files[j][k] = [
                    f'{file_directory}{file}' for file in values['listbox']
                ]

    return found_files


def file_mover(file_list, new_folder=None, skip_same_files=True):
    """
    Takes in a list of file paths and moves a copy of each file to the new folder.

    Parameters
    ----------
    file_list : list, tuple, or str
        A list of strings corresponding to file paths, all of which will
        have their copies moved.
    new_folder : str or Path
        The folder to move all of copies of the files in the file_list into.
    skip_same_files : bool
        If True, will not move any copied files if they already
        exist in the destination folder; if False, will rename the
        copied file and move it to the destination folder.

    Returns
    -------
    new_folder : str
        The string of the destination folder location.

    """

    if not isinstance(file_list, (list, tuple)):
        file_list = [file_list]

    if not new_folder:
        layout = [
            [sg.Text('Choose the folder to move files to:', size=(35, 1))],
            [sg.InputText('', disabled=True),
             sg.FolderBrowse(key='folder')],
            [sg.Button('Submit', bind_return_key=True,
                       button_color=PROCEED_COLOR)]
        ]

        window = sg.Window('Folder Selection', layout)
        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                safely_close_window(window)

            elif values['folder'] == '':
                sg.popup('Please select a folder.')

            else:
                break

        window.close()
        del window

        new_folder = Path(values['folder'])

    elif isinstance(new_folder, str):
        new_folder = Path(new_folder)

    new_folder.mkdir(parents=True, exist_ok=True)

    for files in file_list:
        if not isinstance(files, (list, tuple)):
            files = [files]

        for file in files:
            file_path = Path(file)
            file_base = file_path.name

            if not new_folder.joinpath(file_base).exists():
                shutil.copy(file, new_folder)

            elif not skip_same_files:
                file_name = file_path.stem
                extension = file_path.suffix
                i = 1
                new_file_name = f'{file_name}_COPY_{i}{extension}'
                while new_folder.joinpath(new_file_name).exists():
                    i += 1
                    new_file_name = f'{file_name}_COPY_{i}{extension}'

                shutil.copy(file, new_folder.joinpath(new_file_name))

    return str(new_folder)
