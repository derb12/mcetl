# -*- coding: utf-8 -*-
"""Functions for creating and fitting a model with peaks and a background and plotting the results.

Also contains two classes that create windows to allow selection of peak positions and
background points.

@author: Donald Erb
Created on Sep 14, 2019

"""


from collections import defaultdict
import itertools

import matplotlib.pyplot as plt
import lmfit
import numpy as np
import PySimpleGUI as sg
from scipy import signal

from . import fitting_utils as f_utils
from . import models
from .. import plot_utils, utils


def peak_transformer():
    """
    The expressions needed to convert peak width, height, and mode to model parameters.

    Returns
    -------
    dict(str: dict(str: function))
        A dictionary containing the string for lmfit models as keys, and
        a dictionary as the values, containing the equations to estimate
        parameters of the model using input heights, full-width-at-half-maximums,
        and peak mode (x-position at max y).

    Notes
    -----
    More peak models are available from lmfit, but these are the ones I have
    tested and implemented currently.

    Inputs are max height (h), fwhm (w), and mode (x where y=max height)(m).

    Most equations for approximating the amplitude and sigma were gotten from:
    http://openafox.com/science/peak-function-derivations.html

    The equations for the BreitWignerModel and BreitWignerFanoModel models were
    derived personally, with the formulas for BreitWignerFanoModel
    for fwhm = 2 * sigma * (1 + q**2) / ((q**2) - 1 + 1e-19), where the 1e-19 is in
    case q = 1 or q = -1, and the formula for height = maximum / (1 + 1 / q**2).

    """

    models_dict = {
        # lmfit.models.GaussianModel
        'GaussianModel': {
            'sigma': lambda h, w, *args: w / (2 * np.sqrt(2 * np.log(2))),
            'amplitude': lambda h, w, *args: (h * w * np.sqrt(np.pi / (np.log(2)))) / 2,
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.LorentzianModel
        'LorentzianModel': {
            'sigma': lambda h, w, *args: w / 2,
            'amplitude': lambda h, w, *args: (h * w * np.pi) / 2,
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.VoigtModel
        'VoigtModel': {
            'sigma': lambda h, w, *args: w / 3.6013,
            'gamma': lambda h, w, *args: w / 3.6013,
            'amplitude': lambda h, w, *args: (h * w  * 0.531 * np.sqrt(2 * np.pi)),
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.PseudoVoigtModel
        'PseudoVoigtModel': {
            'sigma': lambda h, w, *args: w / 2,
            'amplitude': lambda h, w, *args: h * w * 1.269,
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.Pearson7Model
        'Pearson7Model': {
            'sigma': lambda h, w, *args: w / (2 * np.sqrt((2**(1 / 1.5)) - 1)),
            'amplitude': lambda h, w, *args: 2 * h * w / (2 * np.sqrt((2**(1 / 1.5)) - 1)),
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.MoffatModel
        'MoffatModel': {
            'sigma': lambda h, w, *args: w / 2,
            'amplitude': lambda h, w, *args: h,
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.SkewedGaussianModel
        'SkewedGaussianModel': {
            'sigma': lambda h, w, *args: w / (2 * np.sqrt(2 * np.log(2))),
            'amplitude': lambda h, w, *args: (h * w * np.sqrt(np.pi / (np.log(2)))) / 2,
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.SkewedVoigtModel
        'SkewedVoigtModel': {
            'sigma': lambda h, w, *args: w / 3.6013,
            'gamma': lambda h, w, *args: w / 3.6013,
            'amplitude': lambda h, w, *args: (h * w  * 0.531 * np.sqrt(2 * np.pi)),
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.SplitLorentzianModel
        'SplitLorentzianModel': {
            'sigma': lambda h, w, *args: w / 2,
            'sigma_r': lambda h, w, *args: w / 2,
            'amplitude': lambda h, w, *args: (h * w * np.pi) / 2,
            'center': lambda h, w, m, *args: m
        },
        # lmfit.models.LognormalModel
        'LognormalModel': {
            'sigma': _lognormal_sigma,
            'amplitude': _lognormal_amplitude,
            'center': _lognormal_center
        },
        # lmfit.models.BreitWignerModel
        'BreitWignerModel': { # assumes q = 1 at init
            'sigma': lambda h, w, *args: w, # leave alone since fwhm=inf for q=1
            'amplitude': lambda h, w, *args: h / 2,
            'center': lambda h, w, m, *args: m - w / 2,
        },
        # mcetl.fitting.models.BreitWignerFanoModel
        'BreitWignerFanoModel': { # assumes q = -3 at init
            'sigma': lambda h, w, *args: w * 4 / 10,
            'height': lambda h, w, *args: h / (1 + 1 / 3**2),
            'center': lambda h, w, m, *args: m - (w * 4 / 10) / (-3),
        }
    }

    return {key: value for key, value in sorted(models_dict.items(), key=lambda kv: kv[0])}


def _lognormal_center(peak_height, peak_width, mode, *args):
    """
    Estimates the center (mean) value of a lognormal distribution.

    Parameters
    ----------
    peak_height : float
        The height of the peak at its maximum.
    peak_width : float
        The estimated full-width-half-maximum of the peak.
    mode : float
        The x-position at which the peak reaches its maximum value.
    *args
        Further arguments will be passed; used in case other lmfit models
        require more than these three parameters.

    Returns
    -------
    float
        The estimated center of the distribution.

    """

    sigma = _lognormal_sigma(peak_height, peak_width, mode)

    return np.log(max(1e-9, mode)) + sigma**2


def _lognormal_sigma(peak_height, peak_width, mode, *args):
    """
    Estimates the sigma value of a lognormal distribution.

    Parameters
    ----------
    peak_height : float
        The height of the peak at its maximum.
    peak_width : float
        The estimated full-width-half-maximum of the peak.
    mode : float
        The x-position at which the peak reaches its maximum value.
    *args
        Further arguments will be passed; used in case other lmfit models
        require more than these three parameters.

    Returns
    -------
    float
        The estimated sigma value for the distribution.

    """

    m2 = mode**2 # m2 denotes mode squared

    return 0.85 * np.log((peak_width + mode * np.sqrt((4 * m2 + peak_width**2) / (m2))) / (2 * mode))


def _lognormal_amplitude(peak_height, peak_width, mode, *args):
    """
    Estimates the amplitude value of a lognormal distribution.

    Parameters
    ----------
    peak_height : float
        The height of the peak at its maximum.
    peak_width : float
        The estimated full-width-half-maximum of the peak.
    mode : float
        The x-position at which the peak reaches its maximum value.
    *args
        Further arguments will be passed; used in case other lmfit models
        require more than these three parameters.

    Returns
    -------
    float
        The estimated amplitude value for the distribution.

    """

    sigma = _lognormal_sigma(peak_height, peak_width, mode)
    mean = np.log(max(1e-9, mode)) + sigma**2

    return (peak_height * sigma * np.sqrt(2 * np.pi)) / (np.exp(((sigma**2) / 2) - mean))


def _initialize_peaks(x, y, peak_centers, peak_width=1.0, center_offset=1.0,
                      vary_Voigt=False, model_list=None,
                      default_model='PseudoVoigtModel', min_sigma=0.0,
                      max_sigma=np.inf, background_y=0.0,
                      params_dict=None, debug=False, peak_heights=None):
    """
    Generates the default parameters for each peak.

    Parameters
    ----------
    x, y : array-like
        x and y values for the fitting.
    peak_centers : list
        A list of centers of every peak.
    peak_width : float or list
        Used in initializing each peak. When first estimating the
        peak parameters, only the data from x - peak_width/2 to
        x + peak_width/2 is used to fit the peak.
        Can also be a list of peak widths.
    center_offset : float
        Value that determines the min and max parameters for
        the center of each peak. min = center - center_offset,
        max = center + center_offset.
    vary_Voigt : bool
        If True, will allow the gamma parameter in the Voigt model
        to be varied as an additional variable; if False, gamma
        will be set equal to sigma.
    model_list : list
        List of strings, with each string corresponding to one of the
        models in lmfit.models.
    default_model : str
        Model used if the model_list is None or does not have
        enough values for the number of peaks found.
    subtract_background : bool
        If True, it will fit the background with the model in background_type.
    min_sigma : float
        Minimum value for the sigma for each peak; typically
        better to not set to any value other than 0.
    max_sigma : float
        Maximum value for the sigma for each peak; typically
        better to not set to any value other than infinity.
    background_y : array-like or float
        The background, which will be subtracted from y before
        initializing the peaks.
    params_dict : dict
        A dictionary with peak prefixes as keys and a list of the
        peak model string and the peak parameters as the values.
    debug : bool
        If True, will create plots at various portions of the code showing
        the peak initialization. Note: will create two plots, one title 'initial'
        and the other titled 'best fit'. The 'initial' plot shows the peaks
        as they are first generated by using lmfit's guess fuction. The 'best fit'
        plot will have potentially two plots for each peak. The plot labeled 'fit'
        corresponds to the peak after fitting to the data, the the plot labled 'model'
        is the peak as it will be used in the actual model. The difference beween
        'model' and 'fit' is that 'model' has the same peak center as input, and
        it will potentially use a different height and/or width than that of the 'fit'
        data if the 'fit' data was disgarded for various reasons.
    peak_heights : list, optional
        A list of peak heights.

    Returns
    -------
    params_dict : dict
        A dictionary with peak prefixes as keys and a list of the
        peak model string and the peak parameters as the values.
        Example output:
            params_dict = {
                'peak_0_': [
                    'GaussianModel',
                    Parameters([
                        ('peak_0_center', <Parameter 'peak_0_center',
                         value=1.0, bounds=[0.0:2.0]>),
                        ('peak_0_sigma', <Parameter 'peak_0_sigma',
                         value=1.0, bounds=[-inf:inf]>)
                    ])
                ]
                'peak_1_': ['LorentzianModel', Parameters(...)]
            }

    Raises
    ------
    NotImplementedError
        Raised if a model is not within the dictionary of implemented peaks
        from the peak_transformer function.

    Notes
    -----
    If params_dict is not None, it means residual data is being fit.
    The residuals are interpolated just a little to smooth the data to
    improve the signal to noise ratio for the initial fits, which only really matters
    when fitting peaks that are small. Any value in the residuals that is < 0 is s
    et to 0 to not influence the peak fitting.

    The residual values are shifted up by (0 - min(y)) to slightly
    overestimate the peak height. In the case of polynomial backgrounds,
    this helps to avoid getting stuck in a local minimum in which the
    peak height is underestimated and the background is overestimated.

    Lognormal models are directly estimated by assuming the input peak center
    is the mode of the peak, since lmfit's guess is not accurate for lognormal
    peaks.

    """

    model_list = model_list if model_list is not None else []
    peak_list = itertools.chain(model_list, itertools.cycle([default_model]))
    peak_widths = peak_width if isinstance(peak_width, (list, tuple)) else [peak_width] * len(peak_centers)

    y = y.copy() - background_y

    if params_dict is not None:
        window = len(x) // 20 if (len(x) // 20) % 2 == 1 else (len(x) // 20) + 1
        y2 = signal.savgol_filter(y, window, 2, deriv=0)
        y2[y2 < 0] = 0
        y = y2 + (0 - np.min(y))
        use_middles = False
        start_num = len(params_dict)

    else:
        params_dict = {}
        start_num = 0
        use_middles = True

    # finds the position between peak centers
    minx, maxx = (np.min(x), np.max(x))
    middles = [0.0 for num in range(len(peak_centers) + 1)]
    middles[0], middles[-1] = minx, maxx
    for i in range(len(peak_centers) - 1):
        middles[i + 1] = np.mean([peak_centers[i], peak_centers[i + 1]])

    if debug:
        ax1 = plt.subplots()[-1]
        ax2 = plt.subplots()[-1]
        ax1.plot(x, y)
        ax2.plot(x, y, label='data')

    models_dict = peak_transformer()
    for i, peak_center in enumerate(peak_centers, start_num):
        prefix = f'peak_{i + 1}_'
        peak_width = peak_widths[i]
        peak_type = f_utils.get_model_name(next(peak_list))

        if peak_type not in models_dict:
            raise NotImplementedError(f'{peak_type} is not an implemented peak model.')

        peak_model = f_utils.get_model_object(peak_type)(prefix=prefix)
        amplitude_key = 'amplitude' if peak_type != 'BreitWignerFanoModel' else 'height'

        if use_middles:
            peak_mask = (x >= middles[i]) & (x <= middles[i + 1])
        else:
            peak_mask = (x > peak_center - (peak_width / 2)) & (x < peak_center + (peak_width / 2))

        x_peak = x[peak_mask]
        y_peak = y[peak_mask]

        if peak_heights is None:
            peak_height = y_peak[np.argmin(np.abs(peak_center - x_peak))] / 2
        else:
            peak_height = peak_heights[i]

        param_kwargs = {'amplitude': {'min': -np.inf if peak_height < 0 else 0,
                                      'max': 0 if peak_height < 0 else np.inf},
                        'sigma': {'min': min_sigma, 'max': max_sigma}}

        if peak_type != 'LognormalModel':
            param_kwargs['center'] = {'value': peak_center,
                                      'min': peak_center - center_offset,
                                      'max': peak_center + center_offset}
        else:
            # estimate the values because lmfit's guess is bad for lognormal
            sigma = _lognormal_sigma(peak_height, peak_width, peak_center)
            # cannot set min, max for center for lognormal since it depends on sigma
            # TODO could create an expression for a parameter called mode, and set the
            # min and max for mode, which would constrain center
            param_kwargs['center'] = {'value': np.log(max(1e-19, peak_center)) + sigma**2}
            param_kwargs['sigma']['value'] = sigma
            param_kwargs['amplitude']['value'] = _lognormal_amplitude(peak_height, peak_width,
                                                                      peak_center)
            param_kwargs['mode'] = {'expr': f'exp({prefix}center - {prefix}sigma**2)',
                                      'min': peak_center - center_offset,
                                      'max': peak_center + center_offset}
            # TODO setting mode doesn't seem to constrain center and sigma...
            peak_model.set_param_hint('mode', **param_kwargs['mode'])

        peak_model.set_param_hint('center', **param_kwargs['center'])
        peak_model.set_param_hint(amplitude_key, **param_kwargs['amplitude'])
        peak_model.set_param_hint('sigma', **param_kwargs['sigma'])

        if peak_type in ('VoigtModel', 'SkewedVoigtModel') and vary_Voigt:
            peak_model.set_param_hint('gamma', min=min_sigma, max=max_sigma,
                                      vary=True, expr='')

        if peak_type != 'LognormalModel':
            default_params = peak_model.guess(y_peak, x_peak, negative=peak_height < 0)
        else:
            default_params = {}
        peak_params = peak_model.make_params(**default_params)

        if debug:
            ax1.plot(x_peak, peak_model.eval(peak_params, x=x_peak))

        lone_peak = False if peak_type != 'LognormalModel' else True
        # peak_width < middles checks whether the peak is isolated or near other peaks
        if peak_heights is None and peak_width < (middles[i + 1] - middles[i]):
            temp_fit = peak_model.fit(y_peak, peak_params, x=x_peak,
                                      method='least_squares')

            if debug:
                ax2.plot(x_peak, peak_model.eval(temp_fit.params, x=x_peak),
                         label=f'{prefix}fit')

            if f'{prefix}fwhm' in peak_params:
                fwhm = temp_fit.values[f'{prefix}fwhm']
            else:
                fwhm = temp_fit.values[f'{prefix}sigma'] * 2.5 # estimate

            # only uses the parameters after fitting if  fwhm < 2 * peak_width
            # used to prevent hidden peaks from flattening before the total fitting
            if fwhm < (2 * peak_width):
                lone_peak = True
                peak_params = temp_fit.params
                # do not allow peak centers to shift during initialization
                peak_params[f'{prefix}center'].value = param_kwargs['center']['value']

        if not lone_peak: # calculates parameters using equations from peak_transformer
            for parameter, equation in models_dict[peak_type].items():
                peak_params[f'{prefix}{parameter}'].value = equation(peak_height, peak_width,
                                                                     peak_center)

        if debug:
            ax2.plot(x_peak, peak_model.eval(peak_params, x=x_peak), label=f'{prefix}model')

        params_dict[prefix] = [peak_type, peak_params]

    if debug:
        ax1.set_title('peak initialization: initial')
        ax2.set_title('peak initialization: best fit')
        ax2.legend(ncol=max(1, len(peak_centers) // 4))

    return params_dict


def _generate_composite_model(params_dict):
    """
    Creates an lmfit composite model using the input dictionary of parameters.

    Parameters
    ----------
    params_dict : dict
        A dictionary with peak prefixes as keys and a list of the
        peak model string and the peak parameters as the values.

    Returns
    -------
    composite_model : lmfit.CompositeModel
        An lmfit CompositeModel containing all of the peaks.
    params : lmfit.Parameters
        An lmfit Parameters object containing the parameters for all peaks.

    Notes
    -----
    This function is separated from the _initialize_peaks function so that peaks
    can be reordered according to their center without having to reinitialize
    each peak, only the composite model.

    """

    params = None
    composite_model = None
    for prefix, param_values in params_dict.items():
        peak_model = f_utils.get_model_object(param_values[0])(prefix=prefix)
        for param in param_values[1]:
            hint_dict = {
                'value' : param_values[1][param].value,
                'min' : param_values[1][param].min,
                'max' : param_values[1][param].max,
                'vary' : param_values[1][param].vary,
                'expr' : param_values[1][param].expr
            }
            peak_model.set_param_hint(param, **hint_dict)
        peak_params = peak_model.make_params()

        if composite_model is None:
            composite_model = peak_model
            params = peak_params
        else:
            composite_model += peak_model
            params += peak_params

    return composite_model, params


def find_peak_centers(x, y, additional_peaks=None, height=None,
                      prominence=np.inf, x_min=-np.inf, x_max=np.inf):
    """
    Creates a list containing the peaks found and peaks accepted.

    Parameters
    ----------
    x, y : array-like
        x and y values for the fitting.
    additional_peaks : list, optional
        Peak centers that are input by the user and
        automatically accepted as peaks if within x_min and x_max.
    height : int or float, optional
        Height that a peak must have for it to be considered a peak by
        scipy's find_peaks.
    prominence : int or float
        Prominence that a peak must have for it to be considered
        a peak by scipy's find_peaks.
    x_min : int or float
        Minimum x value used in fitting the data.
    x_max : int or float
        Maximum x value used in fitting the data.

    Returns
    -------
    peaks_found : list
        A list of all the peak centers found.
    peaks_accepted : list
        A list of peak centers that were accepted because they were within
        x_min and x_max.

    Notes
    -----
    Uses scipy's signal.find_peaks to find peaks matching the specifications,
    and adds those peaks to a list of additionally specified peaks.

    """

    additional_peaks = np.array(additional_peaks) if additional_peaks is not None else np.empty(0)
    if additional_peaks.size > 0:
        additional_peaks = additional_peaks[(additional_peaks > np.nanmin(x))
                                            & (additional_peaks < np.nanmax(x))]

    peaks_located = signal.find_peaks(y, height=height, prominence=prominence)[0]
    peaks = [*peaks_located, *additional_peaks]

    peak_centers = []
    for peak in peaks:
        if peak in peaks_located:
            peak_centers.append(x[peak])
        else:
            peak_centers.append(peak)

    peaks_found = []
    peaks_accepted = []
    for x_peak in sorted(peak_centers):
        peaks_found.append(x_peak)
        if x_peak >= x_min and x_peak <= x_max:
            peaks_accepted.append(x_peak)

    return sorted(peaks_found), sorted(peaks_accepted)


def _find_hidden_peaks(x, fit_result, peak_centers, peak_fwhms,
                       min_resid=0.05, debug=False):
    """
    Locates hidden peaks by using scipy's find_peaks on the fit residuals.

    Parameters
    ----------
    x: array-like
        x values for the fitting.
    fit_result : lmfit.ModelResult
        An lmfit ModelResult object from the last fitting.
    peak_centers : list
        A list of peak centers that are already within the model.
    peak_fwhms : list
        A list of fwhm or estimated fwhm for each peak in the model.
    min_resid : float
        The minimum prominence that a peak must have for it to be considered
        a peak by scipy's find_peaks; the actual prominence used by find_peaks
        is min_resid * (max_y - min_y).
    debug : bool
        If True, will plot the residuals, and the residuals after smoothing.

    Returns
    -------
    residual_peaks_found : list
        A list of the centers of all residual peaks found from peak fitting
        the residuals.
    residual_peaks_accepted : list
        A list of the centers for the residual peaks accepted into the model.
        In order to be accepted, the residual peak must fulfill the following
        condition: x_l + fwhm_l/2 < x_peak < x_r - fwhm_r/2
        where x_l and x_r are the centers of the peaks to the left and right
        of the found residual peak (with center at x_peak), and fwhm_l and
        fwhm_r are the full width at half maximum of the left and right peaks.
        It is an arbitrary condition that has no real basis in science,
        but is just meant to reduce the number of residual peaks accepted.

    Notes
    -----
    Residuals are defined as y_data - y_calculated. Any residual < 0 is
    set to 0 so that an overestimation of y_calc does not produce
    additional peaks. This also prevents negative peaks from being
    fit, if the data has negative peaks; however, data having negative peaks
    and requiring its residuals to be fit is an edge case, so I think it is
    reasonable to ignore for now.

    Can also find hidden peaks by checking curvature of y using the 2nd and
    4th derivatives, but it is typically extremely noisy.

    Fitting residuals is simple enough, but if it does not provide great
    results, set peak positions for the most prominent peaks before fitting
    rather than trying to detect all peaks. This is especially helpful for
    sharp, close peaks.

    A more robust method would be to compare the Bayesian criteria before
    and after adding the peak, and just decide that way without basing
    it off of distance from other peak centers. However, that implementation
    would be almost overkill. The purpose of finding the hidden peaks is so
    that most likely candidates can be established, and then a literature
    search would determine what those peaks correspond to and whether they
    are true or not. A finalized evaluation using this module would not use
    residual fitting because all potential peak positions would be input at
    the start of the fitting.

    """

    residuals = - fit_result.residual
    y = fit_result.best_fit + residuals
    # window has to be odd for scipy's Savitzky-Golay function
    window = int(len(x) / 20) if int(len(x) / 20) % 2 == 1 else int(len(x) / 20) + 1
    poly = 2
    # interpolate residuals to smooth them a bit and improve signal to noise ratio
    resid_interp = signal.savgol_filter(residuals, window, poly)

    resid_interp[resid_interp < 0] = 0
    prominence = min_resid * (np.max(y) - np.min(y))

    residual_peaks = find_peak_centers(x, y=resid_interp, prominence=prominence)
    residual_peaks_found, residual_peak_centers = residual_peaks

    current_centers = np.array(peak_centers)
    fwhm = np.array(peak_fwhms)

    residual_peaks_accepted = []
    for peak_x in residual_peak_centers:
        left_peaks = (current_centers <= peak_x)
        right_peaks = (current_centers > peak_x)
        if np.any(left_peaks):
            left_fwhm = fwhm[left_peaks][-1]
            left_center = current_centers[left_peaks][-1]
        else:
            left_fwhm = 0
            left_center = -np.inf
        if np.any(right_peaks):
            right_fwhm = fwhm[right_peaks][0]
            right_center = current_centers[right_peaks][0]
        else:
            right_fwhm = 0
            right_center = np.inf

        if (peak_x > left_center + (left_fwhm / 2)) and (peak_x < right_center - (right_fwhm / 2)):
            residual_peaks_accepted.append(peak_x)

    if debug:
        ax = plt.subplots()[-1]
        ax.plot(x,residuals, label='residuals')
        ax.plot(x, resid_interp, label='interpolated residuals')
        ax.plot(x, np.array([prominence] * len(x)),
                label='minimum height to be a peak')
        if residual_peak_centers:
            for peak in residual_peak_centers:
                if peak not in residual_peaks_accepted:
                    ax.axvline(peak, 0, 0.9, c='red', linestyle='-.')
            for peak in residual_peaks_accepted:
                ax.axvline(peak, 0, 0.9, c='green', linestyle='--')
            legend = ['peaks rejected', 'peaks accepted']
            colors = ['red', 'green']
            styles = ['-.', '--']
            for i in range(2):
                plt.text(0.1 + 0.35 * i, 0.96, legend[i], ha='left', va='center',
                         transform=ax.transAxes)
                plt.hlines(0.96, 0.02 + 0.35 * i, 0.08 + 0.35 * i, color=colors[i],
                           linestyle=styles[i], transform=ax.transAxes)

        ax.legend()
        ax.set_title('residuals')

    return residual_peaks_found, residual_peaks_accepted


def _re_sort_prefixes(params_dict):
    """
    Reassigns peak prefixes so that peak number increases from left to right.

    Parameters
    ----------
    params_dict : dict
        A dictionary with peak prefixes as keys and a list of the
        peak model string and the peak parameters as the values.

    Returns
    -------
    new_params_dict: dict
        A dictionary with peak prefixes as keys and a list of the peak model
        string and the peak parameters as the values, but sorted so that the
        peak prefixes are in order from left to right.

    Notes
    -----
    Ensures that expressions used to define parameters are correct by replacing
    the old peak name with the new peak name in the expressions.

    """

    centers = []
    for prefix in params_dict:
        if params_dict[prefix][0] != 'LognormalModel':
            centers.append([prefix, params_dict[prefix][1][f'{prefix}center'].value])
        else:
            mean = params_dict[prefix][1][f'{prefix}center'].value
            sigma = params_dict[prefix][1][f'{prefix}sigma'].value
            center = np.exp(mean - sigma**2)
            centers.append([prefix, center])

    sorted_prefixes = [prefix for prefix, center in sorted(centers, key=lambda x: x[1])]

    new_params_dict = {}
    for index, old_prefix in enumerate(sorted_prefixes, 1):
        new_prefix = f'peak_{index}_'
        new_params = lmfit.Parameters()

        for param in params_dict[old_prefix][1]:
            name = params_dict[old_prefix][1][param].name.replace(old_prefix, new_prefix)
            value = params_dict[old_prefix][1][param].value
            param_min = params_dict[old_prefix][1][param].min
            param_max = params_dict[old_prefix][1][param].max
            vary = params_dict[old_prefix][1][param].vary
            if params_dict[old_prefix][1][param].expr is not None:
                params_dict[old_prefix][1][param].expr = (
                    params_dict[old_prefix][1][param].expr.replace(old_prefix, new_prefix)
                )
            expr = params_dict[old_prefix][1][param].expr

            new_params.add(name=name, value=value, vary=vary, min=param_min,
                           max=param_max, expr=expr)

        new_params_dict[new_prefix] = [params_dict[old_prefix][0], new_params]

    return new_params_dict


def _check_background(background_model, background_value, y):
    """
    Ensures that the background_value and y have the same shape.

    ConstantModel and ComplexConstantModel return a single value
    rather than an array, so need to create an array for those
    models so that issues aren't caused during plotting.

    Parameters
    ----------
    background_model : str
        The model used for the background, such as 'ConstantModel'.
    background_value : array-like or float
        The value(s) of the background.
    y : array-like
        The data being fit.

    Returns
    -------
    output : array-like
        An array of the background values, with the same size as the
        input y array.

    """

    if 'Constant' in background_model:
        output = np.full(y.size, background_value)
    else:
        output = background_value

    return output


def fit_peaks(
        x, y, height=None, prominence=np.inf, center_offset=1.0,
        peak_width=1.0, default_model='PseudoVoigtModel', subtract_background=False,
        bkg_min=-np.inf, bkg_max=np.inf, min_sigma=0.0, max_sigma=np.inf,
        min_method='least_squares', x_min=-np.inf, x_max=np.inf,
        additional_peaks=None, model_list=None, background_type='PolynomialModel',
        poly_n=0, fit_kws=None, vary_Voigt=False, fit_residuals=False,
        num_resid_fits=5, min_resid=0.05, debug=False, peak_heights=None):
    """
    Takes x,y data, finds the peaks, fits the peaks, and returns all relevant information.

    Parameters
    ----------
    x, y : array-like
        x and y values for the fitting.
    height : int or float
        Height that a peak must have for it to be considered a peak by
        scipy's find_peaks.
    prominence : int or float
        Prominence that a peak must have for it to be considered a peak by
        scipy's find_peaks.
    center_offset : int or float
        Value that determines the min and max parameters for the center of each
        peak. min = center - center_offset, max = center + center_offset.
    peak_width : int or float
        A guess at the full-width-half-max of the peaks. When first estimating
        the peak parameters, only the data from x - peak_width / 2 to
        x + peak_width / 2 is used to fit the peak.
    default_model : str
        Model used if the model_list is None or does not have
        enough values for the number of peaks found. Must correspond to
        one of the built-in models in lmfit.models.
    subtract_background : bool
        If True, it will fit the background with the model in background_type.
    bkg_min : int or float
        Minimum x value to use for initially fitting the background.
    bkg_max : int or float
        Maximum x value to use for initially fitting the background.
    min_sigma : int or float
        Minimum value for the sigma for each peak; typically better to not
        set to any value other than 0.
    max_sigma : int or float
        maximum value for the sigma for each peak; typically better to not
        set to any value other than infinity.
    min_method : str
        Minimization method used for fitting.
    x_min : int or float
        Minimum x value used in fitting the data.
    x_max : int or float
        Maximum x value used in fitting the data.
    additional_peaks : list
        Peak centers that are input by the user and automatically accepted
        as peaks.
    model_list : list
        List of strings, with each string corresponding to one of the
        models in lmfit.models.
    background_type : str
        String corresponding to a model in lmfit.models; used to fit the background.
    poly_n : int
        Degree of the polynomial; only used if background_type is set
        to 'PolynomialModel'.
    fit_kws : dict
        Keywords to be passed on to the minimizer.
    vary_Voigt : bool
        If True, will allow the gamma parameter in the Voigt model
        to be varied as an additional variable; if False, gamma will be
        set equal to sigma.
    fit_residuals : bool
        If True, it will attempt to fit the residuals after the
        first fitting to find hidden peaks, add them to the model, and fit
        the data again.
    num_resid_fits : int
        Maximum number of times the program will loop to fit the residuals.
    min_resid : int or float
        used as the prominence when finding peaks in the residuals, in which
        the prominence is set to min_resid * (y_max - y_min).
    debug : bool
        If True, will create plots at various portions of the code showing
        the peak initialization, initial fits and backgrounds, and residuals.
    peak_heights : list
        A list of peak heights.

    Returns
    -------
    output : dict
        A dictionary of lists. For most lists, each entry corresponds to
        the results of a peak fitting. The dictionary has the following
        keys (in this order if unpacked into a list):
            'resid_peaks_found':
                All peak centers found during fitting of the residuals.
                Each list entry corresponds to a separate fitting.
            'resid_peaks_accepted':
                Peak centers found during fitting of the residuals which were
                accepted as true peak centers. Each list entry corresponds
                to a separate fitting.
            'peaks_found':
                All peak centers found during the initial peak fitting
                of the original data.
            'peaks_accepted':
                Peaks centers found during the initial peak fitting of the
                original data which were accepted as true peak centers
            'initial_fits':
                List of initial fits. Each list entry corresponds to a
                separate fitting.
            'fit_results':
                List of lmfit's ModelResult objects, which contain the
                majority of information needed. Each list entry corresponds
                to a separate fitting.
            'individual_peaks':
                Nested list of y-data values for each peak. Each list entry
                corresponds to a separate fitting.
            'best_values:
                Nested list of best fit parameters (such as amplitude,
                fwhm, etc.) for each fitting. Each list entry corresponds
                to a separate fitting.

    Notes
    -----
    Uses several of the functions within this module to directly take (x,y) data
    and do peak fitting. All relevant data is returned from this function, so
    it has quite a dense input and output, but it is well worth it!

    For the minimization method (min_method), the 'least_squares' method gives
    fast performance compared to most other methods while still having good
    convergence. The 'leastsq' is also very good, and seems less succeptible
    to getting caught in local minima compared to 'least_squares', but takes
    longer to evaluate. A best practice could be to use 'least_squares' during
    initial testing and then using 'leastsq' for final calculations.

    Global optimizers do not seem to work on complicated models (or rather I cannot
    get them to work), so using the local optimizers 'least_squares' or
    'leastsq' and adjusting the inputs will have to suffice.

    Most relevant data is contained within output['fit_results'], such
    as the parameters for each peak, as well as all the error associated
    with the fitting.

    Within this function:
        params == parameters for all of the peaks
        bkg_params == parameters for the background
        composite_params == parameters for peaks + background

        model == CompositeModel object for all of the peaks
        background == Model object for the background
        composite_model == CompositeModel object for the peaks + background

    peaks_accepted are not necessarily the peak centers after fitting, just
    the peak centers that were found. These values can be used for
    understanding the peak selection process.

    """

    model_list = model_list if model_list is not None else []
    additional_peaks = additional_peaks if additional_peaks is not None else []

    # Creates the output dictionary and initializes two of its lists
    output = defaultdict(list)
    output['resid_peaks_found']
    output['resid_peaks_accepted']

    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)

    # ensures no nan values in the arrays; ~ equivalent to np.logical_not
    nan_mask = (~np.isnan(x_array)) & (~np.isnan(y_array))
    x_array = x_array[nan_mask]
    y_array = y_array[nan_mask]

    # ensures data limits make sense
    x_min = max(x_min, min(x_array))
    x_max = min(x_max, max(x_array))
    bkg_min = max(bkg_min, x_min)
    bkg_max = min(bkg_max, x_max)

    output['peaks_found'], output['peaks_accepted']  = find_peak_centers(
        x_array, y_array, additional_peaks=additional_peaks, height=height,
        prominence=prominence, x_min=x_min, x_max=x_max
    )

    # The domain mask is applied to x and y after finding peaks so that any user
    # supplied peaks in additional_peaks are put into peaks_found, even if
    # they are not within the domain.
    domain_mask = (x_array >= x_min) & (x_array <= x_max)
    x = x_array[domain_mask]
    y = y_array[domain_mask]

    if debug:
        tot_ax = plt.subplots()[-1]
        tot_ax.plot(x, y, label='data')
        tot_ax.set_title('initial fits and backgrounds')

    if subtract_background:
        bkg_mask = (x >= bkg_min) & (x <= bkg_max)
        bkg_kwargs = {'degree': poly_n} if background_type == 'PolynomialModel' else {}

        background = getattr(lmfit.models, background_type)(prefix='background_', **bkg_kwargs)
        bkg_params = background.guess(y[bkg_mask], x=x[bkg_mask])
        initial_bkg = _check_background(background_type, background.eval(bkg_params, x=x), y)

        params_dict = _initialize_peaks(
            x, y, peak_centers=output['peaks_accepted'], peak_width=peak_width,
            default_model=default_model, center_offset=center_offset,
            vary_Voigt=vary_Voigt, model_list=model_list, min_sigma=min_sigma,
            max_sigma=max_sigma, background_y=initial_bkg,
            debug=debug, peak_heights=peak_heights
        )

        model, params = _generate_composite_model(params_dict)
        fit_wo_bkg = model.eval(params, x=x)
        bkg_params = background.guess(y - fit_wo_bkg, x=x)

        if debug:
            tot_ax.plot(x, initial_bkg, label='initialization background')
            tot_ax.plot(
                x,
                _check_background(background_type, background.eval(bkg_params, x=x), y),
                label='background_1'
            )

        composite_model = model + background
        composite_params = params + bkg_params

    else:
        params_dict = _initialize_peaks(
            x, y, peak_centers=output['peaks_accepted'], peak_width=peak_width,
            default_model=default_model, center_offset=center_offset,
            vary_Voigt=vary_Voigt, model_list=model_list, min_sigma=min_sigma,
            max_sigma=max_sigma, debug=debug, peak_heights=peak_heights
        )

        composite_model, composite_params = _generate_composite_model(params_dict)

    if debug:
        tot_ax.plot(x, composite_model.eval(composite_params, x=x),
                    label='initial_fit_1')

    # Fit for the initialized model
    output['initial_fits'] = [composite_model.eval(composite_params, x=x)]
    # Fit for the best fit model
    output['fit_results'] = [composite_model.fit(y, composite_params, x=x,
                                                 method=min_method, fit_kws=fit_kws)]

    print(f'\nFit #1: {output["fit_results"][-1].nfev} evaluations')

    if fit_residuals:
        for eval_num in range(num_resid_fits):

            last_chisq = output['fit_results'][-1].redchi

            # Updates the current parameters and removes the background from the peaks
            composite_params = output['fit_results'][-1].params.copy()
            for prefix in params_dict:
                for param in params_dict[prefix][1]:
                    params_dict[prefix][1][param] = composite_params[param]

            fwhm = []
            for prefix in params_dict:
                if f'{prefix}fwhm' in params_dict[prefix][1]:
                    fwhm.append(params_dict[prefix][1][f'{prefix}fwhm'].value)
                else:
                    fwhm.append(params_dict[prefix][1][f'{prefix}sigma'].value * 2.5) # estimate
            avg_fwhm = np.mean(fwhm)

            #use peaks_accepted as the peak centers instead of the centers of peaks
            #because peaks will move during fitting to fill void space.
            residual_peaks = _find_hidden_peaks(
                x, output['fit_results'][-1], output['peaks_accepted'],
                fwhm, min_resid, debug
            )
            #Keep them as lists so the peaks found at each iteration is available.
            output['resid_peaks_found'].append([residual_peaks[0]])
            output['resid_peaks_accepted'].append([residual_peaks[1]])
            output['peaks_accepted'] = sorted(output['peaks_accepted'] + residual_peaks[1])

            #background_y=output["fit_results"][-1].best_fit means that new peaks
            #will be fit to the residuals (y-background_y)
            if residual_peaks[1]:
                params_dict = _initialize_peaks(
                    x, y, peak_centers=residual_peaks[1], peak_width=avg_fwhm,
                    default_model=default_model, center_offset=center_offset,
                    vary_Voigt=vary_Voigt, model_list=None, min_sigma=min_sigma,
                    max_sigma=max_sigma, background_y=output['fit_results'][-1].best_fit,
                    params_dict=params_dict, debug=debug
                )

                params_dict = _re_sort_prefixes(params_dict)

            model, params = _generate_composite_model(params_dict)

            if subtract_background:
                fit_wo_bkg = model.eval(params, x=x)
                bkg_params = background.guess(y - fit_wo_bkg, x=x)

                composite_params = params + bkg_params
                composite_model = model + background

                if debug:
                    tot_ax.plot(
                        x,
                        _check_background(background_type, background.eval(bkg_params, x=x), y),
                        label=f'background_{eval_num + 2}'
                    )

            else:
                composite_model = model
                composite_params = params

            if debug:
                tot_ax.plot(x, composite_model.eval(composite_params, x=x),
                            label=f'initial fit_{eval_num + 2}')

            output['initial_fits'].append(composite_model.eval(composite_params, x=x))
            output['fit_results'].append(
                composite_model.fit(y, composite_params, x=x,method=min_method,
                                    fit_kws=fit_kws)
            )

            current_chisq = output['fit_results'][-1].redchi

            if np.abs(last_chisq - current_chisq) < 1e-9 and not residual_peaks[1]:
                print((
                    f'\nFit #{eval_num + 2}: {output["fit_results"][-1].nfev} evaluations'
                    '\nDelta \u03c7\u00B2 < 1e-9 \nCalculation ended'
                ))
                break
            else:
                print((
                    f'\nFit #{eval_num + 2}: {output["fit_results"][-1].nfev} evaluations'
                    f'\nDelta \u03c7\u00B2 = {np.abs(last_chisq - current_chisq):.9f}'
                    ))
            if eval_num + 1 == num_resid_fits:
                print('Number of residual fits exceeded.')

    if debug:
        tot_ax.legend()
        plt.show(block=False)
        plt.pause(0.01)

    for fit_result in output['fit_results']:
        # list of y-values for the inidividual models
        output['individual_peaks'].append(fit_result.eval_components(x=x))
        if subtract_background:
            output['individual_peaks'][-1]['background_'] = _check_background(
                background_type, output['individual_peaks'][-1]['background_'], y
            )

        # gets the parameters for each model and their standard errors, if available
        output['best_values'].append([])
        for param in fit_result.params.values():
            output['best_values'][-1].append(
                [param.name, param.value, param.stderr if param.stderr not in (None, np.nan) else 'N/A']
            )
        # perform numeric calculations for each peak
        for model, values in output['individual_peaks'][-1].items():
            if 'peak' in model:
                numeric_calcs = {
                    'numeric area': f_utils.numerical_area(fit_result.userkws['x'], values),
                    'numeric fwhm': f_utils.numerical_fwhm(fit_result.userkws['x'], values),
                    'numeric extremum': f_utils.numerical_extremum(values),
                    'numeric mode': f_utils.numerical_mode(fit_result.userkws['x'], values)
                }
                for calc, value in numeric_calcs.items():
                    output['best_values'][-1].append(
                        [model + calc, value if value is not None else 'N/A', 'None']
                    )

    return output


class BackgroundSelector(plot_utils.EmbeddedFigure):
    """
    A window for selecting points to define the background of data.

    Parameters
    ----------
    x : array-like
        The x-values to be plotted.
    y : array-like
        The y-values to be plotted.
    click_list : list, optional
        A list of selected points on the plot.

    Attributes
    ----------
    axis_2 : plt.Axes
        The secondary axis on the figure which has no events.

    """

    def __init__(self, x, y, click_list=None):

        super().__init__(x, y, click_list)
        desired_dpi = 150
        dpi = plot_utils.determine_dpi(
            {'fig_width': self.canvas_size[0],'fig_height': self.canvas_size[1],
             'dpi': desired_dpi}, canvas_size=self.canvas_size
        )

        self.figure, (self.axis, self.axis_2) = plt.subplots(
            2, num='Background Selector', sharex=True, tight_layout=True,
            gridspec_kw={'height_ratios': [1.5, 1], 'hspace': 0},
            figsize=np.array(self.canvas_size) / desired_dpi, dpi=dpi
        )

        self.axis.plot(self.x, self.y, 'o-', color='dodgerblue', ms=2, label='raw data')
        self.axis_2.plot(self.x, self.y, 'ro-', ms=2, label='subtracted data')

        self.xaxis_limits = self.axis.get_xlim()
        self.yaxis_limits = self.axis.get_ylim()

        # set limits so axis bounds do not change
        self.axis.set_xlim(self.xaxis_limits)
        self.axis.set_ylim(self.yaxis_limits)

        self.axis.legend()
        self.axis_2.legend()
        self.axis.tick_params(labelbottom=False, bottom=False, which='both')

        self._create_window()
        self._place_figure_on_canvas()

        # update plot after placing on canvas because figure.canvas.draw_idle will
        # cause a threading issue otherwise
        if self.click_list:
            self._update_plot()
            for point in self.click_list:
                self._create_circle(point[0], point[1])


    def _create_window(self):
        """Creates the GUI."""

        self.toolbar_canvas = sg.Canvas(key='controls_canvas', pad=(0, (0, 20)),
                                        size=(self.canvas_size[0], 10))
        self.canvas = sg.Canvas(key='fig_canvas', size=self.canvas_size, pad=(0, 0))

        layout = [
            [sg.Column([
                [sg.Text(('Create point: double left click.  Select point: single click.\n'
                        'Delete selected point: double right click or delete key.'),
                        justification='center')],
                [self.canvas]], element_justification='center', pad=(0, 0))],
            [self.toolbar_canvas],
            [sg.Button('Finish', key='close', button_color=utils.PROCEED_COLOR),
             sg.Button('Clear Points', key='clear')]
        ]

        self.window = sg.Window('Background Selector', layout, finalize=True, alpha_channel=0)


    def event_loop(self):
        """
        Handles the event loop for the GUI.

        Returns
        -------
        list(list(float, float))
            A list of the (x, y) values for the selected points on the figure.

        """

        self.window.reappear()

        while True:
            event = self.window.read()[0]
            if event in ('close', sg.WIN_CLOSED):
                break
            elif event == 'clear':
                for patch in self.axis.patches.copy():
                    self.picked_object = patch
                    self._remove_circle()
                self._update_plot()

        self._close()

        return self.click_list


    def _update_plot(self):
        """Updates the plot after events on the matplotlib figure."""

        for line in self.axis.lines[1:] + self.axis_2.lines:
            line.remove()

        y_subtracted = self.y.copy()
        if len(self.click_list) > 1:
            points = sorted(self.click_list, key=lambda cl: cl[0])

            for i in range(len(points) - 1):
                x_points, y_points = zip(*points[i:i + 2])
                self.axis.plot(x_points, y_points, color='k', ls='--', lw=2)
                boundary = (self.x >= x_points[0]) & (self.x <= x_points[1])

                y_line = self.y[boundary]
                y_subtracted[boundary] = y_line - np.linspace(*y_points, y_line.size)

            self.axis.plot(0, 0, 'k--', lw=2, label='background')

        self.axis_2.plot(self.x, y_subtracted, 'ro-', ms=2, label='subtracted data')
        self.axis.legend()
        self.axis_2.legend()
        self.figure.canvas.draw_idle()


    def _remove_circle(self):
        """Removes the selected circle from the axis."""

        coords = self.picked_object.get_center()
        for i, value in enumerate(self.click_list):
            if all(np.isclose(value, coords)):
                del self.click_list[i]
                break

        self.picked_object.remove()
        self.picked_object = None


    def _on_click(self, event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        1) If the button press is not within the self.axis, then nothing is done.
        2) If a double left click is done, then a circle is placed on self.axis.
        3) If a double right click is done and a circle is selected, then the circle
           is deleted from the self.axis.
        4) If a single left or right click is done, it deselects any selected circle
           if the click is not on the circle.

        """

        if event.inaxes == self.axis:
            if event.dblclick: # a double click
                # left click
                if event.button == 1:
                    self.click_list.append([event.xdata, event.ydata])
                    self._create_circle(event.xdata, event.ydata)
                    self._update_plot()

                # right click
                elif event.button == 3 and self.picked_object is not None:
                    self._remove_circle()
                    self._update_plot()

            # left or right single click
            elif (event.button in (1, 3) and self.picked_object is not None
                    and not self.picked_object.contains(event)[0]):
                self.picked_object.set_facecolor('green')
                self.picked_object = None
                self.figure.canvas.draw_idle()


class PeakSelector(plot_utils.EmbeddedFigure):
    """
    A window for selecting peaks on a plot, along with peak width and type.

    Parameters
    ----------
    x : array-like
        The x-values to be plotted and fitted.
    y : array-like
        The y-values to be plotted and fitted.
    click_list : list, optional
        A nested list, with each entry corresponding to a peak. Each entry
        has the following layout:
        [[lmfit model, sigma function, aplitude function], [peak center, peak height, peak width]]
        where lmfit model is something like 'GaussianModel'. The first entry
        in the list comes directly from the mcetl.peak_fitting.peak_transformer function.
    initial_peak_width : int or float
        The initial peak width input in the plot.
    subtract_background : bool
        If True, will subtract the background before showing the plot.
    background_type : str
        String corresponding to a model in lmfit.models; used to fit
        the background.
    poly_n : int
        Degree of the polynomial; only used if background_type is
        set to 'PolynomialModel'.
    bkg_min : float or int
        Minimum x value to use for initially fitting the background.
    bkg_max : float or int
        Maximum x value to use for initially fitting the background.
    default_model : str
        The initial model to have selected on the plot, corresponds to
        a model in lmfit.models.

    Attributes
    ----------
    background : array-like
        The y-values for the background function.

    """

    def __init__(self, x, y, click_list=None, initial_peak_width=1,
                 subtract_background=False, background_type='PolynomialModel',
                 poly_n=4, bkg_min=-np.inf, bkg_max=np.inf, default_model=None):

        super().__init__(x, y, click_list)
        nan_mask = (~np.isnan(self.x)) & (~np.isnan(self.y))
        self.x = self.x[nan_mask]
        self.y = self.y[nan_mask]

        # reduce canvas size a little since the gui has buttons under the figure
        self.canvas_size = (self.canvas_size[0] - 50, self.canvas_size[1] - 50)
        desired_dpi = 150
        dpi = plot_utils.determine_dpi(
            {'fig_width': self.canvas_size[0],'fig_height': self.canvas_size[1],
             'dpi': desired_dpi}, canvas_size=self.canvas_size
        )

        self.figure, self.axis = plt.subplots(
            num='Peak Selector', tight_layout=True,
            figsize=np.array(self.canvas_size) / desired_dpi, dpi=dpi
        )

        self.axis.plot(self.x, self.y, 'o-', color='dodgerblue',
                       ms=2, label='raw data')

        if not subtract_background:
            self.background = np.zeros(x.size)
        else:
            bkg_mask = (self.x > bkg_min) & (self.x < bkg_max)
            bkg_kwargs = {'degree': poly_n} if background_type == 'PolynomialModel' else {}

            bkg_model = getattr(lmfit.models, background_type)(prefix='background_', **bkg_kwargs)
            bkg_params = bkg_model.guess(self.y[bkg_mask], x=self.x[bkg_mask])
            self.background = _check_background(background_type, bkg_model.eval(bkg_params, x=x), y)

        self.axis.plot(self.x, self.background, 'r--', lw=2, label='background')
        self.xaxis_limits = self.axis.get_xlim()
        self.yaxis_limits = self.axis.get_ylim()

        # set limits so axis bounds do not change
        self.axis.set_xlim(self.xaxis_limits)
        self.axis.set_ylim(self.yaxis_limits)

        self.axis.legend()

        self._create_window(initial_peak_width, default_model)
        self._place_figure_on_canvas()

        if self.click_list:
            self._update_plot()
            for peak in self.click_list:
                center = peak[3]
                height = peak[1] + self.background[np.argmin(np.abs(center - self.x))]
                self._create_circle(center, height)


    def _create_window(self, peak_width, peak_model):
        """Creates the GUI."""

        self.toolbar_canvas = sg.Canvas(key='controls_canvas', pad=(0, (0, 10)),
                                        size=(self.canvas_size[0], 10))
        self.canvas = sg.Canvas(key='fig_canvas', size=self.canvas_size, pad=(0, 0))

        models_dict = peak_transformer()
        display_models = [f_utils.get_gui_name(model) for model in models_dict.keys()]
        if f_utils.get_gui_name(peak_model) in display_models:
            initial_model = f_utils.get_gui_name(peak_model)
        else:
            initial_model = display_models[0]

        layout = [
            [sg.Column([
                [sg.Text(('Create point: double left click.  Select point: single click.\n'
                         'Delete selected point: double right click.'),
                         justification='center')],
                [self.canvas]], element_justification='center', pad=(0, 0))],
            [self.toolbar_canvas],
            [sg.Text('Peak model:'),
             sg.Combo(display_models, key='peak_model', readonly=True,
                      default_value=initial_model),
             sg.Text('    Peak FWHM:'),
             sg.Input(peak_width, key='peak_width', size=(10, 1))],
            [sg.Button('Finish', key='close', button_color=utils.PROCEED_COLOR,
                       bind_return_key=True, pad=(5, (15, 0))),
             sg.Button('Clear Points', key='clear', pad=(5, (15, 0)))]
        ]

        self.window = sg.Window('Peak Selector', layout, finalize=True, alpha_channel=0)


    def event_loop(self):
        """
        Handles the event loop for the GUI.

        Returns
        -------
        list
            A nested list, with each entry corresponding to a peak. Each entry
            has the following layout:
            [model, peak center, peak height, peak width]
            where model is something like 'Gaussian'. The first entry
            in the list comes directly from the mcetl.peak_fitting.peak_transformer function.

        """

        self.window.reappear()
        while True:
            event = self.window.read()[0]
            if event in ('close', sg.WIN_CLOSED):
                break
            elif event == 'clear':
                for patch in self.axis.patches.copy():
                    self.picked_object = patch
                    self._remove_circle()
                self._update_plot()

        self._close()

        return self.click_list


    def _update_plot(self):
        """Updates the plot after events on the matplotlib figure."""

        for line in self.axis.lines[2:]:
            line.remove()

        if self.click_list:
            # resets the color cycle to start at 0
            self.axis.set_prop_cycle(plt.rcParams['axes.prop_cycle'])

            models_dict = peak_transformer()
            y_tot = 0 * self.x
            for i, peak in enumerate(sorted(self.click_list, key=lambda cl: cl[3])):
                height = peak[1]
                width = peak[2]
                center = peak[3]
                peak_model = f_utils.get_model_object(peak[0])(prefix=f'peak_{i + 1}')
                peak_params = peak_model.make_params()
                for param, equation in models_dict[peak[0]].items():
                    peak_params[f'peak_{i + 1}{param}'].set(value=equation(height, width, center))

                peak = peak_model.eval(peak_params, x=self.x)
                self.axis.plot(self.x, peak + self.background, ':',
                               lw=2, label=f'peak {i + 1}')
                y_tot += peak

            self.axis.plot(self.x, y_tot + self.background, color='k', ls='--',
                           lw=2, label='total')

        self.axis.legend()
        self.figure.canvas.draw_idle()


    def _remove_circle(self):
        """Removes the selected circle from the axis."""

        center, height = self.picked_object.get_center()
        bkrd_height = self.background[np.argmin(np.abs(center - self.x))]
        for i, value in enumerate(self.click_list):
            if all(np.isclose([value[3], value[1]], [center, height - bkrd_height])):
                del self.click_list[i]
                break

        self.picked_object.remove()
        self.picked_object = None


    def _on_click(self, event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        1) If the button press is not within the self.axis, then nothing is done.
        2) If a double left click is done, then a circle is placed on self.axis.
        3) If a double right click is done and a circle is selected, then the circle
           is deleted from the self.axis.
        4) If a single left or right click is done, it deselects any selected circle
           if the click is not on the circle.

        """

        if event.inaxes == self.axis:
            if event.dblclick: # a double click
                if event.button == 1: # left click
                    try:
                        peak_width = float(self.window['peak_width'].get())
                        if peak_width <= 0:
                            raise ValueError
                    except ValueError:
                        self.window['peak_width'].update('')
                    else:
                        selected_model = f_utils.get_model_name(self.window['peak_model'].get())

                        #[lmfit model, peak height, peak width, peak center]
                        peak_center = event.xdata
                        peak_height = event.ydata - self.background[np.argmin(np.abs(peak_center - self.x))]
                        self.click_list.append([selected_model, peak_height, peak_width, peak_center])

                        self._create_circle(event.xdata, event.ydata)
                        self._update_plot()

                # right click
                elif event.button == 3 and self.picked_object is not None:
                    self._remove_circle()
                    self._update_plot()

            # left or right single click
            elif (event.button in (1, 3) and self.picked_object is not None
                    and not self.picked_object.contains(event)[0]):
                self.picked_object.set_facecolor('green')
                self.picked_object = None
                self.figure.canvas.draw_idle()


def plot_confidence_intervals(fit_result, n_sig=3, return_figure=False):
    """
    Plot the data, the fit, and the fit +- n_sig * sigma confidence intervals.

    Parameters
    ----------
    fit_result : lmfit.ModelResult
        The ModelResult object for the fitting.
    n_sig : float, optional
        The multiple of the standard error to use as the plotted error.
        The default is 3.
    return_figure : bool, optional
        If True, will return the created figure; otherwise, it will display
        the figure using plt.show(block=False) (default).

    Returns
    -------
    plt.Figure or None
        If return_figure is True, the figure is returned; otherwise, None
        is returned.

    Notes
    -----
    This function assumes that the independant variable in the fit_result
    was labeled 'x', as is standard for all built-in lmfit models.

    """

    x = fit_result.userkws['x']
    y = fit_result.data
    del_y = fit_result.eval_uncertainty(sigma=n_sig)

    figure = plt.figure()
    plt.fill_between(
        x, fit_result.best_fit - del_y, fit_result.best_fit + del_y,
        color='darkgrey', label=fr'best fit $\pm$ {n_sig}$\sigma$'
    )
    plt.plot(x, y, 'o', ms=1.5, color='dodgerblue', label='data')
    plt.plot(x, fit_result.best_fit, 'k-', lw=1.5, label='best fit')
    plt.legend()

    if return_figure:
        return figure
    else:
        plt.show(block=False)


def plot_peaks_for_model(x, y, x_min, x_max, peaks_found, peaks_accepted,
                         additional_peaks):
    """
    Plot the peaks found or added, as well as the ones found but rejected from the fitting.

    Parameters
    ----------
    x : array-like
        x data used in the fitting.
    y : array-like
        y data used in the fitting.
    x_min : float or int
        Minimum x values used for the fitting procedure.
    x_max : float or int
        Maximum x values used for the fitting procedure.
    peaks_found : list
        A list of x values corresponding to all peaks found throughout
        the peak fitting and peak finding process, as well as those
        input by the user.
    peaks_accepted : list
        A list of x values corresponding to peaks found throughout
        the peak fitting and peak finding process that were accepted
        into the model.
    additional_peaks : list
        A list of peak centers that were input by the user.

    """

    ax = plt.subplots()[-1]
    legend = ['Rejected Peaks', 'Found Peaks', 'User Peaks']
    colors = ['r', 'g', 'purple']
    ax.plot(x, y, 'b-', ms=2)
    for peak in peaks_found:
        ax.axvline(peak, 0, 0.9, c='red', linestyle='--')
    for peak in peaks_accepted:
        ax.axvline(peak, 0, 0.9, c='green', linestyle='--')
    for peak in np.array(additional_peaks)[(np.array(additional_peaks)>x_min)
                                           & (np.array(additional_peaks)<x_max)]:
        ax.axvline(peak, 0, 0.9, c='purple', linestyle='--')
    for i in range(3):
        plt.text(0.1 + 0.35 * i, 0.95, legend[i], ha='left', va='center',
                 transform=ax.transAxes)
        plt.hlines(0.95, 0.02 + 0.35 * i, 0.08 + 0.35 * i, color=colors[i],
                   linestyle='--', transform=ax.transAxes)
    ax.set_ylim(plot_utils.scale_axis(ax.get_ylim(), None, 0.1))
    plt.show(block=False)


def plot_fit_results(fit_result, label_rsq=False, plot_initial=False, return_figure=False):
    """
    Plot the raw data, best fit, and residuals.

    Parameters
    ----------
    fit_result : lmfit.ModelResult or list(lmfit.ModelResult)
        A ModelResult object from lmfit; can be a list of ModelResults,
        in which case, the initial fit will use fit_result[0], and the
        best fit will use fit_result[-1].
    label_rsq : bool, optional
        If True, will put a label with the adjusted r squared value of the fitting.
    plot_initial : bool, optional
        If True, will plot the initial fitting as well as the best fit.
    return_figure : bool, optional
        If True, will return the created figure; otherwise, it will display
        the figure using plt.show(block=False) (default).

    Returns
    -------
    plt.Figure or None
        If return_figure is True, the figure is returned; otherwise, None
        is returned.

    Notes
    -----
    This function assumes that the independant variable in the fit_result
    was labeled 'x', as is standard for all built-in lmfit models.

    """

    if not isinstance(fit_result, (list, tuple)):
        fit_result = [fit_result]

    x = fit_result[-1].userkws['x']
    y = fit_result[-1].data

    figure, (ax_resid, ax_main) = plt.subplots(
        2, sharex=True, gridspec_kw={'height_ratios':[1, 5], 'hspace': 0}
    )
    ax_main.plot(x, y, 'o', color='dodgerblue', ms=1.5, label='data')
    if plot_initial:
        ax_main.plot(x, fit_result[0].init_fit, 'r--', label='initial fit')
    ax_main.plot(x, fit_result[-1].best_fit, 'k-', label='best fit')
    # don't plot fit_result.residual because it equals inf when there is a bad fit
    ax_resid.plot(x, y - fit_result[-1].best_fit, 'o', color='green',
                  ms=1, label='residuals')
    ax_resid.axhline(0, color='k', linestyle='-')

    ax_main.set_ylim(plot_utils.scale_axis(ax_main.get_ylim(), 0.05, 0.05))
    ax_resid.set_ylim(plot_utils.scale_axis(ax_resid.get_ylim(), 0.05, 0.05))
    ax_main.legend()
    ax_main.set_ylabel('y')

    if label_rsq:
        ax_main.text(
            plot_utils.scale_axis(ax_main.get_xlim(), -0.05, None)[0],
            plot_utils.scale_axis(ax_main.get_ylim(), None, -0.05)[1],
            f'R$^2$= {f_utils.r_squared(y, fit_result[-1].best_fit, fit_result[-1].nvarys)[1]:.3f}',
            ha='left', va='top'
        )
    ax_resid.tick_params(labelbottom=False, bottom=False, which='both')
    ax_main.label_outer()
    ax_main.set_xlabel('x')
    ax_resid.set_ylabel('$y_{data}-y_{fit}$')
    ax_resid.label_outer()

    if return_figure:
        return figure
    else:
        plt.show(block=False)


def plot_individual_peaks(fit_result, individual_peaks, background_subtracted=False,
                          plot_subtract_background=False, plot_separate_background=False,
                          plot_w_background=False, return_figures=False):
    """
    Plots each individual peak in the composite model and the total model.

    Parameters
    ----------
    fit_result : lmfit.ModelResult
        The ModelResult object from the fitting.
    individual_peaks : dict
        A dictionary with keys corresponding to the model prefixes
        in the fitting, and their values corresponding to their y values.
    background_subtracted : bool
        Whether or not the background was subtracted in the fitting.
    plot_subtract_background : bool
        If True, subtracts the background from the raw data as well as all the
        peaks, so everything is nearly flat.
    plot_separate_background : bool
        If True, subtracts the background from just the individual
        peaks, while also showing the raw data with the composite model
        and background.
    plot_w_background : bool
        If True, has the background added to all peaks, i.e. it shows
        exactly how the composite model fits the raw data.
    return_figures : bool, optional
        If True, will return the created figures; otherwise, it will display
        the figures using plt.show(block=False) (default).

    Returns
    -------
    list(plt.Figure) or None
        If return_figures is True, the list of created figures is returned.
        Otherwise, None is returned.

    Notes
    -----
    This function assumes that the independant variable in the fit_result
    was labeled 'x', as is standard for all built-in lmfit models.

    """

    x = fit_result.userkws['x']
    y = fit_result.data

    # Creates a color cycle to override matplotlib's to prevent color clashing
    COLORS = ['#ff7f0e', '#2ca02c', '#d62728', '#8c564b','#e377c2',
              '#bcbd22', '#17becf']
    n_col = max(1, len(individual_peaks) // 5)

    figures = []
    if background_subtracted:
        if plot_subtract_background:
            fig, ax = plt.subplots()
            color_cycle = itertools.cycle(COLORS)
            ax.plot(x, y - individual_peaks['background_'], 'o',
                    color='dodgerblue', label='data', ms=2)
            i = 1
            for peak in individual_peaks:
                if peak != 'background_':
                    ax.plot(x, individual_peaks[peak], label=f'peak {i}',
                            color=next(color_cycle))
                    i += 1
            ax.plot(x, fit_result.best_fit - individual_peaks['background_'],
                    'k--', lw=1.5, label='best fit')
            ax.legend(ncol=n_col)
            figures.append(fig)

        if plot_w_background:
            fig, ax = plt.subplots()
            color_cycle = itertools.cycle(COLORS)
            ax.plot(x, y, 'o', color='dodgerblue', label='data', ms=2)
            i = 1
            for peak in individual_peaks:
                if peak != 'background_':
                    ax.plot(x, individual_peaks[peak] + individual_peaks['background_'],
                            label=f'peak {i}', color=next(color_cycle))
                    i += 1
            ax.plot(x, individual_peaks['background_'], 'k', label='background')
            ax.plot(x, fit_result.best_fit, 'k--', lw=1.5, label='best fit')
            ax.legend(ncol=n_col)
            figures.append(fig)

        if plot_separate_background:
            fig, ax = plt.subplots()
            color_cycle = itertools.cycle(COLORS)
            ax.plot(x, y, 'o', color='dodgerblue', label='data', ms=2)
            i = 1
            for peak in individual_peaks:
                if peak != 'background_':
                    ax.plot(x, individual_peaks[peak], label=f'peak {i}',
                            color=next(color_cycle))
                    i += 1
            ax.plot(x, individual_peaks['background_'], 'k', label='background')
            ax.plot(x, fit_result.best_fit, 'k--', lw=1.5, label='best fit')
            ax.legend(ncol=n_col)
            figures.append(fig)

    else:
        fig, ax = plt.subplots()
        color_cycle = itertools.cycle(COLORS)
        ax.plot(x, y, 'o', color='dodgerblue', label='data', ms=2)
        i = 1
        for peak in individual_peaks:
            if peak != 'background_':
                ax.plot(x, individual_peaks[peak], label=f'peak {i}',
                        color=next(color_cycle))
                i += 1
        ax.plot(x, fit_result.best_fit, 'k--', lw=1.5, label='best fit')
        ax.legend(ncol=n_col)
        figures.append(fig)

    if return_figures:
        return figures
    else:
        plt.show(block=False)
