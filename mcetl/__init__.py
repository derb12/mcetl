# -*- coding: utf-8 -*-
"""
mcetl - A simplified Extract-Transform-Load framework focused on materials characterization.
============================================================================================

**mcetl** is ...describe here

Main Features
-------------
Here are just a few of the things that mcetl does well:
    list things here
    
@author: Donald Erb
Created on Wed Jul 15 23:48:02 2020

"""


__author__ = """Donald Erb"""
__version__ = '0.1.1'


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
