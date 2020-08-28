# -*- coding: utf-8 -*-
"""Shows how to use plotting_gui from mcetl.

@author: Donald Erb
Created on Sat Aug 22 17:34:39 2020

"""


import PySimpleGUI as sg
from mcetl.plotting_gui import configure_plots
import mcetl.utils as utils


# changes some defaults for the plot formatting
changes = {
    'font.serif': 'Times New Roman',
    'font.family': 'serif',
    'font.size': 12,
    'mathtext.default': 'regular',
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.minor.visible': True,
    'ytick.minor.visible': True,
    'xtick.major.size': 5,
    'xtick.major.width': 0.6,
    'xtick.minor.size': 2.5,
    'xtick.minor.width': 0.6,
    'ytick.major.size': 5,
    'ytick.major.width': 0.6,
    'ytick.minor.size': 2.5,
    'ytick.minor.width': 0.6,
    'lines.linewidth': 2,
    'lines.markersize': 5,
    'axes.linewidth': 0.6,
    'legend.frameon': False
}

try:
    num_files = sg.popup_get_text('Enter number of files to open', 'Get Files', '1')
    if num_files:
        dataframes = []
        for _ in range(int(num_files)):
        #gets the values needed to import a datafile, and then imports the data to a dataframe
            import_values = utils.select_file_gui()
            dataframes.append(
                utils.raw_data_import(import_values, import_values['file'], False)
            )
        
        for dataset in dataframes:
            for dataframe in dataset:
                dataframe.columns = [f'Column {num}' for num in range(len(dataframe.columns))]
        figures = configure_plots(dataframes, changes)

except utils.WindowCloseError:
    pass
except KeyboardInterrupt:
    pass
