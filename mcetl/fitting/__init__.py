# -*- coding: utf-8 -*-
"""Provides all objects related to fitting data.


@author: Donald Erb
Created on Nov 15, 2020

"""


from .fitting_gui import launch_fitting_gui
from .fitting_utils import r_squared
from .peak_fitting import (
    fit_peaks, plot_confidence_intervals, plot_fit_results
)
