# -*- coding: utf-8 -*-
"""
mcetl.fitting - Functions and GUI to help fit data
==================================================

Contains functions that ease the fitting of data. The main entry is through
mcetl.fitting.launch_fitting_gui, but also contains useful functions without
needing to launch a GUI.

@author: Donald Erb
Created on Nov 15, 2020

"""


from .fitting_gui import launch_fitting_gui
from .fitting_utils import print_available_models, r_squared, r_squared_model_result
from .peak_fitting import fit_peaks, plot_confidence_intervals, plot_fit_results
from . import models
