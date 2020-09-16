# -*- coding: utf-8 -*-
"""
mcetl - A simple Extract-Transform-Load framework focused on materials characterization
=======================================================================================

mcetl provides user interfaces for processing data, performing peak fitting, and
plotting data.

mcetl is focused on easing the time required to process data files. It does this
by allowing the user to define DataSource objects which contains the information
for reading files for that DataSource (such as what separator to use, which
rows and columns to use, labels for the columns, etc.), the calculations that
will be performed on the data, and the options for writing the data to Excel
(formatting, placement in the worksheet, etc.).

In addition, mcetl provides peak fitting and plotting user interfaces that
can be used without creating any DataSource objects.


@author: Donald Erb
Created on Jul 15, 2020

"""


__author__ = """Donald Erb"""
__version__ = '0.1.2'


from .datasource import DataSource
from .functions import SeparationFunction, CalculationFunction, SummaryFunction
from .main_gui import launch_main_gui
from .peak_fitting_gui import launch_peak_fitting_gui
from .plotting_gui import launch_plotting_gui, load_previous_figure


# Fixes blurry tkinter windows due to weird dpi scaling in Windows os
import os
if os.name == 'nt': # nt designates Windows os
    ctypes_imported = False
    try:
        import ctypes
        ctypes_imported = True
        ctypes.OleDLL('shcore').SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass
    finally:
        if ctypes_imported:
            del ctypes
        del ctypes_imported
del os
