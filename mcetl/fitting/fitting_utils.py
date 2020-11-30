# -*- coding: utf-8 -*-
"""Provides utility functions, classes, and constants for the fitting module.

Useful functions are put here in order to prevent circular importing
within the other files.

@author  : Donald Erb
Created on Nov 18, 2020

"""


import lmfit
import numpy as np


def numerical_extrema(y):
    """
    Computes the numerical maximum or minimum for a peak.

    Parameters
    ----------
    y : array-like
        The y-values for the peak model.

    Returns
    -------
    extrema : float
        The extrema with the highest absolute value from the input y data.
        Assumes the peak is negative if abs(min(y)) > abs(max(y)).

    Notes
    -----
    Use np.nanmin and np.nanmax instead of min and max in order to convert
    the output to a numpy dtype. This way, all of the numerical calculations
    using the output of this function will work, even if y is a list or tuple.

    """

    # use np.nanmin/max to convert the values to numpy
    min_y, max_y = np.nanmin(y), np.nanmax(y)
    if abs(min_y) > abs(max_y):
        extrema = min_y
    else:
        extrema = max_y

    return extrema


def numerical_mode(x, y):
    """
    Computes the numerical mode (x-value at which the extrema occurs) of a peak.

    Parameters
    ----------
    x : array-like
        The x-values for the peak model.
    y : array-like
        The y-values for the peak model.

    Returns
    -------
    float
        The x-value at which the extrema in y occurs.

    """

    return x[np.where(y == numerical_extrema(y))[0][0]]


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
        not at least two x-values at which y = extrema_y / 2, then None
        is returned.

    Notes
    -----
    First finds the x-values where y - extrema_y / 2 changes signs, and
    then uses linear interpolation to approximate the x-values at which
    y - extrema_y / 2 = 0

    """

    # use ravel to ensure pandas Series work
    diff = np.ravel(y - numerical_extrema(y) / 2)
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


    """









def model_directory():
    """
    [summary]

    """

    {'BreitWignerModel': (lmfit.models.BreitWignerModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['q', 1.0, float]]), 'ComplexConstantModel': (lmfit.models.ComplexConstantModel, [['re', 0.0, float], ['im', 0.0, float]]), 'ConstantModel': (lmfit.models.ConstantModel, [['c', 0.0, float]]), 'DampedHarmonicOscillatorModel': (lmfit.models.DampedHarmonicOscillatorModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['gamma', 1.0, float]]),
    'DampedOscillatorModel': (lmfit.models.DampedOscillatorModel, [['amplitude', 1.0, float], ['center', 1.0, float], ['sigma', 0.1, float]]), 'DoniachModel': (lmfit.models.DoniachModel, [['amplitude', 1.0, float], ['center', 0, int], ['sigma', 1.0, float], ['gamma', 0.0, float]]),
    'ExponentialGaussianModel': (lmfit.models.ExponentialGaussianModel, [['amplitude', 1, int], ['center', 0, int], ['sigma', 1.0, float], ['gamma', 1.0, float]]), 'ExponentialModel': (lmfit.models.ExponentialModel, [['amplitude', 1, int], ['decay', 1, int]]),
    'GaussianModel': (lmfit.models.GaussianModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float]]), 'LinearModel': (lmfit.models.LinearModel, [['slope', 1.0, float], ['intercept', 0.0, float]]),
    'LognormalModel': (lmfit.models.LognormalModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1, int]]), 'LorentzianModel': (lmfit.models.LorentzianModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float]]),
    'MoffatModel': (lmfit.models.MoffatModel, [['amplitude', 1, int], ['center', 0.0, float], ['sigma', 1, int], ['beta', 1.0, float]]), 'ParabolicModel': (lmfit.models.QuadraticModel, [['a', 0.0, float], ['b', 0.0, float], ['c', 0.0, float]]),
    'Pearson7Model': (lmfit.models.Pearson7Model, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['expon', 1.0, float]]), 'PolynomialModel': (lmfit.models.PolynomialModel, [['c0', 0, int], ['c1', 0, int], ['c2', 0, int], ['c3', 0, int], ['c4', 0, int], ['c5', 0, int], ['c6', 0, int], ['c7', 0, int], ['degree', 1, int]]),
    'PowerLawModel': (lmfit.models.PowerLawModel, [['amplitude', 1, int], ['exponent', 1.0, float]]), 'PseudoVoigtModel': (lmfit.models.PseudoVoigtModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0,float], ['fraction', 0.5, float]]),
    'QuadraticModel': (lmfit.models.QuadraticModel, [['a', 0.0, float], ['b', 0.0, float], ['c', 0.0, float]]), 'RectangleModel': (lmfit.models.RectangleModel, [['amplitude', 1.0, float], ['center1', 0.0, float], ['sigma1', 1.0, float], ['center2', 1.0, float], ['sigma2', 1.0, float], ['form', 'linear', str]]),
    'SkewedGaussianModel': (lmfit.models.SkewedGaussianModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['gamma', 0.0, float]]), 'SkewedVoigtModel': (lmfit.models.SkewedVoigtModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['gamma', None, type(None)], ['skew', 0.0, float]]),
    'SplitLorentzianModel': (lmfit.models.SplitLorentzianModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['sigma_r', 1.0, float]]), 'StepModel': (lmfit.models.StepModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['form', 'linear', str]]),
    'StudentsTModel': (lmfit.models.StudentsTModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float]]), 'ThermalDistributionModel': (lmfit.models.ThermalDistributionModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['kt', 1.0, float], ['form', 'bose', str]]),
    'VoigtModel': (lmfit.models.VoigtModel, [['amplitude', 1.0, float], ['center', 0.0, float], ['sigma', 1.0, float], ['gamma', None, type(None)]])}
