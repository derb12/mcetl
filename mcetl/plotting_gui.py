# -*- coding: utf-8 -*-
"""GUIs to plot data using various plot layouts and save the resulting figures.

@author: Donald Erb
Created on Sun Jun 28 18:40:04 2020

"""


import string
import json
import itertools
import traceback
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import MaxNLocator
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
import PySimpleGUI as sg
from . import utils


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

COLORS = ('Black', 'Blue', 'Red', 'Green', 'Chocolate', 'Magenta',
          'Cyan', 'Orange', 'Coral', 'Dodgerblue')

FILLER_COLUMN_NAME = 'Blank Filler Column'
THEME_EXTENSION = '.figtheme'
FIGURE_EXTENSION = '.figure'
CANVAS_SIZE = (800, 800)
TIGHT_LAYOUT_PAD = 0.3
TIGHT_LAYOUT_W_PAD = 0.6
TIGHT_LAYOUT_H_PAD = 0.6
PREVIEW_NAME = 'Preview'
HOLLOW_THICKNESS = 0.3 #fraction of the marker that is filled when hollow; rethink this


class PlotToolbar(NavigationToolbar2Tk):
    """
    Custom toolbar without the subplots and save figure buttons.

    Ensures that saving is done through the save menu in the window, which
    gives better options for output image quality and ensures the figure
    dimensions are correct. The subplots button is removed so that the
    user does not mess with the plot layout since it is handled by using
    matplotlib's tight layout.

    """

    def __init__(self, fig_canvas, canvas):
        """

        Parameters
        ----------
        fig_canvas : FigureCanvas
            The figure canvas on which to operate.
        canvas : tk.window
            The parent window which owns this toolbar.

        """

        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        )

        super().__init__(fig_canvas, canvas)


def save_figure_json(gui_values, fig_kwargs, rc_changes, axes, data=None):
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
        The list of dataframes used in the figure.

    Notes
    -----
    The gui_values, fig_kwargs, rc_changes, and axes annotations are saved to either
    a .figure file or a .figtheme file (both of which are just json files). If saving
    the figure, which saves both the values and the data for the figure, then a
    .figure file is saved. Otherwise, a .theme file is saved, which just will
    help recreate the layout of the figure, without the data.

    If saving the data for the figure, the data is saved to a csv file
    containing all of the data, separated by columns labeled with the
    FILLER_COLUMN_NAME string. There are better ways to store the data than csv,
    but this way the data can be readily changed, if desired.

    """

    texts = [[] for key in axes]
    for i, key in enumerate(axes):
        texts[i] = [[] for label in axes[key]]
        for j, label in enumerate(axes[key]):
            axis = axes[key][label]
            for annotation in axis.texts:
                texts[i][j].append({
                    'text': annotation.get_text(),
                    'xy': annotation.xy,
                    'xytext': annotation.xyann,
                    'fontsize': annotation.get_fontsize(),
                    'rotation': annotation.get_rotation(),
                    'color': annotation.get_color(),
                    'arrowprops': annotation.arrowprops,
                    'annotation_clip': False,
                    'in_layout': False
                })

    extension = THEME_EXTENSION if data is None else FIGURE_EXTENSION
    file_types = f'Theme Files ({THEME_EXTENSION})' if data is None else f'Figure Files ({FIGURE_EXTENSION})'

    filename = sg.popup_get_file(
        'Select the filename.', title='Save Figure Options',
        file_types=((file_types, f"*{extension}"),), save_as=True
    )

    if filename:
        try:
            if not filename.endswith(extension):
                filename = filename + extension

            with open(filename, 'w') as f:
                f.write('FIGURE KEYWORD ARGUMENTS\n')
                json.dump(fig_kwargs, f)
                f.write('\nGUI VALUES\n')
                json.dump(gui_values, f)
                f.write('\nMATPLOTLIB RCPARAM CHANGES\n')
                json.dump(rc_changes, f)
                f.write('\nANNOTATIONS\n')
                json.dump(texts, f)

            if data is not None:

                filename = filename.replace(extension, '.csv')
                saved_data = []
                #creates separator columns
                for i, dataframe in enumerate(data):
                    df = dataframe.copy()
                    if i != len(data) - 1:
                        df[FILLER_COLUMN_NAME] = pd.Series()

                    saved_data.append(df)

                with open(filename, 'w') as f:
                    pd.concat(saved_data, axis=1).to_csv(filename, index=False)

            sg.popup(
                f'Successfully saved to {filename.replace(extension, "").replace(".csv", "")}\n',
                title='Save Successful'
            )

        except PermissionError:
            sg.popup(
                'Designated file is currently open. Please close and try to save again.\n',
                title='Save Failed'
            )


def load_previous_figure(filename=None, new_rc_changes=None):
    """
    Load the options and the data to recreate a figure.

    Parameters
    ----------
    filename : str, optional
        The filepath string to the .figure file to be opened.
    new_rc_changes : dict, optional
        New changes to matplotlib's rcParams file to alter the saved figure.

    Returns
    -------
    figures : list or None
        A list of figures (with len=1) using the loaded data. If no file is
        selected, then figures = None.

    TODO maybe make this use the import_file fct, and then load the corresponding
    figure file if one exists, otherwise just set the kwargs to {}. Then
    could only use one 'figure' extension rather than having figure and figtheme
    """

    figures = None
    if filename is None:
        filename = sg.popup_get_file('Select the figure file.', title='Load Figure File',
                                     file_types=((f'Figure Files ({FIGURE_EXTENSION})',
                                                  f"*{FIGURE_EXTENSION}"),))
    if filename:

        with open(filename, 'r') as f:
            file = f.readlines()

        fig_kwargs = json.loads(file[1])
        gui_values = json.loads(file[3])
        annotations = json.loads(file[7])

        interactive = plt.isinteractive()
        plt.ioff()
        fig, axes = create_figure_components(**fig_kwargs)
        plt.close('PREVIEW_NAME')
        fig.clear()
        if interactive:
            plt.ion()

        for i, key in enumerate(axes):
            for j, label in enumerate(axes[key]):
                axis = axes[key][label]
                for annotation in annotations[i][j]:
                    #the annotation text keyword changed from 's' to 'text' in matplotlib version 3.3.0
                    if int(''.join(mpl.__version__.split('.'))) < 330:
                        annotation['s'] = annotation.pop('text')

                    axis.annotate(**annotation)

        rc_changes = json.loads(file[5])
        if new_rc_changes is not None:
            #overwrites values in rc_changes if key in new_rc_changes, and transfers
            #new keys and values from new_rc_changes
            rc_changes.update(**new_rc_changes)

        dataframe = pd.read_csv(filename.replace(FIGURE_EXTENSION, '.csv'), header=0,
                                index_col=False)

        indices = []
        for i, column in enumerate(dataframe.columns):
            if column == FILLER_COLUMN_NAME:
                indices.append(i)

        row = 0
        data = []
        for entry in indices:
            data.append(dataframe.iloc[:, row:entry])
            row += len(data[-1].columns) + 1
        data.append(dataframe.iloc[:, row:])

        figures = configure_plots([data], rc_changes, fig_kwargs, axes, gui_values)

    return figures


def load_figure_theme(current_axes=None, current_values=None, current_fig_kwargs=None):
    """
    Load the options to recreate a figure layout.

    Parameters
    ----------
    current_axes : array-like, optional
        The current array of axes. Just used in case the user does not load a file.
    current_values : dict, optional
        The current window dictionary. Only used if user does not load a file.
    current_fig_kwargs : dict
        The dictionary used to create the current figure. Only used if user does not
        load a file.

    Returns
    -------
    axes : list
        The input axes, with annotations added to them.
    gui_values : dict
        A dictionary that contains all the information to create the figure.
    fig_kwargs : dict
        The dictionary to recreate the loaded figure.

    """

    filename = sg.popup_get_file('Select the theme file.', title='Load Figure Theme',
                                 file_types=((f"Theme Files ({THEME_EXTENSION})",
                                              f"*{THEME_EXTENSION}"),))

    if filename:

        with open(filename, 'r') as f:
            file = f.readlines()

        fig_kwargs = json.loads(file[1])
        gui_values = json.loads(file[3])
        annotations = json.loads(file[7])

        fig, axes = create_figure_components(**fig_kwargs)
        plt.close('PREVIEW_NAME')
        #fig.clear()

        for i, key in enumerate(axes):
            for j, label in enumerate(axes[key]):
                axis = axes[key][label]
                for annotation in annotations[i][j]:
                    #the annotation text keyword changed from 's' to 'text' in matplotlib version 3.3.0
                    if int(''.join(mpl.__version__.split('.'))) < 330:
                        annotation['s'] = annotation.pop('text')
                    axis.annotate(**annotation)

    else:
        axes = current_axes
        gui_values = current_values
        fig_kwargs = current_fig_kwargs

    return axes, gui_values, fig_kwargs


def save_image_options(figure):
    """
    Handles saving a figure through matplotlib.

    If available, will give additional options to change the saved image
    quality and compression.

    Parameters
    ----------
    figure : matplotlib Figure
        The matplotlib Figure to save.

    """

    extension_mapping = {'jpeg':'JPEG', 'jpg':'JPEG', 'tiff':'TIFF', 'tif':'TIFF',
                         'png':'PNG', 'pdf':'PDF', 'eps':'EPS', 'ps':'PS',
                         'svg':'SVG', 'svgz':'SVGZ'}

    extension_dict = defaultdict(list)
    for ext in sorted(set(extension_mapping.values())):
        for key in extension_mapping:
            if ext == extension_mapping[key]:
                extension_dict[ext].append(key)

    extension_displays = {key: f'{key} ({", ".join(extension_dict[key])})' for key in extension_dict}
    extension_regex = [[f'*.{val}' for val in extension_dict[key]] for key in extension_dict]
    file_types = tuple(zip(extension_displays.values(), extension_regex))

    layout = [
        [sg.Text('Filename:'),
         sg.Input('', disabled=True, size=(20, 1), key='file_name'),
         sg.Input('', key='save_as', visible=False,
                  enable_events=True, do_not_clear=False),
         sg.SaveAs(file_types=file_types, key='file_save_as',
                   target='save_as')],
        [sg.Text('Image Type:'),
         sg.Combo([*extension_displays.values()], key='extension',
                  default_value=extension_displays['TIFF'], size=(15, 1))],
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Next', bind_return_key=True, size=(6, 1),
                   button_color=('white', '#00A949'))]
    ]

    window_1 = sg.Window('Save Options', layout)

    window_open = True
    while window_open:
        event, values = window_1.read()

        if event in (sg.WIN_CLOSED, 'Back'):
            break

        elif event == 'save_as':
            if values['save_as']:
                file_path = Path(values['save_as'])
                window_1['file_name'].update(value=file_path.name)
                file_extension = file_path.suffix.lower()
                if file_extension:
                    file_extension = file_extension[1:]
                    if file_extension in extension_mapping.keys():
                        window_1['extension'].update(
                            value=extension_displays[extension_mapping[file_extension]]
                        )

        elif event == 'Next':
            selected_extension = values['extension'].split(' ')[0]
            directory = str(file_path.parent)

            if values['file_name']:
                file_extension = file_path.suffix[1:] if file_path.suffix else selected_extension.lower()

                if ((file_extension.lower() not in extension_mapping.keys()) or
                        (file_extension.lower() not in extension_dict[selected_extension])):

                    error_layout = [
                        [sg.Text('The given filename has an extension that\n'\
                                 'is not the same as the selected extension\n')],
                        [sg.Button(f'Use Filename Extension ({file_extension})',
                                   key='use_filename')],
                        [sg.Button(f'Use Selected Extension ({values["extension"].split(" ")[0]})',
                                   key='use_selected')],
                        [sg.Button('Back')]
                    ]
                    error_window = sg.Window('Extension Error', error_layout)

                    return_to_window = False
                    while True:
                        error_event = error_window.read()[0]
                        if error_event in (sg.WIN_CLOSED, 'Back'):
                            return_to_window = True
                            break
                        elif error_event == 'use_filename':
                            break
                        elif error_event == 'use_selected':
                            file_extension = selected_extension.lower()
                            break

                    error_window.close()
                    del error_window

                    if return_to_window:
                        continue

                file_name = str(Path(directory, file_path.stem + '.' + file_extension))
                window_1.hide()
                layout_2, param_types, use_pillow = image_options(
                    extension_mapping.get(file_extension.lower(), '')
                )
                save_fig = True
                window_open = False

                if layout_2:
                    window_2 = sg.Window(f'Options for {values["extension"]}', layout_2)
                    while True:
                        event_2, save_dict = window_2.read()

                        if event_2 in (sg.WIN_CLOSED, 'Back'):
                            save_fig = False
                            window_open = True
                            break

                        elif event_2 == 'Save':
                            break
                    window_2.close()
                    del window_2
                else:
                    save_dict = {}

                if save_fig:
                    try:
                        for param in param_types:
                            save_dict[param] = param_types[param](save_dict[param])
                        if use_pillow:
                            if ((extension_mapping[file_extension.lower()] == 'TIFF') and
                                    (save_dict['compression'] != 'jpeg')):
                                save_dict.pop('quality')

                            figure.savefig(file_name, pil_kwargs=save_dict)
                        else:
                            figure.savefig(file_name, **save_dict)
                        sg.popup(f'Saved figure to:\n    {file_name}\n',
                                 title='Saved Figure')

                    except Exception as e:
                        sg.popup(f'Save failed...\n\nSaving to "{file_extension}" may not be supported by matplotlib, '\
                                 f'or an additional error may have occurred. \n\nError:\n    {repr(e)}\n',
                                 title='Error')
                        window_open = True
                if window_open:
                    window_1.un_hide()

            else:
                sg.popup('Please select a file name.\n', title='Select a file name')

    window_1.close()
    del window_1


def image_options(extension):
    """
    Constructs the layout for options to save to the given image extension.

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
    use_pillow : bool
        If True, will pass the dictionary from the PySimpleGUI as "pil_kwargs";
        if False, will simply pass the dictionary as "**kwargs".

    """

    if extension == 'JPEG':

        extension_layout = [
            [sg.Text('JPEG Quality (1-95):'),
             sg.Slider((1, 95), plt.rcParams['savefig.jpeg_quality'],
                       key='quality', orientation='h')],
            [sg.Check('Optimize', True, key='optimize')],
            [sg.Check('Progressive', key='progressive')]
        ]
        param_types = {'quality': int}
        use_pillow = True

    elif extension == 'PNG':
        extension_layout = [
            [sg.Text('Compression Level:'),
             sg.Slider((1, 9), 6, key='compress_level', orientation='h')],
            [sg.Check('Optimize', True, key='optimize')]
        ]
        param_types = {'compress_level': int}
        use_pillow = True

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
        param_types = {'quality': int, 'compression': convert_to_pillow_kwargs}
        use_pillow = True

    else:
        extension_layout = []
        param_types = {}
        use_pillow = False

    if extension_layout:
        layout = [
            *extension_layout,
            [sg.Text('')],
            [sg.Button('Back'),
             sg.Button('Save', bind_return_key=True, size=(6, 1),
                       button_color=('white', '#00A949'))]
        ]

    else:
        layout = []

    return layout, param_types, use_pillow


def convert_to_pillow_kwargs(arg):
    """
    Converts a string to the correct keyword to use for tiff compression in pillow.

    Parameters
    ----------
    arg : str
        The string keyword used in the PySimpleGUI window.

    Return
    ------
    arg_dict[arg] : None or str
        The keyword in pillow associated with the input arg string.
    """

    arg_dict = {'None': None, 'Deflate': 'tiff_deflate',
                'LZW': 'tiff_lzw', 'Pack Bits': 'packbits',
                'JPEG': 'jpeg'}

    return arg_dict[arg]


def create_figure_components(saving=False, **fig_kwargs):
    """
    Convenience function to create the figure, gridspec, and axes with one function.

    Later fill this with logic determining which steps can be skipped if no changes
    are made.
    """

    figure = create_figure(fig_kwargs, saving)
    gridspec, gridspec_layout = create_gridspec(fig_kwargs, figure)
    axes = create_axes(gridspec, gridspec_layout, figure, fig_kwargs)

    return figure, axes


def create_figure(fig_kwargs, saving=False):
    """
    Creates a figure corresponding to the value selected in select_plot_type

    Parameters
    ----------
    fig_kwargs : dict
        Keyword arguments for creating the figure.
    saving : bool
        Designates whether the figure will be saved. If True, will use the input
        figure size and dpi. If False, will scale and figure size and dpi to fit
        onto the tkinter canvas with size = CANVAS_SIZE.

    Returns
    -------
    fig : matplotlib.Figure
        The created matplotlib Figure.
    """

    fig_name = fig_kwargs.get('fig_name', PREVIEW_NAME)
    plt.close(fig_name)
    figsize = (float(fig_kwargs['fig_width']), float(fig_kwargs['fig_height']))

    h_pad = 0 if fig_kwargs['share_x'] else TIGHT_LAYOUT_H_PAD
    w_pad = 0 if fig_kwargs['share_y'] else TIGHT_LAYOUT_W_PAD

    if saving:
        dpi = float(fig_kwargs['dpi'])
        fig_size = (figsize[0] / dpi, figsize[1] / dpi)

    else:
        if figsize[0] >= figsize[1]:
            scale = CANVAS_SIZE[0] / figsize[0]
            dpi = scale * float(fig_kwargs['dpi'])
            fig_size = (CANVAS_SIZE[0] / dpi, (scale * figsize[1])  / dpi)
        else:
            scale = CANVAS_SIZE[1] / figsize[1]
            dpi = scale * float(fig_kwargs['dpi'])
            fig_size = ((scale * figsize[0])  / dpi, CANVAS_SIZE[1] / dpi)

    figure = plt.figure(
        num=fig_name, figsize=fig_size, dpi=dpi,
        tight_layout={'pad': TIGHT_LAYOUT_PAD, 'w_pad': w_pad,
                      'h_pad': h_pad}
    )

    return figure


def create_gridspec(gs_kwargs, figure):
    """
    """

    selections = defaultdict(list)
    gridspec_layout = {}

    if gs_kwargs['Single Plot']:
        gridspec = figure.add_gridspec(1, 1)
        gridspec_layout = {'a': ((0, 1), (0, 1))}
    else:
        blank_num = 0
        for key, value in gs_kwargs.items():
            if key.startswith('gs_'):
                if value:
                    selections[value].append(key.split('_')[-1])
                else:
                    selections[f'blank_{blank_num}'].append(key.split('_')[-1])
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

    #set up the twin x and y values
    default_inputs = {}
    for entry, val in gridspec_layout.items():
        if not entry.startswith('blank'):
            default_inputs[f'twin_x_{val[0][0]}{val[1][0]}'] = False
            default_inputs[f'twin_y_{val[0][0]}{val[1][0]}'] = False
    default_inputs.update(gs_kwargs)
    gs_kwargs.update(default_inputs)

    return gridspec, gridspec_layout


def create_axes(gridspec, gridspec_layout, figure, fig_kwargs):
    """
    """

    axes = defaultdict(dict)
    for key, val in gridspec_layout.items():
        entry_key = f'Row {int(val[0][0]) + 1}, Col {int(val[1][0]) + 1}'
        if 'blank' in key:
            #creates the axis without spines or labels, but not invisible so it can be annotated
            ax = figure.add_subplot(
                gridspec[val[0][0]:val[0][1], val[1][0]:val[1][1]],
                label=f'{entry_key} (Invisible)',
                frameon=False
            )
            ax.tick_params(
                which='both', labelbottom=False, labelleft=False, top=False,
                bottom=False, left=False, labelright=False, labeltop=False,
                right=False
            )

        else:
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
            ax.tick_params(which='both', labelbottom=label_bottom, labelleft=label_left)

        axes[entry_key]['Main Axis'] = ax

        if 'blank' not in key:

            if fig_kwargs[f'twin_x_{val[0][0]}{val[1][0]}']:
                ax2 = ax.twinx()
                ax2.set_label(f'{ax.get_label()} (Twin x)')
                ax2.set_frame_on(False)
                ax2.set_ylabel(twin_x_label)
                ax2.tick_params(which='both', labelright=label_right)
                axes[entry_key]['Twin x'] = ax2

            if fig_kwargs[f'twin_y_{val[0][0]}{val[1][0]}']:
                ax3 = ax.twiny()
                ax3.set_label(f'{ax.get_label()} (Twin y)')
                ax3.set_frame_on(False)
                ax3.set_xlabel(twin_y_label)
                ax3.tick_params(which='both', labeltop=label_top)
                axes[entry_key]['Twin y'] = ax3

            ax.set_ylabel(y_label)
            ax.set_xlabel(x_label)


    return axes


def annotate_example_plot(axes, canvas, fig):
    """
    """

    for key in axes:
        for label in axes[key]:
            ax = axes[key][label]
            if label == 'Main Axis':
                ax_label = ax.get_label().split(', ')
                ax.annotate(f'{ax_label[0]}\n{ax_label[1]}', (0.5, 0.5),
                            horizontalalignment='center', in_layout=False,
                            verticalalignment='center', transform=ax.transAxes)

            ax.set_xlim(0.1, 0.9)
            ax.set_ylim(0.1, 0.9)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
            ax.yaxis.set_minor_locator(AutoMinorLocator(2))
            ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
            ax.xaxis.set_minor_locator(AutoMinorLocator(2))

    draw_figure_on_canvas(canvas, fig)


def create_advanced_layout(input_values, canvas, fig):

    num_cols = int(input_values['num_cols'])
    num_rows = int(input_values['num_rows'])

    validations = {'floats': []}
    validations['floats'].extend([[f'width_{i}', f'width {i + 1}'] for i in range(num_cols)])
    validations['floats'].extend([[f'height_{i}', f'height {i + 1}'] for i in range(num_rows)])

    columm_layout =  [
        [sg.Text(i+1, size=(2, 1), justification='right')]
        + [sg.Input(input_values[f'gs_{i}{j}'], size=(5, 1), pad=(1, 1),
                    justification='right', key=f'gs_{i}{j}') for j in range(num_cols)]
        for i in range(num_rows)]

    widths = [
        sg.Input(input_values[f'width_{i}'], key=f'width_{i}', size=(5,1)) for i in range(num_cols)
    ]
    heights = [
        [sg.Input(input_values[f'height_{i}'], key=f'height_{i}', size=(5,1))] for i in range(num_rows)
    ]

    header_layout = [
        [sg.Text('', size=(2, 1))] +
        [sg.Text(j+1, size=(5,1), justification='center') for j in range(num_cols)]]

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

        if event != sg.WIN_CLOSED:
            input_values.update(values)
        else:
            break

        if event in ('Preview', 'Submit'):
            window.TKroot.grab_release()
            proceed = utils.validate_inputs(values, **validations)
            if proceed:
                fig, axes = create_figure_components(**input_values)

                if event == 'Preview':
                    annotate_example_plot(axes, canvas, fig)

                elif event == 'Submit':
                    break

            window.TKroot.tkraise()
            window.TKroot.grab_set()

    window.close()
    del window


def create_gridspec_labels(fig_kwargs):
    """
    """

    num_cols = int(fig_kwargs['num_cols'])
    num_rows = int(fig_kwargs['num_rows'])

    new_kwargs = fig_kwargs.copy()
    #delete previous gridspec values
    for key in fig_kwargs:
        if key.startswith('gs') or key.startswith('width') or key.startswith('height'):
            index = key.split('_')[-1]
            if key.startswith('gs'):
                if num_rows <= int(index[0]) or num_cols <= int(index[1]):
                    new_kwargs.pop(key)
            elif key.startswith('width'):
                if int(index) >= num_cols:
                    new_kwargs.pop(key)
            elif key.startswith('height'):
                if int(index) >= num_rows:
                    new_kwargs.pop(key)


    if any(key.startswith('gs') for key in new_kwargs):
        #ensures a new key is always generated when creating new axes
        len_string = max(len(new_kwargs[key]) for key in new_kwargs if key.startswith('gs')) + 1
        #ensures current height and width ratios are not overwritten
        current_col = max(int(key.split('_')[-1]) for key in new_kwargs if key.startswith('width')) + 1
        current_row = max(int(key.split('_')[-1]) for key in new_kwargs if key.startswith('height')) + 1
    else:
        len_string = 1
        current_col = 0
        current_row = 0

    letters = itertools.cycle(string.ascii_letters)
    new_kwargs.update({f'width_{i}': '1' for i in range(current_col, num_cols)})
    new_kwargs.update({f'height_{i}': '1' for i in range(current_row, num_rows)})
    for i in range(num_rows):
        for j in range(num_cols):
            if f'gs_{i}{j}' not in new_kwargs:
                new_kwargs.update({f'gs_{i}{j}': next(letters) * len_string})

    return new_kwargs


def set_twin_axes(gridspec_layout, user_inputs, canvas):
    """
    """

    default_inputs = {}
    for entry, val in gridspec_layout.items():
        if not entry.startswith('blank'):
            default_inputs[f'twin_x_{val[0][0]}{val[1][0]}'] = False
            default_inputs[f'twin_y_{val[0][0]}{val[1][0]}'] = False

    default_inputs.update(user_inputs)

    layout = [
        [sg.Text('Twin X creates a second Y axis that shares the X-axis\nof the parent plot. '\
                 'Twin Y creates a second X axis,\nsharing the Y-axis of the parent plot.')],
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
                    [sg.Checkbox('      ', key=f'twin_x_{val[0][0]}{val[1][0]}',
                                 default=default_inputs[f'twin_x_{val[0][0]}{val[1][0]}'])]
                ], element_justification='center'),
                sg.Column([
                    [sg.Checkbox('      ', key=f'twin_y_{val[0][0]}{val[1][0]}',
                                 default=default_inputs[f'twin_y_{val[0][0]}{val[1][0]}'])]
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

        fig, axes = create_figure_components(**user_inputs)
        if event == 'Preview':
            annotate_example_plot(axes, canvas, fig)

        elif event in ('Submit', sg.WIN_CLOSED):
            break

    window.close()
    del window


def select_plot_type(user_inputs=None):
    """
    Window that allows selection of the type of plot to use and the plot layout.

    Parameters
    ----------
    user_inputs : dict
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
        'num_rows': '1',
        'num_cols': '1',
        'share_x': False,
        'share_y': False
    }

    default_inputs.update({key: num == 0 for num, key in enumerate(plot_types)})
    fig_kwargs = create_gridspec_labels(default_inputs.copy())

    user_inputs = user_inputs if user_inputs is not None else {}
    default_inputs.update(user_inputs)
    fig_kwargs.update(user_inputs)
    fig_kwargs['fig_name'] = 'example'

    check_buttons = []
    for plot in plot_types:

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
                 sg.Combo([*range(1, 7)], key='num_rows', size=(3, 1), disabled=disabled,
                          default_value=default_inputs['num_rows'], readonly=True)],
                [sg.Text('      Columns:', size=(11, 1)),
                 sg.Combo([*range(1, 7)], key='num_cols', size=(3, 1), disabled=disabled,
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
             [sg.Canvas(key='example_canvas', size=CANVAS_SIZE, pad=(0, 0))]
         ], size=(CANVAS_SIZE[0] + 10, CANVAS_SIZE[1] + 10), pad=(20, 0))]
    ]

    fig= create_figure(fig_kwargs)
    gridspec, gridspec_layout = create_gridspec(fig_kwargs, fig)
    axes = create_axes(gridspec, gridspec_layout, fig, fig_kwargs)
    window = sg.Window('Plot Types', layout, finalize=True)
    annotate_example_plot(axes, window['example_canvas'].TKCanvas, fig)

    validations= {'floats': [['fig_width', 'Figure Width'],
                             ['fig_height', 'Figure Height'],
                             ['dpi', 'DPI']]
    }

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            plt.close('example')
            utils.safely_close_window(window)
            break
        elif event in ('Advanced Options', 'Next', 'Preview', 'Add Twin Axes'):
            fig_kwargs.update(values)
            proceed = utils.validate_inputs(values, **validations)
            if proceed:
                fig_kwargs = create_gridspec_labels(fig_kwargs)
                fig = create_figure(fig_kwargs)
                gridspec, gridspec_layout = create_gridspec(fig_kwargs, fig)
                axes = create_axes(gridspec, gridspec_layout, fig, fig_kwargs)

                if event == 'Preview':
                    annotate_example_plot(axes, window['example_canvas'].TKCanvas, fig)

                elif event == 'Advanced Options':
                    create_advanced_layout(fig_kwargs, window['example_canvas'].TKCanvas, fig)

                elif event == 'Add Twin Axes':
                    set_twin_axes(gridspec_layout, fig_kwargs, window['example_canvas'].TKCanvas)

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


def plot_options_gui(data, figure, axes, user_inputs=None, old_axes=None, **kwargs):
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

    Returns
    -------
    window : sg.Window
        The window that contains the plotting options.

    #TODO disable secondary axes in plots with twin axes
    """

    markers = (' None', 'o Circle', 's Square', '^ Triangle-Up',
               'D Diamond', 'v Triangle-Down', 'p Pentagon',
               '< Triangle-Left', '> Triangle-Right', '* Star')

    line_width = plt.rcParams['lines.linewidth']
    marker_size = plt.rcParams['lines.markersize']
    line_plot = kwargs['line']
    scatter_plot = kwargs['scatter']

    default_inputs = {}
    #generates default values based on the Axes and data length
    for i, key in enumerate(axes):
        if 'Invisible' in axes[key]['Main Axis'].get_label():
            continue
        for j, label in enumerate(axes[key]):

            axis = axes[key][label]

            marker_colors = itertools.cycle(COLORS)
            line_colors = itertools.cycle(COLORS)

            if line_plot:
                marker_cycler = itertools.cycle([''])
                line_cycler = itertools.cycle([*LINE_MAPPING.keys()][1:])
            elif scatter_plot:
                marker_cycler = itertools.cycle(markers[1:])
                line_cycler = itertools.cycle(['None'])
            else:
                marker_cycler = itertools.cycle(markers[1:])
                line_cycler = itertools.cycle([*LINE_MAPPING.keys()][1:])

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

            #Options for each axis
            default_inputs.update({
                f'show_x_label_{i}{j}': show_x_label,
                f'show_y_label_{i}{j}': show_y_label,
                f'x_axis_min_{i}{j}': None,
                f'x_axis_max_{i}{j}': None,
                f'x_label_{i}{j}': x_label,
                f'x_label_offset_{i}{j}': '' if x_label_disabled else plt.rcParams['axes.labelpad'],
                f'x_label_disabled_{i}{j}': x_label_disabled,
                f'y_axis_min_{i}{j}': None,
                f'y_axis_max_{i}{j}': None,
                f'y_label_{i}{j}': y_label,
                f'y_label_offset_{i}{j}': '' if y_label_disabled else plt.rcParams['axes.labelpad'],
                f'y_label_disabled_{i}{j}': y_label_disabled,
                f'secondary_x_{i}{j}': False,
                f'secondary_x_label_{i}{j}': '',
                f'secondary_x_label_offset_{i}{j}': plt.rcParams['axes.labelpad'],
                f'secondary_x_expr_{i}{j}': '',
                f'secondary_y_{i}{j}': False,
                f'secondary_y_label_{i}{j}': '',
                f'secondary_y_label_offset_{i}{j}': plt.rcParams['axes.labelpad'],
                f'secondary_y_expr_{i}{j}': '',
                f'show_legend_{i}{j}': True if 'Invisible' not in axis.get_label() else False,
                f'legend_cols_{i}{j}': 1 if len(data) < 5 else 2,
                f'legend_auto_{i}{j}': True,
                f'legend_auto_loc_{i}{j}': 'best',
                f'legend_manual_{i}{j}': False,
                f'legend_manual_x_{i}{j}': '',
                f'legend_manual_y_{i}{j}': '',
                f'auto_ticks_{i}{j}': True,
                f'x_major_ticks_{i}{j}': 5,
                f'x_minor_ticks_{i}{j}': 2,
                f'y_major_ticks_{i}{j}': 5,
                f'y_minor_ticks_{i}{j}': 2,
                f'secondary_auto_ticks_{i}{j}': True,
                f'secondary_x_major_ticks_{i}{j}': 5,
                f'secondary_x_minor_ticks_{i}{j}': 2,
                f'secondary_y_major_ticks_{i}{j}': 5,
                f'secondary_y_minor_ticks_{i}{j}': 2,
                f'x_major_grid_{i}{j}': False,
                f'x_minor_grid_{i}{j}': False,
                f'y_major_grid_{i}{j}': False,
                f'y_minor_grid_{i}{j}': False,
            })

            #Options for each dataset
            #using update for each dict comprehension is just as fast as using
            #generators for each comprehension and updating once
            default_inputs.update({f'plot_boolean_{i}{j}{k}': True if 'Invisible' not in axis.get_label() else False
                                    for k in range(len(data))})
            default_inputs.update({f'x_col_{i}{j}{k}': '0'
                                    for k in range(len(data))})
            default_inputs.update({f'y_col_{i}{j}{k}': '1'
                                    for k in range(len(data))})
            default_inputs.update({f'label_{i}{j}{k}': f'Data {k+1}'
                                    for k in range(len(data))})
            default_inputs.update({f'offset_{i}{j}{k}': 0
                                    for k in range(len(data))})
            default_inputs.update({f'marker_color_{i}{j}{k}': next(marker_colors)
                                    for k in range(len(data))})
            default_inputs.update({f'marker_style_{i}{j}{k}': next(marker_cycler)
                                    for k in range(len(data))})
            default_inputs.update({f'marker_fill_{i}{j}{k}': 'Filled'
                                    for k in range(len(data))})
            default_inputs.update({f'marker_size_{i}{j}{k}': marker_size
                                    for k in range(len(data))})
            default_inputs.update({f'line_color_{i}{j}{k}': next(line_colors)
                                    for k in range(len(data))})
            default_inputs.update({f'line_style_{i}{j}{k}': next(line_cycler)
                                    for k in range(len(data))})
            default_inputs.update({f'line_size_{i}{j}{k}': line_width
                                    for k in range(len(data))})

    user_inputs = user_inputs if user_inputs is not None else {}
    default_inputs.update(user_inputs)
    #plot to get the axis limits for defaults
    plot_data(data, axes, old_axes, **default_inputs, **kwargs)

    axes_tabs = []
    #column_layout = []
    for i, key in enumerate(axes):
        if 'Invisible' in axes[key]['Main Axis'].get_label():
            continue
        label_tabs = []

        for j, label in enumerate(axes[key]):
            axis = axes[key][label]
            plot_details = []

            #have to update axis limits after plotting the data
            default_inputs.update({
                f'x_axis_min_{i}{j}': axis.get_xlim()[0],
                f'x_axis_max_{i}{j}': axis.get_xlim()[1],
                f'y_axis_min_{i}{j}': axis.get_ylim()[0],
                f'y_axis_max_{i}{j}': axis.get_ylim()[1],
                f'secondary_x_axis_min_{i}{j}': axis.get_xlim()[0],
                f'secondary_x_axis_max_{i}{j}': axis.get_xlim()[1],
                f'secondary_y_axis_min_{i}{j}': axis.get_ylim()[0],
                f'secondary_y_axis_max_{i}{j}': axis.get_ylim()[1],
            })

            if 'Twin x' in axes[key] or 'Twin' in label:
                secondary_y_disabled = True
                default_inputs.update({
                    f'secondary_y_{i}{j}': False,
                    f'secondary_y_label_{i}{j}': '',
                    f'secondary_y_label_offset_{i}{j}': '',
                    f'secondary_y_expr_{i}{j}': '',

                })
            else:
                secondary_y_disabled = False

            if 'Twin y' in axes[key] or 'Twin' in label:
                secondary_x_disabled = True
                default_inputs.update({
                    f'secondary_x_{i}{j}': False,
                    f'secondary_x_label_{i}{j}': '',
                    f'secondary_x_label_offset_{i}{j}': '',
                    f'secondary_x_expr_{i}{j}': '',

                })
            else:
                secondary_x_disabled = False

            for k, dataset in enumerate(data):
                plot_details.extend([[
                    sg.Frame(f'Entry {k + 1}', [[
                        sg.Column([
                            [sg.Check('Show', enable_events=True,
                                      default=default_inputs[f'plot_boolean_{i}{j}{k}'],
                                      key=f'plot_boolean_{i}{j}{k}')],
                            [sg.Text('X Column:'),
                             sg.Combo([num for num in range(len(dataset.columns))],
                                      key=f'x_col_{i}{j}{k}', size=(3, 1), readonly=True,
                                      default_value=default_inputs[f'x_col_{i}{j}{k}'],
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Y Column:'),
                             sg.Combo([num for num in range(len(dataset.columns))],
                                      key=f'y_col_{i}{j}{k}', size=(3, 1), readonly=True,
                                      default_value=default_inputs[f'y_col_{i}{j}{k}'],
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Offset:', size=(6, 1)),
                             sg.Input(default_inputs[f'offset_{i}{j}{k}'], size=(5, 1),
                                      key=f'offset_{i}{j}{k}',
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Label:', size=(6, 1)),
                             sg.Input(default_inputs[f'label_{i}{j}{k}'], key=f'label_{i}{j}{k}',
                                      size=(10, 1), disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])]
                        ], pad=((5, 5), 5)),
                        sg.Column([
                            [sg.Text('      Marker')],
                            [sg.Text('Color:', size=(5, 1)),
                             sg.Combo(COLORS, default_value=default_inputs[f'marker_color_{i}{j}{k}'],
                                      key=f'marker_color_{i}{j}{k}', size=(9, 1),
                                      readonly=True,
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}']),
                             sg.Input(key=f'marker_chooser_{i}{j}{k}', enable_events=True,
                                      visible=False),
                             sg.ColorChooserButton('..', target=f'marker_chooser_{i}{j}{k}',
                                                   disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Syle:', size=(4, 1)),
                             sg.Combo(markers, default_value=default_inputs[f'marker_style_{i}{j}{k}'],
                                      key=f'marker_style_{i}{j}{k}', size=(13, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Fill:'),
                             sg.Combo(['Filled', 'Hollow', 'Hollow (Transparent)'],
                                      key=f'marker_fill_{i}{j}{k}', size=(14, 1),
                                      default_value=default_inputs[f'marker_fill_{i}{j}{k}'],
                                      readonly=True, disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Size:'),
                             sg.Input(default_text=default_inputs[f'marker_size_{i}{j}{k}'],
                                      key=f'marker_size_{i}{j}{k}', size=(4, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])]
                        ], pad=((20, 5), 5), element_justification='center'),
                        sg.Column([
                            [sg.Text('      Line')],
                            [sg.Text('Color:'),
                             sg.Combo(COLORS, default_value=default_inputs[f'line_color_{i}{j}{k}'],
                                      key=f'line_color_{i}{j}{k}', size=(9, 1),
                                      readonly=True,
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}']),
                             sg.Input(key=f'line_chooser_{i}{j}{k}', enable_events=True,
                                      visible=False),
                             sg.ColorChooserButton('..', target=f'line_chooser_{i}{j}{k}',
                                                   disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Syle:'),
                             sg.Combo([*LINE_MAPPING.keys()], readonly=True,
                                      default_value=default_inputs[f'line_style_{i}{j}{k}'],
                                      key=f'line_style_{i}{j}{k}', size=(10, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])],
                            [sg.Text('Size:'),
                             sg.Input(default_text=default_inputs[f'line_size_{i}{j}{k}'],
                                      key=f'line_size_{i}{j}{k}', size=(4, 1),
                                      disabled=not default_inputs[f'plot_boolean_{i}{j}{k}'])]
                        ], pad=((20, 5), 5), element_justification='center')
                    ]])
                ]])

            header_width = 65

            column_layout = [
                [sg.Text(f'\nOptions for {axis.get_label()}\n',
                         relief='ridge', size=(header_width, 3),
                         justification='center')],
                [sg.Text('')],
                [sg.Text('Dataset Details', relief='ridge', size=(header_width, 1),
                         justification='center')],
                *plot_details,
                [sg.Text('')],
                [sg.Text('Axes', relief='ridge', size=(header_width, 1),
                         justification='center')],
                [sg.Text('Main Axes:')],
                [sg.Text('    Bounds')],
                [sg.Text('        X Minimum:'),
                 sg.Input(default_inputs[f'x_axis_min_{i}{j}'], size=(8, 1),
                          key=f'x_axis_min_{i}{j}'),
                 sg.Text('X Maximum:'),
                 sg.Input(default_inputs[f'x_axis_max_{i}{j}'], size=(8, 1),
                          key=f'x_axis_max_{i}{j}')],
                [sg.Text('        Y Minimum:'),
                 sg.Input(default_inputs[f'y_axis_min_{i}{j}'], size=(8, 1),
                          key=f'y_axis_min_{i}{j}'),
                 sg.Text('Y Maximum:'),
                 sg.Input(default_inputs[f'y_axis_max_{i}{j}'], size=(8, 1),
                          key=f'y_axis_max_{i}{j}')],
                [sg.Text('')],
                [sg.Text('    Labels')],
                [sg.Check('X Axis Label:', default=default_inputs[f'show_x_label_{i}{j}'],
                          key=f'show_x_label_{i}{j}', enable_events=True,
                          disabled=default_inputs[f'x_label_disabled_{i}{j}']),
                 sg.Input(default_text=default_inputs[f'x_label_{i}{j}'],
                          key=f'x_label_{i}{j}', size=(40, 1),
                          disabled=default_inputs[f'x_label_disabled_{i}{j}'])],
                [sg.Text('    Label Offset:'),
                 sg.Input(default_inputs[f'x_label_offset_{i}{j}'],
                          key=f'x_label_offset_{i}{j}',
                          disabled=default_inputs[f'x_label_disabled_{i}{j}'])],
                [sg.Check('Y Axis Label:', default=default_inputs[f'show_y_label_{i}{j}'],
                          key=f'show_y_label_{i}{j}', enable_events=True,
                          disabled=default_inputs[f'y_label_disabled_{i}{j}']),
                 sg.Input(default_text=default_inputs[f'y_label_{i}{j}'],
                          key=f'y_label_{i}{j}', size=(40, 1),
                          disabled=default_inputs[f'y_label_disabled_{i}{j}'])],
                [sg.Text('    Label Offset:'),
                 sg.Input(default_inputs[f'y_label_offset_{i}{j}'],
                          key=f'y_label_offset_{i}{j}',
                          disabled=default_inputs[f'y_label_disabled_{i}{j}'])],
                [sg.Text('')],
                [sg.Text('Secondary Axes (show different ticks than main axes):')],
                [sg.Check('X Axis Label:', default=default_inputs[f'secondary_x_{i}{j}'],
                          key=f'secondary_x_{i}{j}', enable_events=True,
                          disabled=secondary_x_disabled),
                 sg.Input(default_text=default_inputs[f'secondary_x_label_{i}{j}'],
                          key=f'secondary_x_label_{i}{j}',
                          disabled=not default_inputs[f'secondary_x_{i}{j}'])],
                [sg.Text('    Label Offset:'),
                 sg.Input(default_inputs[f'secondary_x_label_offset_{i}{j}'],
                          key=f'secondary_x_label_offset_{i}{j}',
                          disabled=not default_inputs[f'secondary_x_{i}{j}'])],
                [sg.Text('    Expression, using "x" as the variable (eg. x + 200):'),
                 sg.Input(default_text=default_inputs[f'secondary_x_expr_{i}{j}'],
                          key=f'secondary_x_expr_{i}{j}', size=(15, 1),
                          disabled=not default_inputs[f'secondary_x_{i}{j}'])],
                [sg.Check('Y Axis Label:', default=default_inputs[f'secondary_y_{i}{j}'],
                          key=f'secondary_y_{i}{j}', enable_events=True,
                          disabled=secondary_y_disabled),
                 sg.Input(default_text=default_inputs[f'secondary_y_label_{i}{j}'],
                          key=f'secondary_y_label_{i}{j}',
                          disabled=not default_inputs[f'secondary_y_{i}{j}'])],
                [sg.Text('    Label Offset:'),
                 sg.Input(default_inputs[f'secondary_y_label_offset_{i}{j}'],
                          key=f'secondary_y_label_offset_{i}{j}',
                          disabled=not default_inputs[f'secondary_y_{i}{j}'])],
                [sg.Text('    Expression, using "y" as the variable (eg. y - 50):'),
                 sg.Input(default_text=default_inputs[f'secondary_y_expr_{i}{j}'],
                          key=f'secondary_y_expr_{i}{j}', size=(15, 1),
                          disabled=not default_inputs[f'secondary_y_{i}{j}'])],
                [sg.Text('')],
                [sg.Text('Legend', relief='ridge', size=(header_width, 1),
                         justification='center')],
                [sg.Check('Show Legend', default=default_inputs[f'show_legend_{i}{j}'],
                          key=f'show_legend_{i}{j}', enable_events=True)],
                [sg.Text('Number of Columns:'),
                 sg.Combo([num + 1 for num in range(len(data))],
                          default_value=default_inputs[f'legend_cols_{i}{j}'],
                          key=f'legend_cols_{i}{j}', readonly=True, size=(3, 1))],
                [sg.Text('Legend Location:')],
                [sg.Radio('Automatic', f'legend_pos_{i}{j}', key=f'legend_auto_{i}{j}',
                          default=default_inputs[f'legend_auto_{i}{j}'],
                          enable_events=True, pad=((20, 10), 3))],
                [sg.Text('Position:', pad=((60, 3), 3)),
                 sg.Combo(['best', 'upper left', 'upper center', 'upper right',
                           'lower left', 'lower center', 'lower right',
                           'center left', 'center', 'center right'],
                          default_inputs[f'legend_auto_loc_{i}{j}'],
                          key=f'legend_auto_loc_{i}{j}', readonly=True,
                          disabled=not default_inputs[f'legend_auto_{i}{j}'])],
                [sg.Radio('Manual', f'legend_pos_{i}{j}', key=f'legend_manual_{i}{j}',
                          default=default_inputs[f'legend_manual_{i}{j}'],
                          enable_events=True, pad=((20, 10), 3))],
                [sg.Text('Position of lower-left corner, as a fraction of the axis size\n'\
                         '    (< 0 or > 1 will be outside of axis)',
                         pad=((60, 3), 3))],
                [sg.Text('x-position:', pad=((60, 3), 3)),
                 sg.Input(default_inputs[f'legend_manual_x_{i}{j}'],
                          key=f'legend_manual_x_{i}{j}', size=(4, 1),
                          disabled=default_inputs[f'legend_auto_{i}{j}']),
                 sg.Text('y-position:', pad=((10, 3), 3)),
                 sg.Input(default_inputs[f'legend_manual_y_{i}{j}'],
                          key=f'legend_manual_y_{i}{j}', size=(4, 1),
                          disabled=default_inputs[f'legend_auto_{i}{j}'])],
                [sg.Text('')],
                [sg.Text('Tick Marks', relief='ridge', size=(header_width, 1),
                         justification='center')],
                [sg.Text('Main Axes')],
                [sg.Radio('Automatic', f'ticks_{i}{j}', key=f'auto_ticks_{i}{j}',
                          default=default_inputs[f'auto_ticks_{i}{j}'],
                          enable_events=True, pad=((20, 10), 3))],
                [sg.Column([
                    [sg.Text('X Axis:')],
                    [sg.Text('Major Ticks'),
                     sg.Spin([num for num in range(2, 11)],
                             initial_value=default_inputs[f'x_major_ticks_{i}{j}'],
                             key=f'x_major_ticks_{i}{j}', size=(3, 1))],
                    [sg.Text('Minor Ticks'),
                     sg.Spin([num for num in range(11)],
                             initial_value=default_inputs[f'x_minor_ticks_{i}{j}'],
                             key=f'x_minor_ticks_{i}{j}', size=(3, 1))]
                    ], pad=((40, 5), 3), element_justification='center'),
                 sg.Column([
                     [sg.Text('Y Axis:')],
                     [sg.Text('Major Ticks'),
                      sg.Spin([num for num in range(2, 21)],
                              initial_value=default_inputs[f'y_major_ticks_{i}{j}'],
                              key=f'y_major_ticks_{i}{j}', size=(3, 1))],
                     [sg.Text('Minor Ticks'),
                      sg.Spin([num for num in range(21)], size=(3, 1),
                              initial_value=default_inputs[f'y_minor_ticks_{i}{j}'],
                              key=f'y_minor_ticks_{i}{j}')]
                 ], pad=((40, 5), 3), element_justification='center')],
                [sg.Text('')],
                [sg.Text('Secondary Axes')],
                [sg.Radio('Automatic', f'secondary_ticks_{i}{j}',
                          key=f'secondary_auto_ticks_{i}{j}',
                          default=default_inputs[f'secondary_auto_ticks_{i}{j}'],
                          enable_events=True, pad=((20, 10), 3))],
                [sg.Column([
                    [sg.Text('X Axis:')],
                    [sg.Text('Major Ticks'),
                     sg.Spin([num for num in range(2, 11)],
                             initial_value=default_inputs[f'secondary_x_major_ticks_{i}{j}'],
                             key=f'secondary_x_major_ticks_{i}{j}', size=(3, 1))],
                    [sg.Text('Minor Ticks'),
                     sg.Spin([num for num in range(11)],
                             initial_value=default_inputs[f'secondary_x_minor_ticks_{i}{j}'],
                             key=f'secondary_x_minor_ticks_{i}{j}', size=(3, 1))]
                    ], pad=((40, 5), 3), element_justification='center'),
                 sg.Column([
                     [sg.Text('Y Axis:')],
                     [sg.Text('Major Ticks'),
                      sg.Spin([num for num in range(2, 21)],
                              initial_value=default_inputs[f'secondary_y_major_ticks_{i}{j}'],
                              key=f'secondary_y_major_ticks_{i}{j}', size=(3, 1))],
                     [sg.Text('Minor Ticks'),
                      sg.Spin([num for num in range(21)], size=(3, 1),
                              initial_value=default_inputs[f'secondary_y_minor_ticks_{i}{j}'],
                              key=f'secondary_y_minor_ticks_{i}{j}')]
                 ], pad=((40, 5), 3), element_justification='center')],
                [sg.Text('')],
                [sg.Text('Grid Lines', relief='ridge', size=(header_width, 1),
                         justification='center')],
                [sg.Column([
                    [sg.Text('X Axis:')],
                    [sg.Check('Major Ticks', key=f'x_major_grid_{i}{j}',
                              default=default_inputs[f'x_major_grid_{i}{j}'])],
                    [sg.Check('Minor Ticks', key=f'x_minor_grid_{i}{j}',
                              default=default_inputs[f'x_minor_grid_{i}{j}'])]
                    ], pad=((20, 5), 3), element_justification='center'),
                 sg.Column([
                     [sg.Text('Y Axis:')],
                     [sg.Check('Major Ticks', key=f'y_major_grid_{i}{j}',
                               default=default_inputs[f'y_major_grid_{i}{j}'])],
                     [sg.Check('Minor Ticks', key=f'y_minor_grid_{i}{j}',
                               default=default_inputs[f'y_minor_grid_{i}{j}'])]
                 ], pad=((20, 5), 3), element_justification='center')],
                [sg.Text('')],
                [sg.Text('Annotations (Text, Arrows, and Lines)', relief='ridge',
                         size=(header_width, 1), justification='center')],
                [sg.Button('Add Annotation', key=f'add_annotation_{i}{j}',
                           disabled='Twin' in label),
                 sg.Button('Edit Annotation', key=f'edit_annotation_{i}{j}',
                           disabled=not axis.texts),
                 sg.Button('Delete Annotation', key=f'delete_annotation_{i}{j}',
                           disabled=not axis.texts)],
                [sg.Text('')]
            ]

            label_tabs += [
                [sg.Tab(label,
                        [[sg.Column(column_layout, scrollable=True,
                                    vertical_scroll_only=True, size=(750, 650))]],
                        key=f'label_tab_{i}{j}')]
            ]

        axis_label = axes[key]['Main Axis'].get_label().split(', ')
        axes_tabs += [
            [sg.Tab(f'R{axis_label[0].split(" ")[1]}, C{axis_label[1].split(" ")[1]}',
                    [[sg.TabGroup(label_tabs, key=f'label_tabgroup_{i}',
                                  tab_background_color=sg.theme_background_color())]],
                    key=f'tab_{i}')]
        ]

    layout = [
        [sg.Menu([
            ['&File', ['&Save Image', 'Save &Figure & Data', '&Export Figure Theme',
                       '&Import Figure Theme']],
            ['&Datasets', ['&Show Data', '&Add Dataset',
                           ['Add &Dataset', 'Add &Empty Dataset'], '&Remove Dataset']]
            ], key='menu')],
        [sg.Column([
            [sg.TabGroup(axes_tabs, key='axes_tabgroup',
                         tab_background_color=sg.theme_background_color())],
            [sg.Column([
                [sg.Button('Update Figure'),
                 sg.Button('Show Data')]
            ], pad=((3, 5), 5)),
             sg.Column([
                 [sg.Button('Reset to Defaults')]
             ], element_justification='right', pad=((200, 5), 5))],
            [sg.Text('')],
            [sg.Button('Back'),
             sg.Button('Save Image'),
             sg.Button('Continue', bind_return_key=True,
                       button_color=('white', '#00A949'))]
        ], key='options_column'),
         sg.Column([
            [sg.Canvas(key='controls_canvas', pad=(0, 0), size=(CANVAS_SIZE[0], 10))],
            [sg.Canvas(key='fig_canvas', size=CANVAS_SIZE, pad=(0, 0))]
         ], size=(CANVAS_SIZE[0] + 40, CANVAS_SIZE[1] + 50), pad=(10, 0))
        ]
    ]

    plot_data(data, axes, old_axes, **default_inputs, **kwargs)
    window = sg.Window('Plot Options', layout, resizable=True, finalize=True)
    draw_figure_on_canvas(window['fig_canvas'].TKCanvas, figure,
                          window['controls_canvas'].TKCanvas)
    window['options_column'].expand(True, True) #expands the column when window changes size

    return window


def draw_figure_on_canvas(canvas, figure, toolbar_canvas=None):
    """
    Places the figure and toolbar onto the tkinter canvas.

    Parameters
    ----------
    canvas : tk.Canvas
        The tkinter Canvas element for the figure.
    figure : matplotlib Figure
        The figure to be place on the canvas.
    toolbar_canvas: tk.Canvas
        The tkinter Canvas element for the toolbar.

    """

    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()

    figure_canvas_agg = FigureCanvasTkAgg(figure, master=canvas)
    if toolbar_canvas is not None:
        if toolbar_canvas.children:
            for child in toolbar_canvas.winfo_children():
                child.destroy()

        toolbar = PlotToolbar(figure_canvas_agg, toolbar_canvas)
        toolbar.update()

    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='left', anchor='nw')


def plot_data(data, axes, old_axes=None, **kwargs):
    """
    Plots data and configures the axes.

    TODO: eventually split this function into several functions, each dealing
    with a separate part of the figure/axes. That way, only the parts that need
    updated will be redrawn, which should speed up the plotting.

    Parameters
    ----------
    data: list
        The list of DataFrames to be plotted.
    axes : dict
        An array of axes.
    kwargs : dict
        Additional keyword arguments to create the plots.

    Returns
    -------
    None

    """

    try:

        for i, key in enumerate(axes):
            if 'Invisible' in axes[key]['Main Axis'].get_label():
                continue
            for j, label in enumerate(axes[key]):
                axis = axes[key][label]

                if old_axes is not None and key in old_axes and label in old_axes[key]:
                    annotations = old_axes[key][label].texts
                else:
                    annotations = []

                axis.clear()

                for k, dataset in enumerate(data):
                    if kwargs[f'plot_boolean_{i}{j}{k}']:

                        headers = dataset.columns
                        x_index = int(kwargs[f'x_col_{i}{j}{k}'])
                        y_index = int(kwargs[f'y_col_{i}{j}{k}'])
                        x_data = dataset[headers[x_index]].astype(float)
                        y_data = dataset[headers[y_index]].astype(float)

                        nan_mask = (~np.isnan(x_data)) & (~np.isnan(y_data))

                        x = x_data[nan_mask]
                        y = y_data[nan_mask] + float(kwargs[f'offset_{i}{j}{k}'])

                        if kwargs[f'marker_fill_{i}{j}{k}'] == 'Filled':
                            marker_kws = {
                                'markerfacecolor': kwargs[f'marker_color_{i}{j}{k}'],
                                'markeredgewidth': plt.rcParams['lines.markeredgewidth']
                            }
                        elif kwargs[f'marker_fill_{i}{j}{k}'] == 'Hollow':
                            marker_kws = {
                                'markerfacecolor': 'white',
                                'markeredgecolor': kwargs[f'marker_color_{i}{j}{k}'],
                                'markeredgewidth': HOLLOW_THICKNESS * float(kwargs[f'marker_size_{i}{j}{k}'])
                            }
                        else:
                            marker_kws = {
                                'markerfacecolor': 'None',
                                'markeredgecolor': kwargs[f'marker_color_{i}{j}{k}'],
                                'markeredgewidth': HOLLOW_THICKNESS * float(kwargs[f'marker_size_{i}{j}{k}'])
                            }

                        axis.plot(
                            x, y,
                            marker=utils.string_to_unicode(kwargs[f'marker_style_{i}{j}{k}'].split(' ')[0]),
                            markersize=float(kwargs[f'marker_size_{i}{j}{k}']),
                            color=kwargs[f'line_color_{i}{j}{k}'],
                            linewidth=float(kwargs[f'line_size_{i}{j}{k}']),
                            label=utils.string_to_unicode(kwargs[f'label_{i}{j}{k}']),
                            linestyle=LINE_MAPPING[kwargs[f'line_style_{i}{j}{k}']],
                            **marker_kws
                        )

                if kwargs[f'show_x_label_{i}{j}']:
                    axis.set_xlabel(utils.string_to_unicode(kwargs[f'x_label_{i}{j}']),
                                    labelpad=float(kwargs[f'x_label_offset_{i}{j}']))
                if kwargs[f'show_y_label_{i}{j}']:
                    axis.set_ylabel(utils.string_to_unicode(kwargs[f'y_label_{i}{j}']),
                                    labelpad=float(kwargs[f'y_label_offset_{i}{j}']))

                axis.grid(kwargs[f'x_major_grid_{i}{j}'], which='major', axis='x')
                axis.grid(kwargs[f'x_minor_grid_{i}{j}'], which='minor', axis='x')
                axis.grid(kwargs[f'y_major_grid_{i}{j}'], which='major', axis='y')
                axis.grid(kwargs[f'y_minor_grid_{i}{j}'], which='minor', axis='y')

                if kwargs['share_x'] and i not in (0, len(axes) - 1):
                    prune = 'both'
                else:
                    prune = None

                if kwargs[f'x_axis_min_{i}{j}'] is not None:
                    axis.set_xlim(float(kwargs[f'x_axis_min_{i}{j}']),
                                  float(kwargs[f'x_axis_max_{i}{j}']))
                    axis.set_ylim(float(kwargs[f'y_axis_min_{i}{j}']),
                                  float(kwargs[f'y_axis_max_{i}{j}']))

                axis.yaxis.set_major_locator(
                    MaxNLocator(prune=prune, nbins=kwargs[f'y_major_ticks_{i}{j}'],
                                steps=[1, 2, 2.5, 4, 5, 10]))
                axis.yaxis.set_minor_locator(
                    AutoMinorLocator(kwargs[f'y_minor_ticks_{i}{j}'] + 1))
                axis.xaxis.set_major_locator(
                    MaxNLocator(prune=None, nbins=kwargs[f'x_major_ticks_{i}{j}'],
                                steps=[1, 2, 2.5, 4, 5, 10]))
                axis.xaxis.set_minor_locator(
                    AutoMinorLocator(kwargs[f'x_minor_ticks_{i}{j}'] + 1))
                #show_ticks = not kwargs.get('hide_ticks', False)
                #axis.tick_params(labelbottom=False, bottom=show_ticks, which='both')

                if kwargs[f'show_legend_{i}{j}']:
                    if kwargs[f'legend_auto_{i}{j}']:
                        loc = kwargs[f'legend_auto_loc_{i}{j}']
                    else:
                        loc = (
                            float(kwargs[f'legend_manual_x_{i}{j}']),
                            float(kwargs[f'legend_manual_y_{i}{j}'])
                        )
                    legend = axis.legend(ncol=kwargs[f'legend_cols_{i}{j}'], loc=loc)
                    legend.set_in_layout(False)

                if kwargs[f'secondary_x_{i}{j}']:
                    expr = kwargs[f'secondary_x_expr_{i}{j}']
                    if expr:
                        eqn_a = parse_expr(expr)
                        forward_eqn = sp.lambdify(['x'], eqn_a, ['numpy'])
                        eqn_b = sp.solve([sp.Symbol('y') - eqn_a],
                                         [sp.Symbol('x')])[sp.Symbol('x')]
                        backward_eqn = sp.lambdify(['y'], eqn_b, ['numpy'])

                        functions = (forward_eqn, backward_eqn)
                    else:
                        functions = None

                    sec_x_axis = axis.secondary_xaxis('top', functions=functions)
                    sec_x_axis.set_xlabel(
                        utils.string_to_unicode(kwargs[f'secondary_x_label_{i}{j}']),
                        labelpad=float(kwargs[f'secondary_x_label_offset_{i}{j}'])
                    )
                    sec_x_axis.xaxis.set_major_locator(
                        MaxNLocator(prune=None, nbins=kwargs[f'secondary_x_major_ticks_{i}{j}'],
                                    steps=[1, 2, 2.5, 4, 5, 10]))
                    sec_x_axis.xaxis.set_minor_locator(
                        AutoMinorLocator(kwargs[f'secondary_x_minor_ticks_{i}{j}'] + 1))

                if kwargs[f'secondary_y_{i}{j}']:
                    expr = kwargs[f'secondary_y_expr_{i}{j}']
                    if expr:
                        eqn_a = parse_expr(expr)
                        forward_eqn = sp.lambdify(['y'], eqn_a, ['numpy'])
                        eqn_b = sp.solve([sp.Symbol('x') - eqn_a],
                                         [sp.Symbol('y')])[sp.Symbol('y')]
                        backward_eqn = sp.lambdify(['x'], eqn_b, ['numpy'])

                        functions = (forward_eqn, backward_eqn)
                    else:
                        functions = None

                    sec_y_axis = axis.secondary_yaxis('right', functions=functions)
                    sec_y_axis.set_ylabel(
                        utils.string_to_unicode(kwargs[f'secondary_y_label_{i}{j}']),
                        labelpad=float(kwargs[f'secondary_y_label_offset_{i}{j}'])
                    )
                    sec_y_axis.yaxis.set_major_locator(
                        MaxNLocator(prune=None, nbins=kwargs[f'secondary_y_major_ticks_{i}{j}'],
                                    steps=[1, 2, 2.5, 4, 5, 10]))
                    sec_y_axis.yaxis.set_minor_locator(
                        AutoMinorLocator(kwargs[f'secondary_y_minor_ticks_{i}{j}'] + 1))

                for annotation in annotations:
                    #cannot directly copy artists because the transformations will not
                    #update in the new axis
                    axis.annotate(
                        annotation.get_text(), xy=annotation.xy, xytext=annotation.xyann,
                        fontsize=annotation.get_fontsize(), arrowprops=annotation.arrowprops,
                        rotation=annotation.get_rotation(), color=annotation.get_color(),
                        annotation_clip=False, in_layout=False
                    )
                    #axis.texts[-1].draggable(True) #unfortunately not currently working in tkinter window


    except Exception as e:
        sg.popup('Error creating plot:\n\n    '+repr(e)+'\n')


def add_remove_dataset(current_data, plot_details, data_list=None,
                       add_dataset=True, axes=None):
    """
    Allows adding a dataset from the available data_list or removing a dataset.

    Parameters
    ----------
    current_data : list
        The current list of DataFrames that are being plotted.
    data_list : list
        A nested list of lists of DataFrames; contains all of the
        data that will eventually be plotted.
    add_dataset : bool
        If True, will launch gui to add a dataset; if False, will launch
        gui to delete a dataset.

    Returns
    -------
    current_data : list
        The input list with the selected dataset appended to it or removed
        from it.

    """

    axes = axes if axes is not None else [[]]

    if add_dataset:
        dataset_text = 'Chose the dataset to add:'
        button_text = 'Add Dataset'
        append_dataset = True
        remove_dataset = False

        upper_layout = [
            [sg.Text('Choose data group to use:')],
            [sg.Combo([f'Group {i + 1}' for i in range(len(data_list))], '', key='group',
                      readonly=True, enable_events=True, size=(10, 1))],
            [sg.Text('')],
            [sg.Text(dataset_text)],
            [sg.Combo([], '', key='data_list', disabled=True, size=(10, 1))]
        ]

    else:
        dataset_text = 'Chose the dataset to remove:'
        button_text = 'Remove Dataset'
        append_dataset = False
        remove_dataset = True

        upper_layout = [
            [sg.Text(dataset_text)],
            [sg.Combo([f'Dataset {i + 1}' for i in range(len(current_data))],
                      '', key='data_list', size=(10, 1), readonly=True)]
        ]

    layout = [
        *upper_layout,
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Show Data'),
         sg.Button(button_text, bind_return_key=True, button_color=('white', '#00A949'))]
    ]

    window = sg.Window('Dataset Selection', layout)

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Back'):
            append_dataset = False
            remove_dataset = False
            break

        elif event == 'Show Data':
            data_window = utils.show_dataframes(data_list)
            data_window.read()
            data_window.close()
            data_window = None

        elif event == 'group':
            index = int(values['group'].split(' ')[-1]) - 1
            datasets = [f'Dataset {i + 1}' for i in range(len(data_list[index]))]
            window['data_list'].update(values=datasets, value=datasets[0],
                                       readonly=True)
        elif event == button_text:
            if values['data_list']:
                break
            else:
                sg.popup('Please select a dataset', title='Error')

    window.close()
    del window

    if append_dataset:
        dataset_index = int(values['data_list'].split(' ')[-1]) - 1
        current_data.append(data_list[index][dataset_index].copy())

    elif remove_dataset:
        dataset_index = int(values['data_list'].split(' ')[-1]) - 1
        del current_data[dataset_index]
        properties = (
            'plot_boolean', 'x_col', 'y_col', 'label', 'offset',
            'marker_color', 'marker_style', 'marker_fill',
            'marker_size', 'line_color', 'line_style', 'line_size'
        )

        #reorders the plot properties
        for i, key in enumerate(axes):
            for j in range(len(axes[key])):
                for k in range(dataset_index, len(current_data)):
                    for prop in properties:
                        plot_details[f'{prop}_{i}{j}{k}'] = plot_details[f'{prop}_{i}{j}{k+1}']

    return current_data, plot_details


def add_remove_annotations(axis, add_annotation=True):
    """
    Gives options to add, edit, or remove text and arrows on the figure.

    Parameters
    ----------
    axis : plt.Axes
        The axis to add or remove annotations from. Contains all of the
        annotation information within axis.texts.
    add_annotation : bool
        If True, will give window to add an annotation; if False, will give
        window to remove an annotation; if None, will give window to edit
        annotations.

    """

    remove_annotation = False
    validations = {'text': {'floats': [], 'strings':[]},
                   'arrows': {'floats': []}}

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
                     sg.Combo(COLORS, default_value='Black',
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
                     sg.Combo([*LINE_MAPPING.keys()][1:], readonly=True,
                              default_value=[*LINE_MAPPING.keys()][1],
                              key='linestyle', size=(11, 1))],
                    [sg.Text('Head-size multiplier:'),
                     sg.Input('1', key='head_scale', size=(5, 1))],
                    [sg.Text('Arrow Style:'),
                     sg.Combo(['-|>', '<|-', '<|-|>', '->', '<-', '<->', '-[',
                               ']-', ']-[', '|-|', '-'], default_value='-|>',
                              readonly=True, key='arrow_style')],
                    [sg.Text('Color:'),
                     sg.Combo(COLORS, default_value='Black',
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
        validations['text']['strings'].extend([
            ['text', 'text']
        ])

        validations['arrows']['floats'].extend([
            ['head_x', 'head x position'],
            ['head_y', 'head y position'],
            ['tail_x', 'tail x position'],
            ['tail_y', 'tail y position'],
            ['linewidth', 'linewidth'],
            ['head_scale', 'head-size multiplier'],
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
            annotations['text_layout'] += [
                [sg.Text(f'{i + 1})')],
                [sg.Column([
                    [sg.Text('Text:', size=(8, 1)),
                     sg.Input(annotation.get_text(), key=f'text_{i}', size=(10, 1),
                              focus=True)],
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
            ]

            validations['text']['floats'].extend([
                [f'x_{i}', f'x position for Text {i + 1}'],
                [f'y_{i}', f'y position for Text {i + 1}'],
                [f'fontsize_{i}', f'fontsize for Text {i + 1}'],
                [f'rotation_{i}', f'rotation for Text {i + 1}'],
            ])

            validations['text']['strings'].extend([
                [f'text_{i}', f'text for Text {i + 1}']
            ])

        for i, annotation in enumerate(annotations['arrows']):
            for style in LINE_MAPPING:
                if LINE_MAPPING[style] == annotation.arrowprops['linestyle']:
                    break

            annotations['arrows_layout'] += [
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
                 sg.Combo([*LINE_MAPPING.keys()][1:], readonly=True,
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
            ]

            validations['arrows']['floats'].extend([
                [f'head_x_{i}', f'head x position for Arrow {i + 1}'],
                [f'head_y_{i}', f'head y position for Arrow {i + 1}'],
                [f'tail_x_{i}', f'tail x position for Arrow {i + 1}'],
                [f'tail_y_{i}', f'tail y position for Arrow {i + 1}'],
                [f'linewidth_{i}', f'linewidth for Arrow {i + 1}'],
                [f'head_scale_{i}', f'head-size multiplier for Arrow {i + 1}'],
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
        annotations = {'text':{}, 'arrows':{}}
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
                sg.Tab('Text', [[sg.Listbox([*annotations['text'].keys()],
                                            select_mode='multiple', size=(40, 5),
                                            key='text_listbox')]],
                       key='text_tab'),
                sg.Tab('Arrows', [[sg.Listbox([*annotations['arrows'].keys()],
                                              select_mode='multiple', size=(40, 5),
                                              key='arrows_listbox')]],
                       key='arrows_tab')
            ]], tab_background_color=sg.theme_background_color())]
        ]

    layout = [
        *tab_layout,
        [sg.Text('')],
        [sg.Button('Back'),
         sg.Button('Submit', bind_return_key=True, button_color=('white', '#00A949'))],
    ]

    window = sg.Window(window_text, layout)

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

                    #color chooser button
        elif 'chooser' in event:
            if values[event] != 'None':
                property_type = event.split('_')[0]
                index = event.split('_')[-1]
                window[f'{property_type}_color_{index}'].update(value=values[event])


        elif event == 'Submit':
            close = True

            if add_annotation:
                if values['radio_text']:
                    close = utils.validate_inputs(values, **validations['text'])
                else:
                    close = utils.validate_inputs(values, **validations['arrows'])

            elif add_annotation is None:
                close = (utils.validate_inputs(values, **validations['text']) and
                         utils.validate_inputs(values, **validations['arrows']))

            else:
                close = values['text_listbox'] or values['arrows_listbox']
                if not close:
                    sg.popup('Please select an annotation to delete.', title='Error')

            if close:
                break

    window.close()
    del window

    if add_annotation:
        if values['radio_text']:
            axis.annotate(
                utils.string_to_unicode(values['text']),
                xy=(float(values['x']), float(values['y'])),
                fontsize=float(values['fontsize']), rotation=float(values['rotation']),
                color=values['text_color_'], annotation_clip=False, in_layout=False
            )
        else:
            axis.annotate(
                '', xy=(float(values['head_x']), float(values['head_y'])),
                xytext=(float(values['tail_x']), float(values['tail_y'])),
                annotation_clip=False, in_layout=False,
                arrowprops={
                    'linewidth': float(values['linewidth']),
                    'mutation_scale': 10 * float(values['head_scale']), #*10 b/c the connectionpatch defaults to 10 rather than 1
                    'arrowstyle': values['arrow_style'],
                    'color': values['arrow_color_'],
                    'linestyle': LINE_MAPPING[values['linestyle']]}
            )

    elif add_annotation is None:
        for i, annotation in enumerate(annotations['text']):
            annotation.update(
                dict(
                    text=values[f'text_{i}'], color=values[f'text_color_{i}'],
                    position=(float(values[f'x_{i}']), float(values[f'y_{i}'])),
                    fontsize=float(values[f'fontsize_{i}']), in_layout=False,
                    rotation=float(values[f'rotation_{i}']), annotation_clip=False
                )
            )

        for i, annotation in enumerate(annotations['arrows']):
            #not able to move arrow head location, so have to create new annotations
            del axis.texts[axis.texts.index(annotation)]

            axis.annotate(
                '', xy=(float(values[f'head_x_{i}']), float(values[f'head_y_{i}'])),
                xytext=(float(values[f'tail_x_{i}']), float(values[f'tail_y_{i}'])),
                annotation_clip=False, in_layout=False,
                arrowprops={
                    'linewidth': float(values[f'linewidth_{i}']),
                    'mutation_scale': 10 * float(values[f'head_scale_{i}']),
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
            del axis.texts[index]


def configure_plots(data_list, rc_changes=None, input_fig_kwargs=None, input_axes=None,
                    input_values=None):
    """


    Parameters
    ----------
    data_list : list
        A nested list of pandas DataFrames. Each list of DataFrames will
        create one figure.
    rc_changes : dict, optional
        A dictionary of values to changes the matplotlib rcParams. Any changes
        made during this function will be reverted when the function is done.
        The default is None.
    input_fig_kwargs : dict, optional
        The fig_kwargs from a previous session. Only used if reloading a figure.
    input_fig : matplotlib.Figure.figure, optional
        The figure from a reloaded session.
    input_axes : dict, optional
        A dictionary of matplotlib.Axes.axes from a reloaded session.

    Returns
    -------
    figures : list
        A nested list of lists, with each entry containing the matplotlib Figure,
        and a dictionary containing the Axes.

    """
    #global values
    #global fig_kwargs

    try:
        interactive = plt.isinteractive()
        #copies the rcParams currently active so they can be reset after plotting.
        defaults = plt.rcParams.copy()
        rc_changes = rc_changes if rc_changes is not None else {}
        #ensures use of tight_layout over constrained_layout
        plt.rcParams.update(**rc_changes, **{'figure.constrained_layout.use': False})
        plt.ioff()

        figures = []
        for i, dataframe_list in enumerate(data_list):

            data = dataframe_list.copy()

            if i == 0 and input_axes is not None: #loading from a previous session
                fig_kwargs = input_fig_kwargs
                fig, axes = create_figure_components(**fig_kwargs)
                window = plot_options_gui(data, fig, axes, input_values, input_axes,
                                          **fig_kwargs)
            else:
                fig_kwargs = select_plot_type()
                fig, axes = create_figure_components(**fig_kwargs)
                window = plot_options_gui(data, fig, axes, **fig_kwargs)

            while True:
                event, values = window.read()
                #close
                if event == sg.WIN_CLOSED:
                    utils.safely_close_window(window)
                #finish changing the plot
                elif event == 'Continue':
                    plt.close(PREVIEW_NAME)
                    old_axes = axes
                    fig, axes = create_figure_components(True, fig_name=f'Figure_{i+1}',
                                                         **fig_kwargs)
                    plot_data(data, axes, old_axes, **values, **fig_kwargs)
                    figures.append([fig, axes])
                    plt.close(f'Figure_{i+1}')
                    break
                #save figure
                elif event == 'Save Image':
                    window.hide()
                    fig_temp, axes_temp = create_figure_components(True,
                                                                   fig_name=f'Save_{i+1}',
                                                                   **fig_kwargs)
                    plot_data(data, axes_temp, axes, **values, **fig_kwargs)
                    save_image_options(fig_temp)
                    plt.close(f'Save_{i+1}')
                    del fig_temp, axes_temp
                    window.un_hide()
                #exports the options and data required to recreate the figure.
                elif event.startswith('Save Figure'):
                    window.hide()
                    save_figure_json(values, fig_kwargs, rc_changes, axes, data)
                    window.un_hide()
                #exports the options required to recreate a figure layout.
                elif event.startswith('Export Figure'):
                    window.hide()
                    save_figure_json(values, fig_kwargs, rc_changes, axes)
                    window.un_hide()
                #load the options required to recreate a figure layout.
                elif event.startswith('Import Figure'):
                    window.close()
                    window = None
                    plt.close(PREVIEW_NAME)
                    old_axes, values, fig_kwargs = load_figure_theme(axes, values, fig_kwargs)
                    fig, axes = create_figure_components(**fig_kwargs)
                    window = plot_options_gui(data, fig, axes, values, old_axes,
                                              **fig_kwargs)

                #show tables of data
                elif event == 'Show Data':
                    data_window = utils.show_dataframes(data)
                    data_window.read()
                    data_window.close()
                    data_window = None
                #add/remove datasets
                elif event.endswith('Dataset'):
                    plt.close(PREVIEW_NAME)
                    window.close()
                    window = None

                    if 'Empty' in event:
                        data.append(pd.DataFrame([[np.nan, np.nan], [np.nan, np.nan]],
                                                 columns=['Empty Column 1', 'Empty Column 2']))
                    else:
                        add_dataset = False
                        if event == 'Add Dataset':
                            add_dataset = True

                        data, values = add_remove_dataset(data, values, data_list,
                                                          add_dataset, axes)
                    window = plot_options_gui(data, fig, axes, values, axes,
                                              **fig_kwargs)
                #add/remove annotations
                elif 'annotation' in event:
                    add_annotation = False
                    if event.startswith('add_annotation'):
                        add_annotation = True
                    elif event.startswith('edit_annotation'):
                        add_annotation = None

                    index = list(map(int, event.split('_')[-1]))
                    key = [*axes.keys()][index[0]]
                    label = [*axes[key].keys()][index[1]]
                    add_remove_annotations(axes[key][label], add_annotation)

                    plot_data(data, axes, axes, **values, **fig_kwargs)
                    draw_figure_on_canvas(window['fig_canvas'].TKCanvas, fig,
                                          window['controls_canvas'].TKCanvas)

                    window[f'edit_annotation_{index[0]}{index[1]}'].update(
                        disabled=not axes[key][label].texts
                    )
                    window[f'delete_annotation_{index[0]}{index[1]}'].update(
                        disabled=not axes[key][label].texts
                    )
                #go back to plot type picker
                elif event == 'Back':
                    plt.close(PREVIEW_NAME)
                    window.close()
                    window = None
                    fig_kwargs = select_plot_type(fig_kwargs)
                    old_axes = axes
                    fig, axes = create_figure_components(**fig_kwargs)
                    window = plot_options_gui(data, fig, axes, values, old_axes,
                                              **fig_kwargs)
                #update the figure
                elif event == 'Update Figure':
                    plot_data(data, axes, axes, **values, **fig_kwargs)
                    draw_figure_on_canvas(window['fig_canvas'].TKCanvas, fig,
                                          window['controls_canvas'].TKCanvas)
                #resets all options to their defaults
                elif event == 'Reset to Defaults':
                    reset = sg.popup_yes_no('All values will be returned to their default.\n\nProceed?\n',
                                            title='Reset to Defaults')
                    if reset == 'Yes':
                        plt.close(PREVIEW_NAME)
                        window.close()
                        window = None
                        fig, axes = create_figure_components(**fig_kwargs)
                        window = plot_options_gui(data, fig, axes, **fig_kwargs)
                #toggles legend options
                elif 'show_legend' in event:
                    index = event.split('_')[-1]
                    properties = ('cols', 'auto', 'auto_loc',
                                  'manual', 'manual_x', 'manual_y')
                    if values[event]:
                        for prop in properties:
                            try:
                                window[f'legend_{prop}_{index}'].update(readonly=window[f'legend_{prop}_{index}'].Readonly)
                            except AttributeError:
                                window[f'legend_{prop}_{index}'].update(disabled=False)
                    else:
                        for prop in properties:
                            window[f'legend_{prop}_{index}'].update(disabled=True)
                #toggles secondary axis options
                elif 'secondary' in event:
                    properties = ('label', 'label_offset', 'expr')
                    index = event.split('_')[-1]
                    if 'secondary_x' in event:
                        prefix = 'secondary_x'
                    else:
                        prefix = 'secondary_y'

                    for prop in properties:
                        window[f'{prefix}_{prop}_{index}'].update(disabled=not values[event])
                #toggles dataset options for an axis
                elif 'plot_boolean' in event:
                    index = event.split('_')[-1]
                    properties = (
                        'x_col', 'y_col', 'label', 'offset', 'marker_color',
                        'marker_style', 'marker_fill', 'marker_size', 'line_color',
                        'line_style', 'line_size'
                    )
                    if values[event]:
                        for prop in properties:
                            try:
                                window[f'{prop}_{index}'].update(readonly=window[f'{prop}_{index}'].Readonly)
                            except AttributeError:
                                window[f'{prop}_{index}'].update(disabled=False)
                    else:
                        for prop in properties:
                            window[f'{prop}_{index}'].update(disabled=True)
                #color chooser button
                elif 'chooser' in event:
                    if values[event] != 'None':
                        property_type = event.split('_')[0]
                        index = event.split('_')[-1]
                        window[f'{property_type}_color_{index}'].update(value=values[event])

            window.close()
            window = None

    except utils.WindowCloseError:
        pass
    except KeyboardInterrupt:
        pass
    except Exception:
        print(traceback.format_exc())

    finally:
        plt.close(PREVIEW_NAME)

        #applies the rcParams that were set before this function
        with mpl.cbook._suppress_matplotlib_deprecation_warning():
            from matplotlib.style.core import STYLE_BLACKLIST
            plt.rcParams.update({k: defaults[k] for k in defaults if k not in STYLE_BLACKLIST})

        if interactive:
            plt.ion()

        return figures


if __name__ == '__main__':

    #changes some defaults for the plot formatting
    changes = {
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
        'legend.frameon': False
    }

    #TODO make this into a convenience function to put in the main namespace
    try:
        num_files = sg.popup_get_text('Enter number of files to open', 'Get Files', '1')
        if num_files:
            dataframes = []
            for _ in range(int(num_files)):
            #gets the values needed to import a datafile, and then imports the data to a dataframe
                import_values = utils.select_file_gui()
                dataframes.append(
                    utils.raw_data_import(import_values, import_values['file'], False)
                )
            figures = configure_plots(dataframes, changes)

    except utils.WindowCloseError:
        pass
    except KeyboardInterrupt:
        pass

    #figures = load_previous_figure(new_rc_changes={'font.size': 12})
