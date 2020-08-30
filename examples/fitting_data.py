# -*- coding: utf-8 -*-
"""Shows how to use peak_fitting_gui from mcetl.

@author: Donald Erb
Created on Sat Aug 22 17:34:39 2020

"""

import matplotlib.pyplot as plt
from mcetl import launch_peak_fitting_gui


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
    'figure.dpi': 100,
    'figure.figsize': (8, 6.5)
}

fit_results, all_data_fit = launch_peak_fitting_gui(mpl_changes=changes)


while plt.get_fignums():
    plt.pause(5) # ensures the program continues while the plots are open
    #TODO use some other waiting method, because it is quite buggy using plt.pause
