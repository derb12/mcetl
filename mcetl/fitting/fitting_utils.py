# -*- coding: utf-8 -*-
"""Provides utility functions, classes, and constants for the fitting module.

Useful functions are put here in order to prevent circular importing
within the other files.

@author  : Donald Erb
Created on Nov 18, 2020

Notes
-----
The functions get_model_name, get_model_object, and get_gui_name are to be
used, rather than referring to the constants _TOTAL_MODELS and _GUI_MODELS
because the implementation of these constants may change in the future while
the output of the functions can be kept constant.

"""


import inspect

import lmfit
import numpy as np

from . import models


# models that require keyword arguments during initialization
_INIT_MODELS = {
    'PolynomialModel': {'degree': [0, tuple(range(8))]},
    'RectangleModel': {'form': ['linear', ('linear', 'atan', 'erf', 'logistic')]},
    'StepModel': {'form': ['linear', ('linear', 'atan', 'erf', 'logistic')]},
    'ThermalDistributionModel': {'form': ['bose', ('bose', 'maxwell', 'fermi')]}
}


def _create_model_cache():
    """
    Builds a dictionary of models that are available through lmfit.models and mcetl.models.

    Returns
    -------
    dict
        A dictionary of models available through lmfit and mcetl. Keys are the
        model class name, such as 'GaussianModel', and the values are a dictionary
        containing the following items:

            'display_name' : str
                The name to use in GUIs, such as 'Gaussian'.
            'model' : lmfit.Model
                The model object, such as lmfit.models.GaussianModel.
            'init_kwargs' : dict(str: list)
                The necessary keyword arguments to initialize the model.
                Keys are keywords, such as 'form' for StepModel, and values
                are explained below.
            'parameters' : dict(str: list)
                The parameters for the model. Keys are parameter names, and values
                are explained below.
            'is_peak' : bool
                If True, the model represents a peak-type model. For peak-type
                models, numerical calculations for fwhm, area, extremum, and mode
                will be included with the other best values from the ModelResult.

        For 'init_kwargs' and 'parameters', the values within the dictionary are a
        list, with the first item being the initial value to use, and the second
        item being a list/tuple/type dictating the possible values of the value.
        For example, 1) 'GaussianModel' parameters are {'amplitude': [1.0, float],
        'center': [0.0, float], 'sigma': [1.0, float]}; 2) 'StepModel' init_kwargs
        are {'form': ['linear', ('linear', 'atan', 'erf', 'logistic')]}.

    Notes
    -----
    Inspects the model object's signature, the model's function signature,
    and the model's guess signature in order to determine the initialization
    parameters, the model parameters, and whether the model is a peak-type
    function, respectively.

    """
    # repeated or unwanted models from lmfit
    unwanted_models = ('Model', 'ParabolicModel', 'ExpressionModel')

    # to make models more identifiable/readable, while allowing
    # their actual names to be reference within code
    replaced_names = {
        'BreitWignerModel': 'Breit-Wigner-Fano',
        'BreitWignerFanoModel': 'Breit-Wigner-Fano_alt',
        'ComplexConstantModel': 'Complex Constant',
        'DampedHarmonicOscillatorModel': 'Damped Harmonic Oscillator',
        'DampedOscillatorModel': 'Damped Oscillator',
        'DoniachModel': 'Doniach-Sujic',
        'ExponentialGaussianModel': 'Exponential Gaussian',
        'LognormalModel': 'Log-normal',
        'PowerLawModel': 'Power Law',
        'PseudoVoigtModel': 'Pseudo-Voigt',
        'SkewedGaussianModel': 'Skewed Gaussian',
        'SkewedVoigtModel': 'Skewed Voigt',
        'SplitLorentzianModel': 'Split Lorentzian',
        'ThermalDistributionModel': 'Thermal Distribution'
    }

    # generated by checking if the keyword 'negative' is in the model's guess
    # function; however, this could easily change in later lmfit versions, so
    # it's better to have a written set.
    peak_models = {
        'BreitWignerFanoModel',
        'BreitWignerModel',
        'DampedHarmonicOscillatorModel',
        'DampedOscillatorModel',
        'DonaichModel',
        'DoniachModel',
        'ExponentialGaussianModel',
        'GaussianModel',
        'LognormalModel',
        'LorentzianModel',
        'MoffatModel',
        'Pearson7Model',
        'PseudoVoigtModel',
        'SkewedGaussianModel',
        'SkewedVoigtModel',
        'SplitLorentzianModel',
        'StudentsTModel',
        'VoigtModel'
    }

    available_models = {}
    for module in (lmfit.models, models):
        for name, obj in inspect.getmembers(module, predicate=inspect.isclass):
            try:
                if not issubclass(obj, lmfit.Model) or name in unwanted_models or '2d' in name:
                    continue

                available_models[name] = {
                    'display_name': replaced_names.get(name, name.replace('Model', '')),
                    'class': obj, 'init_kwargs': {}, 'parameters': {}, 'is_peak': False
                }

                model_sig = inspect.signature(obj)
                for param in model_sig.parameters.values():
                    if param.name not in ('independent_vars', 'prefix', 'nan_policy',
                                          'name', 'kwargs'):
                        # set initial values in order to temporarily initialize the model
                        available_models[name]['init_kwargs'][param.name] = (
                            param.default if param.default != param.empty else 0)

                # initialize the model to get its func and guess attributes
                model = obj(**available_models[name]['init_kwargs'])

                function_sig = inspect.signature(model.func)
                for param in function_sig.parameters.values():
                    if (param.name not in available_models[name]['init_kwargs']
                            and param.default != param.empty):
                        # all built-in models take floats as parameters
                        available_models[name]['parameters'][param.name] = [param.default, float]

                # THE CODE BELOW CAN BE USED TO CHECK IF A MODEL IS A "PEAK",
                # BUT COULD EASILY CHANGE IN LATER lmfit VERSIONS, SO THE
                # CODE IS ONLY HERE FOR REFERENCE.
                # guess_sig = inspect.signature(model.guess)
                # if (any(param.name == 'negative' for param in guess_sig.parameters.values())
                #         and name != 'ThermalDistributionModel'):
                #     available_models[name]['is_peak'] = True
                if name in peak_models:
                    available_models[name]['is_peak'] = True

                # set the actual init_kwargs to include data type/allowed values
                if available_models[name]['init_kwargs']:
                    if name in _INIT_MODELS:
                        available_models[name]['init_kwargs'] = _INIT_MODELS[name]
                    else:  # in case other models are added in the future
                        available_models[name]['init_kwargs'] = {
                            key: [value, type(value)] for key, value in available_models[name]['init_kwargs'].items()
                        }

            except Exception:
                pass  # avoid any models that do not work; none for lmfit version 1.0.1

    # DoniachModel was misspelled as DonaichModel until lmfit v1.0.1
    if 'DoniachModel' not in available_models:
        available_models['DoniachModel'] = available_models.pop('DonaichModel')
    else:
        available_models.pop('DonaichModel', None)

    return {k: v for k, v in sorted(available_models.items(), key=lambda kv: kv[0])}


# for use within code
_TOTAL_MODELS = _create_model_cache()
# for use with GUIs; convert gui names to names in _TOTAL_MODELS
_GUI_MODELS = {vals['display_name']: key for key, vals in _TOTAL_MODELS.items()}


def print_available_models():
    """
    Prints out a dictionary of all models supported by mcetl.

    Also prints out details for each model, including its class,
    the name used when displaying in GUIs, its parameters, and
    whether it is considered a peak function.

    """
    for model_name, model_values in _TOTAL_MODELS.items():
        print(f'\n"{model_name}"')
        for key, value in model_values.items():
            print(f'    "{key}": {value}')


def get_model_name(model):
    """
    Converts the model name used in GUIs to the model class name.

    For example, converts 'Gaussian' to 'GaussianModel' and
    'Skewed Gaussian' to 'SkewedGaussianModel'.

    Useful so that code can always refer to the original model name and
    not be affected if the name of the model used in GUIs changes. Also
    ensures that user-input model names are correctly interpreted.

    Parameters
    ----------
    model : str
        The model name used within a GUI or input by a user.

    Returns
    -------
    output : str
        The class name of the model, which can give other information
        by using _TOTAL_MODELS[output].

    Raises
    ------
    KeyError:
        Raised if the input model name is not valid.

    """
    output = None
    if model in _TOTAL_MODELS:
        output = model
    elif model in _GUI_MODELS:
        output = _GUI_MODELS[model]

    if output is None:
        for model_name, values in _TOTAL_MODELS.items():
            if model.lower() in (model_name.lower(), values['display_name'].lower()):
                output = model_name
                break
        else:  # if there is no break
            raise KeyError((f'"{model}" is not an available model. Check the spelling,'
                            ' and may need to update lmfit and/or mcetl.'))

    return output


def get_model_object(model):
    """
    Returns the model object given a model name, eg. 'Gaussian' -> lmfit.models.GaussianModel.

    Parameters
    ----------
    model : str
        The name of the model desired. Can either be the model class name, such as
        'GaussianModel', or the name used in GUIs, such as 'Gaussian.

    Returns
    -------
    output : lmfit.Model
        The class corresponding to the input model name.

    """
    return _TOTAL_MODELS[get_model_name(model)]['class']


def get_gui_name(model):
    """
    Returns the name used in GUIs for the input model, eg. 'GaussianModel' -> 'Gaussian'.

    Parameters
    ----------
    model : str
        The input model string.

    Returns
    -------
    str
        The model's name as it appears in GUIs.

    Notes
    -----
    This is a convenience function to be used so that the internals
    of how model names are specified can change while code can always
    use this function.

    """
    return _TOTAL_MODELS[get_model_name(model)]['display_name']


def get_is_peak(model):
    """
    Determines if the input model is registered as a peak function.

    Parameters
    ----------
    model : str
        The name of the model. Can either be the GUI name (eg. 'Gaussian')
        or the class name (eg. 'GaussianModel').

    Returns
    -------
    is_peak : bool
        True if the input model is within _TOTAL_MODELS and _TOTAL_MODELS[model]['is_peak']
        is True. If the model cannot be found, or if _TOTAL_MODELS[model]['is_peak']
        is False, then returns False.

    """
    try:
        is_peak = _TOTAL_MODELS[get_model_name(model)]['is_peak']
    except KeyError:
        is_peak = False

    return is_peak


def _check_if_constant(model_name, model_values, fit_data):
    """
    Changes the shape of the data to match the fit data if 'Constant' in model name.

    ConstantModel and ComplexConstantModel return a single value
    rather than an array, so need to create an array for those
    models so that issues aren't caused during plotting.

    Parameters
    ----------
    model_name : str
        The model used for the background, such as 'ConstantModel'.
    model_values : array-like or float
        The value(s) of the background.
    fit_data : array-like
        The data that was used for fitting.

    Returns
    -------
    output : array-like
        An array of the background values, with the same size as the
        input y array.

    """
    try:
        actual_model_name = get_model_name(model_name)
    except KeyError:
        actual_model_name = ''  # won't change any unknown models

    if actual_model_name in ('ConstantModel', 'ComplexConstantModel'):
        output = np.full(len(fit_data), model_values)
    else:
        output = model_values

    return output


def r_squared(y_data, y_fit, num_variables=1):
    """
    Calculates r^2 and adjusted r^2 for a fit.

    Parameters
    ----------
    y_data : array-like
        The experimental y data.
    y_fit : array-like
        The calculated y from fitting.
    num_variables : int, optional
        The number of variables used by the fitting model.

    Returns
    -------
    r_sq : float
        The r squared value for the fitting.
    r_sq_adj : float
        The adjusted r squared value for the fitting, which takes into
        account the number of variables in the fitting model.

    """
    y = np.asarray(y_data)
    y_calc = np.asarray(y_fit)

    n = y.shape[0]
    sum_sq_tot = np.sum((y - np.mean(y))**2)
    sum_sq_res = np.sum((y - y_calc)**2)

    r_sq = 1 - (sum_sq_res / sum_sq_tot)
    r_sq_adj = 1 - (sum_sq_res / (n - num_variables - 1)) / (sum_sq_tot / (n - 1))

    return r_sq, r_sq_adj


def r_squared_model_result(fit_result):
    """
    Calculates r^2 and adjusted r^2 for a fit, given an lmfit.ModelResult.

    Parameters
    ----------
    fit_result : lmfit.ModelResult
        The ModelResult object from a fit.

    Returns
    -------
    tuple(float, float)
        The r^2 and adjusted r^2 values for the fitting.

    """
    return r_squared(fit_result.data, fit_result.best_fit, fit_result.nvarys)


def numerical_extremum(y):
    """
    Computes the numerical maximum or minimum for a peak.

    Parameters
    ----------
    y : array-like
        The y-values for the peak model.

    Returns
    -------
    extremum : float
        The extremum with the highest absolute value from the input y data.
        Assumes the peak is negative if abs(min(y)) > abs(max(y)).

    Notes
    -----
    Use np.nanmin and np.nanmax instead of min and max in order to convert
    the output to a numpy dtype. This way, all of the numerical calculations
    using the output of this function will work, even if y is a list or tuple.

    """
    min_y, max_y = np.nanmin(y), np.nanmax(y)
    if abs(min_y) > abs(max_y):
        extremum = min_y
    else:
        extremum = max_y

    return extremum


def numerical_mode(x, y):
    """
    Computes the numerical mode (x-value at which the extremum occurs) of a peak.

    Parameters
    ----------
    x : array-like
        The x-values for the peak model.
    y : array-like
        The y-values for the peak model.

    Returns
    -------
    float
        The x-value at which the extremum in y occurs.

    """
    return x[np.where(y == numerical_extremum(y))[0][0]]


def numerical_area(x, y):
    """
    Computes the numerical area of a peak using the trapezoidal method.

    Parameters
    ----------
    x : array-like
        The x-values for the peak model.
    y : array-like
        The y-values for the peak model.

    Returns
    -------
    float
        The integrated area of the peak, using the trapezoidal method.

    """
    return np.trapz(y, x)


def numerical_fwhm(x, y):
    """
    Computes the numerical full-width-at-half-maximum of a peak.

    Parameters
    ----------
    x : array-like
        The x-values for the peak model.
    y : array-like
        The y-values for the peak model.

    Returns
    -------
    float or None
        The calculated full-width-at-half-max of the peak. If there are
        not at least two x-values at which y = extremum_y / 2, then None
        is returned.

    Notes
    -----
    First finds the x-values where y - extremum_y / 2 changes signs, and
    then uses linear interpolation to approximate the x-values at which
    y - extremum_y / 2 = 0

    """
    # use ravel to ensure pandas Series work
    diff = np.ravel(y - numerical_extremum(y) / 2)
    roots = np.where(np.sign(diff[:-1]) != np.sign(diff[1:]))[0]

    if roots.size < 2:
        fwhm = None
    else:
        x_intercepts = []
        for root in ([roots[0], roots[0] + 1], [roots[-1], roots[-1] + 1]):
            # uses linear interpolation to find the x-value where y - ymax/2 = 0
            y0, y1 = (diff[root[0]], diff[root[1]])
            x0, x1 = (x[root[0]], x[root[1]])
            x_intercepts.append(x0 - ((y0 * (x1 - x0)) / (y1 - y0)))

        fwhm = abs(x_intercepts[1] - x_intercepts[0])

    return fwhm


def subtract_linear_background(x, y, background_points):
    """
    Returns y-values after subtracting a linear background constructed from points.

    Parameters
    ----------
    x : array-like
        The x-values of the data.
    y : array-like
        The y-values of the data.
    background_points : list(list(float, float))
        A list containing the [x, y] values for each point representing
        the background.

    Returns
    -------
    y_subtracted : np.ndarray
        The input y-values, after subtracting the background.

    Notes
    -----
    Assumes the background is represented by lines connecting each of the
    specified background points.

    """
    x_data = np.asarray(x)
    y_data = np.asarray(y)
    y_subtracted = y_data.copy()
    if len(background_points) > 1:
        points = sorted(background_points, key=lambda p: p[0])
        for i in range(len(points) - 1):
            x_points, y_points = zip(*points[i:i + 2])
            boundary = (x_data >= x_points[0]) & (x_data <= x_points[1])
            y_line = y_data[boundary]
            y_subtracted[boundary] = y_line - np.linspace(*y_points, y_line.shape[0])

    return y_subtracted
