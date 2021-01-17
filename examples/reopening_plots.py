# -*- coding: utf-8 -*-
"""Shows how to use reopen a figure previously saved using mcetl.

@author: Donald Erb
Created on Aug 22, 2020

"""

from mcetl import plotting, set_dpi_awareness


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

#set dpi awareness so GUI is not blurry on Windows os
set_dpi_awareness()

figures = plotting.load_previous_figure(new_rc_changes=changes)
