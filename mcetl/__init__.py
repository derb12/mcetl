# -*- coding: utf-8 -*-
"""
mcetl - An Extract-Transform-Load framework focused on materials characterization
=======================================================================================

mcetl provides user interfaces for processing, fitting, and plotting data.

mcetl is focused on easing the time required to process data files. It does this
by allowing the user to define DataSource objects which contains the information
for reading files for that DataSource (such as what separator to use, which
rows and columns to use, labels for the columns, etc.), the calculations that
will be performed on the data, and the options for writing the data to Excel
(formatting, placement in the worksheet, etc.).

In addition, mcetl provides fitting and plotting user interfaces that
can be used without creating any DataSource objects.

Subpackages include:

    :mod:`mcetl.fitting`
        Contains functions that ease the fitting of data. The main entry is through
        mcetl.fitting.launch_fitting_gui, but also contains useful functions without
        needing to launch a GUI.
    :mod:`mcetl.plotting`
        Contains functions that ease the plotting of data. The main entry is through
        mcetl.plotting.launch_plotting_gui. Can also reopen a previouly saved figure
        using mcetl.plotting.load_previous_figure.

@author: Donald Erb
Created on Jul 15, 2020

"""


__version__ = '0.3.0'


from .data_source import DataSource
from .functions import CalculationFunction, PreprocessFunction, SummaryFunction
from .main_gui import launch_main_gui
from .utils import set_dpi_awareness
from . import excel_writer, file_organizer
