# -*- coding: utf-8 -*-
"""Shows how to use launch_plotting_gui from mcetl.

Since no data is input into the function, it will launch a window
that will prompt the user to select the data files to open and plot.

@author: Donald Erb
Created on Sat Aug 22 17:34:39 2020

"""

from mcetl.plotting import launch_plotting_gui
from mcetl import utils, plot_utils
#import PySimpleGUI as sg

#sg.theme('darkblue10') # Changes overall theme for all windows.
#utils.PROCEED_COLOR = ('white', 'green') # Changes the color of the button used to move to the next window.
#plot_utils.CANVAS_SIZE = (500, 500) # Changes the size of the figure within the GUI.

# changes for matploblib's rcParams to change the plot format
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

output = launch_plotting_gui(mpl_changes=changes)
