# -*- coding: utf-8 -*-
"""Provides a GUI to ease the use of the peak_fitting program and save the results to Excel

@author: Donald Erb
Created on Sun May 24 15:18:18 2020

"""


from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import PySimpleGUI as sg
from . import peak_fitting
from . import utils


def show_fit_plot(dataframe, gui_values):
    """
    Shows a plot of data with the fit range, background range, and possible peaks marked.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The dataframe that contains the x and y data.
    gui_values: dict
        A dictionary of values needed for plotting.
        
    Returns
    -------
    None

    """

    try:
        headers = dataframe.columns
        x_index = int(gui_values['x_fit_index'])
        y_index = int(gui_values['y_fit_index'])
        x_data = dataframe[headers[x_index]].astype(float)
        y_data = dataframe[headers[y_index]].astype(float)
        x_min = float(gui_values['x_min']) if gui_values['x_min'] != '-inf' else -np.inf
        x_max = float(gui_values['x_max']) if gui_values['x_max'] != 'inf' else np.inf
        bkg_min = float(gui_values['bkg_x_min']) if gui_values['bkg_x_min'] != '-inf' else -np.inf
        bkg_max = float(gui_values['bkg_x_max']) if gui_values['bkg_x_max'] != 'inf' else np.inf
        height = float(gui_values['height'])
        prominence = float(gui_values['prominence']) if gui_values['prominence'] != 'inf' else np.inf
        additional_peaks_li = [float(entry) for entry in gui_values['peak_list'].replace(' ', '').split(',') if entry != '']

        if x_min == -np.inf:
            x_min = min(x_data)
        else:
            x_min = max(x_min, min(x_data))
        if x_max == np.inf:
            x_max = max(x_data)
        else:
            x_max = min(x_max, max(x_data))
        if bkg_min == -np.inf:
            bkg_min = min(x_data)
        if bkg_min < x_min:
            bkg_min = x_min
        if bkg_max == np.inf:
            bkg_max = max(x_data)
        if bkg_max > x_max:
            bkg_max = x_max

        x_mid = (x_max + x_min) / 2
        bkg_mid = (bkg_max + bkg_min) / 2
        additional_peaks = np.array(additional_peaks_li)
        additional_peaks = additional_peaks[(additional_peaks > x_min) &
                                            (additional_peaks < x_max)]

        peaks = peak_fitting.find_peak_centers(x_data, y_data, additional_peaks,
                                               height, prominence, x_min, x_max)

        if plt.fignum_exists('Fitting'):
            plt.close('Fitting')

        fig, ax = plt.subplots(num='Fitting')
        ax.plot(x_data, y_data)
        ax_y = ax.get_ylim()
        y_diff = ax_y[1] - ax_y[0]

        other_peaks = False
        for peak in peaks[1]:
            if peak not in additional_peaks:
                other_peaks = True
                found_peaks = ax.vlines(
                    peak, ax_y[0] - (0.01*y_diff), ax_y[1] + (0.03*y_diff),
                    color='green', linestyle='-.', lw=2
                )
        for peak in additional_peaks:
            user_peaks = ax.vlines(
                peak, ax_y[0] - (0.01*y_diff), ax_y[1] + (0.03*y_diff),
                color='blue', linestyle=':', lw=2
                )
        ax.annotate(
            "", (x_max, ax_y[1] + (0.03*y_diff)), (x_mid, ax_y[1] + (0.03*y_diff)),
            arrowprops=dict(width=1.2, headwidth=5, headlength=5, color='black'),
            annotation_clip=False, 
        )
        ax.annotate(
            "", (x_min, ax_y[1] + (0.03*y_diff)), (x_mid, ax_y[1] + (0.03*y_diff)),
            arrowprops=dict(width=1.2, headwidth=5, headlength=5, color='black'),
            annotation_clip=False, 
        )
        ax.annotate(
            'Fitting range', (x_mid, ax_y[1] + (0.063*y_diff)), ha='center'
        )
        ax.vlines(
            x_min, ax_y[0] - (0.01*y_diff), ax_y[1] + (0.03*y_diff),
            color='black', linestyle='-', lw=2
        )
        ax.vlines(
            x_max, ax_y[0] - (0.01*y_diff), ax_y[1] + (0.03*y_diff),
            color='black', linestyle='-', lw=2
        )

        if gui_values['subtract_bkg']:
            ax.annotate(
                "", (bkg_max, ax_y[0] - (0.01*y_diff)), 
                (bkg_mid, ax_y[0] - (0.01*y_diff)), annotation_clip=False,
                arrowprops=dict(width=1.2, headwidth=5, headlength=5, color='red')
            )
            ax.annotate(
                "", (bkg_min, ax_y[0] - (0.01*y_diff)),
                (bkg_mid, ax_y[0] - (0.01*y_diff)),
                arrowprops=dict(width=1.2, headwidth=5, headlength=5, color='red'),
                annotation_clip=False
            )
            ax.annotate(
                'Background range', (bkg_mid, ax_y[0] - (0.085*y_diff)),
                color='red', ha='center'
            )
            ax.vlines(
                bkg_min, ax_y[0] - (0.01*y_diff), ax_y[1] + (0.03*y_diff),
                color='red',linestyle='--', lw=2
            )
            ax.vlines(
                bkg_max, ax_y[0] - (0.01*y_diff), ax_y[1] + (0.03*y_diff),
                color='red', linestyle='--', lw=2
            )

        ax.set_ylim(ax_y[0] - (0.15*y_diff), ax_y[1] + (0.15*y_diff))

        if (additional_peaks.size > 0) and (other_peaks):
            ax.legend(
                [found_peaks, user_peaks], ['Found peaks', 'User input peaks'],
                ncol=2, frameon=False, bbox_to_anchor=(0, 1.01,1,1.01),
                loc='lower left', borderaxespad=0, mode='expand'
            )

        elif (additional_peaks.size > 0):
            ax.legend(
                [user_peaks], ['User input peaks'], ncol=2, frameon=False,
                bbox_to_anchor=(0, 1.01,1,1.01), loc='lower left',
                borderaxespad=0, mode='expand'
            )
        elif peaks[1]:
            ax.legend(
                [found_peaks], ['Found peaks'], frameon=False,
                bbox_to_anchor=(0.0,1.01,1,1.01), loc='lower left',
                borderaxespad=0, mode='expand'
            )

        fig.set_tight_layout(True)
        plt.show(block=False)

    except Exception as e:
        sg.popup('Error creating plot:\n    ' + repr(e))


def fit_dataframe(dataframe, user_inputs=None):
    """
    Creates a GUI to select data from a dataframe for peak fitting.

    Parameters
    ----------
    dataframe : pd.DataFrame
        A pandas dataframe.
    user_inputs : dict
        Values to use as the default inputs in the GUI.

    Returns
    -------
    fit_result : list
        A list of lmfit ModelResults, which gives information for each
        of the fits done on the dataset.
    peaks_df : pd.DataFrame
        The dataframe containing the x and y data, the y data
        for every individual peak, the summed y data of all peaks,
        and the background, if present.
    params_df : pd.DataFrame
        The dataframe containing the value and standard error
        associated with all of the parameters in the fitting
        (eg. coefficients for the baseline, areas and sigmas for each peak).
    descriptors_df : pd.DataFrame
        The dataframe which contains some additional information about the fitting.
        Currently has the adjusted r squared, reduced chi squared, the Akaike
        information criteria, the Bayesian information criteria, and the minimization
        method used for fitting.
    gui_values : dict
        The values selected in the GUI for all of the various fields, which
        can be used to reuse the values from a past interation.

    """

    default_inputs = {
        'sample_name': 'Sample',
        'x_fit_index': '0',
        'y_fit_index': '1',
        'x_label': 'raw x data',
        'y_label': 'raw y data',
        'x_min': '-inf',
        'x_max': 'inf',
        'show_plots': True,
        'batch_fit': False,
        'peak_list': '',
        'prominence': 'inf',
        'height': '-inf',
        'model_list': '',
        'default_model': 'GaussianModel',
        'vary_Voigt': False,
        'peak_width': '',
        'center_offset': '',
        'max_sigma': 'inf',
        'min_method': 'least_squares',
        'subtract_bkg': True,
        'bkg_type': 'PolynomialModel',
        'poly_n': '0',
        'bkg_x_min': '-inf',
        'bkg_x_max': 'inf',
        'fit_residuals': False,
        'min_resid': '0.05',
        'num_resid_fits': '5',
        'automatic' : True,
        'manual': False,
        'debug' : False,
        'automatic_bkg' : True,
        'manual_bkg' : False
    }

    user_inputs = user_inputs if user_inputs is not None else {}

    #values if using manual peak selection
    if 'selected_peaks' in user_inputs:
        peak_list_temp = user_inputs.pop('selected_peaks')
    else:
        peak_list_temp = None
    #values if using manual background selection
    if 'selected_bkg' in user_inputs:
        bkg_points = user_inputs.pop('selected_bkg')
    else:
        bkg_points = None

    #assigns the values from user_inputs to keys in default_inputs
    default_inputs.update(user_inputs)
    peak_list = peak_list_temp if peak_list_temp is not None else []
    bkg_points = bkg_points if bkg_points is not None else []
    headers = dataframe.columns
    available_models = [*peak_fitting.peak_transformer().keys()]

    if (('Voigt' in default_inputs['model_list']) or
        ('VoigtModel' == default_inputs['default_model'])) :
        disable_vary_Voigt = False
    else:
        disable_vary_Voigt = True

    automatic_layout = [
        [sg.Text('Peak x values, separated by commas (leave blank to just use peak finding):')],
        [sg.Input(key='peak_list', size=(50, 1),
                  default_text=default_inputs['peak_list'])],
        [sg.Text('Prominence:', size=(13, 1)),
         sg.Input(key='prominence', size=(5, 1),
                  default_text=default_inputs['prominence'])],
        [sg.Text('Minimum height:', size=(13, 1)),
         sg.Input(key='height', size=(5, 1),
                  default_text=default_inputs['height'])],
        [sg.Text('Model list, separated by commas (leave blank to just use default model):')],
        [sg.Input(key='model_list', size=(50, 1), enable_events=True,
                  default_text=default_inputs['model_list'])]
    ]
    peak_finding_layout = sg.TabGroup(
        [
            [sg.Tab('Options', automatic_layout, key='automatic_tab'),
             sg.Tab('Options', [
                 [sg.Text('')],
                 [sg.Button('Launch Peak Selector', enable_events=True, size=(30, 5)),
                  sg.Button('Update Peak & Model Lists', enable_events=True,
                            size=(30, 5))]
             ], key='manual_tab', visible=False)]
        ], key='tab'
    )
    auto_bkg_layout = [
        [sg.Text('Model for fitting background:'),
         sg.InputCombo(['PolynomialModel','ExponentialModel'],
                       key='bkg_type', readonly=False,
                       enable_events=True,
                       default_value=default_inputs['bkg_type'])],
        [sg.Text('Polynomial order:'),
         sg.InputCombo([j for j in range(8)], key='poly_n',
                       readonly=True,
                       default_value=default_inputs['poly_n'])],
        [sg.Text('Min and max x values to use for fitting the background:')],
        [sg.Text('    x min:', size=(8, 1)),
         sg.Input(key='bkg_x_min', size=(5, 1),
                  default_text=default_inputs['bkg_x_min'])],
        [sg.Text('    x max:', size=(8, 1)),
         sg.Input(key='bkg_x_max', size=(5, 1),
                  default_text=default_inputs['bkg_x_max'])],
    ]

    bkg_layout = sg.TabGroup(
        [
            [sg.Tab('Background Options', auto_bkg_layout, key='auto_bkg_tab'),
             sg.Tab('Background Options', [
                 [sg.Text('')],
                 [sg.Button('Launch Background Selector', key='bkg_selector',
                            enable_events=True, size=(30, 5))]
             ], key='manual_bkg_tab', visible=False)]
        ], key='bkg_tabs'
    )
    column_layout = [
        [sg.Text('Raw Data', relief='ridge', size=(60, 1),
                 justification='center')],
        [sg.Text('Sample Name:'),
         sg.Input(key='sample_name', do_not_clear=True, size=(20, 1),
                  default_text=default_inputs['sample_name'],)],
        [sg.Text('Column of x data for fitting:'),
         sg.InputCombo([j for j in range(len(headers))], size=(3, 1),
                        readonly=True, key='x_fit_index',
                        default_value=default_inputs['x_fit_index'])],
        [sg.Text('Column of y data for fitting:'),
         sg.InputCombo([j for j in range(len(headers))], size=(3, 1),
                       readonly=True, key='y_fit_index',
                       default_value=default_inputs['y_fit_index'])],
        [sg.Text('x data label:'),
         sg.Input(key='x_label', do_not_clear=True, size=(20, 1),
                  default_text=default_inputs['x_label'])],
        [sg.Text('y data label:'),
         sg.Input(key='y_label', do_not_clear=True, size=(20, 1),
                  default_text=default_inputs['y_label'])],
        [sg.Text('Min and max values to use for fitting:')],
        [sg.Text('    x min:', size=(8, 1)),
         sg.Input(key='x_min', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['x_min'])],
        [sg.Text('    x max:', size=(8, 1)),
         sg.Input(key='x_max', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['x_max'])],
        [sg.Text('Fitting Options', relief='ridge', size=(60, 1),
                 pad=(5, (20, 10)), justification='center')],
        [sg.Text('Default peak model:'),
         sg.InputCombo(available_models,
                       key='default_model', readonly=True,
                       default_value=default_inputs['default_model'],
                       enable_events=True)],
        [sg.Checkbox('Vary gamma parameter', key='vary_Voigt',
                      disabled=disable_vary_Voigt,
                      default=default_inputs['vary_Voigt'],
                      tooltip='if True, will allow the gamma parameter in the Voigt model'\
                      ' to be varied as an additional variable')],
        [sg.Text('Peak width:', size=(11, 1)),
         sg.Input(key='peak_width', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['peak_width'])],
        [sg.Text('Center offset:', size=(11, 1)),
         sg.Input(key='center_offset', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['center_offset'])],
        [sg.Text('Maximum sigma value:'),
         sg.Input(key='max_sigma', do_not_clear=True, size=(5, 1),
                  default_text=default_inputs['max_sigma'])],
        [sg.Text('Minimization method:'),
         sg.InputCombo(['least_squares','leastsq'], key='min_method',
                       readonly=False,
                       default_value=default_inputs['min_method'])],
        [sg.Checkbox('Fit residuals', key='fit_residuals',
                     enable_events=True,
                     default=default_inputs['fit_residuals'])],
        [sg.Text('Minimum residual height:'),
         sg.Input(key='min_resid', do_not_clear=True, size=(5, 1),
                  visible=False,
                  default_text=default_inputs['min_resid'])],
        [sg.Text('Number of residual fits:'),
         sg.Input(key='num_resid_fits', do_not_clear=True, size=(5, 1),
                  visible=False,
                  default_text=default_inputs['num_resid_fits'])],
        [sg.Text('')],
        [sg.Checkbox('Subtract background', key='subtract_bkg',
                     enable_events=True,
                     default=default_inputs['subtract_bkg']),
         sg.Text('('),
         sg.Radio('Automatic', 'bkg_fitting',
                  key='automatic_bkg', enable_events=True,
                  default=default_inputs['automatic_bkg']),
         sg.Radio('Manual', 'bkg_fitting',
                  key='manual_bkg', enable_events=True,
                  default=default_inputs['manual_bkg']),
         sg.Text(')')],
        [bkg_layout],
        [sg.Text('Peak Finding Options', relief='ridge', size=(60, 1),
                 pad=(5, (20, 10)), justification='center')],
        [sg.Radio('Automatic Peak Finding', 'peak_finding',
                  key='automatic', enable_events=True,
                  default=default_inputs['automatic']),
         sg.Radio('Manual Peak Finding', 'peak_finding',
                  key='manual', enable_events=True,
                  default=default_inputs['manual'],
                  pad=((50, 10), 5))],
        [peak_finding_layout],
    ]

    integers = [
        ['x_fit_index', 'x column'], ['y_fit_index', 'y column'],
        ['poly_n', 'polynomial order'], ['num_resid_fits', 'number of residual fits']
    ]
    floats = [
        ['x_min', 'x min'], ['x_max', 'x max'], ['height', 'minimum height'],
        ['prominence', 'prominence'], ['peak_width', 'peak width'],
        ['center_offset', 'center offset'], ['bkg_x_min', 'background x min'],
        ['bkg_x_max', 'background x max'], ['min_resid', 'minimum residual height'],
        ['max_sigma', 'maximum sigma']
    ]
    strings = [
        ['sample_name', 'sample name'], ['x_label', 'x label'],
        ['y_label', 'y label'], ['min_method', 'minimization method'],
        ['default_model', 'default model'], ['bkg_type', 'background model']
    ]
    user_inputs = [
        ['model_list', 'model list', str], ['peak_list', 'peak x values', float]
    ]

    if default_inputs['batch_fit']:
        gui_values = default_inputs

    else:
        col = sg.Column(column_layout, scrollable=True,
                        vertical_scroll_only=True, size=(700, 500))
        layout = [
            [sg.Frame('', [[col]])],
            [sg.Checkbox('Show Plots After Fitting', key='show_plots',
                         default=default_inputs['show_plots'])],
            [sg.Checkbox('Batch Fit (will not show this window again)',
                              key='batch_fit',
                              default=default_inputs['batch_fit'])],
            [sg.Checkbox('Debug Fitting Process', key='debug',
                         default=default_inputs['debug'])],
            [sg.Text('')],
            [sg.Button('Fit', bind_return_key=True, size=(6,1),
                       button_color=('white','#00A949')),
             sg.Button('Test Plot'),
             sg.Button('Show Data'),
             sg.Button('Reset to Default')]
        ]

        window = sg.Window('Peak Fitting', layout)
        while True:

            event, gui_values = window.read()

            if event == sg.WIN_CLOSED:
                utils.safely_close_window(window)

            elif event == 'Reset to Default':
                window.Fill(default_inputs)
                plt.close('Peak Selector')
                peak_list = []

            elif event == 'Test Plot':
                show_fit_plot(dataframe, gui_values)

            elif event == 'Show Data':
                data_window = utils.show_dataframes(dataframe)
                if data_window is not None:
                    data_window.read()
                    data_window.close()
                    data_window = None

            elif event == 'Update Peak & Model Lists':
                #updates values in the window from the peak selector plot
                centers = [[peak[0][0], np.round(peak[1][0], 2)] for peak in peak_list]
                sorted_peaks = sorted(centers, key=lambda x: x[1])
                sorted_centers = ', '.join([str(center) for model, center in sorted_peaks])
                tmp_model_list = [model for model, center in sorted_peaks]
                model_list = ', '.join(tmp_model_list)
                window['peak_list'].update(value=sorted_centers)
                window['model_list'].update(value=model_list)
                if any(model in ('VoigtModel', 'SkewedVoigtModel') for model in tmp_model_list):
                    window['vary_Voigt'].update(disabled=False)
                elif gui_values['default_model'] not in ('VoigtModel', 'SkewedVoigtModel'):
                    window['vary_Voigt'].update(disabled=True, value=False)

            elif event == 'bkg_selector':
                plt.close('Background Selector')
                try:
                    x_index = int(gui_values['x_fit_index'])
                    y_index = int(gui_values['y_fit_index'])
                    x_data = dataframe[headers[x_index]].astype(float)
                    y_data = dataframe[headers[y_index]].astype(float)
                    bkg_points = peak_fitting.background_selector(x_data, y_data,
                                                                   bkg_points)
                except Exception as e:
                    sg.popup('Error creating plot:\n    '+repr(e))

            elif event == 'Launch Peak Selector':
                plt.close('Peak Selector')

                integers_tmp = integers[:3]
                floats_tmp = [['x_min','x min'], ['x_max','x max'],
                              ['peak_width','peak width'],
                              ['bkg_x_min','background x min'],
                              ['bkg_x_max','background x max']]
                strings_tmp = [['sample_name','sample name'],
                               ['x_label','x label'],
                               ['y_label','y label'],
                               ['bkg_type','background model']]

                proceed = utils.validate_inputs(gui_values, integers_tmp,
                                                floats_tmp, strings_tmp)
                if proceed:
                    try:
                        headers = dataframe.columns
                        x_index = int(gui_values['x_fit_index'])
                        y_index = int(gui_values['y_fit_index'])
                        x_data = dataframe[headers[x_index]].astype(float)
                        y_data = dataframe[headers[y_index]].astype(float)
                        x_min = float(gui_values['x_min']) if gui_values['x_min'] != '-inf' else -np.inf
                        x_max = float(gui_values['x_max']) if gui_values['x_max'] != 'inf' else np.inf
                        bkg_min = float(gui_values['bkg_x_min']) if gui_values['bkg_x_min'] != '-inf' else -np.inf
                        bkg_max = float(gui_values['bkg_x_max']) if gui_values['bkg_x_max'] != 'inf' else np.inf
                        subtract_bkg = gui_values['subtract_bkg']
                        background_type = gui_values['bkg_type']
                        bkg_min = float(gui_values['bkg_x_min']) if gui_values['bkg_x_min'] != '-inf' else -np.inf
                        bkg_max = float(gui_values['bkg_x_max']) if gui_values['bkg_x_max'] != 'inf' else np.inf
                        poly_n = int(gui_values['poly_n'])
                        peak_width = float(gui_values['peak_width'])
                        default_model = gui_values['default_model']

                        if subtract_bkg:
                            if gui_values['manual_bkg']:
                                subtract_bkg = False
                                y_subtracted = y_data.copy()
                                if len(bkg_points) > 1:
                                    points = sorted(bkg_points, key=lambda x: x[0])

                                    for i in range(len(points)-1):
                                        x_points, y_points = zip(*points[i:i+2])
                                        coeffs = np.polyfit(x_points, y_points, 1)
                                        boundary = (x_data >= x_points[0]) & (x_data <= x_points[1])
                                        x_line = x_data[boundary]
                                        y_line = y_data[boundary]
                                        line = np.polyval(coeffs, x_line)
                                        y_subtracted[boundary] = y_line - line
                                y_data = y_subtracted

                        domain_mask = (x_data > x_min) & (x_data < x_max)
                        x_input = x_data[domain_mask]
                        y_input = y_data[domain_mask]
                        peak_list = peak_fitting.peak_selector(x_input, y_input, peak_list,
                                                               peak_width, subtract_bkg,
                                                               background_type, poly_n,
                                                               bkg_min, bkg_max, default_model)
                    except Exception as e:
                        sg.popup('Error creating plot:\n    '+repr(e))

            elif event in ('automatic', 'manual'):
                if event == 'automatic':
                    window['automatic_tab'].update(visible=True)
                    window['automatic_tab'].Select()
                    window['manual_tab'].update(visible=False)

                else:
                    window['automatic_tab'].update(visible=False)
                    window['manual_tab'].update(visible=True)
                    window['manual_tab'].Select()

            elif event in ('automatic_bkg', 'manual_bkg'):
                if event == 'automatic_bkg':
                    window['auto_bkg_tab'].update(visible=True)
                    window['auto_bkg_tab'].Select()
                    window['manual_bkg_tab'].update(visible=False)
                else:
                    window['manual_bkg_tab'].update(visible=True)
                    window['manual_bkg_tab'].Select()
                    window['auto_bkg_tab'].update(visible=False)

            elif event == 'subtract_bkg':
                if gui_values['subtract_bkg']:
                    window['bkg_type'].update(visible=True)
                    window['poly_n'].update(visible=True)
                    window['bkg_x_min'].update(visible=True)
                    window['bkg_x_max'].update(visible=True)
                    window['automatic_bkg'].update(disabled=False)
                    window['manual_bkg'].update(disabled=False)
                    window['bkg_selector'].update(disabled=False)
                else:
                    window['bkg_type'].update(visible=False, value='PolynomialModel')
                    window['poly_n'].update(visible=False, value='0')
                    window['bkg_x_min'].update(visible=False, value='-inf')
                    window['bkg_x_max'].update(visible=False, value='inf')
                    window['automatic_bkg'].update(disabled=True)
                    window['manual_bkg'].update(disabled=True)
                    window['bkg_selector'].update(disabled=True)

            elif event == 'bkg_type':
                if gui_values['bkg_type'] == 'PolynomialModel':
                    window['poly_n'].update(visible=True)
                else:
                    window['poly_n'].update(visible=False, value='0')

            elif event in ('model_list', 'default_model'):
                tmp_model_list = [entry for entry in gui_values['model_list'].replace(' ', '').split(',') if entry != '']
                v_models = ['VoigtModel', 'SkewedVoigtModel']
                if (any(model in v_models for model in tmp_model_list)) or (gui_values['default_model'] in v_models):
                    window['vary_Voigt'].update(disabled=False)
                else:
                    window['vary_Voigt'].update(disabled=True, value=False)

            elif event == 'fit_residuals':
                if gui_values['fit_residuals']:
                    window['min_resid'].update(visible=True)
                    window['num_resid_fits'].update(visible=True)
                else:
                    window['min_resid'].update(visible=False, value=0.05)
                    window['num_resid_fits'].update(visible=False, value=5)

            elif event =='Fit':
                if ((not plt.fignum_exists('Peak Selector')) and
                    (not plt.fignum_exists('Background Selector'))):

                    close = utils.validate_inputs(gui_values, integers, floats,
                                                  strings, user_inputs)
                else:
                    sg.popup('Please close the Peak and/or Background Selection plots.')
                    continue

                if close:
                    model_list = [entry for entry in
                                  gui_values['model_list'].replace(' ', '').split(',')
                                  if entry != '']
                    for entry in model_list:
                        if entry not in available_models:
                            close = False
                            sg.popup(f'Need to correct the term "{entry}" in the model list',
                                     title='Error')
                            break
                else:
                    continue

                if close:
                    if not gui_values['manual']:

                        x_index = int(gui_values['x_fit_index'])
                        y_index = int(gui_values['y_fit_index'])
                        x_data = dataframe[headers[x_index]]
                        y_data = dataframe[headers[y_index]]
                        x_min = float(gui_values['x_min']) if gui_values['x_min'] != '-inf' else -np.inf
                        x_max = float(gui_values['x_max']) if gui_values['x_max'] != 'inf' else np.inf
                        height = float(gui_values['height'])
                        prominence = float(gui_values['prominence']) if gui_values['prominence'] != 'inf' else np.inf
                        if x_min == -np.inf:
                            x_min = min(x_data)
                        if x_max == np.inf:
                            x_max = max(x_data)
                        additional_peaks = [float(entry) for entry in
                                            gui_values['peak_list'].replace(' ', '').split(',') if entry != '']

                        peaks = peak_fitting.find_peak_centers(x_data, y_data,
                                                               additional_peaks,
                                                               height, prominence,
                                                               x_min, x_max)
                        if not peaks[1]:
                            sg.popup('No peaks found in fitting range. Either manually enter \n'\
                                     'peak positions or change peak finding options', title='Error')
                        else:
                            break
                    else:
                        if peak_list:
                            break
                        else:
                            sg.popup('Please manually select peaks or change peak finding to automatic')

        window.close()
        del window

        plt.close('Fitting')

    #ensures unicode is correctly interpreted
    x_label = gui_values['x_label'].encode('utf-8').decode('unicode_escape')
    y_label = gui_values['y_label'].encode('utf-8').decode('unicode_escape')

    x_index = int(gui_values['x_fit_index'])
    y_index = int(gui_values['y_fit_index'])
    x_data = dataframe[headers[x_index]]
    y_data = dataframe[headers[y_index]]
    x_min = float(gui_values['x_min']) if gui_values['x_min'] != '-inf' else -np.inf
    x_max = float(gui_values['x_max']) if gui_values['x_max'] != 'inf' else np.inf
    height = float(gui_values['height'])
    prominence = float(gui_values['prominence']) if gui_values['prominence'] != 'inf' else np.inf
    default_model = gui_values['default_model']
    vary_Voigt = gui_values['vary_Voigt']
    center_offset = float(gui_values['center_offset'])
    min_method = gui_values['min_method']
    subtract_bkg = gui_values['subtract_bkg']
    background_type = gui_values['bkg_type']
    bkg_min = float(gui_values['bkg_x_min']) if gui_values['bkg_x_min'] != '-inf' else -np.inf
    bkg_max = float(gui_values['bkg_x_max']) if gui_values['bkg_x_max'] != 'inf' else np.inf
    max_sigma = float(gui_values['max_sigma']) if gui_values['max_sigma'] != 'inf' else np.inf
    poly_n = int(gui_values['poly_n'])
    fit_residuals = gui_values['fit_residuals']
    min_resid = float(gui_values['min_resid'])
    num_resid_fits = int(gui_values['num_resid_fits'])
    debug = gui_values['debug']

    if gui_values['manual']:
        peaks = sorted(peak_list, key=lambda x: x[1][0])
        additional_peaks = [peak[1][0] for peak in peaks]
        model_list = [peak[0][0] for peak in peaks]
        peak_width = [peak[1][2] for peak in peaks]
        peak_heights = [peak[1][1] for peak in peaks]
        gui_values['selected_peaks'] = peak_list

    else:
        additional_peaks = [float(entry) for entry in gui_values['peak_list'].replace(' ', '').split(',') if entry != '']
        model_list = [entry for entry in gui_values['model_list'].replace(' ', '').split(',') if entry != '']
        peak_width = float(gui_values['peak_width'])
        peak_heights = None
        gui_values['selected_peaks'] = None

    if subtract_bkg:
        if gui_values['manual_bkg']:
            gui_values['selected_bkg'] = bkg_points
            subtract_bkg = False
            y_subtracted = y_data.copy()
            if len(bkg_points) > 1:
                points = sorted(bkg_points, key=lambda x: x[0])

                for i in range(len(points)-1):
                    x_points, y_points = zip(*points[i:i+2])
                    coeffs = np.polyfit(x_points, y_points, 1)
                    boundary = (x_data >= x_points[0]) & (x_data <= x_points[1])
                    x_line = x_data[boundary]
                    y_line = y_data[boundary]
                    line = np.polyval(coeffs, x_line)
                    y_subtracted[boundary] = y_line - line
            y_data = y_subtracted
        else:
            gui_values['selected_bkg'] = None

    fitting_results = peak_fitting.plugNchug_fit(
        x_data, y_data, height, prominence, center_offset, peak_width, default_model,
        subtract_bkg, bkg_min, bkg_max, 0, max_sigma, min_method, x_min, x_max,
        additional_peaks, model_list, background_type, poly_n, None, vary_Voigt,
        fit_residuals, num_resid_fits, min_resid, debug, peak_heights
    )

    output_list = [fitting_results[key] for key in fitting_results]
    resid_found, resid_accept, peaks_found, peaks_accept, initial_fit, fit_result, individual_peaks, best_values = output_list

    #renames amplitude to area for peaks to be more clear; lmfit has amplitude==area
    #by the way the module defines the peaks
    for result in best_values:
        for param in result:
            if ('peak' in param[0]) and ('amplitude' in param[0]):
                param[0] = '_'.join([*param[0].split('_')[0:2], 'area'])

    #creation of dataframe for best values of all peak parameters
    vals = defaultdict(dict)
    st_dev = defaultdict(dict)
    for term in best_values[-1]:
        if 'peak' in term[0]:
            key = f'{term[0].split("_")[0]} {int(term[0].split("_")[1])+1}'
            param_key = '_'.join(term[0].split('_')[2:])
        else:
            key = term[0].split('_')[0]
            param_key = term[0].split('_')[-1]
        vals[key][param_key] = term[1]
        st_dev[key][param_key] = term[2]
    vals_df = pd.DataFrame(vals).transpose()
    st_dev_df = pd.DataFrame(st_dev).transpose()

    df_1 = pd.DataFrame()
    for name in vals_df.columns:
        df_1[f'{name}_val'] = vals_df[name]
        df_1[f'{name}_sterr'] = st_dev_df[name]
    df_1 = df_1.fillna('-')

    model_names = [component._name for component in fit_result[-1].components]
    if 'pvoigt' in model_names:
        for i, name in enumerate(model_names):
            if name == 'pvoigt':
                model_names[i] = 'pseudovoigt'
    df_0 = pd.DataFrame(model_names, columns=['model'], index=vals.keys())
    params_df = pd.concat([df_0, df_1], axis=1)

    #creation of dataframe for peak values and x and y raw data
    x = fit_result[-1].userkws['x']
    y = fit_result[-1].data
    peaks_df = pd.DataFrame()
    peaks_df[x_label] = x
    peaks_df[y_label] = y

    bkg_term = '+ background' if subtract_bkg else ''
    bkg = individual_peaks[-1]['background_'] if subtract_bkg else 0
    for term in individual_peaks[-1]:
        if 'peak' in term:
            key = f'{term.split("_")[0]} {int(term.split("_")[1])+1} {bkg_term}'
            peaks_df[key] = individual_peaks[-1][term] + bkg
        else:
            key = term.split('_')[0]
            peaks_df[key] = individual_peaks[-1][term]
    peaks_df['total fit'] = fit_result[-1].best_fit

    #creation of dataframe for descriptions of the fitting
    adj_r_sq = peak_fitting.r_squared(y, fit_result[-1].best_fit,
                                      fit_result[-1].nvarys)[1]
    red_chi_sq = fit_result[-1].redchi
    bayesian_info_criteria = fit_result[-1].bic
    akaike_info_criteria = fit_result[-1].aic

    descriptors_df = pd.DataFrame(
        [adj_r_sq, red_chi_sq, akaike_info_criteria, bayesian_info_criteria,
         min_method], index=['adjusted R\u00B2', 'reduced \u03c7\u00B2',
                             'A.I.C.',  'B.I.C.', 'minimization method']
    )

    if gui_values['show_plots']:
        peak_fitting.plot_fit_results(x, y, fit_result, True, True)
        peak_fitting.plot_individual_peaks(x, y, individual_peaks[-1], fit_result[-1],
                                           subtract_bkg, plot_w_background=True)
        plt.pause(0.01)

    return fit_result, peaks_df, params_df, descriptors_df, gui_values


def fit_to_excel(peaks_dataframe, params_dataframe, descriptors_dataframe,
                 excel_writer, sheet_name=None, plot_excel=False):
    """
    Outputs the relevant data from peak fitting to an Excel file.

    Parameters
    ----------
    peaks_dataframe : pd.DataFrame
        The dataframe containing the x and y data, the y data
        for every individual peak, the summed y data of all peaks,
        and the background, if present.
    params_dataframe : pd.DataFrame
        The dataframe containing the value and standard error
        associated with all of the parameters in the fitting
        (eg. coefficients for the baseline, areas and sigmas for each peak).
    descriptors_dataframe : pd.DataFrame
        The dataframe which contains some additional information about the fitting.
        Currently has the adjusted r squared, reduced chi squared, the Akaike
        information criteria, the Bayesian information criteria, and the minimization
        method used for fitting.
    excel_writer : pd.ExcelWriter
        The pandas ExcelWriter object that contains all of the
        information about the Excel file being created.
    excel_book : xlsxwriter.WorkBook
        The xlsxwriter book object corresponding to the Excel file being created.
    sheet_name: str
        The Excel sheet name.
    plot_excel : bool
        If True, will create a simple plot in Excel that plots the raw x and
        y data, the data for each peak, the total of all peaks, and
        the background if it is present.

    Returns
    -------
    None

    """

    excel_book = excel_writer.book

    #Formatting styles for the Excel workbook
    if len(excel_book.formats) < 6: # a new writer
        odd_subheader_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'DBEDFF', 'font_size':12, 'bottom': True
        })
        even_subheader_format = excel_book.add_format({
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
        odd_header_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'73A2DB', 'font_size':12, 'bottom': True
        })
        even_header_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'F9B381', 'font_size':12, 'bottom': True
        })
        odd_bold_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'DBEDFF', 'font_size':11, 'num_format': '0.000'
        })
        even_bold_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'FFEAD6', 'font_size':11, 'num_format': '0.000'
        })

    elif len(excel_book.formats) < 10: # a writer used from excel_gui
        odd_subheader_format, even_subheader_format, odd_colnum_format, even_colnum_format = excel_book.formats[2:6]
        odd_header_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'73A2DB', 'font_size':12, 'bottom': True
        })
        even_header_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'F9B381', 'font_size':12, 'bottom': True
        })
        odd_bold_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'DBEDFF', 'font_size':11, 'num_format': '0.000'
        })
        even_bold_format = excel_book.add_format({
            'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
            'bg_color':'FFEAD6', 'font_size':11, 'num_format': '0.000'
        })

    else:
        odd_subheader_format, even_subheader_format, odd_colnum_format, even_colnum_format, odd_header_format, even_header_format, odd_bold_format, even_bold_format = excel_book.formats[2:10]

    #Ensures that the sheet name is unique so it does not overwrite data
    num = 1
    if sheet_name is not None:
        #ensures unicode is read correctly
        sheet_name = utils.string_to_unicode(sheet_name)
        sheet_base = sheet_name
    else:
        sheet_base = 'Sheet'
        sheet_name = 'Sheet_1'
    while True:
        close_loop = True
        for sheet in excel_writer.sheets:
            if sheet_name.lower() == sheet.lower():
                num +=1
                close_loop = False
                sheet_name = f'{sheet_base}_{num}'
                break
        if close_loop:
            break

    param_names = dict.fromkeys([
        params_dataframe.columns[0],
        *[name.replace('_sterr', '').replace('_val', '') for name in params_dataframe.columns]
    ])
    total_width = (len(peaks_dataframe.columns) + len(params_dataframe.columns)
                   + len(descriptors_dataframe.columns) + 1)

    peaks_dataframe.to_excel(excel_writer, sheet_name=sheet_name, index=False,
                             startrow=3, header=False)
    params_dataframe.to_excel(excel_writer, sheet_name=sheet_name, startrow=3,
                              startcol=len(peaks_dataframe.columns) + 1,
                              header=False, index=False)
    descriptors_dataframe.to_excel(excel_writer, sheet_name=sheet_name, startrow=1,
                                   startcol=(len(peaks_dataframe.columns)
                                             +len(params_dataframe.columns) + 2),
                                   header=False, index=False)
    worksheet = excel_writer.sheets[sheet_name]

    #Modifies the formatting to look good in Excel
    worksheet.merge_range(0, 0, 0, len(peaks_dataframe.columns)-1, 'Values',
                          even_header_format)
    worksheet.merge_range(1, 0, 1, 1, 'Raw Data', odd_header_format)
    worksheet.merge_range(1, 2, 1, len(peaks_dataframe.columns)-1, 'Fitted Data',
                          even_header_format)

    #formatting for peaks_dataframe
    for i, peak_name in enumerate(peaks_dataframe.columns):
        if i % 2 == 0:
            formats = [even_subheader_format, even_colnum_format]
        else:
            formats = [odd_subheader_format, odd_colnum_format]
        worksheet.write(2, i, peak_name, formats[0])
        worksheet.set_column(i, i, 12.5, formats[1])

    worksheet.merge_range(0, len(peaks_dataframe.columns), 0,
                          len(peaks_dataframe.columns)+len(params_dataframe.columns),
                          'Peak Parameters', odd_header_format)
    worksheet.merge_range(0, len(peaks_dataframe.columns)+len(params_dataframe.columns) + 1,
                          0, total_width, 'Fit Description', even_header_format)

    #formatting for params_dataframe
    for j, param in enumerate(param_names.keys()):
        if j == 0:
            for k, peak in enumerate(params_dataframe.index):
                worksheet.write(3 + k, i + 1, peak)

            if (j + i + 1) % 2 == 0:
                formats = [odd_subheader_format, even_bold_format, odd_colnum_format]

            else:
                formats = [even_subheader_format, odd_bold_format, even_colnum_format]
            worksheet.merge_range(1, 1 + i, 2, 1 + i, '')
            worksheet.merge_range(1, 2 + i, 2, 2 + i, param, formats[0])
            worksheet.set_column(i + 1, i + 1, 12.5, formats[1])
            worksheet.set_column(i + 2, i + 2, 12.5, formats[2])
        else:
            if (j + i) % 2 == 0:
                formats = [even_subheader_format, even_colnum_format]
            else:
                formats = [odd_subheader_format, odd_colnum_format]
            worksheet.merge_range(1, j * 2 + i + 1, 1, j * 2 + i + 2, param,
                                  formats[0])
            worksheet.write(2, j * 2 + i + 1, 'value', formats[0])
            worksheet.write(2, j * 2 + i + 2, 'standard error', formats[0])
            worksheet.set_column(j * 2 + i + 1, j * 2 + i + 2, 12.5, formats[1])

    #formatting for descriptors_dataframe
    if (j + i + 1) % 2 == 0:
        formats = [even_bold_format, odd_bold_format]
    else:
        formats = [odd_bold_format, even_bold_format]
    for k, parameter in enumerate(descriptors_dataframe.index):
        worksheet.write(1 + k, 2 * (j + 1) + i + 1, parameter, formats[0])
    worksheet.set_column((j + 1) * 2 + i + 1, (j + 1) * 2 + i + 1, 22, formats[0])
    worksheet.set_column((j + 1) * 2 + i + 2, (j + 1) * 2 + i + 2, 15, formats[1])

    #changes row height in Excel
    worksheet.set_row(0, 18)

    if plot_excel:

        x_col_name = peaks_dataframe.columns[0]
        chart = excel_book.add_chart({'type': 'scatter',
                                      'subtype':'straight'})

        for i, col_name in enumerate(peaks_dataframe.columns):
            if i != 0:
                if i == 1:
                    legend_name = 'raw data'
                else:
                    legend_name = ' '.join(col_name.split(' ')[0:2])

                #categories is the x column and values is the y column
                chart.add_series({
                    'name': legend_name,
                    'categories':[sheet_name, 3, 0,
                                  peaks_dataframe[x_col_name].count() + 2, 0],
                    'values':[sheet_name, 3, i,
                                          peaks_dataframe[x_col_name].count() + 2, i],
                    'line': {'width':2}
                })

        chart.set_x_axis({'name': peaks_dataframe.columns[0]})

        chart.set_y_axis({'name': peaks_dataframe.columns[1]})
        worksheet.insert_chart('D8', chart)


if __name__ == '__main__':

    #changes some defaults for the plot formatting
    plt.rcParams['font.serif'] = "Times New Roman"
    plt.rcParams['font.family'] = "serif"
    plt.rcParams['font.size'] = 12
    plt.rcParams['mathtext.default'] = "regular"
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    plt.rcParams['xtick.minor.visible']=True
    plt.rcParams['ytick.minor.visible']=True
    plt.rcParams['xtick.major.size'] = 5
    plt.rcParams['xtick.major.width'] = 0.6
    plt.rcParams['xtick.minor.size'] = 2.5
    plt.rcParams['xtick.minor.width'] = 0.6
    plt.rcParams['ytick.major.size'] = 5
    plt.rcParams['ytick.major.width'] = 0.6
    plt.rcParams['ytick.minor.size'] = 2.5
    plt.rcParams['ytick.minor.width'] = 0.6
    plt.rcParams['lines.linewidth'] = 1.2
    plt.rcParams['lines.markersize'] = 5
    plt.rcParams['axes.linewidth'] = 0.6
    plt.rcParams['legend.frameon'] = False

    #TODO make this into a convenience function to put in the main namespace
    try:
        num_files = sg.popup_get_text('Enter number of files to open', 'Get Files', '1')
        if num_files:
            dataframes = []
            for _ in range(int(num_files)):
                #gets the values needed to import a datafile, and then imports the data to a dataframe
                import_values = utils.select_file_gui()
                dataframes.extend(
                    utils.raw_data_import(import_values, import_values['file'], False)
                )

            #writer used to save fitting results to Excel
            writer = pd.ExcelWriter('temporary file from peak fitting.xlsx',
                                    engine='xlsxwriter')

            #loops through the list of dataframes, fits each set of data, and writes the results to Excel
            peak_dfs = []
            params_dfs = []
            descriptors_dfs = []
            fit_results = []
            default_inputs = None
            for dataframe in dataframes:

                fit_output = fit_dataframe(dataframe, default_inputs)
                fit_results.append(fit_output[0])
                peak_dfs.append(fit_output[1])
                params_dfs.append(fit_output[2])
                descriptors_dfs.append(fit_output[3])
                default_inputs = fit_output[4]

                fit_to_excel(peak_dfs[-1], params_dfs[-1], descriptors_dfs[-1],
                             writer, default_inputs['sample_name'], True)

            #save the Excel file
            writer.save()

    except utils.WindowCloseError:
        pass
    except KeyboardInterrupt:
        pass
