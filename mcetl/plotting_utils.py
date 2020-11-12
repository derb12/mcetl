# -*- coding: utf-8 -*-
"""Provides utility functions, classes, and constants for plotting.

Useful functions are put here in order to prevent circular importing
within the other files.

@author: Donald Erb
Created on Nov 11, 2020

Attributes
----------
CANVAS_SIZE : tuple(int, int)
    A tuple specifying the size (in pixels) of the figure canvas in the GUI.
    This can be modified if the user wishes a larger or smaller canvas.

"""


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt
import numpy as np
import PySimpleGUI as sg


CANVAS_SIZE = (800, 800)


class PeakFittingToolbar(NavigationToolbar2Tk):
    """
    Custom toolbar without the subplots button.

    The subplots button is removed so that the user does not mess with the
    plot layout since it is handled by using matplotlib's tight layout.

    Parameters
    ----------
    fig_canvas : matplotlib.FigureCanvas
        The figure canvas on which to operate.
    canvas : tkinter.Canvas
        The Canvas element which owns this toolbar.

    """

    def __init__(self, fig_canvas, canvas):

        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),
            ('Save', 'Save the figure', 'filesave', 'save_figure')
        )

        super().__init__(fig_canvas, canvas)


class PlotToolbar(NavigationToolbar2Tk):
    """
    Custom toolbar without the subplots and save figure buttons.

    Ensures that saving is done through the save menu in the window, which
    gives better options for output image quality and ensures the figure
    dimensions are correct. The subplots button is removed so that the
    user does not mess with the plot layout since it is handled by using
    matplotlib's tight layout.

    Parameters
    ----------
    fig_canvas : matplotlib.FigureCanvas
        The figure canvas on which to operate.
    canvas : tkinter.Canvas
        The Canvas element which owns this toolbar.

    """

    def __init__(self, fig_canvas, canvas):

        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        )

        super().__init__(fig_canvas, canvas)


def draw_figure_on_canvas(canvas, figure, toolbar_canvas=None, toolbar_class=PlotToolbar):
    """
    Places the figure and toolbar onto the PySimpleGUI canvas.

    Parameters
    ----------
    canvas : sg.Canvas
        The PySimpleGUI Canvas element for the figure.
    figure : plt.Figure
        The figure to be place on the canvas.
    toolbar_canvas : sg.Canvas, optional
        The PySimpleGUI Canvas element for the toolbar.
    toolbar_class : NavigationToolbar2Tk, optional
        The toolbar class used to create the toolbar for the figure. The
        default is PlotToolbar.

    Notes
    -----
    The canvas children are destroyed after drawing the canvas so that
    there is a seamless transition from the old canvas to the new canvas.

    """

    figure_canvas = FigureCanvasTkAgg(figure, master=canvas)
    try:
        figure_canvas.draw()
        figure_canvas.get_tk_widget().pack(side='left', anchor='nw')
    except Exception as e:
        sg.popup(
            ('Exception occurred during figure creation. Could be due to '
             f'incorrect Mathtext usage.\n\nError:\n    {repr(e)}\n'),
            title='Plotting Error'
        )
    finally:
        for child in canvas.winfo_children()[:-1]:
            child.destroy()

    if toolbar_canvas is not None:
        toolbar = toolbar_class(figure_canvas, toolbar_canvas)
        toolbar.update()
        for child in toolbar_canvas.winfo_children()[:-1]:
            child.destroy()


def get_dpi_correction(dpi):
    """
    Calculates the correction factor needed to create a figure with the desired dpi.

    Necessary because some matplotlib backends (namely qt5Agg) will adjust
    the dpi of the figure after creation.

    Parameters
    ----------
    dpi : float or int
        The desired figure dpi.

    Returns
    -------
    dpi_correction : float
        The scaling factor needed to create a figure with the desired dpi.

    Notes
    -----
    The matplotlib dpi correction occurs when the operating system display
    scaling is set to any value not equal to 100% (at least on Windows,
    other operating systems are unknown). This may cause issues when
    using UHD monitors, but I cannot test.

    To get the desired dpi, simply create a figure with a dpi equal
    to dpi * dpi_correction.

    """

    with plt.rc_context({'interactive': False}):
        dpi_correction = dpi / plt.figure('dpi_corrrection', dpi=dpi).get_dpi()
        plt.close('dpi_corrrection')

    return dpi_correction


def determine_dpi(fig_kwargs=None):
    """
    Gives the correct dpi to fit the figure within the GUI canvas.

    Parameters
    ----------
    fig_kwargs : dict, optional
        Keyword arguments for creating the figure.

    Returns
    -------
    float
        The correct dpi to fit the figure onto the GUI canvas.

    """

    fig_kwargs = fig_kwargs if fig_kwargs is not None else {
        'fig_width': plt.rcParams['figure.figsize'][0] * plt.rcParams['figure.dpi'],
        'fig_height': plt.rcParams['figure.figsize'][1] * plt.rcParams['figure.dpi'],
        'dpi': plt.rcParams['figure.dpi']
    }
    dpi_scale = get_dpi_correction(fig_kwargs['dpi'])

    if fig_kwargs['fig_width'] >= fig_kwargs['fig_height']:
        size_scale = CANVAS_SIZE[0] / fig_kwargs['fig_width']
    else:
        size_scale = CANVAS_SIZE[1] / fig_kwargs['fig_height']

    return fig_kwargs['dpi'] * dpi_scale * size_scale
