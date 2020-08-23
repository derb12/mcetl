# -*- coding: utf-8 -*-
"""Functions for creating and fitting a model with peaks and a background and plotting the results

@author: Donald Erb
Created on Sat Sep 14 16:07:15 2019

"""


import itertools
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from lmfit import models, Parameters
from matplotlib.widgets import TextBox, RadioButtons
from matplotlib.patches import Ellipse


def peak_transformer():
    """
    Provides the expressions needed to convert peak width and height to sigma and amplitude.

    Returns
    -------
    models_dict : dict
        A dictionary containing the string for lmfit models as keys, and
        a list as the values. The first item in the value list is the lmfit
        model name without 'Model' to be used in GUIs. The second item in the
        value list is a list containing the equations to estimate sigma and
        amplitude, respecitively, using input heights and
        full-width-at-half-maximums.

    Notes
    -----
    The equations for approximating the amplitude and sigma were gotten from:
    http://openafox.com/science/peak-function-derivations.html

    Lognormal does not have equations for sigma and amplitude because the equations
    rely on different parameters, so the calculations are done during peak
    initialization.

    """

    #more peak models may work, but these are the ones I have tested
    model_list = ['GaussianModel', 'LorentzianModel', 'VoigtModel',
                  'PseudoVoigtModel', 'Pearson7Model', 'MoffatModel',
                  'SkewedGaussianModel', 'SkewedVoigtModel',
                  'SplitLorentzianModel', 'LognormalModel']

    models_dict = {model: [model.split('Model')[0]] for model in model_list}

    #lambda expressions for sigma and amplitude, respectively, with inputs of height(h) and fwhm(w)
    models_dict['GaussianModel'].append([lambda h, w: w/(2*np.sqrt(2*np.log(2))),
                                         lambda h, w: (h * w * np.sqrt(np.pi/(np.log(2)))) / 2])
    models_dict['LorentzianModel'].append([lambda h, w: w / 2,
                                           lambda h, w: (h * w * np.pi) / 2])
    models_dict['VoigtModel'].append([lambda h, w: w / 3.6013,
                                      lambda h, w: (h * w  * 0.531 * np.sqrt(2 * np.pi))])
    models_dict['PseudoVoigtModel'].append([lambda h, w: w / 2,
                                            lambda h, w: h * w * 1.269])
    models_dict['Pearson7Model'].append([lambda h, w: w / (2 * np.sqrt((2**(1/1.5))-1)),
                                         lambda h, w: 2 * h * w / (2 * np.sqrt((2**(1/1.5))-1))])
    models_dict['MoffatModel'].append([lambda h, w: w / 2,
                                       lambda h, w: h])
    models_dict['SkewedGaussianModel'].append([lambda h, w: w/(2*np.sqrt(2*np.log(2))),
                                               lambda h, w: (h * w * np.sqrt(np.pi/(np.log(2)))) / 2])
    models_dict['SkewedVoigtModel'].append([lambda h, w: w / 3.6013,
                                            lambda h, w: (h * w  * 0.531 * np.sqrt(2 * np.pi))])
    models_dict['SplitLorentzianModel'].append([lambda h, w: w / 2,
                                                lambda h, w: (h * w * np.pi) / 2])
    models_dict['LognormalModel'].append([]) #no simple equations for lognormal

    return models_dict


def initialize_peaks(x, y, peak_centers, peak_width=1.0, center_offset=1.0,
                     vary_Voigt=False, model_list=None, default_model='PseudoVoigtModel',
                     min_sigma=0.0, max_sigma=np.inf, background_y=0.0,
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
            params_dict = {'peak_0_' : ['GaussianModel',
                                        Parameters([('peak_0_center',
                                                     <Parameter 'peak_0_center',
                                                     value=1.0,
                                                     bounds=[0.0:2.0]>),
                                                      ('peak_0_sigma',
                                                       <Parameter 'peak_0_sigma',
                                                       value=1.0,
                                                       bounds=[-inf:inf]>)
                                                      ])
                                                      ]
                            'peak_1_' : ['LorentzianModel',
                                         Parameters(etc.)
                                         ]
                            }

    Notes
    -----
    If params_dict is not None, it means residual data is being fit.
    The residuals are interpolated just a little to smooth the data to
    improve the signal to noise ratio for the initial fits, which only really matters
    when fitting peaks that are small. Any value in the residuals that is < 0 is s
    et to 0 to not influence the peak fitting.

    The residual values are shifted up by (0 - min_y) to slightly
    overestimate the peak height. In the case of polynomial backgrounds,
    this helps to avoid getting stuck in a local minimum in which the
    peak height is underestimated and the background is overestimated.

    Lognormal models are directly estimated by assuming the input peak center
    is the mode of the peak, since lmfit's guess is not accurate for lognormal
    peaks.

    """

    model_list = model_list if model_list is not None else []
    peak_list = iter(model_list + [default_model]*(len(peak_centers)-len(model_list)))
    peak_widths = peak_width if isinstance(peak_width, (list, tuple)) else [peak_width]*len(peak_centers)

    y = y - background_y

    if params_dict is not None:
        window = int(len(x) / 20) if int(len(x) / 20) % 2 == 1 else int(len(x) / 20) + 1
        y2 = signal.savgol_filter(y, window, 2, deriv=0)
        y2[y2 < 0] = 0
        y = y2 + (0-np.min(y))
        use_middles = False
        j = len(params_dict)

    else:
        params_dict = {}
        j = 0
        use_middles = True

    #finds the position between peaks
    minx, maxx = [np.min(x), np.max(x)]
    middles = [0.0 for num in range(len(peak_centers) + 1)]
    middles[0], middles[-1] = minx, maxx
    for i in range(len(peak_centers) - 1):
        middles[i + 1] = np.mean([peak_centers[i], peak_centers[i + 1]])

    if debug:
        fig1, ax1 = plt.subplots()
        fig2, ax2 = plt.subplots()
        ax1.plot(x, y)
        ax2.plot(x, y, label='data')

    models_dict = peak_transformer()
    for i, peak_center in enumerate(peak_centers):
        prefix = f'peak_{i+j}_'
        peak_width = peak_widths[i]
        peak_type = next(peak_list)

        if peak_type in models_dict.keys():
            peak_model = getattr(models, peak_type)(prefix=prefix)

            if use_middles:
                peak_mask = (x>=middles[i]) & (x<=middles[i + 1])
            else:
                peak_mask = (x>peak_center-(peak_width/2)) & (x<peak_center+(peak_width/2))

            x_peak = x[peak_mask]
            y_peak = y[peak_mask]

            if peak_heights is None:
                peak_height = y_peak[np.argmin(np.abs(peak_center-x_peak))] / 2
            else:
                peak_height = peak_heights[i]
            negative_peak = peak_height < 0

            if negative_peak:
                min_area = -np.inf
                max_area = 0
            else:
                min_area = 0
                max_area = np.inf

            if peak_type != 'LognormalModel':

                peak_model.set_param_hint('center', value=peak_center,
                                          min=peak_center-center_offset,
                                          max=peak_center+center_offset)
                peak_model.set_param_hint('amplitude', min=min_area, max=max_area)
                peak_model.set_param_hint('sigma', min=min_sigma, max=max_sigma)

                if (peak_type == 'VoigtModel') and (vary_Voigt):
                    peak_model.set_param_hint('gamma', min=min_sigma, max=max_sigma,
                                              vary=True, expr='')

                default_params = peak_model.guess(y_peak, x_peak, negative=negative_peak)
                peak_params = peak_model.make_params(**default_params)

            else:
                #directly estimates the parameters for lognormal model
                #since lmfit's guess is not accurate for lognormal
                xm2 = peak_center**2 #xm2 denotes x_mode squared
                sigma = 0.85 * np.log((peak_width + peak_center* np.sqrt((4*xm2 + peak_width**2)/(xm2))) / (2 * peak_center))
                mean = np.log(peak_center) + sigma**2
                amplitude = (peak_height * sigma * np.sqrt(2*np.pi)) / (np.exp(((sigma**2)/2) - mean))

                #cannot easily set bounds for center for lognormal since it depends on sigma
                peak_model.set_param_hint('center', value=mean)
                peak_model.set_param_hint('sigma', value=sigma)
                peak_model.set_param_hint('amplitude', value=amplitude,
                                          min=min_area, max=max_area)
                peak_params = peak_model.make_params()

        else:
            raise NotImplementedError(f'"{peak_model}" is not implemented in the'\
                                      'peak_transformer function.')

        if debug:
            ax1.plot(x_peak, peak_model.eval(peak_params, x=x_peak))

        lone_peak = False if peak_type != 'LognormalModel' else True

        # peak_width < middles checks whether the peak is isolated or near other peaks
        if (peak_heights is None) and (peak_width < (middles[i+1] - middles[i])):

            temp_fit = peak_model.fit(y_peak, peak_params, x=x_peak,
                                      method='least_squares')

            if debug:
                ax2.plot(x_peak, peak_model.eval(temp_fit.params, x=x_peak),
                         label=f'{prefix}fit')

            if f'{prefix}fwhm' in peak_params:
                fwhm = temp_fit.values[f'{prefix}fwhm']
            else:
                fwhm = temp_fit.values[f'{prefix}sigma'] * 2.5 #estimate

            #only uses the parameters after fitting if  fwhm < 2*peak_width
            #used to prevent hidden peaks from flattening before the total fitting
            if fwhm < (2 * peak_width):
                peak_params = temp_fit.params
                if peak_type != 'LognormalModel':
                    #do not allow peak centers to shift during initialization
                    peak_params[f'{prefix}center'].value = peak_center
                    lone_peak = True
                else:
                    peak_params[f'{prefix}center'].value = mean

        if not lone_peak:
            sigma_eq = models_dict[peak_type][1][0]
            amplitude_eq = models_dict[peak_type][1][1]

            peak_params[f'{prefix}sigma'].value = sigma_eq(peak_height, peak_width)
            peak_params[f'{prefix}amplitude'].value = amplitude_eq(peak_height, peak_width)
            if peak_type == 'SplitLorentzianModel':
                peak_params[f'{prefix}sigma_r'].value = sigma_eq(peak_height, peak_width)

        if debug:
            ax2.plot(x_peak, peak_model.eval(peak_params, x=x_peak), label=f'{prefix}model')

        params_dict[prefix] = [peak_type, peak_params]

    if debug:
        ax1.set_title('peak initialization: initial')
        ax2.set_title('peak initialization: best fit')
        ax2.legend(ncol=max(1, len(peak_centers) // 4))

    return params_dict


def generate_lmfit_model(params_dict):
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

    """

    params = None
    composite_model = None
    for prefix in params_dict:

        peak_type = params_dict[prefix][0]
        peak_model = getattr(models, peak_type)(prefix=prefix)
        for param in params_dict[prefix][1]:
            hint_dict = {'value' : params_dict[prefix][1][param].value,
                         'min' : params_dict[prefix][1][param].min,
                         'max' : params_dict[prefix][1][param].max,
                         'vary' : params_dict[prefix][1][param].vary,
                         'expr' : params_dict[prefix][1][param].expr
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
        additional_peaks = additional_peaks[(additional_peaks>np.min(x)) &
                                            (additional_peaks<np.max(x))]

    peaks_located = signal.find_peaks(y, height=height, prominence=prominence)[0]

    peaks = [*peaks_located, *additional_peaks]
    peaks_found = []
    peaks_accepted = []
    peak_centers = []

    for peak in peaks:
        if peak in peaks_located:
            peak_centers.append(x[peak])
        else:
            peak_centers.append(peak)

    for x_peak in np.sort(peak_centers):
        if (x_peak > x_min) and (x_peak < x_max):
            peaks_accepted.append(x_peak)
        peaks_found.append(x_peak)

    peaks_found = sorted(peaks_found)
    peaks_accepted = sorted(peaks_accepted)

    return peaks_found, peaks_accepted


def find_hidden_peaks(x, fit_result, peak_centers, peak_fwhms,
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
    #window has to be odd for scipy's Savitzky-Golay function
    window = int(len(x)/20) if int(len(x)/20)%2==1 else int(len(x)/20)+1
    poly = 2
    #interpolate residuals to smooth them a bit and improve signal to noise ratio
    resid_interp = signal.savgol_filter(residuals, window, poly, deriv=0)

    resid_interp[resid_interp < 0] = 0
    prominence = min_resid*(np.max(y)-np.min(y))

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

        if (peak_x > left_center + (left_fwhm/2)) and (peak_x < right_center - (right_fwhm/2)):
            residual_peaks_accepted.append(peak_x)

    if debug:
        fig, ax = plt.subplots()
        ax.plot(x,residuals, label='residuals')
        ax.plot(x, resid_interp, label='interpolated residuals')
        ax.plot(x, np.array([prominence]*len(x)),
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
                plt.text(0.1+0.35*i, 0.96, legend[i], ha='left', va='center',
                         transform=ax.transAxes)
                plt.hlines(0.96, 0.02+0.35*i, 0.08+0.35*i, color=colors[i],
                           linestyle=styles[i], transform=ax.transAxes)

        ax.legend()
        fig.title('residuals')

    return residual_peaks_found, residual_peaks_accepted


def re_sort_prefixes(params_dict):
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
    for index, old_prefix in enumerate(sorted_prefixes):
        new_prefix = f'peak_{index}_'
        new_params = Parameters()

        for param in params_dict[old_prefix][1]:
            name = params_dict[old_prefix][1][param].name.replace(old_prefix, new_prefix)
            value = params_dict[old_prefix][1][param].value
            min = params_dict[old_prefix][1][param].min
            max = params_dict[old_prefix][1][param].max
            vary = params_dict[old_prefix][1][param].vary
            if params_dict[old_prefix][1][param].expr is not None:
                params_dict[old_prefix][1][param].expr = params_dict[old_prefix][1][param].expr.replace(old_prefix, new_prefix)
            expr = params_dict[old_prefix][1][param].expr

            new_params.add(name=name, value=value, vary=vary, min=min, max=max,
                           expr=expr)

        new_params_dict[new_prefix] = [params_dict[old_prefix][0], new_params]

    return new_params_dict


def plugNchug_fit(x, y, height=None, prominence=np.inf, center_offset=1.0,
                  peak_width=1.0, default_model='PseudoVoigtModel', subtract_background=False,
                  bkg_min=-np.inf, bkg_max=np.inf, min_sigma=0.0, max_sigma=np.inf,
                  min_method='least_squares', x_min=-np.inf, x_max=np.inf,
                  additional_peaks=None, model_list=None, background_type='PolynomialModel',
                  poly_n=4, fit_kws=None, vary_Voigt=False, fit_residuals=False,
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
        bkrd_params == parameters for the background
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

    #Creates the output dictionary and initializes two of its lists
    output = defaultdict(list)
    output['resid_peaks_found']
    output['resid_peaks_accepted']

    x_array = np.array(x, dtype=float)
    y_array = np.array(y, dtype=float)

    #ensures no nan values in the arrays; ~ equivalent to np.logical_not
    nan_mask = (~np.isnan(x_array)) & (~np.isnan(y_array))
    x_array = x_array[nan_mask]
    y_array = y_array[nan_mask]

    #ensures data limits make sense
    if x_min == -np.inf:
        x_min = min(x_array)
    else:
        x_min = max(x_min, min(x_array))
    if x_max == np.inf:
        x_max = max(x_array)
    else:
        x_max = min(x_max, max(x_array))
    if bkg_min == -np.inf:
        bkg_min = min(x_array)
    if bkg_min < x_min:
        bkg_min = x_min
    if bkg_max == np.inf:
        bkg_max = max(x_array)
    if bkg_max > x_max:
        bkg_max = x_max

    output['peaks_found'], output['peaks_accepted']  = find_peak_centers(
        x_array, y_array, additional_peaks=additional_peaks, height=height,
        prominence=prominence, x_min=x_min, x_max=x_max
    )

    #The domain mask is applied to x and y after finding peaks so that any user
    #supplied peaks in additional_peaks are put into peaks_found, even if
    #they are not within the domain.
    domain_mask = (x_array >= x_min) & (x_array <= x_max)
    x = x_array[domain_mask]
    y = y_array[domain_mask]

    if debug:

        interactive = plt.isinteractive()
        plt.ioff()
        tot_fig, tot_ax = plt.subplots()
        tot_ax.plot(x, y, label='data')
        tot_ax.set_title('initial fits and backgrounds')

    if subtract_background:
        bkg_mask = (x >= bkg_min) & (x <= bkg_max)

        if background_type == 'PolynomialModel':
            background = getattr(models, background_type)(poly_n, prefix='background_')
        else:
            background = getattr(models, background_type)(prefix='background_')

        init_bkrd_params = background.guess(y[bkg_mask], x=x[bkg_mask])
        initial_bkrd = background.eval(init_bkrd_params, x=x)

        params_dict = initialize_peaks(
            x, y, peak_centers=output['peaks_accepted'], peak_width=peak_width,
            default_model=default_model, center_offset=center_offset,
            vary_Voigt=vary_Voigt, model_list=model_list, min_sigma=min_sigma,
            max_sigma=max_sigma, background_y=initial_bkrd,
            debug=debug, peak_heights=peak_heights
        )

        model, params = generate_lmfit_model(params_dict)
        fit_wo_bkrd = model.eval(params, x=x)
        bkrd_params = background.guess(y - fit_wo_bkrd, x=x)

        if debug:
            tot_ax.plot(x, initial_bkrd, label='initial_bkrd')
            tot_ax.plot(x, background.eval(bkrd_params, x=x), label='background_1')

        composite_model = model + background
        composite_params = params + bkrd_params

    else:
        params_dict = initialize_peaks(
            x, y, peak_centers=output['peaks_accepted'], peak_width=peak_width,
            default_model=default_model, center_offset=center_offset,
            vary_Voigt=vary_Voigt, model_list=model_list, min_sigma=min_sigma,
            max_sigma=max_sigma, debug=debug, peak_heights=peak_heights
        )

        composite_model, composite_params = generate_lmfit_model(params_dict)

    if debug:
        tot_ax.plot(x, composite_model.eval(composite_params, x=x),
                    label='initial_fit_1')

    #Fit for the initialized model
    output['initial_fits'] = [composite_model.eval(composite_params, x=x)]
    #Fit for the best fit model
    output['fit_results'] = [composite_model.fit(y, composite_params, x=x,
                                                 method=min_method, fit_kws=fit_kws)]

    print(f'\nFit #1: {output["fit_results"][-1].nfev} evaluations')

    if fit_residuals:
        for eval_num in range(num_resid_fits):

            last_chisq = output['fit_results'][-1].redchi

            #Updates the current parameters and removes the background from the peaks
            composite_params = output['fit_results'][-1].params.copy()
            for prefix in params_dict:
                for param in params_dict[prefix][1]:
                    params_dict[prefix][1][param] = composite_params[param]

            fwhm = []
            for prefix in params_dict:
                if f'{prefix}fwhm' in params_dict[prefix][1]:
                    fwhm.append(params_dict[prefix][1][f'{prefix}fwhm'].value)
                else:
                    fwhm.append(params_dict[prefix][1][f'{prefix}sigma'].value * 2.5) #estimate
            avg_fwhm = np.mean(fwhm)

            #use peaks_accepted as the peak centers instead of the centers of peaks
            #because peaks will move during fitting to fill void space.
            residual_peaks = find_hidden_peaks(x, output['fit_results'][-1],
                                               output['peaks_accepted'], fwhm,
                                               min_resid, debug)
            #Keep them as lists so the peaks found at each iteration is available.
            output['resid_peaks_found'].append([residual_peaks[0]])
            output['resid_peaks_accepted'].append([residual_peaks[1]])
            output['peaks_accepted'] = sorted(output['peaks_accepted'] + residual_peaks[1])

            #background_y=output["fit_results"][-1].best_fit means that new peaks
            #will be fit to the residuals (y-background_y)
            if residual_peaks[1]:
                params_dict = initialize_peaks(
                    x, y, peak_centers=residual_peaks[1], peak_width=avg_fwhm,
                    default_model=default_model, center_offset=center_offset,
                    vary_Voigt=vary_Voigt, model_list=None, min_sigma=min_sigma,
                    max_sigma=max_sigma, background_y=output['fit_results'][-1].best_fit,
                    params_dict=params_dict, debug=debug
                )

                params_dict = re_sort_prefixes(params_dict)

            model, params = generate_lmfit_model(params_dict)

            if subtract_background:
                fit_wo_bkrd = model.eval(params, x=x)
                bkrd_params = background.guess(y - fit_wo_bkrd, x=x)

                composite_params = params + bkrd_params
                composite_model = model + background

                if debug:
                    tot_ax.plot(x, background.eval(bkrd_params, x=x),
                                label=f'background_{eval_num+2}')

            else:
                composite_model = model
                composite_params = params

            if debug:
                tot_ax.plot(x, composite_model.eval(composite_params, x=x),
                            label=f'initial fit_{eval_num+2}')

            output['initial_fits'].append(composite_model.eval(composite_params, x=x))
            output['fit_results'].append(composite_model.fit(y, composite_params, x=x,
                                                             method=min_method,
                                                             fit_kws=fit_kws))

            current_chisq = output['fit_results'][-1].redchi

            if (np.abs(last_chisq - current_chisq) < 1e-9) and (not residual_peaks[1]):
                print(f'\nFit #{eval_num+2}: {output["fit_results"][-1].nfev} evaluations')
                print('Delta \u03c7\u00B2 < 1e-9 \nCalculation ended')
                break
            else:
                print(f'\nFit #{eval_num+2}: {output["fit_results"][-1].nfev} evaluations')
                print(f'Delta \u03c7\u00B2 = {np.abs(last_chisq - current_chisq):.9f}')
            if eval_num + 1 == num_resid_fits:
                print('Number of residual fits exceeded.')

    if debug:
        tot_ax.legend()
        plt.show(block=False)
        if interactive:
            plt.ion()

    for fit_result in output['fit_results']:
        #list of y-values for the inidividual models
        output['individual_peaks'].append(fit_result.eval_components(x=x))
        if background_type == 'ConstantModel':
            output['individual_peaks'][-1]['background_'] = np.array(
                [output['individual_peaks'][-1]['background_'],] * len(y)
            )

        #Gets the parameters for each model and their standard deviations, if available
        if None not in {fit_result.params[var].stderr for var in fit_result.var_names}:
            output['best_values'].append([
                [var, fit_result.params[var].value,
                 fit_result.params[var].stderr] for var in fit_result.params
            ])
        else:
            output['best_values'].append([
                [var, fit_result.params[var].value, 'N/A'] for var in fit_result.params
            ])

    return output


def r_squared(y, y_calc, num_variables):
    """
    Calculates r^2 and adjusted r^2.

    Parameters
    ----------
    y : array-like
        The experimental y data.
    y_calc : array-like
        The calculated y from fitting.
    num_variables : int
        The number of variables used by the fitting model.

    Returns
    -------
    r_sq : float
        The r squared value for the fitting.
    r_sq_adj : float
        The adjusted r squared value for the fitting, which takes into
        account the number of variables in the fitting model.

    """

    mean = np.mean(y)
    n = len(y)
    SS_tot = np.sum((y - mean)**2)
    SS_res = np.sum((y - y_calc)**2)

    r_sq = 1 - (SS_res/SS_tot)
    r_sq_adj = 1 - (SS_res/(n-num_variables-1))/(SS_tot/(n-1))

    return r_sq, r_sq_adj


def background_selector(x_input, y_input, click_list=None):
    """
    Allows selection of the background for the data on a matplotlib plot.

    Parameters
    ----------
    x_input, y_input : array-like
        x and y values for the fitting.
    click_list : list, optional
        A nested list, with each entry corresponding to [x, y] locations
        for the points needed fit the background.

    Returns
    -------
    click_list : list
        A nested list, with each entry corresponding to [x, y] locations
        for the points needed fit the background.

    #TODO: maybe change it so that the input click_list and output click_list are different
    """


    def remove_circle(axis):
        """
        Removes the selected circle from the axis.

        Parameters
        ----------
        axis : plt.Axes
            The axis to use.

        """

        coords = [*axis.picked_object.get_center()]
        for i, value in enumerate(click_list):
            if all(np.isclose(value, coords)):
                del click_list[i]
                break
        axis.picked_object.remove()
        axis.picked_object = None


    def create_circle(x, y, axis):
        """
        Places a circle at the designated x,y position.

        Parameters
        ----------
        x, y : float
            The x, y position to place the center of the circle.
        axis : plt.Axes
            The axis to use.

        """

        x_min, x_max, y_min, y_max = axis.axis()
        circle_width = 0.03 * (x_min - x_max)
        circle_height = 0.03 * (y_min - y_max) * 2 # *2 because the aspect ratio is not square

        circ = Ellipse((x, y), circle_width, circle_height, edgecolor='black',
                       facecolor='green', picker = True)
        axis.add_patch(circ)


    def plot_background(x, y, axis, axis_2):
        """
        Plots a background that fits the selected peaks.

        Parameters
        ----------
        x, y : array-like
            The x and y values of the raw data.
        axis : plt.Axes
            The axis upon which to plot the background.
        axis_2 : plt.Axes
            The axis to show the background after subtracting the user
            specified points.

        """

        for line in axis.lines[1:]:
            line.remove()
        for line in axis_2.lines:
            line.remove()

        y_subtracted = y.copy()
        if len(click_list) > 1:
            points = sorted(click_list, key=lambda cl: cl[0])

            for i in range(len(points)-1):
                x_points, y_points = zip(*points[i:i+2])
                axis.plot(x_points, y_points, color='k', ls='--',
                          lw=2)
                coeffs = np.polyfit(x_points, y_points, 1)
                boundary = (x >= x_points[0]) & (x <= x_points[1])
                x_line = x[boundary]
                y_line = y[boundary]
                line = np.polyval(coeffs, x_line)
                y_subtracted[boundary] = y_line - line

            axis.plot(0, 0, 'k--', lw=2, label='background')

        axis_2.plot(x, y_subtracted, 'ro-', ms=2, label='subtracted data')
        axis.legend()
        axis_2.legend()


    def on_click(event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        1) If the button press is not within the 'ax' axis, then nothing is done
        2) If a double left click is done, then a circle is place on the ax axis
        3) If a double right click is done, and a circle is selected, then the circle
           is deleted from the ax axis
        4) If a single left or right click is done, it deselects any selected circle
           if the click is not on the circle
        Peaks will be (re)plotted if 2) or 3) occurs

        """

        if event.inaxes == ax:

            if event.dblclick: #is a double click
                if event.button == 1: #left click

                    click_list.append([event.xdata, event.ydata])

                    create_circle(event.xdata, event.ydata, ax)

                    plot_background(x, y, ax, ax_2)
                    ax.figure.canvas.draw_idle()

                elif event.button == 3: #right click
                    if ax.picked_object is not None:
                        remove_circle(ax)
                        plot_background(x, y, ax, ax_2)
                        ax.figure.canvas.draw_idle()

            elif event.button in [1, 3]: #left or right click
                if ax.picked_object is not None and not ax.picked_object.contains(event)[0]:
                    ax.picked_object.set_facecolor('green')
                    ax.picked_object = None
                    ax.figure.canvas.draw_idle()


    def on_pick(event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        If a circle is selected, its color will change from green to red.
        It assigns the circle artist as the attribute 'picked_object' to the ax axis,
        which is just an easy way to keep the axis and the objects lumped together.

        """

        if ax.picked_object is not None and ax.picked_object != event.artist:
            ax.picked_object.set_facecolor('green')
            ax.picked_object = None
        ax.picked_object = event.artist
        ax.picked_object.set_facecolor('red')
        ax.figure.canvas.draw_idle()


    def on_key(event):
        """
        The function to be executed if a key is pressed.

        Parameters
        ----------
        event : matplotlib.backend_bases.KeyEvent
            key_press_event event.

        Notes
        -----
        If the 'delete' key is pressed and a circle is selected, the circle
        will be removed from the ax axis and the peaks will be replotted

        """

        if event.key == 'delete':
            if ax.picked_object is not None:
                remove_circle(ax)
                plot_background(x, y, ax, ax_2)
                ax.figure.canvas.draw_idle()


    x = np.array(x_input, float)
    y = np.array(y_input, float)
    click_list = click_list if click_list is not None else []

    fig, (ax, ax_2) = plt.subplots(2, num='Background Selector', sharex=True,
                                   gridspec_kw={'height_ratios':[2, 1], 'hspace': 0})

    ax.text(0.5, 1.01, 'Create point: double left click.  Select point: single click.\n'\
            'Delete selected point: double right click or delete key.',
            ha='center', va='bottom', transform=ax.transAxes)
    ax.picked_object = None
    ax.plot(x, y, 'o-', color='dodgerblue', ms=2, label='raw data')
    ax_2.plot(x, y, 'ro-', ms=2, label='subtracted data')

    #create references (cid#) to the events so they are not garbage collected
    cid1 = fig.canvas.mpl_connect('button_press_event', on_click)
    cid2 = fig.canvas.mpl_connect('pick_event', on_pick)
    cid3 = fig.canvas.mpl_connect('key_press_event', on_key)

    if click_list:
        plot_background(x, y, ax, ax_2)
        for point in click_list:
            create_circle(point[0], point[1], ax)

    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())
    ax.legend()
    ax_2.legend()
    ax.tick_params(labelbottom=False, bottom=False, which='both')
    fig.set_tight_layout(True)

    plt.show(block=False)

    return click_list


def peak_selector(x_input, y_input, click_list=None, initial_peak_width=1,
                  subtract_background=False, background_type='PolynomialModel',
                  poly_n=4, bkg_min=-np.inf, bkg_max=np.inf, default_model=None):
    """
    Allows selection of peaks on a matplotlib plot, along with peak width and type.

    Parameters
    ----------
    x_input, y_input : array-like
        x and y values for the fitting.
    click_list : list
        A nested list, with each entry corresponding to a peak. Each entry
        has the following layout:
        [[lmfit model, sigma fct, aplitude fct], [peak center, peak height, peak width]]
        where lmfit model is something like 'GaussianModel'. The first entry
        in the list comes directly from the peak_transformer function.
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

    Returns
    -------
    click_list : list
        A nested list, with each entry corresponding to a peak. Each entry
        has the following layout:
        [[lmfit model, sigma fct, aplitude fct], [peak center, peak height, peak width]]
        where lmfit model is something like 'GaussianModel'.

    """


    def remove_circle(axis):
        """
        Removes the selected circle from the axis.

        Parameters
        ----------
        axis : plt.Axes
            The axis to use.

        """

        center, height = [*axis.picked_object.get_center()]
        bkrd_height = initial_bkrd[np.argmin(np.abs(center-x))]
        for i, value in enumerate(click_list):
            if all(np.isclose(value[1][:2], [center, height - bkrd_height])):
                del click_list[i]
                break
        axis.picked_object.remove()
        axis.picked_object = None


    def create_circle(x, y, axis):
        """
        Places a circle at the designated x,y position.

        Parameters
        ----------
        x, y : float
            The x, y position to place the center of the circle.
        axis : plt.Axes
            The axis to use.

        """

        ax_width = axis.get_xlim()
        ax_height = axis.get_ylim()
        circle_width = 0.05 * (ax_width[1] - ax_width[0])
        circle_height = 0.05 * (ax_height[1] - ax_height[0])

        circ = Ellipse((x, y), circle_width, circle_height, edgecolor='black',
                       facecolor='green', picker = True)
        axis.add_patch(circ)


    def plot_total_peaks(x, axis):
        """
        Plots each selected peak and the sum of all peaks on the axis.

        Parameters
        ----------
        x, y : array-like
            The x and y values of the raw data.
        axis : plt.Axes
            The axis upon which to plot the peaks.
        """

        y_tot=0*x

        for line in axis.lines[2:]:
            line.remove()

        if click_list:
            #resets the color cycle to start at 0
            axis.set_prop_cycle(plt.rcParams['axes.prop_cycle'])
            peaks = sorted(click_list, key=lambda cl: cl[1][0])
            minx, maxx = [min(x), max(x)]

            middles = [0.0 for num in range(len(peaks)+1)]
            middles[0] = minx
            middles[-1] = maxx
            for i in range(len(peaks)-1):
                middles[i+1] = np.mean([peaks[i][1][0], peaks[i+1][1][0]])

            for i, peak in enumerate(peaks):
                center = peak[1][0]
                height = peak[1][1]
                width = peak[1][2]
                x_peak = x[(x >= middles[i]) & (x <= middles[i+1])]
                bkrd_peak = initial_bkrd[(x >= middles[i]) & (x <= middles[i+1])]
                prefix = f'peak_{i+1}'

                peak_model = getattr(models, peak[0][0])(prefix=prefix)
                if peak[0][0] != 'LognormalModel':
                    peak_model.set_param_hint('center',value=center, min=-np.inf,
                                              max=np.inf)
                    peak_model.set_param_hint('height', min=0)
                    peak_model.set_param_hint('amplitude',
                                              value=peak[0][1][1](height, width))
                    peak_model.set_param_hint('sigma',
                                              value=peak[0][1][0](height, width))
                else:
                    xm2 = center**2 # xm2 denotes x_mode squared
                    sigma = 0.85 * np.log((width + center* np.sqrt((4*xm2 + width**2)/(xm2))) / (2 * center))
                    mean = np.log(center) + sigma**2
                    amplitude = (height * sigma * np.sqrt(2*np.pi)) / (np.exp(((sigma**2)/2) - mean))

                    peak_model.set_param_hint('center', value=mean, min=1.e-19)
                    peak_model.set_param_hint('sigma', value=sigma)
                    peak_model.set_param_hint('amplitude', value=amplitude)

                if peak[0][0] == 'SplitLorentzianModel':
                    peak_model.set_param_hint('sigma_r',
                                              value=peak[0][1][0](height, width))

                peak_params = peak_model.make_params()
                plot_peak = peak_model.eval(peak_params, x=x_peak)
                peak = peak_model.eval(peak_params, x=x)
                axis.plot(x_peak, plot_peak+bkrd_peak, ':', lw=2, label=prefix)
                y_tot += peak

            axis.plot(x, y_tot + initial_bkrd, color='k', ls='--',
                      lw=2, label='total')
        axis.legend()


    def on_click(event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        1) If the button press is not within the 'ax' axis, then nothing is done
        2) If a double left click is done, then a circle is place on the ax axis
        3) If a double right click is done, and a circle is selected, then the circle
           is deleted from the ax axis
        4) If a single left or right click is done, it deselects any selected circle
           if the click is not on the circle
        Peaks will be (re)plotted if 2) or 3) occurs
        """

        if event.inaxes == ax:

            if event.dblclick: #is a double click
                if (event.button == 1) and (text_box.text): #left click

                    for key in models_dict:
                        if radio.value_selected == models_dict[key][0]:
                            model = [key, models_dict[key][1]]
                            break

                    #[[lmfit model, sigma fct, aplitude fct], [peak center, peak height, peak width]]
                    peak_center = event.xdata
                    peak_height = event.ydata - initial_bkrd[np.argmin(np.abs(peak_center-x))]
                    click_list.append([model, [peak_center, peak_height,
                                               float(text_box.text)]])

                    create_circle(event.xdata, event.ydata, ax)

                    plot_total_peaks(x, ax)
                    ax.figure.canvas.draw_idle()

                elif event.button == 3: #right click
                    if ax.picked_object is not None:
                        remove_circle(ax)
                        plot_total_peaks(x, ax)
                        ax.figure.canvas.draw_idle()

            elif event.button in [1, 3]: #left or right click
                if ax.picked_object is not None and not ax.picked_object.contains(event)[0]:
                    ax.picked_object.set_facecolor('green')
                    ax.picked_object = None
                    ax.figure.canvas.draw_idle()


    def on_pick(event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        If a circle is selected, its color will change from green to red.
        It assigns the circle artist as the attribute 'picked_object' to the ax axis,
        which is just an easy way to keep the axis and the objects lumped together.
        """

        if ax.picked_object is not None and ax.picked_object != event.artist:
            ax.picked_object.set_facecolor('green')
            ax.picked_object = None
        ax.picked_object = event.artist
        ax.picked_object.set_facecolor('red')
        ax.figure.canvas.draw_idle()


    def on_key(event):
        """
        The function to be executed if a key is pressed.

        Parameters
        ----------
        event : matplotlib.backend_bases.KeyEvent
            key_press_event event.

        Notes
        -----
        If the 'delete' key is pressed and a circle is selected, the circle
        will be removed from the ax axis and the peaks will be replotted

        """

        if event.key == 'delete':
            if ax.picked_object is not None:
                remove_circle(ax)
                plot_total_peaks(x, ax)
                ax.figure.canvas.draw_idle()


    x = np.array(x_input, float)
    y = np.array(y_input, float)
    click_list = click_list if click_list is not None else []
    fig = plt.figure(num='Peak Selector')
    #[left, bottom, width, height]
    ax = plt.axes([0.32, 0.07, 0.64, 0.83])
    ax.tick_params(labelbottom=False, labelleft=False)
    ax.text(0.5, 1.01, 'Create peak: double left click.  Select peak: single click.\n'\
            'Delete selected peak: double right click or delete key.',
            ha='center', va='bottom', transform=ax.transAxes)
    ax.picked_object = None
    ax.plot(x, y, 'o-', color='dodgerblue', ms=2, label='raw data')

    if subtract_background:
        bkg_mask = (x > bkg_min) & (x < bkg_max)
        if background_type == 'PolynomialModel':
            background = getattr(models, background_type)(poly_n, prefix='background_')
        else:
            background = getattr(models, background_type)(prefix='background_')

        init_bkrd_params = background.guess(y[bkg_mask], x=x[bkg_mask])
        initial_bkrd = background.eval(init_bkrd_params, x=x)

    else:
        initial_bkrd = np.array([0]*len(x))

    ax.plot(x, initial_bkrd, 'r--', lw=2, label='background')
    ax.legend()

    #create references (cid#) to the events so they are not garbage collected
    cid1 = fig.canvas.mpl_connect('button_press_event', on_click)
    cid2 = fig.canvas.mpl_connect('pick_event', on_pick)
    cid3 = fig.canvas.mpl_connect('key_press_event', on_key)

    ax_text = plt.axes([0.1, 0.25, 0.1, 0.1])
    ax_radio = plt.axes([0.02, 0.4, 0.26, 0.5])
    text_box = TextBox(ax_text, 'Peak \nWidth', initial=f'{initial_peak_width}',
                       label_pad=0.1)

    models_dict = peak_transformer()
    if default_model is not None:
        default_index = 0
        for index, key in enumerate(models_dict):
            if default_model == key:
                default_index = index
                break
    else:
        default_index = 0
    display_values = [models_dict[model][0] for model in models_dict]
    radio = RadioButtons(ax_radio, display_values, active=default_index)

    if click_list:
        plot_total_peaks(x, ax)
        for peak in click_list:
            center = peak[1][0]
            height = peak[1][1] + initial_bkrd[np.argmin(np.abs(center - x))]
            create_circle(center, height, ax)

    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())
    plt.show(block=False)

    return click_list


def plot_confidence_intervals(x, y, fit_result, n_sig=3):
    """
    Plot the data, fit, and the fit +- n_sig*sigma confidence intervals.

    Parameters
    ----------
    x, y : array-like
        x and y data used in the fitting.
    fit_result : lmfit.ModelResult
        The ModelResult object for the fitting.
    n_sig : int
        An integer describing the multiple of the standard error to use
        as the plotted error.

    """

    del_y = fit_result.eval_uncertainty(sigma=n_sig)
    plt.figure()
    plt.fill_between(x, fit_result.best_fit-del_y,
                     fit_result.best_fit+del_y, color='darkgrey',
                     label=f'best fit $\pm$ {n_sig}$\sigma$')
    plt.plot(x, y, 'o', ms=1.5, color='dodgerblue', label='data')
    plt.plot(x, fit_result.best_fit, 'k-', lw=1.5, label='best fit')
    plt.legend()
    plt.show(block=False)


def plot_peaks_for_model(x, y, x_min, x_max, peaks_found, peaks_accepted,
                         additional_peaks):
    """
    Plot the peaks found or added, as well as the ones found but rejected from the fitting.

    Parameters
    ----------
    x, y : array-like
        x and y data used in the fitting.
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

    fig, ax = plt.subplots()
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
        plt.text(0.1+0.35*i, 0.95, legend[i], ha='left', va='center',
                 transform=ax.transAxes)
        plt.hlines(0.95, 0.02+0.35*i, 0.08+0.35*i, color=colors[i], linestyle='--',
                   transform=ax.transAxes)
    plt.ylim(ax.get_ylim()[0], ax.get_ylim()[1]*1.1)
    plt.show(block=False)


def plot_fit_results(x, y, fit_result, label_rsq=False, plot_initial=False):
    """
    Plot the raw data, best fit, and residuals.

    Parameters
    ----------
    x, y : array-like
        x and y data used in the fitting.
    fit_result : lmfit.ModelResult
        A ModelResult object from lmfit; can be a list of ModelResults,
        in which case, the initial fit will use fit_result[0], and the
        best fit will use fit_result[-1].
    label_rsq : bool
        If True, will put a label with the adjusted r squared value of the fitting.
    plot_initial : bool
        If True, will plot the initial fitting as well as the best fit.

    """

    if not isinstance(fit_result, (list, tuple)):
        fit_result = [fit_result]

    fig_a, (ax_resid, ax_1) = plt.subplots(2, sharex=True,
                                           gridspec_kw={'height_ratios':[1, 5],
                                                        'hspace': 0})
    ax_1.plot(x, y, 'o', color='dodgerblue', ms=1.5, label='data')
    if plot_initial:
        ax_1.plot(x, fit_result[0].init_fit, 'r--', label='initial fit')
    ax_1.plot(x, fit_result[-1].best_fit, 'k-', label='best fit')
    ax_resid.plot(x, -fit_result[-1].residual, 'o', color='dodgerblue',
                  ms=1, label='residuals')
    ax_resid.axhline(0, color='k', linestyle='-')
    ax_1.legend()

    ax_1.set_ylabel('y')
    ax_1.set_xlim(np.min(x)-5, np.max(x)+5)
    ax_1.set_ylim(ax_1.get_ylim()[0] * (1 - 0.1), ax_1.get_ylim()[1] * (1 + 0.1))
    if label_rsq:
        ax_1.text((ax_1.get_xlim()[1]-ax_1.get_xlim()[0])*0.05 + ax_1.get_xlim()[0],
                  (ax_1.get_ylim()[1]-ax_1.get_ylim()[0])*0.95 + ax_1.get_ylim()[0],
                   f'R$^2$= {r_squared(y, fit_result[-1].best_fit, fit_result[-1].nvarys)[1]:.3f}',
                   ha='left', va='top')
    ax_resid.tick_params(labelbottom=False, bottom=False, which='both')
    ax_1.label_outer()

    ax_1.set_xlabel('x')
    ax_resid.set_ylabel('$y_{obs}-y_{calc}$')
    ax_resid.set_ylim(ax_resid.get_ylim()[0] * (1 + 0.1), ax_resid.get_ylim()[1] * (1 + 0.1))
    ax_resid.label_outer()
    plt.show(block=False)


def plot_individual_peaks(x, y, individual_peaks, fit_result, background_subtracted=False,
                          plot_subtract_background=False, plot_separate_background=False,
                          plot_w_background=False):
    """
    Plots each individual peak in the composite model and the total model.

    Parameters
    ----------
    x, y : array-like
        x and y data used in the fitting.
    individual_peaks : dict
        A dictionary with keys corresponding to the model prefixes
        in the fitting, and their values corresponding to their y values.
    fit_result : lmfit.ModelResult
        The ModelResult object from the fitting.
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

    """

    #Creates a color cycle to override matplotlib's to prevent color clashing
    COLORS = ['#ff7f0e', '#2ca02c', '#d62728', '#8c564b','#e377c2',
              '#bcbd22', '#17becf']
    n_col = int(np.ceil(len(individual_peaks) / 5))

    if background_subtracted:
        if plot_subtract_background:
            fig, ax = plt.subplots()
            color_cycle = itertools.cycle(COLORS)
            ax.plot(x, y-individual_peaks['background_'], 'o',
                    color='dodgerblue', label='data', ms=2)
            i = 0
            for peak in individual_peaks:
                if peak != 'background_':
                    ax.plot(x, individual_peaks[peak], label=f'peak {i+1}',
                            color=next(color_cycle))
                    i += 1
            ax.plot(x, fit_result.best_fit-individual_peaks['background_'],
                    'k--', lw=1.5, label='best fit')
            ax.legend(ncol=n_col)
            plt.show(block=False)

        if plot_w_background:
            fig, ax = plt.subplots()
            color_cycle = itertools.cycle(COLORS)
            ax.plot(x, y, 'o', color='dodgerblue', label='data', ms=2)
            i = 0
            for peak in individual_peaks:
                if peak != 'background_':
                    ax.plot(x, individual_peaks[peak]+individual_peaks['background_'],
                            label=f'peak {i+1}', color=next(color_cycle))
                    i += 1
            ax.plot(x, individual_peaks['background_'], 'k', label='background')
            ax.plot(x, fit_result.best_fit, 'k--', lw=1.5, label='best fit')
            ax.legend(ncol=n_col)
            plt.show(block=False)

        if plot_separate_background:
            fig, ax = plt.subplots()
            color_cycle = itertools.cycle(COLORS)
            ax.plot(x, y, 'o', color='dodgerblue', label='data', ms=2)
            i = 0
            for peak in individual_peaks:
                if peak != 'background_':
                    ax.plot(x, individual_peaks[peak], label=f'peak {i+1}',
                            color=next(color_cycle))
                    i += 1
            ax.plot(x, individual_peaks['background_'], 'k', label='background')
            ax.plot(x, fit_result.best_fit, 'k--', lw=1.5, label='best fit')
            ax.legend(ncol=n_col)
            plt.show(block=False)

    else:
        fig, ax = plt.subplots()
        color_cycle = itertools.cycle(COLORS)
        ax.plot(x, y, 'o', color='dodgerblue', label='data', ms=2)
        for i, peak in enumerate(individual_peaks):
            if peak != 'background_':
                ax.plot(x, individual_peaks[peak], label=f'peak {i+1}',
                        color=next(color_cycle))
        ax.plot(x, fit_result.best_fit, 'k--', lw=1.5, label='best fit')
        ax.legend(ncol=n_col)
        plt.show(block=False)


if __name__ == '__main__':

    import time
    from lmfit import lineshapes

    #data
    x_array = np.linspace(0, 60, 100)
    background = 0.1 * x_array
    noise = 0.1 * np.random.randn(len(x_array))
    peaks = lineshapes.gaussian(x_array, 30, 15, 5) + lineshapes.gaussian(x_array, 50, 35, 3)
    y_array = background + noise + peaks

    #inputs for plugNchug_fit function
    rel_height = 0
    prominence = np.inf
    center_offset = 10
    peak_width = 10
    x_min = 5
    x_max = 55
    additional_peaks = [2, 10, 36]
    subtract_background=True
    model_list = []
    min_method = 'least_squares'
    background_type = 'PolynomialModel'
    poly_n = 1
    default_model='GaussianModel'
    fit_kws = {}
    vary_Voigt=False
    fit_residuals=True
    num_resid_fits=5
    min_resid = 0.1
    debug=True
    bkg_min = 45

    #options for plotting data after fitting
    plot_data_wo_background=False
    plot_data_w_background=True
    plot_data_separatebackground=False
    plot_fit_result=True
    plot_CI=True
    n_sig = 3
    plot_peaks=True
    plot_initial=False

    time0 = time.time()

    fitting_results = plugNchug_fit(
        x_array, y_array, height=rel_height, prominence=prominence,
        center_offset=center_offset, peak_width=peak_width, model_list=model_list,
        subtract_background=subtract_background, x_min=x_min, x_max=x_max,
        additional_peaks=additional_peaks, background_type=background_type,
        poly_n=poly_n, min_method=min_method, default_model=default_model,
        fit_kws=fit_kws, vary_Voigt=vary_Voigt, fit_residuals=fit_residuals,
        num_resid_fits=num_resid_fits, min_resid=min_resid,
        debug=debug, bkg_min=bkg_min
    )

    print('\n\n'+'-'*8+f' {time.time()-time0:.1f} seconds '+'-'*8)

    #unpacks all of the data from the output of the plugNchug_fit function
    output_list = [fitting_results[key] for key in fitting_results]
    resid_found, resid_accept, peaks_found, peaks_accept, initial_fit, fit_results, individual_peaks, best_values = output_list
    fit_result = fit_results[-1]
    individual_peaks = individual_peaks[-1]
    best_values = best_values[-1]

    domain_mask = (x_array > x_min) & (x_array < x_max)
    x_array = x_array[domain_mask]
    y_array = y_array[domain_mask]

    #Plot the peaks found or added, as well as if they were used in the fitting
    if plot_peaks:
        plot_peaks_for_model(x_array, y_array, x_min, x_max, peaks_found,
                             peaks_accept, additional_peaks)

    #Plot the initial model used for fitting
    if plot_initial:
        fig=plt.figure()
        plt.plot(x_array, y_array, 'o', x_array, initial_fit[0], ms=2)
        plt.legend(['data', 'initial guess'])
        plt.show(block=False)

    #Plot the best fit and residuals
    if plot_fit_result:
        plot_fit_results(x_array, y_array, fit_results, True, True)

    #Plots individual peaks from the fitting
    plot_individual_peaks(x_array, y_array, individual_peaks, fit_result, subtract_background,
                          plot_data_wo_background, plot_data_separatebackground,
                          plot_data_w_background)

    #Plot the data, fit, and the fit +- n_sig*sigma confidence intervals
    if plot_CI:
        plot_confidence_intervals(x_array, y_array, fit_result, n_sig)

    print('\n\n', fit_result.fit_report(min_correl=0.5))