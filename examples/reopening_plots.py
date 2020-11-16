# -*- coding: utf-8 -*-
"""Shows how to use reopen a figure previously saved using mcetl.

@author: Donald Erb
Created on Sat Aug 22 17:34:39 2020

"""

from mcetl.plotting import load_previous_figure


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

figures = load_previous_figure(new_rc_changes=changes)
