# -*- coding: utf-8 -*-
"""GUIs to plot data using various plot layouts and save the resulting figures.

@author: Donald Erb
Created on Jun 28, 2020

Attributes
----------
COLORS : tuple(str)
    A tuple with values that are used in GUIs to select the color to
    plot with in matplotlib.
LINE_MAPPING : dict
    A dictionary with keys that are displayed in GUIs, and values that
    are used by matplotlib to specify the line style.
MARKERS : tuple(str)
    A tuple of strings for the default markers to use for plotting.
TIGHT_LAYOUT_PAD : float
    The padding placed between the edge of the figure and the edge of
    the canvas; used by matplotlib's tight_layout option.
TIGHT_LAYOUT_H_PAD : float
    The height (vertical) padding between axes in a figure; used by
    matplotlib's tight_layout option.
TIGHT_LAYOUT_W_PAD : float
    The width (horizontal) padding between axes in a figure; used by
    matplotlib's tight_layout option.

Notes
-----
The sympy import is within the _parse_equation function because sympy
takes a significant time to load, is only used for that function, and
the function is only used when making secondary axes with different scales
than the main axes.

"""


from collections import defaultdict
import itertools
import json
from pathlib import Path
import string
import traceback

import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MaxNLocator
import numpy as np
import pandas as pd
import PySimpleGUI as sg

from .. import plot_utils, utils

# determine if Pillow is available; was not a requirement for matplotlib until v3.3.0
# minimum Pillow version is v6.2
try:
    from PIL import __version__ as _pillow_version
    if int(''.join(_pillow_version.split('.')[:2])) >= 62:
        _HAS_PIL = True
    else:
        _HAS_PIL = False
    del _pillow_version
except ImportError:
    _HAS_PIL = False

COLORS = (
    'None', 'Black', 'Blue', 'Red', 'Green', 'Chocolate',
    'Magenta', 'Cyan', 'Orange', 'Coral', 'Dodgerblue'
)
LINE_MAPPING = {
    'None': '',
    'Solid': '-',
    'Dashed': '--',
    'Dash-Dot': '-.',
    'Dot': ':',
    'Dash-Dot-Dot': (0,
                     [0.75 * plt.rcParams['lines.dashdot_pattern'][0]]
                     + plt.rcParams['lines.dashdot_pattern'][1:]
                     + plt.rcParams['lines.dashdot_pattern'][-2:])
}
MARKERS = (
    ' None', 'o Circle', 's Square', '^ Triangle-Up', 'D Diamond',
    'v Triangle-Down', 'p Pentagon', '< Triangle-Left',
    '> Triangle-Right', '* Star'
)
TIGHT_LAYOUT_PAD = 0.3
TIGHT_LAYOUT_H_PAD = 0.6
TIGHT_LAYOUT_W_PAD = 0.6

# column name for the blank columns inserted between data entries when saving data to csv
_FILLER_COLUMN_NAME = 'BLANK SEPARATION COLUMN'
# the default figure name used by matplotlib
_PREVIEW_NAME = 'Preview'
# the file extension for the json file containing all of the plot layout information
_THEME_EXTENSION = '.figtheme'


def _save_figure_json(gui_values, fig_kwargs, rc_changes, axes, data=None):
    """
    Save the values required to recreate the theme or the figure.

    Parameters
    ----------
    gui_values : dict
        A dictionary of values that correspond to all of the selections in
        the plot options window.
    fig_kwargs : dict
        Dictionary of keyword arguments required to recreate the figure and axes.
    rc_changes : dict
        A dictionary of the changes made to matplotlib's rcParam file used
        when making the figure.
    axes : list
        A nested list of lists of matplotlib Axes objects. Used to save
        their annotations.
    data : list, optional
        The list of dataframes used in the figure. If not None, the data
        will be saved to a csv file with the same name as the theme file.

    Notes
    -----
    The gui_values, fig_kwargs, rc_changes, and axes annotations are saved to
    a .figtheme file (just a json file).

    If saving the data for the figure, the data is saved to a csv file
    containing all of the data, separated by columns labeled with the
    _FILLER_COLUMN_NAME string. There are better ways to store the data than csv,
    but this way the data can be readily changed, if desired.

    """

    filename = sg.popup_get_file(
        '', no_window=True, save_as=True,
        file_types=((f"Theme Files (*{_THEME_EXTENSION})", f"*{_THEME_EXTENSION}"),)
    )

    if filename:

        annotations = {}
        peaks = {}
        for key in axes:
            annotations[key] = []
            peaks[key] = []
            # only the main axis is allowed annotations and peaks
            for annotation in axes[key]['Main Axis'].texts:
                annotations[key].append({
                    'text': annotation.get_text(),
                    'xy': annotation.xy,
                    'xytext': annotation.xyann,
                    'fontsize': annotation.get_fontsize(),
                    'rotation': annotation.get_rotation(),
                    'color': annotation.get_color(),
                    'horizontalalignment': annotation.get_horizontalalignment(),
                    'verticalalignment': annotation.get_verticalalignment(),
                    'arrowprops': annotation.arrowprops,
                    'annotation_clip': False,
                    'in_layout': False
                })

            for line in axes[key]['Main Axis'].lines:
                if line.get_label().startswith('-PEAK-'):
                    peaks[key].append({
                        'xdata': line.get_xdata().tolist(),
                        'ydata': line.get_ydata().tolist(),
                        'label': line.get_label(),
                        'marker': line.get_marker(),
                        'markerfacecolor': line.get_markerfacecolor(),
                        'markeredgecolor': line.get_markeredgecolor(),
                        'markeredgewidth': line.get_markeredgewidth(),
                        'markersize': line.get_markersize(),
                        'linestyle': line.get_linestyle(),
                        'linewidth': line.get_linewidth(),
                        'color': line.get_color(),
                        'alpha': line.get_alpha()
                    })

        if Path(filename).suffix != _THEME_EXTENSION:
            filename = str(
                Path(Path(filename).parent, Path(filename).stem + _THEME_EXTENSION)
            )

        try:
            with open(filename, 'w') as f:
                json.dump(
                    {'FIGURE KEYWORD ARGUMENTS': fig_kwargs,
                     'GUI VALUES': gui_values,
                     'MATPLOTLIB RCPARAM CHANGES': rc_changes,
                     'ANNOTATIONS': annotations,
                     'PEAKS': peaks},
                    f, indent=2
                )
        except PermissionError:
            sg.popup(
                ('The .figtheme file is currently open.\n'
                 'Please close and try to save again.\n'),
                title='Save Failed'
            )
        else:
            if data is None:
                sg.popup(
                    ('Successfully saved to '
                     f'{str(Path(filename).with_suffix(""))}\n'),
                    title='Save Successful'
                )
            else:
                saved_data = []
                # inserts separator columns between datasets
                for dataframe in data[:-1]:
                    df = dataframe.copy()
                    df[_FILLER_COLUMN_NAME] = pd.Series(np.nan, dtype=np.float16)
                    saved_data.append(df)
                saved_data.append(data[-1])

                filename = str(Path(filename).with_suffix('.csv'))
                try:
                    pd.concat(saved_data, axis=1).to_csv(filename, index=False,
                                                         encoding='raw_unicode_escape')
                except PermissionError:
                    sg.popup(
                        ('The .csv file is currently open.\n'
                         'Please close and try to save again.\n'),
                        title='Save Failed'
                    )
                else:
                    sg.popup(
                        ('Successfully saved to '
                         f'{str(Path(filename).with_suffix(""))}\n'),
                        title='Save Successful'
                    )


def load_previous_figure(filename=None, new_rc_changes=None):
    """
    Load the options and the data to recreate a figure.

    Parameters
    ----------
    filename : str, optional
        The filepath string to the csv data file to be opened.
    new_rc_changes : dict, optional
        New changes to matplotlib's rcParams file to alter the saved figure.

    Returns
    -------
    figures : list or None
        A list of figures (with len=1) using the loaded data. If no file is
        selected, then figures = None.

    Notes
    -----
    Will load the data from the csv file specified by filename. If there also
    exists a .figtheme file with the same name as the csv file, it will be
    loaded to set the figure layout. Otherwise, a new figure is created.

    """

    if filename is None:
        filename = sg.popup_get_file(
            '', file_types=(('CSV Files (*.csv)', '*.csv'),), no_window=True
        )

    figures = None
    if filename:
        # loads the figure theme file, if it exists
        if Path(filename).with_suffix(_THEME_EXTENSION).exists():
            axes, gui_values, fig_kwargs, rc_changes = _load_theme_file(
                str(Path(filename).with_suffix(_THEME_EXTENSION))
            )
            if new_rc_changes is not None:
                rc_changes.update(new_rc_changes)

        else:
            rc_changes = new_rc_changes
            fig_kwargs = None
            axes = None
            gui_values = None

        # try standard utf-8 encoding first; will throw an error only if there is
        # unicode previously saved by this module using 'raw_unicode_escape' encoding.
        try:
            dataframe = pd.read_csv(filename, header=None, index_col=False)
        except UnicodeDecodeError:
            dataframe = pd.read_csv(filename, header=None, index_col=False,
                                    encoding='raw_unicode_escape')

        # if column headers were repeated, read_csv would rename them,
        # so set header=None and manually set the headers after reading
        headers = utils.string_to_unicode(dataframe.loc[0].to_list())
        dataframe = dataframe.drop(0).reset_index(drop=True)
        dataframe.columns = headers

        # splits data into separate entries
        indices = []
        for i, column in enumerate(dataframe.columns):
            if _FILLER_COLUMN_NAME in column:
                indices.append(i)

        row = 0
        data = []
        for entry in indices:
            data.append(dataframe.iloc[:, row:entry])
            row += len(data[-1].columns) + 1
        data.append(dataframe.iloc[:, row:])

        figures = launch_plotting_gui(
            [data], rc_changes, fig_kwargs, axes, gui_values
        )

    return figures


def _load_theme_file(filename):
    """
    Loads the specified file and returns the parameters to recreate a figure theme.

    Parameters
    ----------
    filename : str
        The string of the path of the file to open.

    Returns
    -------
    fig_kwargs : dict
        The dictionary to recreate the loaded figure.
    gui_values : dict
        A dictionary that contains all the information to create the figure
        and set the values in the plot options gui.
    rc_changes : dict
        Changes to matplotlib's rcParams file to alter the saved figure.
    axes : dict
        The dictionary of plt.Axes objects, with annotations and peaks
        added to them.

    """

    with open(filename, 'r') as f:
        theme_file = json.load(f)

    #TODO should change these to theme_file.get(key, default) since user can modify/delete; check that defaults will be okay
    fig_kwargs = theme_file['FIGURE KEYWORD ARGUMENTS']
    gui_values = theme_file['GUI VALUES']
    rc_changes = theme_file['MATPLOTLIB RCPARAM CHANGES']
    annotations = theme_file['ANNOTATIONS']
    peaks = theme_file['PEAKS']

    with plt.rc_context({'interactive': False}):
        fig, axes = _create_figure_components(**fig_kwargs)
        plt.close(_PREVIEW_NAME)
        del fig

    for key in axes:
        for annotation in annotations.get(key, []):
            axes[key]['Main Axis'].annotate(annotation.pop('text'), **annotation)

        for peak in peaks.get(key, []):
            axes[key]['Main Axis'].plot(
                peak.pop('xdata'), peak.pop('ydata'), **peak
            )

    return axes, gui_values, fig_kwargs, rc_changes


def _load_figure_theme(current_axes, current_values, current_fig_kwargs):
    """
    Load the options to recreate a figure layout.

    Parameters
    ----------
    current_axes : dict
        The current dictionary of plt.Axes objects. Returned if the
        user does not load a file.
    current_values : dict
        The current window dictionary. Returned if user does not load a file.
    current_fig_kwargs : dict
        The dictionary used to create the current figure. Returned if user
        does not load a file.

    Returns
    -------
    new_theme : tuple
        If a theme file is not selected, an empty tuple is returned. Otherwise,
        a tuple with three entries is returned, with the entries being:
            axes : dict
                The dictionary of plt.Axes objects, with annotations added to them.
            gui_values : dict
                A dictionary that contains all the information to create the figure
                and set the values in the plot options gui.
            fig_kwargs : dict
                The dictionary to recreate the loaded figure.

    """

    filename = sg.popup_get_file(
        '', no_window=True,
        file_types=((f"Theme Files (*{_THEME_EXTENSION})", f"*{_THEME_EXTENSION}"),)
    )

    if filename:
        new_theme = _load_theme_file(filename)[:-1]
    else:
        new_theme = ()

    return new_theme


def _save_image_options(figure):
    """
    Handles saving a figure through matplotlib.

    If available, will give additional options to change the saved image
    quality and compression.

    Parameters
    ----------
    figure : plt.Figure
        The matplotlib Figure to save.

    """

    extension_mapping = {
        'jpeg': 'JPEG', 'jpg': 'JPEG', 'tiff': 'TIFF', 'tif': 'TIFF',
        'png': 'PNG', 'pdf': 'PDF', 'eps': 'EPS', 'ps': 'PS', 'svg': 'SVG',
        'svgz': 'SVGZ'
    }

    extension_dict = defaultdict(list)
    for key, value in sorted(extension_mapping.items(), key=lambda tup: tup[1]):
        extension_dict[value].append(key)

    extension_displays = {
        key: f'{key} ({", ".join(values)})' for key, values in extension_dict.items()
    }
    extension_regex = (
        [f'*.{value}' for value in values] for values in extension_dict.values()
    )

    layout = [
        [sg.Text('Filename:'),
         sg.Input('', disabled=True, size=(20, 1), key='file_name'),
         sg.Input('', key='save_as', visible=False,
                  enable_events=True, do_not_clear=False),
         sg.SaveAs(file_types=tuple(zip(extension_displays.values(), extension_regex)),
                   key='file_save_as', target='save_as')],
        [sg.Text('Image Type:'),
         sg.Combo(list(extension_displays.values()), key='extension',
                  default_value=extension_displays['TIFF'], size=(15, 1),
                  readonly=True)],
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Next', bind_return_key=True, size=(6, 1),
                   button_color=utils.PROCEED_COLOR)]
    ]

    window_1 = sg.Window('Save Options', layout)
    while True:
        event, values = window_1.read()

        if event in (sg.WIN_CLOSED, 'Back'):
            break

        elif event == 'save_as' and values['save_as']:
            file_path = Path(values['save_as'])
            window_1['file_name'].update(value=file_path.name)
            file_extension = file_path.suffix.lower()
            if file_extension and file_extension[1:] in extension_mapping:
                window_1['extension'].update(
                    value=extension_displays[extension_mapping[file_extension[1:]]]
                )

        elif event == 'Next':
            if not values['file_name']:
                sg.popup('\nPlease select a file name.\n',
                         title='Select a file name')
            else:
                window_1.hide()
                selected_extension = values['extension'].split(' ')[0]
                directory = str(file_path.parent)
                file_extension = file_path.suffix[1:] if file_path.suffix else selected_extension.lower()

                if (file_extension.lower() not in extension_mapping or
                        file_extension.lower() not in extension_dict[selected_extension]):

                    error_window = sg.Window(
                        'Extension Error',
                        layout=[
                            [sg.Text(('The given filename has an extension that\n'
                                      'is not the same as the selected extension\n'))],
                            [sg.Button(f'Use Filename Extension ({file_extension})',
                                       key='use_filename')],
                            [sg.Button(f'Use Selected Extension ({selected_extension})',
                                       key='use_selected')],
                            [sg.Button('Back')]
                        ]
                    )
                    error_event = error_window.read(close=True)[0]
                    error_window = None
                    if error_event in (sg.WIN_CLOSED, 'Back'):
                        window_1.un_hide()
                        continue
                    elif error_event == 'use_selected':
                        file_extension = selected_extension.lower()

                file_name = str(Path(directory, file_path.stem + '.' + file_extension))
                layout_2, param_types = _get_image_options(
                    extension_mapping.get(file_extension.lower(), '')
                )

                if not layout_2:
                    pil_kwargs = None
                else:
                    window_2 = sg.Window(f'Options for {file_extension.upper()}',
                                         layout_2)
                    event_2, pil_kwargs = window_2.read(close=True)
                    window_2 = None
                    if event_2 in (sg.WIN_CLOSED, 'Back'):
                        window_1.un_hide()
                        continue

                for param, function in param_types.items():
                    pil_kwargs[param] = function(pil_kwargs[param])

                if (extension_mapping[file_extension.lower()] == 'TIFF'
                        and pil_kwargs['compression'] != 'jpeg'):
                    pil_kwargs.pop('quality')

                try:
                    figure.savefig(file_name, pil_kwargs=pil_kwargs)
                    sg.popup(f'Saved figure to:\n    {file_name}\n', title='Saved Figure')
                    break

                except Exception as e:
                    sg.popup(
                        (f'Save failed...\n\nSaving to "{file_extension}" may not '
                         'be supported by matplotlib, or an additional error may '
                         f'have occured.\n\nError:\n    {repr(e)}\n'),
                        title='Error'
                    )
                    window_1.un_hide()

    window_1.close()
    del window_1


def _get_image_options(extension):
    """
    Constructs the layout for options to save to the given image extension.

    Allows setting options for compressing and/or setting the quality of the
    output image.

    Parameters
    ----------
    extension : str
        The file extension for the image to be saved.

    Returns
    -------
    layout : list
        A nested list of lists to be used as the layout in a PySimpleGUI window.
    param_types : dict
        A dictionary with keywords corresponding to keys in the PySimpleGUI layout
        and values corresponding to a function that will convert the key values
        to a desired output. Usually used to change the type from string to
        the desired type.

    Notes
    -----
    If Pillow is not installed (was not a requirement of matplotlib until v3.3.0),
    then no options are given to compress/optimize the output image.

    """

    if not _HAS_PIL:
        return [], {}

    if extension == 'JPEG':
        extension_layout = [
            [sg.Text('JPEG Quality (1-95):'),
             sg.Slider((1, 95), plt.rcParams['savefig.jpeg_quality'],
                       key='quality', orientation='h')],
            [sg.Check('Optimize', True, key='optimize')],
            [sg.Check('Progressive', key='progressive')]
        ]
        param_types = {'quality': int}

    elif extension == 'PNG':
        extension_layout = [
            [sg.Text('Compression Level:'),
             sg.Slider((1, 9), 6, key='compress_level', orientation='h')],
            [sg.Check('Optimize', True, key='optimize')]
        ]
        param_types = {'compress_level': int}

    elif extension == 'TIFF':
        extension_layout = [
            [sg.Text('Compression:'),
             sg.Combo(['None', 'Deflate', 'LZW', 'Pack Bits', 'JPEG'], 'Deflate',
                      key='compression', readonly=True)],
            [sg.Text('')],
            [sg.Text('Quality (1-95), only used for JPEG compression:')],
            [sg.Slider((1, 95), plt.rcParams['savefig.jpeg_quality'],
                       size=(30, 30), key='quality', orientation='h')],
        ]
        param_types = {'quality': int, 'compression': _convert_to_pillow_kwargs}

    else:
        extension_layout = []
        param_types = {}

    if extension_layout:
        layout = [
            *extension_layout,
            [sg.Text('')],
            [sg.Button('Back'),
             sg.Button('Save', bind_return_key=True, size=(6, 1),
                       button_color=utils.PROCEED_COLOR)]
        ]

    else:
        layout = []

    return layout, param_types


def _convert_to_pillow_kwargs(arg):
    """
    Converts a string to the correct keyword to use for tiff compression in pillow.

    Parameters
    ----------
    arg : str
        The string keyword used in the PySimpleGUI window.

    Return
    ------
    arg_mapping[arg] : None or str
        The keyword in pillow associated with the input arg string.

    """

    arg_mapping = {
        'None': None, 'Deflate': 'tiff_deflate', 'LZW': 'tiff_lzw',
        'Pack Bits': 'packbits', 'JPEG': 'jpeg'
    }

    return arg_mapping[arg]


def _create_figure_components(saving=False, **fig_kwargs):
    """
    Convenience function to create the figure, gridspec, and axes with one function.

    Later fill this with logic determining which steps can be skipped if no changes
    are made.

    Parameters
    ----------
    saving : bool
        If True, designate that the figure is being saved, so the figure dpi
        will not be adjusted. Otherwise, the figure dpi is adjusted so that
        it fits on plot_utils.CANVAS_SIZE.
    fig_kwargs : dict
        Keyword arguments to pass on to the various functions. Unpacking
        is used so that the figure name can be easily specified without
        changing the fig_kwargs dictionary used to control figure size, dpi, etc.

    Returns
    -------
    figure : plt.Figure
        The created matplotlib Figure.
    axes : dict
        A nested dictionary containing all of the axes within the figure. Each
        key details the position of the axis within the figure, and each value
        is a dictionary containing at most three keys, 'Main Axis', 'Twin x axis',
        and 'Twin y axis', with each value corresponding to the plt.Axes object
        for that key.

    """

    #TODO should set defaults for fig_kwargs since user can modify/delete them in the saved json file

    figure = _create_figure(fig_kwargs, saving)
    gridspec, gridspec_layout = _create_gridspec(fig_kwargs, figure)
    axes = _create_axes(gridspec, gridspec_layout, figure, fig_kwargs)

    return figure, axes


def _create_figure(fig_kwargs, saving=False):
    """
    Creates a figure corresponding to the value selected in select_plot_type

    Parameters
    ----------
    fig_kwargs : dict
        Keyword arguments for creating the figure.
    saving : bool
        Designates whether the figure will be saved. If True, will use the input
        figure size and dpi. If False, will scale the dpi to fit the figure onto
        the PySimpleGUI canvas with size = plot_utils.CANVAS_SIZE.

    Returns
    -------
    fig : plt.Figure
        The created matplotlib Figure.

    Notes
    -----
    Uses different dpi if not saving. When saving, matplotlib
    saves the correct size and dpi, regardless of the backend.

    """

    defaults = {
        'fig_name': _PREVIEW_NAME,
        'fig_width': plt.rcParams['figure.figsize'][0] * plt.rcParams['figure.dpi'],
        'fig_height': plt.rcParams['figure.figsize'][1] * plt.rcParams['figure.dpi'],
        'dpi': plt.rcParams['figure.dpi'],
        'share_x': False,
        'share_y': False
    }
    for key, value in defaults.items():
        fig_kwargs.setdefault(key, value)

    if saving:
        dpi = fig_kwargs['dpi']
    else:
        dpi = plot_utils.determine_dpi(fig_kwargs)

    plt.close(fig_kwargs['fig_name'])
    figure = plt.figure(
        num=fig_kwargs['fig_name'], dpi=dpi,
        figsize = (fig_kwargs['fig_width'] / fig_kwargs['dpi'],
                   fig_kwargs['fig_height'] / fig_kwargs['dpi']),
        tight_layout={'pad': TIGHT_LAYOUT_PAD,
                      'w_pad': 0 if fig_kwargs['share_y'] else TIGHT_LAYOUT_W_PAD,
                      'h_pad': 0 if fig_kwargs['share_x'] else TIGHT_LAYOUT_H_PAD}
    )

    return figure


def _create_gridspec(gs_kwargs, figure):
    """
    Creates the gridspec detailing the layout of plots within the figure.

    Also updates the gs_kwargs to match the created gridspec.

    Parameters
    ----------
    gs_kwargs : dict
        A dictionary containing the relevant values for creating the gridspec.
    figure : plt.Figure
        The matplotlib figure that the gridspec will be added to.

    Returns
    -------
    gridspec : plt.GridSpec
        The created GridSpec object, detailing the layout of plots in the figure.
    gridspec_layout : dict
        A dictionary that details where plots go within the gridspec. Each key
        is a unique plot, and its values are the row and column indices for
        the plot within the gridspec.

    """

    selections = defaultdict(list)
    gridspec_layout = {}

    if gs_kwargs['Single Plot']:
        gridspec = figure.add_gridspec(1, 1)
        gridspec_layout = {'a': ((0, 1), (0, 1))}
    else:
        blank_num = 0
        for key, value in gs_kwargs.items():
            if key.startswith('gridspec_'):
                if value:
                    selections[value].append(key.split('_')[-2:])
                else:
                    selections[f'blank_{blank_num}'].append(key.split('_')[-2:])
                    blank_num += 1
        for key, vals in selections.items():
            rows = [int(val[0]) for val in vals]
            cols = [int(val[1]) for val in vals]

            gridspec_layout[key] = ((min(rows), max(rows) + 1), (min(cols), max(cols) + 1))

        width_ratios = [float(gs_kwargs[f'width_{i}']) for i in range(gs_kwargs['num_cols'])]
        height_ratios = [float(gs_kwargs[f'height_{i}']) for i in range(gs_kwargs['num_rows'])]

        gridspec = figure.add_gridspec(
            gs_kwargs['num_rows'], gs_kwargs['num_cols'],
            width_ratios=width_ratios, height_ratios=height_ratios
        )

    # set up the twin x and y values
    default_inputs = {}
    for entry, val in gridspec_layout.items():
        if not entry.startswith('blank'):
            default_inputs[f'twin_x_{val[0][0]}_{val[1][0]}'] = False
            default_inputs[f'twin_y_{val[0][0]}_{val[1][0]}'] = False
    default_inputs.update(gs_kwargs)
    gs_kwargs.update(default_inputs)

    return gridspec, gridspec_layout


def _create_axes(gridspec, gridspec_layout, figure, fig_kwargs):
    """
    Creates all of the axes for the figure using the gridspec.

    Parameters
    ----------
    gridspec : plt.GridSpec
        The created GridSpec object, detailing the layout of plots in the figure.
    gridspec_layout : dict
        A dictionary that details where plots go within the gridspec. Each key
        is a unique plot, and its values are the row and column indices for
        the plot within the gridspec.
    figure : plt.Figure
        The Figure that the gridspec and axes belong to.
    fig_kwargs : dict
        The keyword arguments needed to create the figure and axes.

    Returns
    -------
    axes : dict
        A nested dictionary containing all of the axes within the figure. Each
        key details the position of the axis within the figure, and each value
        is a dictionary containing at most three keys, 'Main Axis', 'Twin X axis',
        and 'Twin Y axis', with each value corresponding to the plt.Axes object
        for that key.

    """

    axes = defaultdict(dict)
    for key, val in gridspec_layout.items():
        entry_key = f'Row {int(val[0][0]) + 1}, Col {int(val[1][0]) + 1}'
        if 'blank' in key:
            # creates the axis without spines or labels, but not invisible so it can be annotated
            ax = figure.add_subplot(
                gridspec[val[0][0]:val[0][1], val[1][0]:val[1][1]],
                label=f'{entry_key} (Invisible)', frameon=False
            )
            ax.tick_params(
                which='both', labelbottom=False, labelleft=False, top=False,
                bottom=False, left=False, labelright=False, labeltop=False, right=False
            )

        else: #TODO maybe collect all the options into a single dictionary
            sharex = None
            sharey = None
            x_label = 'x label'
            y_label = 'y label'
            label_bottom = True
            label_left = True
            twin_x_label = 'twin x label'
            twin_y_label = 'twin y label'
            label_top = True
            label_right = True

            if fig_kwargs['share_x']:
                if f'Row 1, Col {int(val[1][0]) + 1}' in axes:
                    sharex = axes[f'Row 1, Col {int(val[1][0]) + 1}']['Main Axis']

                if int(val[0][0]) + 1 != fig_kwargs['num_rows']:
                    x_label = ''
                    label_bottom = False

                if int(val[0][0]) != 0:
                    twin_y_label = ''
                    label_top = False

            if fig_kwargs['share_y']:
                if f'Row {int(val[0][0]) + 1}, Col 1' in axes:
                    sharey = axes[f'Row {int(val[0][0]) + 1}, Col 1']['Main Axis']

                if int(val[1][0]) != 0:
                    y_label = ''
                    label_left = False

                if int(val[1][0]) + 1 !=  fig_kwargs['num_cols']:
                    twin_x_label = ''
                    label_right = False

            ax = figure.add_subplot(
                gridspec[val[0][0]:val[0][1], val[1][0]:val[1][1]],
                label=entry_key, sharex=sharex, sharey=sharey
            )
            ax.tick_params(which='both', labelbottom=label_bottom,
                           labelleft=label_left)

        axes[entry_key]['Main Axis'] = ax

        if 'blank' not in key:

            if fig_kwargs[f'twin_x_{val[0][0]}_{val[1][0]}']:
                ax2 = ax.twinx()
                ax2.set_label(f'{ax.get_label()} (Twin x)')
                ax2.set_frame_on(False)
                ax2.set_ylabel(twin_x_label)
                ax2.tick_params(which='both', labelright=label_right)
                axes[entry_key]['Twin X'] = ax2

            if fig_kwargs[f'twin_y_{val[0][0]}_{val[1][0]}']:
                ax3 = ax.twiny()
                ax3.set_label(f'{ax.get_label()} (Twin y)')
                ax3.set_frame_on(False)
                ax3.set_xlabel(twin_y_label)
                ax3.tick_params(which='both', labeltop=label_top)
                axes[entry_key]['Twin Y'] = ax3

            ax.set_ylabel(y_label)
            ax.set_xlabel(x_label)

    return axes


def _annotate_example_figure(axes, canvas, figure):
    """
    Adds labels to all axes on the figure to specify their locations.

    Parameters
    ----------
    axes : dict
        A dictionary of axes in the figure.
    canvas : tkinter.Canvas
        The canvas for the figure.
    figure : plt.Figure
        The figure that will be shown.

    """

    for key in axes:
        for label in axes[key]:
            ax = axes[key][label]
            if label == 'Main Axis':
                ax_label = ax.get_label().split(', ')
                ax.annotate(
                    f'{ax_label[0]}\n{ax_label[1]}', (0.5, 0.5),
                    horizontalalignment='center', in_layout=False,
                    verticalalignment='center', transform=ax.transAxes
                )

            ax.set_xlim(0.1, 0.9)
            ax.set_ylim(0.1, 0.9)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
            ax.yaxis.set_minor_locator(AutoMinorLocator(2))
            ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
            ax.xaxis.set_minor_locator(AutoMinorLocator(2))

    plot_utils.draw_figure_on_canvas(canvas, figure)


def _create_advanced_layout(input_values, canvas, figure):
    """
    Specifies the row and column layout for plots in the figure

    Parameters
    ----------
    input_values : dict
        The dictionary containing the values describing the layout
        of axes within the figure. Will be modified inplace by
        this function.
    canvas : tkinter.Canvas
        The canvas for the figure.
    figure : plt.Figure
        The figure that will be shown.

    """

    num_cols = input_values['num_cols']
    num_rows = input_values['num_rows']

    validations = {'floats': [], 'constraints': []}
    for i in range(num_cols):
        validations['floats'].append([f'width_{i}', f'width {i + 1}'])
        validations['constraints'].append( [f'width_{i}', f'width {i + 1}', '> 0'])

    for i in range(num_rows):
        validations['floats'].append([f'height_{i}', f'height {i + 1}'])
        validations['constraints'].append([f'height_{i}', f'height {i + 1}', '> 0'])

    columm_layout =  [
        [sg.Text(i + 1, size=(2, 1), justification='right')]
        + [sg.Input(input_values[f'gridspec_{i}_{j}'], size=(5, 1), pad=(1, 1),
                    justification='right', key=f'gridspec_{i}_{j}') for j in range(num_cols)]
        for i in range(num_rows)]

    widths = [
        sg.Input(input_values[f'width_{i}'], key=f'width_{i}', size=(5, 1)) for i in range(num_cols)
    ]
    heights = [
        [sg.Input(input_values[f'height_{i}'], key=f'height_{i}', size=(5, 1))] for i in range(num_rows)
    ]

    header_layout = [
        [sg.Text('', size=(2, 1))] +
        [sg.Text(j + 1, size=(5,1), justification='center') for j in range(num_cols)]]

    layout = [
        [sg.Text('Figure Layout\n')],
        [sg.Column([*header_layout, *columm_layout]),
         sg.VerticalSeparator(),
         sg.Column([
             [sg.Text('Height Ratios')],
             *heights
         ])],
        [sg.Text('', size=(2, 1)),
         sg.Text('-' * 10 * num_cols)],
        [sg.Text('', size=(2, 1)),
         *widths],
        [sg.Text('', size=(2, 1)),
         sg.Text('Width Ratios')],
        [sg.Text('')],
        [sg.Button('Preview'),
         sg.Button('Submit', bind_return_key=True, button_color=utils.PROCEED_COLOR)]
    ]

    window = sg.Window('Table', layout, finalize=True)
    window.TKroot.grab_set()
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        elif event in ('Preview', 'Submit'):
            window.TKroot.grab_release()
            if utils.validate_inputs(values, **validations):
                input_values.update(values)
                figure, axes = _create_figure_components(**input_values)

                if event == 'Preview':
                    _annotate_example_figure(axes, canvas, figure)

                elif event == 'Submit':
                    break

            window.TKroot.tkraise()
            window.TKroot.grab_set()

    window.close()
    del window


def _create_gridspec_labels(fig_kwargs):
    """
    Ensures that the gridspec layout matches the desired rows and columns in the plot.

    Parameters
    ----------
    fig_kwargs : dict
        The keyword arguments used to create the figure.

    Returns
    -------
    new_kwargs : dict
        A dictionary containing the original keyword arguments from
        fig_kwargs after modifying to match the new number of rows
        and columns within the figure.

    """

    num_cols = fig_kwargs['num_cols']
    num_rows = fig_kwargs['num_rows']

    new_kwargs = fig_kwargs.copy()
    # deletes previous gridspec values
    for key in fig_kwargs:
        if key.startswith('gridspec') or key.startswith('width') or key.startswith('height'):
            if key.startswith('gridspec'):
                index = key.split('_')[-2:]
                if num_rows <= int(index[0]) or num_cols <= int(index[1]):
                    new_kwargs.pop(key)
            else:
                index = key.split('_')[-1]
                if key.startswith('width'):
                    if int(index) >= num_cols:
                        new_kwargs.pop(key)
                if key.startswith('height'):
                    if int(index) >= num_rows:
                        new_kwargs.pop(key)

    if any(key.startswith('gridspec') for key in new_kwargs):
        # ensures a new key is always generated when creating new axes
        len_string = max(len(new_kwargs[key]) for key in new_kwargs if key.startswith('gridspec')) + 1
        # ensures current height and width ratios are not overwritten
        current_col = max(int(key.split('_')[-1]) for key in new_kwargs if key.startswith('width')) + 1
        current_row = max(int(key.split('_')[-1]) for key in new_kwargs if key.startswith('height')) + 1
    else:
        len_string = 1
        current_col = 0
        current_row = 0

    new_kwargs.update({f'width_{i}': 1 for i in range(current_col, num_cols)})
    new_kwargs.update({f'height_{i}': 1 for i in range(current_row, num_rows)})
    letters = itertools.cycle(string.ascii_letters)
    for i in range(num_rows):
        for j in range(num_cols):
            if f'gridspec_{i}_{j}' not in new_kwargs:
                new_kwargs.update({f'gridspec_{i}_{j}': next(letters) * len_string})

    return new_kwargs


def _set_twin_axes(gridspec_layout, user_inputs, canvas):
    """
    Allows setting twin axes for any of the axes in the figure.

    Parameters
    ----------
    gridspec_layout : dict
        A dictionary that details where plots go within the gridspec. Each key
        is a unique plot, and its values are the row and column indices for
        the plot within the gridspec.
    user_inputs : dict
        The dictionary containing the values needed to create the plt.Figure.
        Will be modified inplace by this function to include any twin axes.
    canvas : tkinter.Canvas
        The tkinter canvas on which the figure resides.

    """

    default_inputs = {}
    for entry, val in gridspec_layout.items():
        if not entry.startswith('blank'):
            default_inputs[f'twin_x_{val[0][0]}_{val[1][0]}'] = False
            default_inputs[f'twin_y_{val[0][0]}_{val[1][0]}'] = False

    default_inputs.update(user_inputs)

    layout = [
        [sg.Text(('Twin X creates a second Y axis that shares the X-axis\n'
                  'of the parent plot. Twin Y creates a second X axis,\n'
                  'sharing the Y-axis of the parent plot.'))],
        [sg.Text('')],
        [sg.Column([[sg.Text('                        ')]]),
         sg.Column([[sg.Text('Twin X', justification='center')]],
                   element_justification='center'),
         sg.Column([[sg.Text('Twin Y')]], element_justification='center')]
    ]

    for entry, val in gridspec_layout.items():
        if not entry.startswith('blank'):
            layout.append([
                sg.Column([
                    [sg.Text(f'Row {val[0][0] + 1}, Column {val[1][0] + 1}   ')]
                ]),
                sg.Column([
                    [sg.Check('      ', default_inputs[f'twin_x_{val[0][0]}_{val[1][0]}'],
                              key=f'twin_x_{val[0][0]}_{val[1][0]}')]
                ], element_justification='center'),
                sg.Column([
                    [sg.Check('      ', default_inputs[f'twin_y_{val[0][0]}_{val[1][0]}'],
                              key=f'twin_y_{val[0][0]}_{val[1][0]}')]
                ], element_justification='center')
            ])

    layout.extend([
        [sg.Text('')],
        [sg.Button('Preview'),
         sg.Button('Submit', button_color=utils.PROCEED_COLOR,
                   bind_return_key=True)]
    ])
    window = sg.Window('Twin Axes', layout, finalize=True)
    window.TKroot.tkraise()
    window.TKroot.grab_set()

    while True:
        event, values = window.read()

        if event != sg.WIN_CLOSED:
            user_inputs.update(values)

        fig, axes = _create_figure_components(**user_inputs)
        if event == 'Preview':
            _annotate_example_figure(axes, canvas, fig)

        elif event in ('Submit', sg.WIN_CLOSED):
            break

    window.close()
    del window


def _select_plot_type(user_inputs=None):
    """
    Window that allows selection of the type of plot to use and the plot layout.

    Parameters
    ----------
    user_inputs : dict, optional
        A dictionary containing values to recreate a previous layout.

    Returns
    -------
    fig_kwargs : dict
        A dictionary containing all of the information to create the figure
        with the desired layout.
    axes : dict
        A dictionary containing all of the main axes, and their twin x- and y-axes,
        if selected.

    """

    plot_types = {'Single Plot': 'single_plot',
                  'Multiple Plots': 'multiple_plots'}

    default_inputs = {
        'fig_width': plt.rcParams['figure.figsize'][0] * plt.rcParams['figure.dpi'],
        'fig_height': plt.rcParams['figure.figsize'][1] * plt.rcParams['figure.dpi'],
        'dpi': plt.rcParams['figure.dpi'],
        'scatter': False,
        'line': False,
        'line_scatter': True,
        'num_rows': 1,
        'num_cols': 1,
        'share_x': False,
        'share_y': False
    }

    default_inputs.update({key: num == 0 for num, key in enumerate(plot_types)})
    fig_kwargs = _create_gridspec_labels(default_inputs.copy())
    if user_inputs is not None:
        default_inputs.update(user_inputs)
        fig_kwargs.update(user_inputs)

    fig_kwargs['fig_name'] = 'example'

    check_buttons = []
    for plot in plot_types: #TODO just make it manually since there are only two entries

        if plot != 'Multiple Plots':
            check_buttons.append(
                [sg.Radio(plot, 'plots', key=plot, enable_events=True,
                          default=default_inputs[plot])]
            )
        else:
            disabled = not default_inputs['Multiple Plots']
            check_buttons.extend([
                [sg.Radio(plot, 'plots', key=plot, enable_events=True,
                          default=default_inputs[plot])],
                [sg.Text('      Rows:', size=(11, 1)),
                 sg.Combo(list(range(1, 7)), key='num_rows', size=(3, 1), disabled=disabled,
                          default_value=default_inputs['num_rows'], readonly=True)],
                [sg.Text('      Columns:', size=(11, 1)),
                 sg.Combo(list(range(1, 7)), key='num_cols', size=(3, 1), disabled=disabled,
                          default_value=default_inputs['num_cols'], readonly=True)],
                [sg.Check('Same X Axis', key='share_x', disabled=disabled,
                          default=default_inputs['share_x'], pad=(40, 1))],
                [sg.Check('Same Y Axis', key='share_y', disabled=disabled,
                          default=default_inputs['share_y'], pad=(40, 1))]
            ])

    layout = [
        [sg.Column([
            [sg.Text('Plot Layout', relief='ridge', size=(30, 1), justification='center')],
            *check_buttons,
            [sg.Button('Advanced Options', disabled=not default_inputs['Multiple Plots'],
                       pad=(40, 1))],
            [sg.Button('Add Twin Axes', pad=(3, (15, 3)))],
            [sg.Text('Default Marker', relief='ridge', size=(30, 1),
                     justification='center')],
            [sg.Radio('Line + Scatter', 'markers', key='line_scatter',
                      default=default_inputs['line_scatter'])],
            [sg.Radio('Line', 'markers', key='line', default=default_inputs['line'])],
            [sg.Radio('Scatter', 'markers', key='scatter', default=default_inputs['scatter'])],
            [sg.Text('Size and DPI', relief='ridge', size=(30, 1), justification='center')],
            [sg.Text('Figure Width (in pixels):', size=(19, 1)),
             sg.Input(default_inputs['fig_width'], key='fig_width', size=(6, 1))],
            [sg.Text('Figure Height (in pixels):', size=(19, 1)),
             sg.Input(default_inputs['fig_height'], key='fig_height', size=(6, 1))],
            [sg.Text('Dots per inch (DPI):', size=(19, 1)),
             sg.Input(default_inputs['dpi'], key='dpi', size=(6, 1))],
            [sg.Text('')],
            [sg.Button('Preview'),
             sg.Button('Next', bind_return_key=True, size=(6, 1),
                       button_color=utils.PROCEED_COLOR)]
         ]),
         sg.Column([
             [sg.Canvas(key='example_canvas', size=plot_utils.CANVAS_SIZE, pad=(0, 0))]
         ], size=(plot_utils.CANVAS_SIZE[0] + 10, plot_utils.CANVAS_SIZE[1] + 10),
         pad=(20, 0))]
    ]

    fig = _create_figure(fig_kwargs)
    gridspec, gridspec_layout = _create_gridspec(fig_kwargs, fig)
    axes = _create_axes(gridspec, gridspec_layout, fig, fig_kwargs)
    window = sg.Window('Plot Types', layout, finalize=True)
    _annotate_example_figure(axes, window['example_canvas'].TKCanvas, fig)

    validations= {
        'floats': [['fig_width', 'Figure Width'], ['fig_height', 'Figure Height'],
                   ['dpi', 'DPI']],
        'integers': [['num_rows', 'Number of rows'],
                     ['num_cols', 'Number of columns']],
        'constraints': [['fig_width', 'Figure Width', '> 0'],
                        ['fig_height', 'Figure Height', '> 0'],
                        ['dpi', 'DPI', '> 0']]
    }

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            plt.close('example')
            utils.safely_close_window(window)

        elif (event in ('Advanced Options', 'Next', 'Preview', 'Add Twin Axes')
                and utils.validate_inputs(values, **validations)):

            fig_kwargs.update(values)
            fig_kwargs = _create_gridspec_labels(fig_kwargs)
            fig = _create_figure(fig_kwargs)
            gridspec, gridspec_layout = _create_gridspec(fig_kwargs, fig)
            axes = _create_axes(gridspec, gridspec_layout, fig, fig_kwargs)

            if event == 'Preview':
                _annotate_example_figure(
                    axes, window['example_canvas'].TKCanvas, fig
                )

            elif event == 'Advanced Options':
                _create_advanced_layout(
                    fig_kwargs, window['example_canvas'].TKCanvas, fig
                )

            elif event == 'Add Twin Axes':
                _set_twin_axes(
                    gridspec_layout, fig_kwargs, window['example_canvas'].TKCanvas
                )

            elif event == 'Next':
                break

        elif event in plot_types:
            if values['Multiple Plots']:
                window['num_rows'].update(readonly=True)
                window['num_cols'].update(readonly=True)
                window['share_x'].update(disabled=False)
                window['share_y'].update(disabled=False)
                window['Advanced Options'].update(disabled=False)
            else:
                window['num_rows'].update(value='1', disabled=True)
                window['num_cols'].update(value='1', disabled=True)
                window['share_x'].update(value=False, disabled=True)
                window['share_y'].update(value=False, disabled=True)
                window['Advanced Options'].update(disabled=True)

    window.close()
    plt.close('example')
    del window, fig
    fig_kwargs.pop('fig_name')
    fig_kwargs.pop('example_canvas')

    return fig_kwargs


def _create_plot_options_gui(data, figure, axes, user_inputs=None, old_axes=None,
                             location=(None, None), **kwargs):
    """
    Creates a new window with all of the plotting options.

    Parameters
    ----------
    data : list or tuple
        A collection of (x,y) arrays.
    figure : matplotlib Figure
        The figure being created.
    axes : dict
        A collection of matplotlib Axes objects; should be a 2D array
        of Axes.
    user_inputs : dict
        A dictionary to recreate a previous layout of the window.
    old_axes : dict
        A dictionary of plt.Axes objects that were previously used. Used
        to transfer annotations to the new axes.
    location : tuple(int, int)
        Describes the position to place the window.
    kwargs : dict
        Additional keyword arguments to create the plots.

    Returns
    -------
    window : sg.Window
        The window that contains the plotting options.
    validations : dict
        A dictionary containing all of the validations for the created
        window for use in the utils.validate_inputs function.

    TODO set metadata for elements to determine whether they should be readonly when enabled

    """

    default_inputs = {}
    validations = {
        'integers': [],
        'floats': [],
        'user_inputs': [],
        'constraints': []
    }
    # generates default values based on the Axes and data length
    for i, key in enumerate(axes):
        if 'Invisible' in axes[key]['Main Axis'].get_label():
            continue
        for j, label in enumerate(axes[key]):
            axis = axes[key][label]
            axis_label = axis.get_label()
            color_cyle = itertools.cycle(COLORS[1:])

            if kwargs['line']:
                marker_cycler = itertools.cycle([''])
                line_cycler = itertools.cycle(list(LINE_MAPPING)[1:])
            elif kwargs['scatter']:
                marker_cycler = itertools.cycle(MARKERS[1:])
                line_cycler = itertools.cycle(['None'])
            else:
                marker_cycler = itertools.cycle(MARKERS[1:])
                line_cycler = itertools.cycle(list(LINE_MAPPING)[1:])

            if not axis.get_xlabel():
                x_label = ''
                show_x_label = False
                x_label_disabled = True
            else:
                x_label = axis.get_xlabel()
                show_x_label = True
                x_label_disabled = False

            if not axis.get_ylabel():
                y_label = ''
                show_y_label = False
                y_label_disabled = True
            else:
                y_label = axis.get_ylabel()
                show_y_label = True
                y_label_disabled = False

            # Options for each axis
            default_inputs.update({
                f'show_x_label_{i}_{j}': show_x_label,
                f'show_y_label_{i}_{j}': show_y_label,
                f'x_axis_min_{i}_{j}': None,
                f'x_axis_max_{i}_{j}': None,
                f'x_label_{i}_{j}': x_label,
                f'x_label_offset_{i}_{j}': '' if x_label_disabled else plt.rcParams['axes.labelpad'],
                f'x_label_disabled_{i}_{j}': x_label_disabled,
                f'y_axis_min_{i}_{j}': None,
                f'y_axis_max_{i}_{j}': None,
                f'y_label_{i}_{j}': y_label,
                f'y_label_offset_{i}_{j}': '' if y_label_disabled else plt.rcParams['axes.labelpad'],
                f'y_label_disabled_{i}_{j}': y_label_disabled,
                f'secondary_x_{i}_{j}': False,
                f'secondary_x_label_{i}_{j}': '',
                f'secondary_x_label_offset_{i}_{j}': plt.rcParams['axes.labelpad'],
                f'secondary_x_expr_{i}_{j}': '',
                f'secondary_y_{i}_{j}': False,
                f'secondary_y_label_{i}_{j}': '',
                f'secondary_y_label_offset_{i}_{j}': plt.rcParams['axes.labelpad'],
                f'secondary_y_expr_{i}_{j}': '',
                f'show_legend_{i}_{j}': True,
                f'legend_cols_{i}_{j}': 1 if len(data) < 5 else 2,
                f'legend_auto_{i}_{j}': True,
                f'legend_auto_loc_{i}_{j}': 'best',
                f'legend_manual_{i}_{j}': False,
                f'legend_manual_x_{i}_{j}': '',
                f'legend_manual_y_{i}_{j}': '',
                f'auto_ticks_{i}_{j}': True,
                f'x_major_ticks_{i}_{j}': 5 if label != 'Twin X' else '',
                f'x_minor_ticks_{i}_{j}': 2 if label != 'Twin X' else '',
                f'y_major_ticks_{i}_{j}': 5 if label != 'Twin Y' else '',
                f'y_minor_ticks_{i}_{j}': 2 if label != 'Twin Y' else '',
                f'auto_ticks_secondary_{i}_{j}': True,
                f'secondary_x_major_ticks_{i}_{j}': 5,
                f'secondary_x_minor_ticks_{i}_{j}': 2,
                f'secondary_y_major_ticks_{i}_{j}': 5,
                f'secondary_y_minor_ticks_{i}_{j}': 2,
                f'x_major_grid_{i}_{j}': False,
                f'x_minor_grid_{i}_{j}': False,
                f'y_major_grid_{i}_{j}': False,
                f'y_minor_grid_{i}_{j}': False,
            })

            validations['floats'].extend([
                [f'x_axis_min_{i}_{j}', f'x axis minimum for {axis_label}'],
                [f'x_axis_max_{i}_{j}', f'x axis maximum for {axis_label}'],
                [f'x_label_offset_{i}_{j}', f'x axis label offset for {axis_label}'],
                [f'y_axis_min_{i}_{j}', f'y axis minimum for {axis_label}'],
                [f'y_axis_max_{i}_{j}', f'y axis maximum for {axis_label}'],
                [f'y_label_offset_{i}_{j}', f'y axis label offset for {axis_label}'],
                [f'secondary_x_label_offset_{i}_{j}', f'secondary x axis label offset for {axis_label}'],
                [f'secondary_y_label_offset_{i}_{j}', f'secondary y axis label offset for {axis_label}'],
            ])
            validations['user_inputs'].extend([
                [f'x_axis_min_{i}_{j}', f'x axis minimum for {axis_label}', float, label == 'Twin X', None],
                [f'x_axis_max_{i}_{j}', f'x axis maximum for {axis_label}', float, label == 'Twin X', None],
                [f'x_label_offset_{i}_{j}', f'x axis label offset for {axis_label}', float, label == 'Twin X', None],
                [f'y_axis_min_{i}_{j}', f'y axis minimum for {axis_label}', float, label == 'Twin Y', None],
                [f'y_axis_max_{i}_{j}', f'y axis maximum for {axis_label}', float, label == 'Twin Y', None],
                [f'y_label_offset_{i}_{j}', f'y axis label offset for {axis_label}', float, label == 'Twin Y', None],
                [f'secondary_x_label_offset_{i}_{j}', f'secondary x axis label offset for {axis_label}'],
                [f'secondary_y_label_offset_{i}_{j}', f'secondary y axis label offset for {axis_label}'],
            ])

            # Options for each data entry
            for k in range(len(data)):
                data_color = next(color_cyle)

                default_inputs.update({
                    f'plot_boolean_{i}_{j}_{k}': True,
                    f'x_col_{i}_{j}_{k}': '0',
                    f'y_col_{i}_{j}_{k}': '1',
                    f'label_{i}_{j}_{k}': f'Data {k + 1}',
                    f'offset_{i}_{j}_{k}': 0,
                    f'markerface_color_{i}_{j}_{k}': data_color,
                    f'markeredge_color_{i}_{j}_{k}': data_color,
                    f'marker_edgewidth_{i}_{j}_{k}': plt.rcParams['lines.markeredgewidth'],
                    f'marker_style_{i}_{j}_{k}': next(marker_cycler),
                    f'marker_size_{i}_{j}_{k}': plt.rcParams['lines.markersize'],
                    f'line_color_{i}_{j}_{k}': data_color,
                    f'line_style_{i}_{j}_{k}': next(line_cycler),
                    f'line_size_{i}_{j}_{k}': plt.rcParams['lines.linewidth']
                })

    if user_inputs is not None:
        default_inputs.update(user_inputs)
    # Have to plot to get the default axes limits
    _plot_data(data, axes, old_axes, **default_inputs, **kwargs)

    axes_tabs = []
    for i, key in enumerate(axes):
        if 'Invisible' in axes[key]['Main Axis'].get_label():
            continue

        label_tabs = []
        for j, label in enumerate(axes[key]):
            axis = axes[key][label]

            # Have to update axis limits after plotting the data
            default_inputs.update({
                f'x_axis_min_{i}_{j}': axis.get_xlim()[0] if label != 'Twin X' else '',
                f'x_axis_max_{i}_{j}': axis.get_xlim()[1] if label != 'Twin X' else '',
                f'y_axis_min_{i}_{j}': axis.get_ylim()[0] if label != 'Twin Y' else '',
                f'y_axis_max_{i}_{j}': axis.get_ylim()[1] if label != 'Twin Y' else '',
                f'secondary_x_axis_min_{i}_{j}': axis.get_xlim()[0],
                f'secondary_x_axis_max_{i}_{j}': axis.get_xlim()[1],
                f'secondary_y_axis_min_{i}_{j}': axis.get_ylim()[0],
                f'secondary_y_axis_max_{i}_{j}': axis.get_ylim()[1],
            })

            if 'Twin X' in axes[key] or 'Twin' in label: #TODO why is this here and not in the upper statement??
                secondary_y_disabled = True
                default_inputs.update({
                    f'secondary_y_{i}_{j}': False,
                    f'secondary_y_label_{i}_{j}': '',
                    f'secondary_y_label_offset_{i}_{j}': '',
                    f'secondary_y_expr_{i}_{j}': ''
                })
            else:
                secondary_y_disabled = False

            if 'Twin Y' in axes[key] or 'Twin' in label:
                secondary_x_disabled = True
                default_inputs.update({
                    f'secondary_x_{i}_{j}': False,
                    f'secondary_x_label_{i}_{j}': '',
                    f'secondary_x_label_offset_{i}_{j}': '',
                    f'secondary_x_expr_{i}_{j}': ''
                })
            else:
                secondary_x_disabled = False

            plot_details = []
            for k, dataset in enumerate(data):
                plot_details.extend([[
                    sg.Frame(f'Entry {k + 1}', [[
                        sg.Column([
                            [sg.Check('Show', enable_events=True,
                                      default=default_inputs[f'plot_boolean_{i}_{j}_{k}'],
                                      key=f'plot_boolean_{i}_{j}_{k}')],
                            [sg.Text('X Column:'),
                             sg.Combo([num for num in range(len(dataset.columns))],
                                      key=f'x_col_{i}_{j}_{k}', size=(3, 1), readonly=True,
                                      default_value=default_inputs[f'x_col_{i}_{j}_{k}'],
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Y Column:'),
                             sg.Combo([num for num in range(len(dataset.columns))],
                                      key=f'y_col_{i}_{j}_{k}', size=(3, 1), readonly=True,
                                      default_value=default_inputs[f'y_col_{i}_{j}_{k}'],
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Offset:', size=(6, 1)),
                             sg.Input(default_inputs[f'offset_{i}_{j}_{k}'], size=(8, 1),
                                      key=f'offset_{i}_{j}_{k}',
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Label:', size=(6, 1)),
                             sg.Input(default_inputs[f'label_{i}_{j}_{k}'], key=f'label_{i}_{j}_{k}',
                                      size=(8, 1), disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])]
                        ], pad=((5, 5), 5)),
                        sg.Column([
                            [sg.Text('      Marker')],
                            [sg.Text('Face\nColor:'),
                             sg.Combo(COLORS, default_value=default_inputs[f'markerface_color_{i}_{j}_{k}'],
                                      key=f'markerface_color_{i}_{j}_{k}', size=(9, 1),
                                      readonly=True,
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}']),
                             sg.Input(key=f'markerface_chooser_{i}_{j}_{k}', enable_events=True,
                                      visible=False),
                             sg.ColorChooserButton('..', target=f'markerface_chooser_{i}_{j}_{k}',
                                                   disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Edge\nColor:'),
                             sg.Combo(COLORS, default_value=default_inputs[f'markeredge_color_{i}_{j}_{k}'],
                                      key=f'markeredge_color_{i}_{j}_{k}', size=(9, 1),
                                      readonly=True,
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}']),
                             sg.Input(key=f'markeredge_chooser_{i}_{j}_{k}', enable_events=True,
                                      visible=False),
                             sg.ColorChooserButton('..', target=f'markeredge_chooser_{i}_{j}_{k}',
                                                   disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Style:'),
                             sg.Combo(MARKERS, default_value=default_inputs[f'marker_style_{i}_{j}_{k}'],
                                      key=f'marker_style_{i}_{j}_{k}', size=(13, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Edge Width:'),
                             sg.Input(default_inputs[f'marker_edgewidth_{i}_{j}_{k}'],
                                      key=f'marker_edgewidth_{i}_{j}_{k}', size=(4, 1))],
                            [sg.Text('Marker Size:'),
                             sg.Input(default_text=default_inputs[f'marker_size_{i}_{j}_{k}'],
                                      key=f'marker_size_{i}_{j}_{k}', size=(4, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])]
                        ], pad=((20, 5), 5), element_justification='center'),
                        sg.Column([
                            [sg.Text('      Line')],
                            [sg.Text('Color:'),
                             sg.Combo(COLORS, default_value=default_inputs[f'line_color_{i}_{j}_{k}'],
                                      key=f'line_color_{i}_{j}_{k}', size=(9, 1),
                                      readonly=True,
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}']),
                             sg.Input(key=f'line_chooser_{i}_{j}_{k}', enable_events=True,
                                      visible=False),
                             sg.ColorChooserButton('..', target=f'line_chooser_{i}_{j}_{k}',
                                                   disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Style:'),
                             sg.Combo(list(LINE_MAPPING), readonly=True,
                                      default_value=default_inputs[f'line_style_{i}_{j}_{k}'],
                                      key=f'line_style_{i}_{j}_{k}', size=(10, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])],
                            [sg.Text('Line Width:'),
                             sg.Input(default_text=default_inputs[f'line_size_{i}_{j}_{k}'],
                                      key=f'line_size_{i}_{j}_{k}', size=(4, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}_{j}_{k}'])]
                        ], pad=((20, 5), 5), element_justification='center')
                    ]])
                ]])

            sections = {
                'Plot Details': plot_details,
                'Legend': [
                    [sg.Check('Show Legend', default=default_inputs[f'show_legend_{i}_{j}'],
                              key=f'show_legend_{i}_{j}', enable_events=True)],
                    [sg.Text('Number of Columns:'),
                     sg.Combo([num + 1 for num in range(len(data))],
                              default_value=default_inputs[f'legend_cols_{i}_{j}'],
                              key=f'legend_cols_{i}_{j}', readonly=True, size=(3, 1))],
                    [sg.Text('Legend Location:')],
                    [sg.Radio('Automatic', f'legend_pos_{i}_{j}', key=f'legend_auto_{i}_{j}',
                              default=default_inputs[f'legend_auto_{i}_{j}'],
                              enable_events=True, pad=((20, 10), 3))],
                    [sg.Text('Position:', pad=((60, 3), 3)),
                     sg.Combo(['best', 'upper left', 'upper center', 'upper right',
                               'lower left', 'lower center', 'lower right',
                               'center left', 'center', 'center right'],
                              default_inputs[f'legend_auto_loc_{i}_{j}'],
                              key=f'legend_auto_loc_{i}_{j}', readonly=True,
                              disabled=not default_inputs[f'legend_auto_{i}_{j}'])],
                    [sg.Radio('Manual', f'legend_pos_{i}_{j}', key=f'legend_manual_{i}_{j}',
                              default=default_inputs[f'legend_manual_{i}_{j}'],
                              enable_events=True, pad=((20, 10), 3))],
                    [sg.Text(('Position of lower-left corner, as a fraction of the axis size'
                              '\n    (< 0 or > 1 will be outside of axis)'),
                             pad=((60, 3), 3))],
                    [sg.Text('x-position:', pad=((60, 3), 3)),
                     sg.Input(default_inputs[f'legend_manual_x_{i}_{j}'],
                              key=f'legend_manual_x_{i}_{j}', size=(4, 1),
                              disabled=default_inputs[f'legend_auto_{i}_{j}']),
                     sg.Text('y-position:', pad=((10, 3), 3)),
                     sg.Input(default_inputs[f'legend_manual_y_{i}_{j}'],
                              key=f'legend_manual_y_{i}_{j}', size=(4, 1),
                              disabled=default_inputs[f'legend_auto_{i}_{j}'])]
                ],
                'Grid Lines': [
                    [sg.Column([
                        [sg.Text('X Axis:')],
                        [sg.Check('Major Ticks', key=f'x_major_grid_{i}_{j}',
                                  default=default_inputs[f'x_major_grid_{i}_{j}'],
                                  disabled=label=='Twin X')],
                        [sg.Check('Minor Ticks', key=f'x_minor_grid_{i}_{j}',
                                  default=default_inputs[f'x_minor_grid_{i}_{j}'],
                                  disabled=label=='Twin X')]
                     ], pad=((20, 5), 3), element_justification='center'),
                     sg.Column([
                         [sg.Text('Y Axis:')],
                         [sg.Check('Major Ticks', key=f'y_major_grid_{i}_{j}',
                                   default=default_inputs[f'y_major_grid_{i}_{j}'],
                                   disabled=label=='Twin Y')],
                         [sg.Check('Minor Ticks', key=f'y_minor_grid_{i}_{j}',
                                   default=default_inputs[f'y_minor_grid_{i}_{j}'],
                                   disabled=label=='Twin Y')]
                     ], pad=((20, 5), 3), element_justification='center')]
                ],
                'Axes': [
                    [sg.Text('Labels')],
                    [sg.Check('X Axis Label:', default=default_inputs[f'show_x_label_{i}_{j}'],
                              key=f'show_x_label_{i}_{j}', enable_events=True,
                              disabled=default_inputs[f'x_label_disabled_{i}_{j}']),
                     sg.Input(default_text=default_inputs[f'x_label_{i}_{j}'],
                              key=f'x_label_{i}_{j}', size=(40, 1),
                              disabled=default_inputs[f'x_label_disabled_{i}_{j}'])],
                    [sg.Text('    Label Offset:'),
                     sg.Input(default_inputs[f'x_label_offset_{i}_{j}'],
                              key=f'x_label_offset_{i}_{j}',
                              disabled=default_inputs[f'x_label_disabled_{i}_{j}'])],
                    [sg.Check('Y Axis Label:', default=default_inputs[f'show_y_label_{i}_{j}'],
                              key=f'show_y_label_{i}_{j}', enable_events=True,
                              disabled=default_inputs[f'y_label_disabled_{i}_{j}']),
                     sg.Input(default_text=default_inputs[f'y_label_{i}_{j}'],
                              key=f'y_label_{i}_{j}', size=(40, 1),
                              disabled=default_inputs[f'y_label_disabled_{i}_{j}'])],
                    [sg.Text('    Label Offset:'),
                    sg.Input(default_inputs[f'y_label_offset_{i}_{j}'],
                             key=f'y_label_offset_{i}_{j}',
                             disabled=default_inputs[f'y_label_disabled_{i}_{j}'])],
                    [sg.Text('')],
                    [sg.Text('Bounds')],
                    [sg.Text('    X Minimum:'),
                     sg.Input(default_inputs[f'x_axis_min_{i}_{j}'], size=(12, 1),
                              key=f'x_axis_min_{i}_{j}', disabled=label=='Twin X'),
                     sg.Text('X Maximum:'),
                     sg.Input(default_inputs[f'x_axis_max_{i}_{j}'], size=(12, 1),
                              key=f'x_axis_max_{i}_{j}', disabled=label=='Twin X')],
                    [sg.Text('    Y Minimum:'),
                     sg.Input(default_inputs[f'y_axis_min_{i}_{j}'], size=(12, 1),
                              key=f'y_axis_min_{i}_{j}', disabled=label=='Twin Y'),
                     sg.Text('Y Maximum:'),
                     sg.Input(default_inputs[f'y_axis_max_{i}_{j}'], size=(12, 1),
                              key=f'y_axis_max_{i}_{j}', disabled=label=='Twin Y')],
                    [sg.Text('')],
                    [sg.Text('Tick Marks')],
                    [sg.Radio('Automatic', f'ticks_{i}_{j}', key=f'auto_ticks_{i}_{j}',
                              default=default_inputs[f'auto_ticks_{i}_{j}'],
                              enable_events=True, pad=((20, 10), 3))],
                    [sg.Column([
                        [sg.Text('X Axis:')],
                        [sg.Text('Major Ticks'),
                         sg.Spin(list(range(2, 11)),
                                 initial_value=default_inputs[f'x_major_ticks_{i}_{j}'],
                                 key=f'x_major_ticks_{i}_{j}', size=(3, 1),
                                 disabled=label=='Twin X')],
                        [sg.Text('Minor Ticks'),
                         sg.Spin(list(range(11)),
                                 initial_value=default_inputs[f'x_minor_ticks_{i}_{j}'],
                                 key=f'x_minor_ticks_{i}_{j}', size=(3, 1),
                                 disabled=label=='Twin X')]
                     ], pad=((40, 5), 3), element_justification='center'),
                     sg.Column([
                         [sg.Text('Y Axis:')],
                         [sg.Text('Major Ticks'),
                         sg.Spin(list(range(2, 11)), size=(3, 1),
                                 initial_value=default_inputs[f'y_major_ticks_{i}_{j}'],
                                 key=f'y_major_ticks_{i}_{j}', disabled=label=='Twin Y')],
                         [sg.Text('Minor Ticks'),
                         sg.Spin(list(range(11)), size=(3, 1),
                                 initial_value=default_inputs[f'y_minor_ticks_{i}_{j}'],
                                 key=f'y_minor_ticks_{i}_{j}', disabled=label=='Twin Y')]
                     ], pad=((40, 5), 3), element_justification='center')]
                ]
            }

            if 'Twin' not in label:
                sections.update({
                    'Secondary Axes': [
                        [sg.Text('Labels')],
                        [sg.Check('X Axis Label:', default=default_inputs[f'secondary_x_{i}_{j}'],
                                  key=f'secondary_x_{i}_{j}', enable_events=True,
                                  disabled=secondary_x_disabled),
                        sg.Input(default_text=default_inputs[f'secondary_x_label_{i}_{j}'],
                                 key=f'secondary_x_label_{i}_{j}',
                                 disabled=not default_inputs[f'secondary_x_{i}_{j}'])],
                        [sg.Text('    Label Offset:'),
                        sg.Input(default_inputs[f'secondary_x_label_offset_{i}_{j}'],
                                 key=f'secondary_x_label_offset_{i}_{j}',
                                 disabled=not default_inputs[f'secondary_x_{i}_{j}'])],
                        [sg.Text('    Expression, using "x" as the variable (eg. x + 200):'),
                        sg.Input(default_text=default_inputs[f'secondary_x_expr_{i}_{j}'],
                                 key=f'secondary_x_expr_{i}_{j}', size=(15, 1),
                                 disabled=not default_inputs[f'secondary_x_{i}_{j}'])],
                        [sg.Check('Y Axis Label:', default=default_inputs[f'secondary_y_{i}_{j}'],
                                  key=f'secondary_y_{i}_{j}', enable_events=True,
                                  disabled=secondary_y_disabled),
                        sg.Input(default_text=default_inputs[f'secondary_y_label_{i}_{j}'],
                                 key=f'secondary_y_label_{i}_{j}',
                                 disabled=not default_inputs[f'secondary_y_{i}_{j}'])],
                        [sg.Text('    Label Offset:'),
                        sg.Input(default_inputs[f'secondary_y_label_offset_{i}_{j}'],
                                 key=f'secondary_y_label_offset_{i}_{j}',
                                 disabled=not default_inputs[f'secondary_y_{i}_{j}'])],
                        [sg.Text('    Expression, using "y" as the variable (eg. y - 50):'),
                        sg.Input(default_text=default_inputs[f'secondary_y_expr_{i}_{j}'],
                                 key=f'secondary_y_expr_{i}_{j}', size=(15, 1),
                                 disabled=not default_inputs[f'secondary_y_{i}_{j}'])],
                        [sg.Text('')],
                        [sg.Text('Tick Marks')],
                        [sg.Radio('Automatic', f'secondary_ticks_{i}_{j}',
                                  key=f'auto_ticks_secondary_{i}_{j}',
                                  default=default_inputs[f'auto_ticks_secondary_{i}_{j}'],
                                  enable_events=True, pad=((20, 10), 3))],
                        [sg.Column([
                            [sg.Text('X Axis:')],
                            [sg.Text('Major Ticks'),
                             sg.Spin(list(range(2, 11)),
                                     initial_value=default_inputs[f'secondary_x_major_ticks_{i}_{j}'],
                                     key=f'secondary_x_major_ticks_{i}_{j}', size=(3, 1))],
                            [sg.Text('Minor Ticks'),
                             sg.Spin(list(range(11)),
                                     initial_value=default_inputs[f'secondary_x_minor_ticks_{i}_{j}'],
                                     key=f'secondary_x_minor_ticks_{i}_{j}', size=(3, 1))]
                         ], pad=((40, 5), 3), element_justification='center'),
                         sg.Column([
                             [sg.Text('Y Axis:')],
                             [sg.Text('Major Ticks'),
                              sg.Spin(list(range(2, 11)),
                                      initial_value=default_inputs[f'secondary_y_major_ticks_{i}_{j}'],
                                      key=f'secondary_y_major_ticks_{i}_{j}', size=(3, 1))],
                             [sg.Text('Minor Ticks'),
                              sg.Spin(list(range(11)), size=(3, 1),
                                      initial_value=default_inputs[f'secondary_y_minor_ticks_{i}_{j}'],
                                      key=f'secondary_y_minor_ticks_{i}_{j}')]
                         ], pad=((40, 5), 3), element_justification='center')]
                    ],
                    'Annotations': [
                        [sg.Button('Add Annotation', key=f'add_annotation_{i}_{j}'),
                         sg.Button('Edit Annotations', key=f'edit_annotation_{i}_{j}',
                                   disabled=not axis.texts),
                         sg.Button('Delete Annotations', key=f'delete_annotation_{i}_{j}',
                                   disabled=not axis.texts)]
                    ],
                    'Peak Labels': [
                        [sg.Button('Add Peak', key=f'add_peak_{i}_{j}'),
                         sg.Button('Edit Peaks', key=f'edit_peak_{i}_{j}',
                                   disabled=not any(line.get_label().startswith('-PEAK-') for line in axis.lines)),
                         sg.Button('Delete Peaks', key=f'delete_peak_{i}_{j}',
                                   disabled=not any(line.get_label().startswith('-PEAK-') for line in axis.lines))]
                    ]
                })

            column_width = 65
            column_layout = []
            #TODO later add the arrow symbols for collapsable sections, and add enable_events for the Text element
            #TODO need some way to know if a section should be collapsed -> if right-arrow in default_inputs[key]
            for k, section in enumerate(sections.items()):
                column_layout.extend([
                    [sg.Text(section[0], key=f'-SECTION_header_{i}_{j}_{k}', relief='ridge',
                             size=(column_width, 1), justification='center')],
                    [sg.Frame('', section[1], key=f'-SECTION_{i}_{j}_{k}',
                              border_width=0,  pad=(5, (10, 20)))]
                ])
            label_tabs.append(
                [sg.Tab(
                    label,
                    [[
                        sg.Column([
                            [sg.Text(f'\nOptions for Plot in {axis.get_label()}\n',
                                     relief='ridge', size=(column_width, 3),
                                     justification='center')],
                            [sg.Text('')],
                            *column_layout
                        ], scrollable=True, vertical_scroll_only=True,
                        size=(750, plot_utils.CANVAS_SIZE[1] - 100))
                    ]],
                    key=f'label_tab_{i}_{j}')]
            )

        axis_label = axes[key]['Main Axis'].get_label().split(', ')
        axes_tabs.append(
            [sg.Tab(f'R{axis_label[0].split(" ")[1]}, C{axis_label[1].split(" ")[1]}',
                    [[sg.TabGroup(label_tabs, key=f'label_tabgroup_{i}',
                                  tab_background_color=sg.theme_background_color())]],
                    key=f'tab_{i}')]
        )

    layout = [
        [sg.Menu([
            ['&File', ['&Save Figure Theme', ['&Save Theme', 'Save &Theme & Data'],
                       '&Load Figure Theme', '---', 'Save &Image']],
            ['&Data', ['&Show Data', '&Add Entry',
                      ['&Add Entry', 'Add &Empty Entry'], '&Remove Entry']]
        ], key='menu')],
        [sg.Column([
            [sg.TabGroup(axes_tabs, key='axes_tabgroup',
                         tab_background_color=sg.theme_background_color())],
            [sg.Button('Back', pad=(5, 10)),
             sg.Button('Update Figure', pad=(5, 10)),
             sg.Button('Reset to Defaults', pad=(5, 10)),
             sg.Button('Continue', bind_return_key=True, pad=(5, 10),
                       button_color=utils.PROCEED_COLOR)]
        ], key='options_column'),
         sg.Column([
            [sg.Canvas(key='controls_canvas', pad=(0, 0),
                       size=(plot_utils.CANVAS_SIZE[0], 10))],
            [sg.Canvas(key='fig_canvas', size=plot_utils.CANVAS_SIZE, pad=(0, 0))]
         ], size=(plot_utils.CANVAS_SIZE[0] + 20, plot_utils.CANVAS_SIZE[1] + 50),
         pad=(10, 0))
        ]
    ]

    _plot_data(data, axes, old_axes, **default_inputs, **kwargs)
    window = sg.Window('Plot Options', layout, resizable=True,
                       finalize=True, location=location)
    plot_utils.draw_figure_on_canvas(window['fig_canvas'].TKCanvas, figure,
                                     window['controls_canvas'].TKCanvas, plot_utils.PlotToolbar)
    window['options_column'].expand(True, True) # expands the column when window changes size

    return window, validations


def _plot_data(data, axes, old_axes=None, **kwargs):
    """
    Plots data and configures the axes.

    TODO: eventually split this function into several functions, each dealing
    with a separate part of the figure/axes. That way, only the parts that need
    updated will be redrawn, which should speed up the plotting.

    Parameters
    ----------
    data : list
        The list of DataFrames to be plotted.
    axes : dict
        A dictionary of plt.Axes objects.
    old_axes : dict
        A dictionary of plt.Axes objects that were previously used. Used
        to transfer annotations to the new axes.
    kwargs : dict
        Additional keyword arguments to create the plots.

    """

    try:

        if old_axes is not None:
            annotations = {}
            peaks = {}
            for key in axes:
                if 'Invisible' not in axes[key]['Main Axis'].get_label() and key in old_axes:
                    annotations[key] = old_axes[key]['Main Axis'].texts
                    peaks[key] = []
                    for line in old_axes[key]['Main Axis'].lines:
                        if line.get_label().startswith('-PEAK-'):
                            peaks[key].append(line)

        for i, key in enumerate(axes):
            if 'Invisible' in axes[key]['Main Axis'].get_label():
                continue
            # Reverse the axes so that Main Axis is plotted last, while keeping the indices correct
            for j, label in zip(itertools.count(len(axes[key]) - 1, -1), reversed(list(axes[key].keys()))):
                axis = axes[key][label]
                axis.clear() #TODO check if this is needed, or can be replaced with a faster alternative

                for k, dataset in enumerate(data):
                    if kwargs[f'plot_boolean_{i}_{j}_{k}']:

                        x_index = int(kwargs[f'x_col_{i}_{j}_{k}'])
                        y_index = int(kwargs[f'y_col_{i}_{j}_{k}'])
                        x_data = dataset.iloc[:, x_index].astype(float).to_numpy()
                        y_data = dataset.iloc[:, y_index].astype(float).to_numpy()

                        nan_mask = (~np.isnan(x_data)) & (~np.isnan(y_data))

                        x = x_data[nan_mask]
                        y = y_data[nan_mask] + float(kwargs[f'offset_{i}_{j}_{k}']) #TODO put the scale multiplier here, would be like * float(kwargs[f'y_axis_scale_{i}_{j}'])

                        axis.plot(
                            x, y,
                            marker=utils.string_to_unicode(kwargs[f'marker_style_{i}_{j}_{k}'].split(' ')[0]),
                            markersize=float(kwargs[f'marker_size_{i}_{j}_{k}']),
                            markerfacecolor=kwargs[f'markerface_color_{i}_{j}_{k}'],
                            markeredgecolor=kwargs[f'markeredge_color_{i}_{j}_{k}'],
                            markeredgewidth=float(kwargs[f'marker_edgewidth_{i}_{j}_{k}']),
                            color=kwargs[f'line_color_{i}_{j}_{k}'],
                            linewidth=float(kwargs[f'line_size_{i}_{j}_{k}']),
                            label=utils.string_to_unicode(kwargs[f'label_{i}_{j}_{k}']),
                            linestyle=LINE_MAPPING[kwargs[f'line_style_{i}_{j}_{k}']],
                        )

                if kwargs[f'show_x_label_{i}_{j}']:
                    axis.set_xlabel(utils.string_to_unicode(kwargs[f'x_label_{i}_{j}']),
                                    labelpad=float(kwargs[f'x_label_offset_{i}_{j}']))
                if kwargs[f'show_y_label_{i}_{j}']:
                    axis.set_ylabel(utils.string_to_unicode(kwargs[f'y_label_{i}_{j}']),
                                    labelpad=float(kwargs[f'y_label_offset_{i}_{j}']))

                if label != 'Twin X':
                    axis.grid(kwargs[f'x_major_grid_{i}_{j}'], which='major', axis='x')
                    axis.grid(kwargs[f'x_minor_grid_{i}_{j}'], which='minor', axis='x')
                if label != 'Twin Y':
                    axis.grid(kwargs[f'y_major_grid_{i}_{j}'], which='major', axis='y')
                    axis.grid(kwargs[f'y_minor_grid_{i}_{j}'], which='minor', axis='y')

                if kwargs['share_x'] and i not in (0, len(axes) - 1): #TODO does this actually do anything??/will it be needed since user can set tick marks?
                    prune = 'both'
                else:
                    prune = None

                if kwargs[f'x_axis_min_{i}_{j}'] is not None:
                    if label != 'Twin X':
                        axis.set_xlim(float(kwargs[f'x_axis_min_{i}_{j}']),
                                      float(kwargs[f'x_axis_max_{i}_{j}']))
                    if label != 'Twin Y':
                        axis.set_ylim(float(kwargs[f'y_axis_min_{i}_{j}']),
                                      float(kwargs[f'y_axis_max_{i}_{j}']))

                if label != 'Twin X':
                    axis.xaxis.set_major_locator(
                        MaxNLocator(prune=None, nbins=kwargs[f'x_major_ticks_{i}_{j}'],
                                    steps=[1, 2, 2.5, 4, 5, 10]))
                    axis.xaxis.set_minor_locator(
                        AutoMinorLocator(kwargs[f'x_minor_ticks_{i}_{j}'] + 1))
                if label != 'Twin Y':
                    axis.yaxis.set_major_locator(
                        MaxNLocator(prune=prune, nbins=kwargs[f'y_major_ticks_{i}_{j}'],
                                    steps=[1, 2, 2.5, 4, 5, 10]))
                    axis.yaxis.set_minor_locator(
                        AutoMinorLocator(kwargs[f'y_minor_ticks_{i}_{j}'] + 1))

                if kwargs[f'show_legend_{i}_{j}']:
                    if kwargs[f'legend_auto_{i}_{j}']:
                        loc = kwargs[f'legend_auto_loc_{i}_{j}']
                    else:
                        loc = (
                            float(kwargs[f'legend_manual_x_{i}_{j}']),
                            float(kwargs[f'legend_manual_y_{i}_{j}'])
                        )
                    legend = axis.legend(ncol=kwargs[f'legend_cols_{i}_{j}'], loc=loc)
                    legend.set_in_layout(False)

                if 'Twin' not in label and kwargs[f'secondary_x_{i}_{j}']:
                    if kwargs[f'secondary_x_expr_{i}_{j}']:
                        functions = _parse_equation(kwargs[f'secondary_x_expr_{i}_{j}'])
                    else:
                        functions = None

                    sec_x_axis = axis.secondary_xaxis('top', functions=functions)
                    sec_x_axis.set_xlabel(
                        utils.string_to_unicode(kwargs[f'secondary_x_label_{i}_{j}']),
                        labelpad=float(kwargs[f'secondary_x_label_offset_{i}_{j}'])
                    )
                    sec_x_axis.xaxis.set_major_locator(
                        MaxNLocator(prune=None, nbins=kwargs[f'secondary_x_major_ticks_{i}_{j}'],
                                    steps=[1, 2, 2.5, 4, 5, 10]))
                    sec_x_axis.xaxis.set_minor_locator(
                        AutoMinorLocator(kwargs[f'secondary_x_minor_ticks_{i}_{j}'] + 1))

                if 'Twin' not in label and kwargs[f'secondary_y_{i}_{j}']:
                    if kwargs[f'secondary_y_expr_{i}_{j}']:
                        functions = _parse_equation(kwargs[f'secondary_y_expr_{i}_{j}'], False)
                    else:
                        functions = None

                    sec_y_axis = axis.secondary_yaxis('right', functions=functions)
                    sec_y_axis.set_ylabel(
                        utils.string_to_unicode(kwargs[f'secondary_y_label_{i}_{j}']),
                        labelpad=float(kwargs[f'secondary_y_label_offset_{i}_{j}'])
                    )
                    sec_y_axis.yaxis.set_major_locator(
                        MaxNLocator(prune=None, nbins=kwargs[f'secondary_y_major_ticks_{i}_{j}'],
                                    steps=[1, 2, 2.5, 4, 5, 10]))
                    sec_y_axis.yaxis.set_minor_locator(
                        AutoMinorLocator(kwargs[f'secondary_y_minor_ticks_{i}_{j}'] + 1))

    except Exception as e:
        sg.popup(f'Error creating plot:\n\n    {repr(e)}\n')
    finally:
        # Ensures that the annotations and peaks are maintained if an exception occurres
        if old_axes is not None:
            for key in annotations:
                for annotation in annotations[key]:
                    # Cannot directly copy artists because the transformations will not
                    # update in the new axis
                    axes[key]['Main Axis'].annotate(
                        annotation.get_text(),
                        xy=annotation.xy,
                        xytext=annotation.xyann,
                        fontsize=annotation.get_fontsize(),
                        arrowprops=annotation.arrowprops,
                        rotation=annotation.get_rotation(),
                        color=annotation.get_color(),
                        horizontalalignment=annotation.get_horizontalalignment(),
                        verticalalignment=annotation.get_verticalalignment(),
                        annotation_clip=False,
                        in_layout=False
                    )

                for peak in peaks[key]:
                    axes[key]['Main Axis'].plot(
                        *peak.get_data(),
                        linestyle=peak.get_linestyle(),
                        linewidth=peak.get_linewidth(),
                        color=peak.get_color(),
                        marker=peak.get_marker(),
                        markerfacecolor=peak.get_markerfacecolor(),
                        markeredgecolor=peak.get_markeredgecolor(),
                        markeredgewidth=peak.get_markeredgewidth(),
                        markersize=peak.get_markersize(),
                        label=peak.get_label()
                    )


def _parse_equation(expression, x_axis=True):
    """
    Uses sympy to parse a string expression and obtain the function and its inverse.

    Used to create forward and backward equations for secondary axes.

    Parameters
    ----------
    expression : str
        The string to parse and turn into a function. Must have the variable
        'x' or 'y'. For example, 'x + 50' would mean the values of the secondary
        x-axis would be equal to the main x-axis values + 50.
    x_axis : bool
        True designates that the expression is for the x-axis, in which case the
        main variable will be 'x' in the input expression. If False, the main
        variable in the input expression is 'y'

    Returns
    -------
    equation : function
        The function corresponding to the input expression.
    inverse : function
        The inverse function of the input expression.

    Notes
    -----
    sympy is imported within the function because this function will rarely
    be used, and sympy takes a significant time to import.

    """

    import sympy as sp

    var_a, var_b = ('x', 'y') if x_axis else ('y', 'x')

    eqn_a = sp.parse_expr(expression)
    equation = sp.lambdify([var_a], eqn_a, ['numpy'])

    eqn_b = sp.solve([sp.Symbol(var_b) - eqn_a],
                     [sp.Symbol(var_a)], dict=True)[0][sp.Symbol(var_a)]
    inverse = sp.lambdify([var_b], eqn_b, ['numpy'])

    return equation, inverse


def _add_remove_dataset(current_data, plot_details, data_list=None,
                        add_dataset=True, axes=None):
    """
    Allows adding a data entry from the available data_list or removing a data entry.

    Parameters
    ----------
    current_data : list
        The current list of DataFrames that are being plotted.
    plot_details : dict
        The dictionary containing all the plot properties for each dataset.
    data_list : list
        A nested list of lists of DataFrames; contains all of the
        data that will eventually be plotted.
    add_dataset : bool
        If True, will launch gui to add a dataset; if False, will launch
        gui to delete a dataset.
    axes : dict, optional
        A dictionary of axes in the figure.

    Returns
    -------
    current_data : list
        The input list with the selected dataset appended to it or removed
        from it.

    """

    axes = axes if axes is not None else [[]]

    if add_dataset:
        dataset_text = 'Chose the data entry to add:'
        button_text = 'Add Entry'
        append_dataset = True
        remove_dataset = False
        display_data = data_list

        upper_layout = [
            [sg.Text('Choose dataset to use:')],
            [sg.Combo([f'Dataset {i + 1}' for i in range(len(data_list))], '',
                      key='group', readonly=True,
                      enable_events=True, size=(10, 1))],
            [sg.Text('')],
            [sg.Text(dataset_text)],
            [sg.Combo([], '', key='data_list', disabled=True, size=(10, 1))]
        ]

    else:
        dataset_text = 'Chose the data entry to remove:'
        button_text = 'Remove Entry'
        append_dataset = False
        remove_dataset = True
        display_data = current_data

        upper_layout = [
            [sg.Text(dataset_text)],
            [sg.Listbox([f'Entry {i + 1}' for i in range(len(current_data))],
                        select_mode='multiple', key='data_list', size=(20, 5))]
        ]

    layout = [
        *upper_layout,
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Show Data'),
         sg.Button(button_text, bind_return_key=True,
                   button_color=utils.PROCEED_COLOR)]
    ]

    window = sg.Window('Entry Selection', layout, finalize=True)
    window.TKroot.grab_set()
    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Back'):
            append_dataset = False
            remove_dataset = False
            break

        elif event == 'Show Data':
            window.TKroot.grab_release()
            data_window = utils.show_dataframes(display_data, 'Data').finalize()
            data_window.TKroot.grab_set()
            data_window.read(close=True)
            data_window = None
            window.TKroot.grab_set()

        elif event == 'group':
            index = int(values['group'].split(' ')[-1]) - 1
            datasets = [f'Entry {i + 1}' for i in range(len(data_list[index]))]
            window['data_list'].update(values=datasets, value=datasets[0],
                                       readonly=True)
        elif event == button_text:
            if values['data_list']:
                break
            else:
                window.TKroot.grab_release()
                sg.popup('Please select an entry', title='Error')
                window.TKroot.grab_set()

    window.close()
    del window

    if append_dataset:
        dataset_index = int(values['data_list'].split(' ')[-1]) - 1
        current_data.append(data_list[index][dataset_index].copy())

    elif remove_dataset:
        indices = [int(value.split(' ')[-1]) - 1 for value in values['data_list']]
        for dataset_index in sorted(indices, reverse=True):
            del current_data[dataset_index]
            properties = (
                'plot_boolean', 'x_col', 'y_col', 'label', 'offset', 'markerface_color',
                'markeredge_color', 'marker_edgewidth', 'marker_style',
                'marker_size', 'line_color', 'line_style', 'line_size'
            )
            # reorders the plot properties
            for i, key in enumerate(axes):
                for j in range(len(axes[key])):
                    for k in range(dataset_index, len(current_data)):
                        for prop in properties:
                            plot_details[f'{prop}_{i}_{j}_{k}'] = plot_details.pop(f'{prop}_{i}_{j}_{k + 1}')

    return current_data, plot_details


def _add_remove_annotations(axis, add_annotation):
    """
    Gives options to add, edit, or remove text and arrows on the figure.

    Parameters
    ----------
    axis : plt.Axes
        The axis to add or remove annotations from. Contains all of the
        annotation information within axis.texts.
    add_annotation : bool or None
        If True, will give window to add an annotation; if False, will give
        window to remove annotations; if None, will give window to edit
        annotations.

    """

    remove_annotation = False
    validations = {'text': {'floats': [], 'user_inputs': [], 'constraints': []},
                   'arrows': {'floats': [], 'constraints': []}}

    if add_annotation:
        window_text = 'Add Annotation'
        tab_layout = [
            [sg.Radio('Text', 'annotation', default=True, key='radio_text',
                      enable_events=True),
             sg.Radio('Arrow', 'annotation', key='radio_arrow', enable_events=True)],
            [sg.TabGroup([[
                sg.Tab('Options', [
                    [sg.Text('Text:', size=(8, 1)),
                     sg.Input(key='text', size=(10, 1), focus=True)],
                    [sg.Text('x-position:', size=(8, 1)),
                     sg.Input(key='x', size=(10, 1))],
                    [sg.Text('y-position:', size=(8, 1)),
                     sg.Input(key='y', size=(10, 1))],
                    [sg.Text('Fontsize:', size=(8, 1)),
                     sg.Input(plt.rcParams['font.size'], key='fontsize', size=(10, 1))],
                    [sg.Text('Rotation, in degrees\n(positive angle rotates\ncounter-clockwise)'),
                     sg.Input('0', key='rotation', size=(5, 1))],
                    [sg.Text('Color:'),
                     sg.Combo(COLORS, default_value=COLORS[1],
                              key='text_color_', size=(9, 1), readonly=True),
                     sg.Input(key='text_chooser_', enable_events=True,
                              visible=False),
                     sg.ColorChooserButton('..', target='text_chooser_')]
                ], key='text_tab'),
                sg.Tab('Options', [
                    [sg.Text('Head:')],
                    [sg.Text('    x-position:', size=(10, 1)),
                     sg.Input(key='head_x', size=(10, 1), focus=True)],
                    [sg.Text('    y-position:', size=(10, 1)),
                     sg.Input(key='head_y', size=(10, 1))],
                    [sg.Text('Tail:')],
                    [sg.Text('    x-position:', size=(10, 1)),
                     sg.Input(key='tail_x', size=(10, 1))],
                    [sg.Text('    y-position:', size=(10, 1)),
                     sg.Input(key='tail_y', size=(10, 1))],
                    [sg.Text('')],
                    [sg.Text('Line width:'),
                     sg.Input(plt.rcParams['lines.linewidth'], key='linewidth',
                              size=(5, 1))],
                    [sg.Text('Line Syle:'),
                     sg.Combo(list(LINE_MAPPING)[1:], readonly=True,
                              default_value=list(LINE_MAPPING)[1],
                              key='linestyle', size=(11, 1))],
                    [sg.Text('Head-size multiplier:'),
                     sg.Input('1', key='head_scale', size=(5, 1))],
                    [sg.Text('Arrow Style:'),
                     sg.Combo(['-|>', '<|-', '<|-|>', '->', '<-', '<->', '-[',
                               ']-', ']-[', '|-|', '-'], default_value='-|>',
                              readonly=True, key='arrow_style')],
                    [sg.Text('Color:'),
                     sg.Combo(COLORS, default_value=COLORS[1],
                              key='arrow_color_', size=(9, 1), readonly=True),
                     sg.Input(key='arrow_chooser_', enable_events=True,
                              visible=False),
                     sg.ColorChooserButton('..', target='arrow_chooser_')]
                    ], visible=False, key='arrows_tab')
            ]], tab_background_color=sg.theme_background_color(), key='tab')]
        ]

        validations['text']['floats'].extend([
            ['x', 'x position'],
            ['y', 'y position'],
            ['fontsize', 'fontsize'],
            ['rotation', 'rotation'],
        ])
        validations['text']['constraints'].extend([
            ['fontsize', 'fontsize', '> 0'],
        ])
        validations['text']['user_inputs'].extend([
            ['text', 'Text', utils.string_to_unicode, False, None]
        ])

        validations['arrows']['floats'].extend([
            ['head_x', 'head x position'],
            ['head_y', 'head y position'],
            ['tail_x', 'tail x position'],
            ['tail_y', 'tail y position'],
            ['linewidth', 'linewidth'],
            ['head_scale', 'head-size multiplier'],
        ])
        validations['arrows']['constraints'].extend([
            ['linewidth', 'linewidth', '> 0'],
            ['head_scale', 'head-size multiplier', '> 0'],
        ])


    elif add_annotation is None:
        window_text = 'Edit Annotations'
        annotations = {'text' : [], 'text_layout': [],
                       'arrows': [], 'arrows_layout': []}

        for annotation in axis.texts:
            if annotation.arrowprops is None:
                annotations['text'].append(annotation)
            else:
                annotations['arrows'].append(annotation)

        for i, annotation in enumerate(annotations['text']):
            annotations['text_layout'].extend([
                [sg.Text(f'{i + 1})')],
                [sg.Column([
                    [sg.Text('Text:', size=(8, 1)),
                     sg.Input(utils.stringify_backslash(annotation.get_text()),
                              key=f'text_{i}', size=(10, 1))],
                    [sg.Text('x-position:', size=(8, 1)),
                     sg.Input(annotation.get_position()[0], key=f'x_{i}', size=(10, 1))],
                    [sg.Text('y-position:', size=(8, 1)),
                     sg.Input(annotation.get_position()[1], key=f'y_{i}', size=(10, 1))]
                ]),
                 sg.Column([
                     [sg.Text('Fontsize:', size=(7, 1)),
                      sg.Input(annotation.get_fontsize(), key=f'fontsize_{i}', size=(10, 1))],
                     [sg.Text('Rotation:', size=(7, 1)),
                      sg.Input(annotation.get_rotation(), key=f'rotation_{i}', size=(10, 1))],
                     [sg.Text('Color:'),
                      sg.Combo(COLORS, default_value=annotation.get_color(),
                               key=f'text_color_{i}', size=(9, 1), readonly=True),
                      sg.Input(key=f'text_chooser_{i}', enable_events=True, visible=False),
                      sg.ColorChooserButton('..', target=f'text_chooser_{i}')]
                 ])],
                [sg.Text('')]
            ])

            validations['text']['floats'].extend([
                [f'x_{i}', f'x position for Text {i + 1}'],
                [f'y_{i}', f'y position for Text {i + 1}'],
                [f'fontsize_{i}', f'fontsize for Text {i + 1}'],
                [f'rotation_{i}', f'rotation for Text {i + 1}'],
            ])
            validations['text']['constraints'].extend([
                [f'fontsize_{i}', f'fontsize for Text {i + 1}', '> 0'],
            ])
            validations['text']['user_inputs'].extend([
                [f'text_{i}', f'text in Text {i + 1}',
                 utils.string_to_unicode, False, None]
            ])

        for i, annotation in enumerate(annotations['arrows']):
            for style in LINE_MAPPING:
                if LINE_MAPPING[style] == annotation.arrowprops['linestyle']:
                    break

            annotations['arrows_layout'].extend([
                [sg.Text(f'{i + 1})')],
                [sg.Column([
                    [sg.Text('Head:')],
                    [sg.Text('    x-position:', size=(10, 1)),
                     sg.Input(annotation.xy[0], key=f'head_x_{i}', size=(10, 1),
                              focus=True)],
                    [sg.Text('    y-position:', size=(10, 1)),
                     sg.Input(annotation.xy[1], key=f'head_y_{i}', size=(10, 1))]
                ]),
                 sg.Column([
                     [sg.Text('Tail:')],
                     [sg.Text('    x-position:', size=(10, 1)),
                      sg.Input(annotation.xyann[0], key=f'tail_x_{i}', size=(10, 1))],
                     [sg.Text('    y-position:', size=(10, 1)),
                      sg.Input(annotation.xyann[1], key=f'tail_y_{i}', size=(10, 1))]
                 ])],
                [sg.Text('Line width:'),
                 sg.Input(annotation.arrowprops['linewidth'], key=f'linewidth_{i}',
                          size=(5, 1))],
                [sg.Text('Line Syle:'),
                 sg.Combo(list(LINE_MAPPING)[1:], readonly=True,
                          default_value=style,
                          key=f'linestyle_{i}', size=(11, 1))],
                [sg.Text('Head-size multiplier:'),
                 sg.Input(annotation.arrowprops['mutation_scale'] / 10,
                          key=f'head_scale_{i}', size=(5, 1))],
                [sg.Text('Arrow Style:'),
                 sg.Combo(['-|>', '<|-', '<|-|>', '->', '<-', '<->', '-[',
                           ']-', ']-[', '|-|', '-'],
                          default_value=annotation.arrowprops['arrowstyle'],
                          readonly=True, key=f'arrow_style_{i}')],
                [sg.Text('Color:'),
                 sg.Combo(COLORS, default_value=annotation.arrowprops['color'],
                          key=f'arrow_color_{i}', size=(9, 1), readonly=True),
                 sg.Input(key=f'arrow_chooser_{i}', enable_events=True, visible=False),
                 sg.ColorChooserButton('..', target=f'arrow_chooser_{i}')],
                [sg.Text('')]
            ])

            validations['arrows']['floats'].extend([
                [f'head_x_{i}', f'head x position for Arrow {i + 1}'],
                [f'head_y_{i}', f'head y position for Arrow {i + 1}'],
                [f'tail_x_{i}', f'tail x position for Arrow {i + 1}'],
                [f'tail_y_{i}', f'tail y position for Arrow {i + 1}'],
                [f'linewidth_{i}', f'linewidth for Arrow {i + 1}'],
                [f'head_scale_{i}', f'head-size multiplier for Arrow {i + 1}'],
            ])
            validations['arrows']['constraints'].extend([
                [f'linewidth_{i}', f'linewidth for Arrow {i + 1}', '> 0'],
                [f'head_scale_{i}', f'head-size multiplier for Arrow {i + 1}', '> 0'],
            ])

        tab_layout = [[
            sg.TabGroup([[
                sg.Tab('Text', [[sg.Column(annotations['text_layout'],
                                           scrollable=True, size=(None, 400),
                                           vertical_scroll_only=True)]],
                       key='text_tab'),
                sg.Tab('Arrows', [[sg.Column(annotations['arrows_layout'],
                                             scrollable=True, size=(None, 400),
                                             vertical_scroll_only=True)]],
                       key='arrows_tab')
            ]], tab_background_color=sg.theme_background_color())
        ]]

    else:
        remove_annotation = True
        window_text = 'Remove Annotations'
        annotations = {'text': {}, 'arrows': {}}
        for i, annotation in enumerate(axis.texts):
            if annotation.arrowprops is not None:
                annotations['arrows'][
                    f'{len(annotations["arrows"]) + 1}) Tail: {annotation.xyann}, Head: {annotation.xy}'
                ] = i
            else:
                annotations['text'][
                    f'{len(annotations["text"]) + 1}) Text: "{annotation.get_text():.15}", Position: {annotation.get_position()}'
                ] = i

        tab_layout = [
            [sg.Text('All selected annotations will be deleted!\n')],
            [sg.TabGroup([[
                sg.Tab('Text', [[sg.Listbox(list(annotations['text']),
                                            select_mode='multiple', size=(40, 5),
                                            key='text_listbox')]],
                       key='text_tab'),
                sg.Tab('Arrows', [[sg.Listbox(list(annotations['arrows']),
                                              select_mode='multiple', size=(40, 5),
                                              key='arrows_listbox')]],
                       key='arrows_tab')
            ]], tab_background_color=sg.theme_background_color())]
        ]

    layout = [
        *tab_layout,
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Submit', bind_return_key=True, button_color=utils.PROCEED_COLOR)]
    ]

    window = sg.Window(window_text, layout, finalize=True)
    window.TKroot.grab_set()
    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Back'):
            add_annotation = False
            remove_annotation = False
            break

        elif event.startswith('radio'):
            if values['radio_text']:
                window['text_tab'].update(visible=True)
                window['text_tab'].select()
                window['arrows_tab'].update(visible=False)
            else:
                window['arrows_tab'].update(visible=True)
                window['arrows_tab'].select()
                window['text_tab'].update(visible=False)

        # color chooser button
        elif 'chooser' in event:
            if values[event] != 'None':
                property_type = event.split('_')[0]
                index = event.split('_')[-1]
                window[f'{property_type}_color_{index}'].update(value=values[event])

        elif event == 'Submit':
            window.TKroot.grab_release()
            close = True

            if add_annotation:
                if values['radio_text']:
                    close = utils.validate_inputs(values, **validations['text'])
                else:
                    close = utils.validate_inputs(values, **validations['arrows'])

            elif add_annotation is None:
                close = (utils.validate_inputs(values, **validations['text'])
                         and utils.validate_inputs(values, **validations['arrows']))

            else:
                close = values['text_listbox'] or values['arrows_listbox']
                if not close:
                    sg.popup('Please select an annotation to delete.',
                             title='Error')

            if not close:
                window.TKroot.grab_set()
            else:
                break

    window.close()
    del window

    if add_annotation:
        if values['radio_text']:
            axis.annotate(
                values['text'],
                xy=(values['x'], values['y']), fontsize=values['fontsize'],
                rotation=values['rotation'], color=values['text_color_'],
                annotation_clip=False, in_layout=False
            )
        else:
            axis.annotate(
                '', xy=(values['head_x'], values['head_y']),
                xytext=(values['tail_x'], values['tail_y']),
                annotation_clip=False, in_layout=False,
                arrowprops={
                    'linewidth': values['linewidth'],
                    'mutation_scale': 10 * values['head_scale'], # *10 b/c the connectionpatch defaults to 10 rather than 1
                    'arrowstyle': values['arrow_style'],
                    'color': values['arrow_color_'],
                    'linestyle': LINE_MAPPING[values['linestyle']]}
            )

    elif add_annotation is None:
        for i, annotation in enumerate(annotations['text']):
            annotation.update({
                'text': values[f'text_{i}'],
                'color': values[f'text_color_{i}'],
                'position': (values[f'x_{i}'], values[f'y_{i}']),
                'fontsize': values[f'fontsize_{i}'],
                'rotation': values[f'rotation_{i}'],
                'in_layout': False, 'annotation_clip': False
            })

        for i, annotation in enumerate(annotations['arrows']):
            # not able to move arrow head location, so have to create new annotations
            axis.texts[axis.texts.index(annotation)].remove()
            axis.annotate(
                '', xy=(values[f'head_x_{i}'], values[f'head_y_{i}']),
                xytext=(values[f'tail_x_{i}'], values[f'tail_y_{i}']),
                annotation_clip=False, in_layout=False,
                arrowprops={
                    'linewidth': values[f'linewidth_{i}'],
                    'mutation_scale': 10 * values[f'head_scale_{i}'],
                    'arrowstyle': values[f'arrow_style_{i}'],
                    'color': values[f'arrow_color_{i}'],
                    'linestyle': LINE_MAPPING[values[f'linestyle_{i}']]}
            )

    elif remove_annotation:
        indices = []
        for entry in values['text_listbox']:
            indices.append(annotations['text'][entry])
        for entry in values['arrows_listbox']:
            indices.append(annotations['arrows'][entry])

        for index in sorted(indices, reverse=True):
            axis.texts[index].remove()


def _add_remove_peaks(axis, add_peak):
    """
    Gives options to add, edit, or remove peaks and peak markers on the figure.

    Parameters
    ----------
    axis : plt.Axes
        The axis to add or remove peaks from. Contains all of the
        peaks information within axis.lines. Each line for a peak
        has a label corresponding to '-PEAK-peak_name'.
    add_peak : bool or None
        If True, will give window to add a peak; if False, will give
        window to remove peaks; if None, will give window to edit
        peaks.

    """

    remove_peak = False
    validations = {'line': {'floats': [], 'user_inputs': [], 'constraints': []},
                   'marker': {'floats': [], 'user_inputs': [], 'constraints': []}}

    peaks = {}
    non_peaks = {}
    for i, line in enumerate(axis.lines):
        if line.get_label().startswith('-PEAK-'):
            key = ''.join(line.get_label().split('-PEAK-'))
            if key not in peaks:
                peaks[key] = {'peaks': [], 'annotations': []}
            peaks[key]['peaks'].append(line)

        elif not all(np.isnan(line.get_xdata())):
            non_peaks[i] = line

    for annotation in axis.texts:
        if annotation.get_text() in peaks:
            peaks[annotation.get_text()]['annotations'].append(annotation)

    if add_peak:
        window_text = 'Add Peak'
        non_peak_labels = [
            f'Line #{key + 1} ({line.get_label()})' for key, line in non_peaks.items()
        ]

        inner_layout = [
            [sg.Text('Peak Label:'),
             sg.Input(key='label', size=(10, 1))],
            [sg.Check('Place label above each marker', key='show_label')],
            [sg.Text('Defining Axis:'),
             sg.Combo(('x', 'y'), key='defining_axis', default_value='x',
                      size=(5, 1), readonly=True)],
            [sg.Text('Peak Positions (separate\nmultiple entries with a comma):'),
             sg.Input(key='positions', size=(10, 1))],
            [sg.Text('Select all lines to add peaks to')],
            [sg.Listbox(non_peak_labels, select_mode='multiple',
                        size=(30, 5), key='peak_listbox')],
            [sg.Text('Peak Label Type:'),
             sg.Radio('Marker', 'label_type', default=True, key='radio_marker',
                      enable_events=True),
             sg.Radio('Line', 'label_type', key='radio_line', enable_events=True)],
            [sg.TabGroup([[
                sg.Tab('Options', [
                    [sg.Text('Face Color:'),
                     sg.Combo(COLORS, default_value=COLORS[1], size=(9, 1),
                              key='face_color_', readonly=True),
                     sg.Input(key='face_chooser_', enable_events=True, visible=False),
                     sg.ColorChooserButton('..', target='face_chooser_')],
                    [sg.Text('Edge Color:'),
                     sg.Combo(COLORS, default_value=COLORS[1], size=(9, 1),
                              key='edge_color_', readonly=True),
                     sg.Input(key='edge_chooser_', enable_events=True, visible=False),
                     sg.ColorChooserButton('..', target='edge_chooser_')],
                    [sg.Text('Edge Line Width:'),
                     sg.Input(plt.rcParams['lines.markeredgewidth'],
                              key='edge_width', size=(4, 1))],
                    [sg.Text('Style:'),
                     sg.Combo(MARKERS, default_value=MARKERS[1],
                              key='marker_style', size=(13, 1))],
                    [sg.Text('Size:'),
                     sg.Input(plt.rcParams['lines.markersize'],
                              key='marker_size', size=(4, 1))]
                ], key='tab_marker'),
                sg.Tab('Options', [
                    [sg.Text('Color:'),
                     sg.Combo(COLORS, default_value=COLORS[1], size=(9, 1),
                              key='line_color_', readonly=True),
                     sg.Input(key='line_chooser_', enable_events=True, visible=False),
                     sg.ColorChooserButton('..', target='line_chooser_')],
                    [sg.Text('Style:'),
                     sg.Combo(list(LINE_MAPPING), readonly=True, size=(10, 1),
                              default_value=list(LINE_MAPPING)[1], key='line_style')],
                    [sg.Text('Line Width:'),
                     sg.Input(plt.rcParams['lines.linewidth'], key='line_size',
                              size=(4, 1))]
                    ], visible=False, key='tab_line')
            ]], tab_background_color=sg.theme_background_color(), key='tab')]
        ]

        for key in ('line', 'marker'):
            validations[key]['user_inputs'].extend([
                ['label', 'Peak Label', utils.string_to_unicode, False, None],
                ['positions', 'Peak Positions', float]
            ])
            validations[key]['floats'].append(
                [f'{key}_size', f'{key} size']
            )
            validations[key]['constraints'].append(
                [f'{key}_size', f'{key} size', '> 0']
            )
        validations['marker']['user_inputs'].append(
            ['marker_style', 'marker style', utils.string_to_unicode, True, None]
        )
        validations['marker']['floats'].append(['edge_width', 'edge line width'])
        validations['marker']['constraints'].append(
            ['edge_width', 'edge line width', '> 0']
        )

    elif add_peak is None:
        window_text = 'Edit Peaks'

        column_layout = []
        for i, peak in enumerate(peaks):
            column_layout.extend([
                [sg.Text(f'Peak #{i + 1}', relief='ridge', justification='center')],
                [sg.Text('Peak Label:'),
                 sg.Input(utils.stringify_backslash(peak),
                          key=f'label_{i}', size=(10, 1))],
                [sg.Text('Positions:')]
            ])

            for j, line in enumerate(peaks[peak]['peaks']):
                column_layout.append([
                    sg.Text(f'  Position #{j + 1}:    '),
                    sg.Check('Delete?', key=f'delete_peak_{i}_{j}')
                ])

                for k, data in enumerate(line.get_xydata()):
                    column_layout.append([
                        sg.Text(f'    X{k + 1}:'),
                        sg.Input(data[0], size=(8, 1), key=f'x_{i}_{j}_{k}'),
                        sg.Text(f'Y{k + 1}:'),
                        sg.Input(data[1], size=(8, 1), key=f'y_{i}_{j}_{k}')
                    ])

                    validations['marker']['floats'].extend([
                        [f'x_{i}_{j}_{k}', f'Position #{j + 1}, X{k + 1} for peak #{i + 1}'],
                        [f'y_{i}_{j}_{k}', f'Position #{j + 1}, Y{k + 1} for peak #{i + 1}']
                    ])

            validations['marker']['user_inputs'].append(
                [f'label_{i}', f'Peak Label {i + 1}', utils.string_to_unicode, False, None]
            )

            if peaks[peak]['peaks'][0].get_xdata().size > 1: # a line
                for style, linestyle in LINE_MAPPING.items():
                    if linestyle == line.get_linestyle():
                        break
                else: # in case no break
                    style = line.get_linestyle()

                column_layout.extend([
                    [sg.Text('Color:'),
                     sg.Combo(COLORS, default_value=line.get_color(), size=(9, 1),
                              key=f'line_color_{i}', readonly=True),
                     sg.Input(key=f'line_chooser_{i}', enable_events=True, visible=False),
                     sg.ColorChooserButton('..', target=f'line_chooser_{i}')],
                    [sg.Text('Style:'),
                     sg.Combo(list(LINE_MAPPING), readonly=True, size=(10, 1),
                              default_value=style, key=f'line_style_{i}')],
                    [sg.Text('Line Width:'),
                     sg.Input(line.get_linewidth(), key=f'line_size_{i}',
                              size=(5, 1))]
                ])

                validations['marker']['floats'].append(
                    [f'line_size_{i}', f'line width for peak #{i + 1}']
                )
                validations['marker']['constraints'].append(
                    [f'line_size_{i}', f'line width for peak #{i + 1}', '> 0']
                )

            else: # a marker
                marker = utils.stringify_backslash(line.get_marker())
                for j, mark in enumerate(MARKERS):
                    if mark[0] == marker:
                        marker = MARKERS[j]
                        break

                column_layout.extend([
                    [sg.Text('Face Color:'),
                     sg.Combo(COLORS, default_value=line.get_markerfacecolor(),
                              size=(9, 1), key=f'face_color_{i}', readonly=True),
                     sg.Input(key=f'face_chooser_{i}', enable_events=True, visible=False),
                     sg.ColorChooserButton('..', target=f'face_chooser_{i}')],
                    [sg.Text('Edge Color:'),
                     sg.Combo(COLORS, default_value=line.get_markeredgecolor(),
                              size=(9, 1), key=f'edge_color_{i}', readonly=True),
                     sg.Input(key=f'edge_chooser_{i}', enable_events=True, visible=False),
                     sg.ColorChooserButton('..', target=f'edge_chooser_{i}')],
                    [sg.Text('Edge Line Width:'),
                     sg.Input(line.get_markeredgewidth(),
                              key=f'edge_width_{i}', size=(4, 1))],
                    [sg.Text('Style:'),
                     sg.Combo(MARKERS, default_value=marker,
                              key=f'marker_style_{i}', size=(13, 1))],
                    [sg.Text('Size:'),
                     sg.Input(line.get_markersize(),
                              key=f'marker_size_{i}', size=(4, 1))],
                ])

                validations['marker']['floats'].extend([
                    [f'marker_size_{i}', f'marker size for peak #{i + 1}'],
                    [f'edge_width_{i}', f'edge line width for peak #{i + 1}']
                ])
                validations['marker']['constraints'].extend([
                    [f'marker_size_{i}', f'marker size for peak #{i + 1}', '> 0'],
                    [f'edge_width_{i}', f'edge line width for peak #{i + 1}', '> 0']
                ])
                validations['marker']['user_inputs'].append(
                    [f'marker_style_{i}', f'marker style for peak #{i + 1}',
                     utils.string_to_unicode, True, None]
                )

        inner_layout = [
            [sg.Column(column_layout, #size=(None, 400),
                       scrollable=True, vertical_scroll_only=True)]
        ]

    else:
        remove_peak = True
        window_text = 'Remove Peaks'

        labels = {}
        for peak in peaks:
            labels[utils.stringify_backslash(peak)] = peak

        inner_layout = [
            [sg.Text('All markers and text for selected peaks will be deleted!\n')],
            [sg.Listbox(list(labels.keys()), select_mode='multiple', size=(20, 5),
                        key='peak_listbox')]
        ]

    layout = [
        *inner_layout,
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Submit', bind_return_key=True, button_color=utils.PROCEED_COLOR)]
    ]

    window = sg.Window(window_text, layout, finalize=True)
    window.TKroot.grab_set()
    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Back'):
            add_peak = False
            remove_peak = False
            break

        elif event.startswith('radio'):
            if values['radio_marker']:
                window['tab_marker'].update(visible=True)
                window['tab_marker'].select()
                window['tab_line'].update(visible=False)
            else:
                window['tab_line'].update(visible=True)
                window['tab_line'].select()
                window['tab_marker'].update(visible=False)

        # color chooser button
        elif 'chooser' in event:
            if values[event] != 'None':
                property_type = event.split('_')[0]
                index = event.split('_')[-1]
                window[f'{property_type}_color_{index}'].update(value=values[event])

        elif event == 'Submit':
            window.TKroot.grab_release()
            close = True

            if add_peak:
                if values['radio_marker']:
                    close = utils.validate_inputs(values, **validations['marker'])
                else:
                    close = utils.validate_inputs(values, **validations['line'])

                if close:
                    if values['label'] in peaks:
                        close = False
                        sg.popup(
                            'The selected peak label is already a peak.\n',
                            title='Error'
                        )
                    elif not values['peak_listbox']:
                        close = False
                        sg.popup(
                            'Please select a line on which to add peak markers.\n',
                            title='Error'
                        )

            elif add_peak is None:
                close = utils.validate_inputs(values, **validations['marker'])
                if close:
                    labels = [
                        values[label] for label in values if label.startswith('label')
                    ]
                    if len(labels) != len(set(labels)):
                        close = False
                        sg.popup(
                            'There cannot be repeated peak labels.\n', title='Error'
                        )

            else:
                close = values['peak_listbox']
                if not close:
                    sg.popup('Please select a peak to delete.\n', title='Error')

            if not close:
                window.TKroot.grab_set()
            else:
                break

    window.close()
    del window

    if add_peak:
        # main designates defining axis, secondary designates non-defining axis
        positions = values['positions']
        secondary_limits = getattr(
            axis, f'get_{"xy".replace(values["defining_axis"], "")}lim')()
        offset = 0.05 * (secondary_limits[1] - secondary_limits[0])

        plot_data = {'x': [], 'y': []}
        for peak in values['peak_listbox']:
            line = non_peaks[int(peak.split(' ')[1].replace('#', '')) - 1]

            main_data = getattr(line, f'get_{values["defining_axis"]}data')()
            secondary_data = getattr(
                line, f'get_{"xy".replace(values["defining_axis"], "")}data')()

            for position in positions:
                plot_data[values['defining_axis']].append(
                    (position, position) if values['radio_line'] else (position,)
                )

                if values['radio_marker']:
                    data_point = (secondary_data[np.abs(main_data - position).argmin()] + offset,)
                else:
                    min_secondary = secondary_data.min()
                    max_secondary = secondary_data.max()
                    data_point = (min_secondary - offset, max_secondary + offset)

                plot_data['xy'.replace(values['defining_axis'], '')].append(data_point)

        for data in zip(plot_data['x'], plot_data['y']):
            axis.plot(
                *data,
                label='-PEAK-' + values['label'],
                marker=values['marker_style'].split(' ')[0] if values['radio_marker'] else 'None',
                markersize=values['marker_size'] if values['radio_marker'] else None,
                markerfacecolor=values['face_color_'] if values['radio_marker'] else 'None',
                markeredgecolor=values['edge_color_'] if values['radio_marker'] else 'None',
                markeredgewidth=values[f'edge_width'] if values['radio_marker'] else None,
                color=values['line_color_'] if values['radio_line'] else 'None',
                linewidth=values['line_size'] if values['radio_line'] else None,
                linestyle=LINE_MAPPING[values['line_style']] if values['radio_line'] else ''
            )

            if values['show_label']:
                annotation_position = (
                    data[0][-1] + offset if values['defining_axis'] == 'y' else data[0][-1],
                    data[1][-1] + offset if values['defining_axis'] == 'x' else data[1][-1]
                )
                axis.annotate(
                    values['label'],
                    xy=annotation_position,
                    rotation=90 if values['defining_axis'] == 'x' else 0,
                    horizontalalignment='center' if values['defining_axis'] == 'x' else 'left',
                    verticalalignment='center' if values['defining_axis'] == 'y' else 'baseline',
                    annotation_clip=False,
                    in_layout=False,
                )

    elif add_peak is None:
        for i, key in enumerate(peaks):
            for annotation in peaks[key]['annotations']:
                annotation.update({'text': values[f'label_{i}']})

            deleted_peaks = []
            for j, line in enumerate(peaks[key]['peaks']):
                if values[f'delete_peak_{i}_{j}']:
                    deleted_peaks.append(line)
                else:
                    line.update({
                        'xdata': [values[entry] for entry in values if entry.startswith(f'x_{i}_{j}_')],
                        'ydata': [values[entry] for entry in values if entry.startswith(f'y_{i}_{j}_')],
                        'label': '-PEAK-' + values[f'label_{i}'],
                        'marker': values.get(f'marker_style_{i}', 'None').split(' ')[0],
                        'markerfacecolor': values.get(f'face_color_{i}', 'None'),
                        'markeredgecolor': values.get(f'edge_color_{i}', 'None'),
                        'markeredgewidth': values.get(f'edge_width_{i}', 0),
                        'markersize': values.get(f'marker_size_{i}', 0),
                        'linestyle': LINE_MAPPING[values.get(f'line_style_{i}', 'None')],
                        'linewidth': values.get(f'line_size_{i}', 0),
                        'color': values.get(f'line_color_{i}', 'None'),
                    })

            for line in deleted_peaks:
                line.remove()

    elif remove_peak:
        for entry in values['peak_listbox']:
            for line in peaks[labels[entry]]['peaks']:
                line.remove()
            for annotation in peaks[labels[entry]]['annotations']:
                annotation.remove()


def _plot_options_event_loop(data_list, mpl_changes=None, input_fig_kwargs=None,
                             input_axes=None, input_values=None):
    """
    Handles the event loop for the plot options gui.

    Parameters
    ----------
    data_list : list
        A nested list of pandas DataFrames. Each list of DataFrames will
        create one figure.
    mpl_changes : dict
        Changes to matplotlib's rcParams file to alter the figure.
    input_fig_kwargs : dict, optional
        The fig_kwargs from a previous session. Only used if reloading a figure.
    input_axes : dict, optional
        A dictionary of plt.Axes objects from a reloaded session.
    input_values : dict, optional
        The values needed to recreate the previous gui window from
        a reloaded figure, or to set some default values.
        #TODO need to allow a list of dictionaries to set defaults for each dataset, like entry labels

    Returns
    -------
    figures : list
        A nested list of lists, with each entry containing the matplotlib Figure,
        and a dictionary containing the Axes.

    """

    rc_changes = mpl_changes if mpl_changes is not None else {}
    figures = []

    try:
        for i, dataframe_list in enumerate(data_list):
            data = dataframe_list.copy()

            if i == 0 and input_axes is not None: # loading a previous figure
                fig_kwargs = input_fig_kwargs.copy()
                fig, axes = _create_figure_components(**fig_kwargs)
                window, validations = _create_plot_options_gui(
                    data, fig, axes, input_values, input_axes, **fig_kwargs
                )
            else:
                fig_kwargs = _select_plot_type()
                fig, axes = _create_figure_components(**fig_kwargs)
                window, validations = _create_plot_options_gui(
                    data, fig, axes, **fig_kwargs
                )

            while True:
                event, values = window.read()
                # close
                if event == sg.WIN_CLOSED:
                    utils.safely_close_window(window)
                # finish changing the plot
                elif event == 'Continue':
                    plt.close(_PREVIEW_NAME)
                    old_axes = axes
                    fig, axes = _create_figure_components(
                        True, fig_name=f'Figure_{i+1}', **fig_kwargs
                    )
                    _plot_data(data, axes, old_axes, **values, **fig_kwargs)
                    figures.append([fig, axes])
                    plt.close(f'Figure_{i+1}')
                    break
                # save figure
                elif event == 'Save Image':
                    window.hide()
                    fig_temp, axes_temp = _create_figure_components(
                        True, fig_name=f'Save_{i+1}', **fig_kwargs
                    )
                    _plot_data(data, axes_temp, axes, **values, **fig_kwargs)
                    _save_image_options(fig_temp)
                    plt.close(f'Save_{i+1}')
                    del fig_temp, axes_temp
                    window.un_hide()
                # exports the options and potentially data required to recreate the figure
                elif event.startswith('Save Theme'):
                    window.hide()
                    if event =='Save Theme':
                        saved_data = None
                    else:
                        saved_data = data
                    _save_figure_json(values, fig_kwargs, rc_changes, axes, saved_data)
                    window.un_hide()
                # load the options required to recreate a figure layout
                elif event.startswith('Load Figure'):
                    window.hide()
                    new_figure_theme = _load_figure_theme(axes, values, fig_kwargs)

                    if not new_figure_theme:
                        window.un_hide()
                    else:
                        old_location = window.current_location()
                        window.close()
                        window = None
                        plt.close(_PREVIEW_NAME)
                        old_axes, values, fig_kwargs = new_figure_theme
                        fig, axes = _create_figure_components(**fig_kwargs)
                        window, validations = _create_plot_options_gui(
                            data, fig, axes, values, old_axes, old_location, **fig_kwargs
                        )
                # show tables of data
                elif event == 'Show Data':
                    data_window = utils.show_dataframes(data, 'Data').finalize()
                    data_window.TKroot.grab_set()
                    data_window.read(close=True)
                    data_window = None
                # add/remove data entries
                elif event.endswith('Entry'):
                    if 'Empty' in event:
                        data.append(
                            pd.DataFrame([[np.nan, np.nan], [np.nan, np.nan]],
                                         columns=['Empty Entry Column_0',
                                                  'Empty Entry Column_1'])
                        )
                    else:
                        if event == 'Add Entry':
                            window.hide()
                            add_dataset = True
                        else:
                            add_dataset = False

                        data, values = _add_remove_dataset(
                            data, values, data_list, add_dataset, axes
                        )

                    plt.close(_PREVIEW_NAME)
                    old_location = window.current_location()
                    window.close()
                    window = None
                    window, validations = _create_plot_options_gui(
                        data, fig, axes, values, axes, old_location, **fig_kwargs
                    )
                # add/edit/remove annotations
                elif 'annotation' in event:
                    if event.startswith('add_annotation'):
                        add_annotation = True
                    elif event.startswith('edit_annotation'):
                        add_annotation = None
                    else:
                        add_annotation = False

                    index = [int(num) for num in event.split('_')[-2:]]
                    key = list(axes)[index[0]]
                    label = list(axes[key])[index[1]]
                    _add_remove_annotations(axes[key][label], add_annotation)

                    _plot_data(data, axes, axes, **values, **fig_kwargs)
                    plot_utils.draw_figure_on_canvas(
                        window['fig_canvas'].TKCanvas, fig,
                        window['controls_canvas'].TKCanvas,
                        plot_utils.PlotToolbar
                    )

                    window[f'edit_annotation_{index[0]}_{index[1]}'].update(
                        disabled=not axes[key][label].texts
                    )
                    window[f'delete_annotation_{index[0]}_{index[1]}'].update(
                        disabled=not axes[key][label].texts
                    )
                # add/edit/remove peaks
                elif 'peak' in event:
                    if event.startswith('add_peak'):
                        add_peak = True
                    elif event.startswith('edit_peak'):
                        add_peak = None
                    else:
                        add_peak = False

                    index = [int(num) for num in event.split('_')[-2:]]
                    key = list(axes)[index[0]]
                    label = list(axes[key])[index[1]]
                    _add_remove_peaks(axes[key][label], add_peak)

                    _plot_data(data, axes, axes, **values, **fig_kwargs)
                    plot_utils.draw_figure_on_canvas(
                        window['fig_canvas'].TKCanvas, fig,
                        window['controls_canvas'].TKCanvas,
                        plot_utils.PlotToolbar
                    )

                    window[f'edit_peak_{index[0]}_{index[1]}'].update(
                        disabled=not any(
                            line.get_label().startswith('-PEAK-') for line in axes[key][label].lines)
                    )
                    window[f'delete_peak_{index[0]}_{index[1]}'].update(
                        disabled=not any(
                            line.get_label().startswith('-PEAK-') for line in axes[key][label].lines)
                    )
                    window[f'edit_annotation_{index[0]}_{index[1]}'].update(
                        disabled=not axes[key][label].texts
                    )
                    window[f'delete_annotation_{index[0]}_{index[1]}'].update(
                        disabled=not axes[key][label].texts
                    )
                # go back to plot type picker
                elif event == 'Back':
                    plt.close(_PREVIEW_NAME)
                    old_location = window.current_location()
                    window.close()
                    window = None
                    fig_kwargs = _select_plot_type(fig_kwargs)
                    old_axes = axes
                    fig, axes = _create_figure_components(**fig_kwargs)
                    window, validations = _create_plot_options_gui(
                        data, fig, axes, values, old_axes, old_location, **fig_kwargs
                    )
                # update the figure
                elif event == 'Update Figure':
                    _plot_data(data, axes, axes, **values, **fig_kwargs)
                    plot_utils.draw_figure_on_canvas(
                        window['fig_canvas'].TKCanvas, fig,
                        window['controls_canvas'].TKCanvas,
                        plot_utils.PlotToolbar
                    )
                # resets all options to their defaults
                elif event == 'Reset to Defaults':
                    reset = sg.popup_yes_no(
                        'All values will be returned to their default.\n\nProceed?\n',
                        title='Reset to Defaults'
                    )
                    if reset == 'Yes':
                        plt.close(_PREVIEW_NAME)
                        old_location = window.current_location()
                        window.close()
                        window = None
                        fig, axes = _create_figure_components(**fig_kwargs)
                        window, validations = _create_plot_options_gui(
                            data, fig, axes, location=old_location, **fig_kwargs
                        )
                # toggles legend options
                elif 'show_legend' in event:
                    index = '_'.join(event.split('_')[-2:])
                    properties = (
                        'cols', 'auto', 'auto_loc', 'manual', 'manual_x', 'manual_y' #TODO later check whether manual or auto and enable accordingly
                    )
                    if values[event]:
                        for prop in properties:
                            try:
                                window[f'legend_{prop}_{index}'].update(
                                    readonly=window[f'legend_{prop}_{index}'].Readonly
                                )
                            except AttributeError:
                                window[f'legend_{prop}_{index}'].update(disabled=False)
                    else:
                        for prop in properties:
                            window[f'legend_{prop}_{index}'].update(disabled=True)
                # toggles secondary axis options
                elif event.startswith('secondary'):
                    properties = ('label', 'label_offset', 'expr')
                    index = '_'.join(event.split('_')[-2:])
                    if 'secondary_x' in event:
                        prefix = 'secondary_x'
                    else:
                        prefix = 'secondary_y'

                    for prop in properties:
                        window[f'{prefix}_{prop}_{index}'].update(
                            disabled=not values[event]
                        )
                # toggles dataset options for an axis
                elif 'plot_boolean' in event:
                    index = '_'.join(event.split('_')[-3:])
                    properties = (
                        'x_col', 'y_col', 'label', 'offset', 'markerface_color',
                        'markeredge_color', 'marker_edgewidth', 'marker_style',
                        'marker_size', 'line_color', 'line_style', 'line_size'
                    )
                    if values[event]:
                        for prop in properties:
                            try:
                                window[f'{prop}_{index}'].update(
                                    readonly=window[f'{prop}_{index}'].Readonly
                                )
                            except AttributeError:
                                window[f'{prop}_{index}'].update(disabled=False)
                    else:
                        for prop in properties:
                            window[f'{prop}_{index}'].update(disabled=True)
                # color chooser button
                elif 'chooser' in event:
                    if values[event] != 'None':
                        property_type = event.split('_')[0]
                        index = '_'.join(event.split('_')[-3:])
                        window[f'{property_type}_color_{index}'].update(
                            value=values[event]
                        )

            window.close()
            window = None

    except (utils.WindowCloseError, KeyboardInterrupt):
        pass
    except Exception:
        print(traceback.format_exc())

    finally:
        plt.close(_PREVIEW_NAME)
        while len(figures) < len(data_list):
            figures.append([None, None])

    return figures


def launch_plotting_gui(dataframes=None, mpl_changes=None, input_fig_kwargs=None,
                        input_axes=None, input_values=None):
    """
    Convenience function to plot lists of dataframes with matplotlib.

    Wraps the plotting in a context manager that applies the changes
    to the matplotlib rcParams.

    Parameters
    ----------
    dataframes : list
        A nested list of pandas DataFrames. Each list of DataFrames will
        create one figure.
    mpl_changes : dict
        Changes to matplotlib's rcParams file to alter the figure.
    input_fig_kwargs : dict, optional
        The fig_kwargs from a previous session. Only used if reloading a figure.
    input_axes : dict, optional
        A dictionary of plt.Axes objects from a reloaded session.
    input_values : dict, optional
        The values needed to recreate the previous gui window from
        a reloaded figure.

    Returns
    -------
    figures : list
        A nested list of lists, with each entry containing the matplotlib Figure,
        and a dictionary containing the Axes.

    """

    rc_params = mpl_changes.copy() if mpl_changes is not None else {}
    rc_params.update({
        'interactive': False,
        'figure.constrained_layout.use': False
    })

    if dataframes is not None:
        plot_data = dataframes
    else:
        plot_data = [utils.open_multiple_files()]
        for dataframe in plot_data[0]:
            dataframe.columns = [
                f'Column {num}' for num in range(len(dataframe.columns))
            ]

    if plot_data:
        with plt.rc_context(rc_params):
            figures = _plot_options_event_loop(
                plot_data, rc_params, input_fig_kwargs, input_axes, input_values
            )

    return figures
