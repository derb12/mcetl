# -*- coding: utf-8 -*-
"""Provides a GUI to ease the use of the peak_fitting program and save the results to Excel

@author: Donald Erb
Created on Sun May 24 15:18:18 2020

"""


from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import PySimpleGUI as sg

from . import peak_fitting
from . import utils


def _show_fit_plot(dataframe, gui_values):
    """
    Shows a plot of data with the fit range, background range, and possible peaks marked.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The dataframe that contains the x and y data.
    gui_values: dict
        A dictionary of values needed for plotting.

    """

    try: #TODO make the peak finding into a function because it is used multiple times
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

        peak_list = []
        if (additional_peaks.size > 0) and (other_peaks):
            peak_list = [found_peaks, user_peaks]
            label_list = ['Found peaks', 'User input peaks']
        elif (additional_peaks.size > 0):
            peak_list = [user_peaks]
            label_list = ['User input peaks']
        elif peaks[1]:
            peak_list = [found_peaks]
            label_list = ['Found peaks']

        if peak_list:
            ax.legend(
                peak_list, label_list, frameon=False, ncol=2,
                bbox_to_anchor=(0.0, 1.01, 1, 1.01), loc='lower left',
                borderaxespad=0, mode='expand'
            )

        fig.show()

    except Exception as e:
        sg.popup('Error creating plot:\n    ' + repr(e))

#TODO split this up into several functions?
#TODO need to add/verify validations for plotting, peak finding, and background selection
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
    tuple or bool
        If peak fitting was skipped for an entry, then False is returned. Otherwise,
        a tuple is returned with the following entries:
            fit_result : list
                A list of lmfit.ModelResult objects, which give information for each
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
                information criteria, the Bayesian information criteria,
                and the minimization method used for fitting.
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
        'automatic_peaks' : True,
        'manual_peaks': False,
        'debug': False,
        'automatic_bkg': True,
        'manual_bkg': False,
        'selected_peaks': [],
        'selected_bkg': []
    }

    #assigns the values from user_inputs to keys in default_inputs
    if user_inputs is not None:
        default_inputs.update(user_inputs)
    # values if using manual peak selection
    peak_list = default_inputs['selected_peaks']
    #values if using manual background selection
    bkg_points = default_inputs['selected_bkg']

    headers = dataframe.columns

    if default_inputs['batch_fit']:
        values = default_inputs

    else:
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
                [sg.Tab('Options', automatic_layout, key='automatic_tab',
                        visible=default_inputs['automatic_peaks']),
                 sg.Tab('Options', [
                     [sg.Text('')],
                     [sg.Button('Launch Peak Selector', enable_events=True, size=(30, 5)),
                      sg.Button('Update Peak & Model Lists', enable_events=True,
                                size=(30, 5))]
                 ], key='manual_tab', visible=default_inputs['manual_peaks'])]
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
                [sg.Tab('Background Options', auto_bkg_layout, key='auto_bkg_tab',
                        visible=default_inputs['automatic_bkg']),
                 sg.Tab('Background Options', [
                     [sg.Text('')],
                     [sg.Button('Launch Background Selector', key='bkg_selector',
                                enable_events=True, size=(30, 5))]
                 ], key='manual_bkg_tab', visible=default_inputs['manual_bkg'])]
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
                      key='automatic_peaks', enable_events=True,
                      default=default_inputs['automatic_peaks']),
             sg.Radio('Manual Peak Finding', 'peak_finding',
                      key='manual_peaks', enable_events=True,
                      default=default_inputs['manual_peaks'],
                      pad=((50, 10), 5))],
            [peak_finding_layout],
        ]

        layout = [
            [sg.Frame('', [
                [sg.Column(column_layout, scrollable=True,
                           vertical_scroll_only=True, size=(700, 500))]
            ])],
            [sg.Checkbox('Show Plots After Fitting', key='show_plots',
                         default=default_inputs['show_plots'])],
            [sg.Checkbox('Batch Fit (will not show this window again)',
                              key='batch_fit',
                              default=default_inputs['batch_fit'])],
            [sg.Checkbox('Debug Fitting Process', key='debug',
                         default=default_inputs['debug'])],
            [sg.Text('')],
            [sg.Button('Fit', bind_return_key=True, size=(6, 1),
                       button_color=utils.PROCEED_COLOR),
             sg.Button('Test Plot'),
             sg.Button('Show Data'),
             sg.Button('Reset to Default'),
             sg.Button('Skip Fitting')]
        ]
        validations = {
            'integers': [
                ['x_fit_index', 'x column'],
                ['y_fit_index', 'y column'],
                ['poly_n', 'polynomial order'],
                ['num_resid_fits', 'number of residual fits']
            ],
            'floats': [
                ['x_min', 'x min'],
                ['x_max', 'x max'],
                ['peak_width', 'peak width'],
                ['bkg_x_min', 'background x min'],
                ['bkg_x_max', 'background x max'],
                ['height', 'minimum height'],
                ['prominence', 'prominence'],
                ['center_offset', 'center offset'],
                ['min_resid', 'minimum residual height'],
                ['max_sigma', 'maximum sigma']
            ],
            'strings': [
                ['bkg_type', 'background model'],
                ['min_method', 'minimization method'],
                ['default_model', 'default model'],
            ],
            'user_inputs': [
                ['sample_name', 'sample name', utils.string_to_unicode, False, None],
                ['x_label', 'x label', utils.string_to_unicode, False, None],
                ['y_label', 'y label', utils.string_to_unicode, False, None],
                ['model_list', 'model list', str, True],
                ['peak_list', 'peak x values', float, True]
            ]
        }

        plot_validations = {
            'integers': validations['integers'][:3],
            'floats': validations['floats'][:5],
            'strings': validations['strings'][:1],
        }

        window = sg.Window('Peak Fitting', layout, finalize=True)
        if default_inputs['manual_peaks']:
            window['manual_tab'].select()
            window['automatic_tab'].update(visible=False)
        if default_inputs['manual_bkg']:
            window['manual_bkg_tab'].select()
            window['automatic_bkg_tab'].update(visible=False)

        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                utils.safely_close_window(window)

            elif event == 'Skip Fitting':
                skip = sg.popup_yes_no(
                        'Peak fitting will be skipped for this entry.\n\nProceed?\n',
                        title='Skip Fitting'
                    )
                if skip == 'Yes':
                    window.close()
                    del window
                    return False

            elif event == 'Reset to Default':
                window.fill(default_inputs)
                plt.close('Peak Selector')
                peak_list = []

            elif event == 'Test Plot':
                _show_fit_plot(dataframe, values)

            elif event == 'Show Data':
                data_window = utils.show_dataframes(dataframe)
                if data_window is not None:
                    data_window.read()
                    data_window.close()
                    data_window = None

            elif event == 'Update Peak & Model Lists':
                # updates values in the window from the peak selector plot
                centers = [[peak[0][0], np.round(peak[1][0], 2)] for peak in peak_list]
                sorted_peaks = sorted(centers, key=lambda x: x[1])
                sorted_centers = ', '.join([str(center) for model, center in sorted_peaks])
                tmp_model_list = [model for model, center in sorted_peaks]
                model_list = ', '.join(tmp_model_list)
                window['peak_list'].update(value=sorted_centers)
                window['model_list'].update(value=model_list)
                if any(model in ('VoigtModel', 'SkewedVoigtModel') for model in tmp_model_list):
                    window['vary_Voigt'].update(disabled=False)
                elif values['default_model'] not in ('VoigtModel', 'SkewedVoigtModel'):
                    window['vary_Voigt'].update(disabled=True, value=False)

            elif event == 'bkg_selector':
                plt.close('Background Selector')
                try:
                    x_index = int(values['x_fit_index'])
                    y_index = int(values['y_fit_index'])
                    x_data = dataframe[headers[x_index]].astype(float)
                    y_data = dataframe[headers[y_index]].astype(float)
                    bkg_points = peak_fitting.background_selector(x_data, y_data,
                                                                  bkg_points)
                except Exception as e:
                    sg.popup(f'\nError creating plot:\n    {repr(e)}\n')

            elif event == 'Launch Peak Selector':
                plt.close('Peak Selector')
                if utils.validate_inputs(values, **plot_validations):
                    try:
                        headers = dataframe.columns
                        x_index = int(values['x_fit_index'])
                        y_index = int(values['y_fit_index'])
                        x_data = dataframe[headers[x_index]].astype(float)
                        y_data = dataframe[headers[y_index]].astype(float)
                        x_min = float(values['x_min']) if values['x_min'] != '-inf' else -np.inf
                        x_max = float(values['x_max']) if values['x_max'] != 'inf' else np.inf
                        bkg_min = float(values['bkg_x_min']) if values['bkg_x_min'] != '-inf' else -np.inf
                        bkg_max = float(values['bkg_x_max']) if values['bkg_x_max'] != 'inf' else np.inf
                        subtract_bkg = values['subtract_bkg']
                        background_type = values['bkg_type']
                        bkg_min = float(values['bkg_x_min']) if values['bkg_x_min'] != '-inf' else -np.inf
                        bkg_max = float(values['bkg_x_max']) if values['bkg_x_max'] != 'inf' else np.inf
                        poly_n = int(values['poly_n'])
                        peak_width = float(values['peak_width'])
                        default_model = values['default_model']

                        if subtract_bkg:
                            if values['manual_bkg']:
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
                        peak_list = peak_fitting.peak_selector(
                            x_input, y_input, peak_list, peak_width, subtract_bkg,
                            background_type, poly_n, bkg_min, bkg_max, default_model
                        )
                    except Exception as e:
                        sg.popup(f'Error creating plot:\n    {repr(e)}')

            elif event in ('automatic_peaks', 'manual_peaks'):
                if event == 'automatic_peaks':
                    window['automatic_tab'].update(visible=True)
                    window['automatic_tab'].select()
                    window['manual_tab'].update(visible=False)

                else:
                    window['automatic_tab'].update(visible=False)
                    window['manual_tab'].update(visible=True)
                    window['manual_tab'].select()

            elif event in ('automatic_bkg', 'manual_bkg'):
                if event == 'automatic_bkg':
                    window['auto_bkg_tab'].update(visible=True)
                    window['auto_bkg_tab'].select()
                    window['manual_bkg_tab'].update(visible=False)
                else:
                    window['manual_bkg_tab'].update(visible=True)
                    window['manual_bkg_tab'].select()
                    window['auto_bkg_tab'].update(visible=False)

            elif event == 'subtract_bkg':
                if values['subtract_bkg']:
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
                if values['bkg_type'] == 'PolynomialModel':
                    window['poly_n'].update(visible=True)
                else:
                    window['poly_n'].update(visible=False, value='0')

            elif event in ('model_list', 'default_model'):
                tmp_model_list = [entry for entry in values['model_list'].replace(' ', '').split(',') if entry != '']
                v_models = ['VoigtModel', 'SkewedVoigtModel']
                if (any(model in v_models for model in tmp_model_list)) or (values['default_model'] in v_models):
                    window['vary_Voigt'].update(disabled=False)
                else:
                    window['vary_Voigt'].update(disabled=True, value=False)

            elif event == 'fit_residuals':
                if values['fit_residuals']:
                    window['min_resid'].update(visible=True)
                    window['num_resid_fits'].update(visible=True)
                else:
                    window['min_resid'].update(visible=False, value=0.05)
                    window['num_resid_fits'].update(visible=False, value=5)

            elif event =='Fit':
                if (not plt.fignum_exists('Peak Selector')
                        and not plt.fignum_exists('Background Selector')):

                    close = utils.validate_inputs(values, **validations)
                else:
                    sg.popup('Please close the Peak and/or Background Selection plots.')
                    continue

                if close:
                    model_list = [entry for entry in
                                  values['model_list'].replace(' ', '').split(',')
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
                    if not values['manual_peaks']:

                        x_index = int(values['x_fit_index'])
                        y_index = int(values['y_fit_index'])
                        x_data = dataframe[headers[x_index]]
                        y_data = dataframe[headers[y_index]]
                        x_min = float(values['x_min']) if values['x_min'] != '-inf' else -np.inf
                        x_max = float(values['x_max']) if values['x_max'] != 'inf' else np.inf
                        height = float(values['height'])
                        prominence = float(values['prominence']) if values['prominence'] != 'inf' else np.inf
                        if x_min == -np.inf:
                            x_min = min(x_data)
                        if x_max == np.inf:
                            x_max = max(x_data)
                        additional_peaks = [float(entry) for entry in
                                            values['peak_list'].replace(' ', '').split(',') if entry != '']

                        peaks = peak_fitting.find_peak_centers(
                            x_data, y_data, additional_peaks,
                            height, prominence, x_min, x_max
                        )
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

    x_label = utils.string_to_unicode(values['x_label'])
    y_label = utils.string_to_unicode(values['y_label'])
    x_index = int(values['x_fit_index'])
    y_index = int(values['y_fit_index'])
    x_data = dataframe[headers[x_index]]
    y_data = dataframe[headers[y_index]]
    x_min = float(values['x_min']) if values['x_min'] != '-inf' else -np.inf
    x_max = float(values['x_max']) if values['x_max'] != 'inf' else np.inf
    default_model = values['default_model']
    vary_Voigt = values['vary_Voigt']
    center_offset = float(values['center_offset'])
    min_method = values['min_method']
    subtract_bkg = values['subtract_bkg']
    background_type = values['bkg_type']
    bkg_min = float(values['bkg_x_min']) if values['bkg_x_min'] != '-inf' else -np.inf
    bkg_max = float(values['bkg_x_max']) if values['bkg_x_max'] != 'inf' else np.inf
    max_sigma = float(values['max_sigma']) if values['max_sigma'] != 'inf' else np.inf
    poly_n = int(values['poly_n'])
    fit_residuals = values['fit_residuals']
    min_resid = float(values['min_resid'])
    num_resid_fits = int(values['num_resid_fits'])
    debug = values['debug']

    if values['manual_peaks']:
        peaks = sorted(peak_list, key=lambda x: x[1][0])
        additional_peaks = [peak[1][0] for peak in peaks]
        model_list = [peak[0][0] for peak in peaks]
        peak_width = [peak[1][2] for peak in peaks]
        peak_heights = [peak[1][1] for peak in peaks]
        values['selected_peaks'] = peak_list
        # ensures no additional peaks are found
        height = np.inf
        prominence = np.inf

    else:
        additional_peaks = [
            float(entry) for entry in values['peak_list'].replace(' ', '').split(',') if entry
        ]
        model_list = [
            entry for entry in values['model_list'].replace(' ', '').split(',') if entry
        ]
        peak_width = float(values['peak_width'])
        peak_heights = None
        values['selected_peaks'] = []
        height = float(values['height'])
        prominence = float(values['prominence']) if values['prominence'] != 'inf' else np.inf


    if subtract_bkg:
        if values['manual_bkg']:
            values['selected_bkg'] = bkg_points
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
            values['selected_bkg'] = []

    fitting_results = peak_fitting.plugNchug_fit(
        x_data, y_data, height, prominence, center_offset, peak_width, default_model,
        subtract_bkg, bkg_min, bkg_max, 0, max_sigma, min_method, x_min, x_max,
        additional_peaks, model_list, background_type, poly_n, None, vary_Voigt,
        fit_residuals, num_resid_fits, min_resid, debug, peak_heights
    )

    output_list = [fitting_results[key] for key in fitting_results]
    fit_result, individual_peaks, best_values = output_list[5:]

    #renames amplitude to area for peaks to be more clear; lmfit has amplitude==area
    #by the way the module defines the peaks
    for result in best_values:
        for param in result:
            if 'peak' in param[0] and 'amplitude' in param[0]:
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

    if values['show_plots']:
        peak_fitting.plot_fit_results(x, y, fit_result, True, True)
        peak_fitting.plot_individual_peaks(
            x, y, individual_peaks[-1], fit_result[-1],
            subtract_bkg, plot_w_background=True
        )
        plt.pause(0.01)

    return fit_result, peaks_df, params_df, descriptors_df, values


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

    """

    excel_book = excel_writer.book

    #Formatting styles for the Excel workbook
    if len(excel_book.formats) < 10: # a new writer
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

    else:
        (odd_subheader_format, even_subheader_format, odd_colnum_format,
         even_colnum_format, odd_header_format, even_header_format,
         odd_bold_format, even_bold_format) = excel_book.formats[2:10]

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

    peaks_dataframe.to_excel(
        excel_writer, sheet_name=sheet_name, index=False,startrow=3, header=False
    )
    params_dataframe.to_excel(
        excel_writer, sheet_name=sheet_name, startrow=3,
        startcol=len(peaks_dataframe.columns) + 1, header=False, index=False
    )
    descriptors_dataframe.to_excel(
        excel_writer, sheet_name=sheet_name, startrow=1,
        startcol=len(peaks_dataframe.columns) + len(params_dataframe.columns) + 2,
        header=False, index=False
    )
    worksheet = excel_writer.sheets[sheet_name]

    #Modifies the formatting to look good in Excel
    worksheet.merge_range(
        0, 0, 0, len(peaks_dataframe.columns) - 1, 'Values', even_header_format
    )
    worksheet.merge_range(1, 0, 1, 1, 'Raw Data', odd_header_format)
    worksheet.merge_range(
        1, 2, 1, len(peaks_dataframe.columns) - 1, 'Fitted Data',
        even_header_format
    )

    #formatting for peaks_dataframe
    for i, peak_name in enumerate(peaks_dataframe.columns):
        if i % 2 == 0:
            formats = [even_subheader_format, even_colnum_format]
        else:
            formats = [odd_subheader_format, odd_colnum_format]
        worksheet.write(2, i, peak_name, formats[0])
        worksheet.set_column(i, i, 12.5, formats[1])

    worksheet.merge_range(
        0, len(peaks_dataframe.columns), 0,
        len(peaks_dataframe.columns) + len(params_dataframe.columns),
        'Peak Parameters', odd_header_format
    )
    worksheet.merge_range(
        0, len(peaks_dataframe.columns) + len(params_dataframe.columns) + 1,
        0, total_width, 'Fit Description', even_header_format
    )

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

    # formatting for descriptors_dataframe
    if (j + i + 1) % 2 == 0:
        formats = [even_bold_format, odd_bold_format]
    else:
        formats = [odd_bold_format, even_bold_format]
    for k, parameter in enumerate(descriptors_dataframe.index):
        worksheet.write(1 + k, 2 * (j + 1) + i + 1, parameter, formats[0])

    worksheet.set_column((j + 1) * 2 + i + 1, (j + 1) * 2 + i + 1, 22, formats[0])
    worksheet.set_column((j + 1) * 2 + i + 2, (j + 1) * 2 + i + 2, 15, formats[1])
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


def launch_peak_fitting_gui(dataframe=None, gui_values=None, excel_writer=None,
                            save_excel=True, plot_excel=True, mpl_changes=None,
                            save_when_done=True):
    """
    Convenience function to fit dataframe(s) and write their results to Excel.

    Parameters
    ----------
    dataframe : pd.DataFrame or list/tuple, optional
        The dataframe or list/tuple of dataframes to fit.
    gui_values : dict, optional
        A dictionary containing the default gui values to pass to fit_dataframe.
    excel_writer : pd.ExcelWriter, optional
        The Excel writer used to save the results to Excel.
    save_excel : bool, optional
        If True (default), then the fit results will be saved to an Excel file.
    plot_excel : bool, optional
        If True (default), then the fit results will be plotted in the
        Excel file (if saving).
    mpl_changes : dict, optional
        A dictionary of changes to apply to matplotlib's rcParams file.
    save_when_done : bool, optional
        If True (default), then the Excel file will be saved once all dataframes
        are fit.

    Returns
    -------
    fit_results : list
        A list of lists of lmfit.ModelResult objects, which give information
        for each of the fits done on the dataframes.
    gui_values : dict, optional
        A dictionary containing the default gui values to pass to fit_dataframe.
    proceed : bool
        True if the fitting gui was not exited from prematurely, otherwise,
        the value is False. Useful when calling this function from an
        outside function that needs to know whether to continue doing
        peak fitting.

    """
    #TODO check that mpl backend is interactive; if not, try to switch to tkAgg
    rc_params = mpl_changes.copy() if mpl_changes is not None else {}
    rc_params.update({
        'interactive': False,
        'figure.constrained_layout.use': False,
        'figure.autolayout': True
    })
    # Correctly scales the dpi to match the desired dpi.
    dpi = rc_params.get('figure.dpi', plt.rcParams['figure.dpi'])
    dpi_scale = utils.get_dpi_correction(dpi)
    rc_params.update({'figure.dpi': dpi_scale * dpi})

    if dataframe is not None and isinstance(dataframe, pd.DataFrame):
        fit_dataframes = [dataframe]
    else:
        fit_dataframes = utils.open_multiple_files()

    if save_excel and excel_writer is None: #TODO maybe make a pop-up to allow selecting the file name and location
        writer = pd.ExcelWriter('temporary file from peak fitting.xlsx',
                                engine='xlsxwriter')
    else:
        writer = excel_writer

    fit_results = []
    proceed = True
    for dataframe in fit_dataframes:
        try:
            with plt.rc_context(rc_params):
                fit_output = fit_dataframe(dataframe, gui_values)

        except (utils.WindowCloseError, KeyboardInterrupt):
            proceed = False
            break

        if not fit_output: # Fitting was skipped for the data entry
            fit_results.append(None)
        else:
            fit_results.append(fit_output[0])
            peak_df = fit_output[1]
            params_df = fit_output[2]
            descriptors_df = fit_output[3]
            gui_values = fit_output[4]

            if save_excel:
                fit_to_excel(peak_df, params_df, descriptors_df,
                             writer, gui_values['sample_name'], plot_excel)

    if save_excel and save_when_done and not all(entry is None for entry in fit_results):
        #save the Excel file
        writer.save()

    return fit_results, gui_values, proceed
