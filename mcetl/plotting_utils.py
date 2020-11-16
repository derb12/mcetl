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


class EmbeddedFigure:
    """
    Class defining a PySimpleGUI window with an embedded matplotlib Figure.

    Class to be used to define BackgroundSelector and PeakSelector
    classes, which share common functions.

    Parameters
    ----------
    x : array-like
        The x-values to be plotted.
    y : array-like
        The y-values to be plotted.
    click_list : list, optional
        A list of selected points on the plot.

    Attributes
    ----------
    x : array-like
        The x-values to be plotted.
    y : array-like
        The y-values to be plotted.
    click_list : list
        A list of selected points on the plot.
    figure : plt.Figure
        The figure embedded in the window.
    axis : plt.Axes
        The main axis on the figure which owns the events.
    canvas : sg.Canvas
        The PySimpleGUI canvas element in the window which contains the figure.
    toolbar_canvas : sg.Canvas
        The PySimpleGUI canvas element that contains the toolbar for the figure.
    picked_object : plt.Artist
        The selected Artist objected on the figure.
    xaxis_limits : tuple
        The x axis limits when the figure is first created. The values
        are used to determine the size of the Ellipse place by the
        _create_circle function. The initial limits are used so that
        zooming on the figure does not change the size of the Ellipse.
    yaxis_limits : tuple
        The y axis limits when the figure is first created.
    enable_events : bool
        If True, will enable the embedded matplotlib figure to connect
        events.
    toolbar_class : NavigationToolbar2Tk
        The class of the toolbar to place in the window. The default
        is PeakFittingToolbar.
    window : sg.Window
        The PySimpleGUI window containing the figure.

    Notes
    -----
    This class allows easy subclassing to create simple windows with
    embedded matplotlib figures.

    The only function that should be publically available is the
    event_loop method, which should return the desired output.

    To close the window, use the internal _close method, which ensures
    that both the window and the figure are correctly closed.

    """

    def __init__(self, x, y, click_list=None):

        self.x = np.array(x, float)
        self.y = np.array(y, float)
        self.click_list = click_list if click_list is not None else []

        self.toolbar_class = PeakFittingToolbar
        self.figure = None
        self.axis = None
        self.window = None
        self.canvas = None
        self.toolbar_canvas = None
        self.picked_object = None
        self.xaxis_limits = (0, 1)
        self.yaxis_limits = (0, 1)
        self.enable_events = True


    def event_loop(self):
        """Handles the event loop for the GUI."""


    def _create_window(self):
        """Creates the GUI."""


    def _update_plot(self):
        """Updates the plot after events on the matplotlib figure."""


    def _remove_circle(self):
        """Removes the selected circle from the axis."""


    def _on_click(self, event):
        """The function to be executed whenever this is a button press event."""


    def _on_pick(self, event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        If a circle is selected, its color will change from green to red.
        It assigns the circle artist as the attribute 'picked_object' to the ax axis,
        which is just an easy way to keep the axis and the objects lumped together.

        """

        if self.picked_object is not None and self.picked_object != event.artist:
            self.picked_object.set_facecolor('green')
            self.picked_object = None

        self.picked_object = event.artist
        self.picked_object.set_facecolor('red')
        self.figure.canvas.draw_idle()


    def _on_key(self, event):
        """
        The function to be executed if a key is pressed.

        Parameters
        ----------
        event : matplotlib.backend_bases.KeyEvent
            key_press_event event.

        Notes
        -----
        If the 'delete' key is pressed and a circle is selected, the circle
        will be removed from self.axis and the plot will be updated.

        """

        if event.key == 'delete' and self.picked_object is not None:
            self._remove_circle()
            self._update_plot()


    def _create_circle(self, x, y):
        """
        Places a circle at the designated x, y position.

        Parameters
        ----------
        x : float
            The x position to place the center of the circle.
        y : float
            The y position to place the center of the circle.

        """

        circle_width = 0.03 * (self.xaxis_limits[1] - self.xaxis_limits[0])
        circle_height = 0.03 * (self.yaxis_limits[1] - self.yaxis_limits[0])
        # scale the height based on the axis width/height ratio to get perfect circles
        circle_height *= self.axis.bbox.width / self.axis.bbox.height

        self.axis.add_patch(
            Ellipse((x, y), circle_width, circle_height, edgecolor='black',
                    facecolor='green', picker=True)
        )


    def _place_figure_on_canvas(self):
        """Places the figure and toolbar onto the PySimpleGUI canvas."""

        if self.toolbar_canvas is not None:
            toolbar_canvas = self.toolbar_canvas.TKCanvas
        else:
            toolbar_canvas = None

        draw_figure_on_canvas(self.canvas.TKCanvas, self.figure,
                              toolbar_canvas, self.toolbar_class)

        if self.enable_events:
            # create references (_cid#) to the connections so they are not garbage collected
            self._cid1 = self.figure.canvas.mpl_connect('button_press_event', self._on_click)
            self._cid2 = self.figure.canvas.mpl_connect('pick_event', self._on_pick)
            self._cid3 = self.figure.canvas.mpl_connect('key_press_event', self._on_key)


    def _close(self):
        """Safely stops the event loop and closes the window and figure."""

        if self.window is not None:
            try:
                self.window.TKroot.quit() # exits GUI's event loop first
            except AttributeError:
                pass # window's root was already destroyed
            else:
                self.window.close()
            finally:
                self.window = None

        plt.close(self.figure)
        self.figure = None


def draw_figure_on_canvas(canvas, figure, toolbar_canvas=None,
                          toolbar_class=PlotToolbar, kwargs=None):
    """
    Places the figure and toolbar onto the PySimpleGUI canvas.

    Parameters
    ----------
    canvas : tkinter.Canvas
        The tkinter Canvas element for the figure.
    figure : plt.Figure
        The figure to be place on the canvas.
    toolbar_canvas : tkinter.Canvas, optional
        The tkinter Canvas element for the toolbar.
    toolbar_class : NavigationToolbar2Tk, optional
        The toolbar class used to create the toolbar for the figure. The
        default is PlotToolbar.
    kwargs : dict, optional
        Keyword arguments designating how to pack the figure into the window.

    Notes
    -----
    The canvas children are destroyed after drawing the canvas so that
    there is a seamless transition from the old canvas to the new canvas.

    """

    if kwargs is None:
        kwargs = {'side': 'top', 'anchor': 'nw'}

    figure_canvas = FigureCanvasTkAgg(figure, master=canvas)
    try:
        figure_canvas.draw()
        figure_canvas.get_tk_widget().pack(**kwargs)
    except Exception as e:
        create_toolbar = False
        sg.popup(
            ('Exception occurred during figure creation. Could be due to '
             f'incorrect Mathtext usage.\n\nError:\n    {repr(e)}\n'),
            title='Plotting Error'
        )
    else:
        create_toolbar = True
    finally:
        for child in canvas.winfo_children()[:-1]:
            child.destroy()

    if toolbar_canvas is not None:
        if create_toolbar:
            toolbar = toolbar_class(figure_canvas, toolbar_canvas)
            toolbar.update()
            last_index = -1 if toolbar_canvas is not canvas else -2
        else:
            last_index = None

        for child in toolbar_canvas.winfo_children()[:last_index]:
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


def scale_axis(axis_bounds, lower_scale=None, upper_scale=None):
    """
    Calculates the new bounds to scale the current axis bounds.

    The new bounds are calculated by multiplying the desired scale factor
    by the current difference of the upper and lower bounds, and then
    adding (for upper bound) or subtracting (for lower bound) from
    the current bound.

    Parameters
    ----------
    axis_bounds : tuple(float, float)
        The current lower and upper axis bounds.
    lower_scale : float, optional
        The desired fraction by which to scale the current lower bound.
        If None, will not scale the current lower bounds.
    upper_scale : float, optional
        The desired fraction by which to scale the current upper bound.
        If None, will not scale the current upper bounds.

    Returns
    -------
    lower_bound : float
        The lower bound after scaling.
    upper_bound : float
        The upper bound after scaling.

    """

    l_scale = lower_scale if lower_scale is not None else 0
    u_scale = upper_scale if upper_scale is not None else 0

    difference = axis_bounds[1] - axis_bounds[0]

    lower_bound = axis_bounds[0] - (l_scale * difference)
    upper_bound = axis_bounds[1] + (u_scale * difference)

    return lower_bound, upper_bound
