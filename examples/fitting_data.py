# -*- coding: utf-8 -*-
"""Shows how to use launch_fitting_gui from mcetl.

Since no data is input into the function, it will launch a window
that will prompt the user to select the data files to open and fit.

@author: Donald Erb
Created on Sat Aug 22 17:34:39 2020

"""

import matplotlib.pyplot as plt
from mcetl.fitting import launch_fitting_gui


# changes some defaults for the plot formatting so it looks nice
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
    'legend.frameon': False,
    'figure.dpi': 150,
    'figure.figsize': (6, 4.5)
}

fit_results, gui_values, all_data_fit = launch_fitting_gui(mpl_changes=changes)

# Ensures program will not end until all plots are closed
if plt.get_fignums():
    plt.show(block=True)
