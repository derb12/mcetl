# -*- coding: utf-8 -*-
"""Provides GUIs to find files containing combinations of keywords and move files.

#TODO add an option to select each file individually

@author: Donald Erb
Created on Sep 2, 2019

"""


import itertools
from pathlib import Path
import shutil

import PySimpleGUI as sg

from .utils import safely_close_window, validate_inputs, PROCEED_COLOR


__all__ = ['file_finder', 'file_mover']


def _prepare_for_search(input_str):
    """
    Ensures that no consecutive stars ('*') are in the search term to work with Path.rglob.

    Parameters
    ----------
    input_str : str
        A string that will be used for file searching.

    Returns
    -------
    str
        The input string containing no consecutive stars ('*').

    """

    output_list = [input_str[0]]
    output_list.extend(
        [letter for i, letter in enumerate(input_str[1:]) if letter != '*' or input_str[i] != '*']
    )

    return ''.join(output_list)


def _generate_num_keyword_window(file_directory=None, file_type=None, num_files=None,
                                 previous_inputs=None, location=(None, None)):
    """
    Creates a Window to select the number of keywords and other file search parameters.

    Parameters
    ----------
    file_directory : str
        String for the topmost folder under which all files are searched.
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
        'num_datasets': '',
        'file_type': file_type.replace('.', '') if file_type is not None else '',
        'min_files': num_files if num_files is not None else 1,
        'max_files': num_files if num_files is not None else 1,
        'folder' : file_directory if file_directory is not None else '',
        'folder_initial': file_directory
    }

    if previous_inputs is not None:
        default_inputs.update(previous_inputs)

    layout = [
        [sg.Text('Choose the topmost folder for searching:', size=(35, 1))],
        [sg.Input(default_inputs['folder'], key='folder', disabled=True,
                  size=(26, 1)),
         sg.FolderBrowse(key='search', target='folder',
                         initial_folder=default_inputs['folder_initial'])],
        [sg.Text('Number of datasets:', size=(28, 1)),
         sg.Input(key='num_datasets', do_not_clear=True, size=(5, 1), focus=True,
                  default_text=default_inputs['num_datasets'])],
        [sg.Text('File extension (eg. csv or txt):', size=(28, 1)),
         sg.Input(key='file_type', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['file_type'])],
        [sg.Text('Number of files per search term:')],
        [sg.Text('    Minimum:', size=(14, 1)),
         sg.Input(key='min_files', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['min_files'])],
        [sg.Text('    Maximum:', size=(14, 1)),
         sg.Input(key='max_files', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['max_files'])],
        [sg.Text('')],
        [sg.Button('Help'),
         sg.Button('Next', bind_return_key=True, button_color=PROCEED_COLOR)]
    ]

    return sg.Window('Search Criteria', layout, location=location)


def _get_num_keywords(file_directory=None, file_type=None, num_files=None,
                      previous_inputs=None, location=(None, None)):
    """
    Launches a GUI to get the number of keywords and other file search parameters.

    Parameters
    ----------
    file_directory : str
        String for the topmost folder under which all files are searched.
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
    values : dict
        The values needed to regenerate the layout with the final selected fields.

    """

    window = _generate_num_keyword_window(
        file_directory, file_type, num_files, previous_inputs, location
    )

    validations = {
        'strings': [
            ['folder', 'topmost folder'],
            ['file_type', 'file extension']
        ],
        'integers': [
            ['num_datasets', 'number of datasets'],
            ['min_files', 'mininum number of files per search term'],
            ['max_files', 'maximum number of files per search term']
        ],
        'constraints' : [
            ['num_datasets', 'number of datasets', '> 0'],
            ['min_files', 'mininum files', '> 0'],
            ['max_files', 'maximum files', '> 0']
        ]
    }

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            safely_close_window(window)

        elif event == 'Help':
            sg.popup(
                ('All folders and files under the topmost folder will be searched.\n\n'
                 'The number of datasets is equal to the number of sheets '
                 'to create in Excel, if writing to Excel.\n'),
                title='Help')

        elif event == 'Next':
            if validate_inputs(values, **validations):
                if values['min_files'] > values['max_files']:
                    sg.popup(
                        'Minimum files must be less than or equal to maximum files.\n',
                        title='Error'
                    )
                else:
                    break

    window.close()
    del window

    return values


def _generate_keyword_window(num_datasets, previous_inputs=None, location=(None, None)):
    """
    Creates a Window to enter the terms for each keyword.

    Parameters
    ----------
    num_datasets : int
        The number of datasets.
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

    default_inputs = {f'shared_keyword_{i}': '' for i in range(num_datasets)}
    default_inputs.update({f'unique_keyword_{i}': '' for i in range(num_datasets)})

    if previous_inputs is not None:
        default_inputs.update(previous_inputs)

    dataset_inputs = []
    for i in range(num_datasets):
        dataset_inputs.extend([
            [sg.Text(f'Dataset {i+1} (search terms:'),
             sg.Text(f'{len(default_inputs[f"unique_keyword_{i}"].split(";"))})',
                     key=f'num_terms_{i}')],
            [sg.Text('  Shared keyword(s):', size=(18, 1)),
             sg.Input(default_inputs[f'shared_keyword_{i}'],
                      key=f'shared_keyword_{i}', size=(20, 1))],
            [sg.Text('  Unique keyword(s):', size=(18, 1)),
             sg.Input(default_inputs[f'unique_keyword_{i}'], size=(20, 1),
                      key=f'unique_keyword_{i}', enable_events=True)],
            [sg.Text('')]
        ])

    layout = [
        [sg.Frame('Search Terms',
                  [[sg.Column(dataset_inputs, scrollable=True,
                              vertical_scroll_only=True)]])],
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Help'),
         sg.Button('Submit', bind_return_key=True, button_color=PROCEED_COLOR)]
    ]

    return sg.Window('Keyword Selection', layout, location=location)


def _get_keywords(num_keyword_values):
    """
    Launches the GUI to enter the terms for each keyword.

    Parameters
    ----------
    num_keyword_values : dict
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

    location = (None, None)
    old_text = ''
    window = _generate_keyword_window(num_keyword_values['num_datasets'])
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            safely_close_window(window)

        elif event == 'Help':
            sg.popup(
                ('Shared keywords are repeated for each search term in a dataset, '
                 'while unique keywords are used once.\n\n'
                 'Separate terms within keywords using "," and separate each unique '
                 'keyword using ";".\n\nFor example, consider the following files:\n\n'
                 '    Ti-10Ni-700, Ti-20Ni-700, Ti-10Ni-800, Ti-20Ni-800,\n'
                 '    Ti-10Fe-700, Ti-20Fe-700, Ti-10Fe-800, Ti-20Fe-800,\n'
                 '    Co-10Ni-700, Co-20Ni-700, Co-10Ni-800, Co-20Ni-800,\n'
                 '    Co-10Fe-700, Co-20Fe-700, Co-10Fe-800, Co-20Fe-800\n\n'
                 'If only the files for the Ti-700 samples were wanted, then '
                 'one possible search could be \n a shared keyword of "ti, 700"'
                 ' and unique keywords "10, ni; 20, ni; 30, ni; 10, fe; 20, fe; 30, fe".\n\n'
                 'The six resulting search terms would be:\n    "ti, 700, 10, ni", '
                 '"ti, 700, 20, ni", "ti, 700, 30, ni", "ti, 700, 10, fe", "ti, 700, 20, fe", '
                 '"ti, 700, 30, fe".\n\nLeave keyword(s) blank to find all '
                 'files with the given file extension under the specified folder.\n'),
                title='Help')

        elif event == 'Back':
            location = window.current_location()
            window.close()
            window = None
            num_keyword_values = _get_num_keywords(
                previous_inputs=num_keyword_values, location=location
            )
            window = _generate_keyword_window(
                num_keyword_values['num_datasets'], values, location
            )

        elif 'unique_keyword' in event:
            max_index = max(int(key.split('_')[-1]) for key in values if key.startswith('unique'))
            if int(event.split('_')[-1]) == 0:
                for i in range(1, max_index + 1):
                    if values[f'unique_keyword_{i}'] == old_text:
                        window[f'unique_keyword_{i}'].update(values[event])
                old_text = values[event]

            for i in range(max_index + 1):
                window[f'num_terms_{i}'].update(
                    f"{len(window[f'unique_keyword_{i}'].get().split(';'))})"
                )

        elif event == 'Submit':
            break

    window.close()
    del window

    shared_keywords = []
    unique_keywords = []
    for i in range(num_keyword_values['num_datasets']):
        # deletes repeated entries to reduce the permutations and search time
        shared_keywords.append(
            set(entry.strip() for entry in values[f'shared_keyword_{i}'].split(',') if entry)
        )

        kw_2_tmp = [entry.strip() for entry in values[f'unique_keyword_{i}'].split(';')]
        unique_keywords.append([
            set(entry.strip() for entry in entries.split(',') if entry) for entries in kw_2_tmp
        ])

    file_directory = Path(num_keyword_values['folder'])
    file_type = num_keyword_values['file_type'].replace('.', '')
    min_files = num_keyword_values['min_files']
    max_files = num_keyword_values['max_files']

    return file_directory, shared_keywords, unique_keywords, file_type, min_files, max_files


def file_finder(file_directory=None, file_type=None, num_files=None):
    """
    Finds files that match the given keywords and file type using a GUI.

    Parameters
    ----------
    file_directory : str
        String for the topmost folder under which all files are searched.
    file_type : str
        The file extension that is being searched, eg. csv, txt, pdf.
    num_files : int
        The default maximum and minimum number of files to be associated with
        each search term.

    Returns
    -------
    output_list : list
        A nested list of lists containing the file locations as strings
        for the files that matched the search term. len(output_list)
        is equal to the number of datasets, len(output_list[i]) is equal
        to the number of unique keywords for dataset i, and len(outupt_list[i][j])
        is equal to the number of files for dataset i and unique keyword j.

    """

    num_keyword_values = _get_num_keywords(file_directory, file_type, num_files)

    (file_directory, shared_keywords, unique_keywords,
     file_type, min_files, max_files) = _get_keywords(num_keyword_values)

    window_location = (None, None)
    found_files = [[[] for j in range(len(unique_keywords[i]))] for i in range(len(shared_keywords))]
    for i, keyword1 in enumerate(shared_keywords):
        for j, keyword2 in enumerate(unique_keywords[i]):
            # Tries each variation of (keyword1, keyword2) and collects all files that fit
            keywords = [*keyword1, *keyword2]
            permutations = ['*'.join(p) for p in itertools.permutations(keywords) if p]
            for permutation in permutations:
                search_term = _prepare_for_search(f'*{permutation}*.{file_type}')
                found_files[i][j].extend(file_directory.rglob(search_term))

            # Relaxes the search criteria and tries to find the file using only
            # one keyword if not enough files were found using the original two keywords
            if len(found_files[i][j]) < min_files:

                keywords = [*keyword1]
                permutations = ['*'.join(p) for p in itertools.permutations(keywords)]

                for permutation in permutations:
                    search_term = _prepare_for_search(f'*{permutation}*.{file_type}')
                    found_files[i][j].extend(file_directory.rglob(search_term))

                keywords = [*keyword2]
                permutations = ['*'.join(p) for p in itertools.permutations(keywords)]

                for permutation in permutations:
                    search_term = _prepare_for_search(f'*{permutation}*.{file_type}')
                    found_files[i][j].extend(file_directory.rglob(search_term))

                # Relaxes the search criteria to match any of the keywords
                if len(found_files[i][j]) < min_files:
                    for keyword in [*keyword1, *keyword2]:
                        search_term = _prepare_for_search(f'*{keyword}*.{file_type}')
                        found_files[i][j].extend(file_directory.rglob(search_term))

                    # Relaxes the search criteria to just include the file extension
                    # if not enough files have been found yet
                    if len(found_files[i][j]) < min_files:
                        found_files[i][j].extend(file_directory.rglob(f'*.{file_type}'))

                        # Relaxes the search criteria completely and includes all files in the folder
                        if len(found_files[i][j]) < min_files:
                            found_files[i][j].extend(file_directory.rglob('*.*'))

            # Converts the list to a set to remove duplicates and then converts back using sorted
            found_files[i][j] = [str(file) for file in sorted(set(found_files[i][j]))]

            if len(found_files[i][j]) >= min_files and len(found_files[i][j]) <= max_files:
                continue
            else:
                files = [
                    file.replace(str(file_directory), '') for file in found_files[i][j]
                ]
                layout = [
                    [sg.Text('Select the file(s).')],
                    [sg.Text(('Current search term:\n'
                              f'    "{", ".join((*keyword1, *keyword2))}"'))],
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
                    elif len(values['listbox']) < min_files:
                        sg.popup(f'Please select at least {min_files} file(s).\n',
                                 title='Error')
                    elif len(values['listbox']) > max_files:
                        sg.popup(f'Please select no more than {max_files} file(s).\n',
                                 title='Error')
                    else:
                        window_location = window.current_location()
                        break

                window.close()
                window = None

                found_files[i][j] = [
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
