# -*- coding: utf-8 -*-
"""Provides all objects related to fitting data.


@author: Donald Erb
Created on Nov 15, 2020

"""


from .fitting_gui import (
    SimpleEmbeddedFigure, fit_dataframe, fit_to_excel, launch_fitting_gui
)
from .peak_fitting import (
    BackgroundSelector, PeakSelector, find_peak_centers, peak_fitting,
    peak_transformer, plot_fit_results, plot_individual_peaks, r_squared
)
