# -*- coding: utf-8 -*-
"""Provides all objects related to fitting data.


@author: Donald Erb
Created on Nov 15, 2020

"""


from .fitting_gui import launch_fitting_gui
from .peak_fitting import (
    BackgroundSelector, PeakSelector, fit_peaks, plot_confidence_intervals,
    plot_fit_results, plot_individual_peaks, plot_peaks_for_model, r_squared
)
