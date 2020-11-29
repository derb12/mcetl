# -*- coding: utf-8 -*-
"""Provides utility functions, classes, and constants for the fitting module.

Useful functions are put here in order to prevent circular importing
within the other files.

@author  : Donald Erb
Created on Nov 18, 2020

"""


import lmfit


    """


    """



    """


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
