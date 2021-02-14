# -*- coding: utf-8 -*-
"""Provides utility functions, classes, and constants for plotting.

Separated from utils.py to reduce import load time since matplotlib imports
are not needed for base usage. Useful functions are put here in order to
prevent circular importing within the other files.

@author: Donald Erb
Created on Nov 11, 2020

Attributes
----------
CANVAS_SIZE : tuple(int, int)
    A tuple specifying the size (in pixels) of the figure canvas used in
    various GUIs for mcetl. This can be modified if the user wishes a
    larger or smaller canvas. The default is (500, 500).

"""

from pathlib import Path
import traceback
import warnings

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt
import numpy as np
import wx

from . import gui_utils
from . import utils


CANVAS_SIZE = (500, 500)


class Toolbar(NavigationToolbar2WxAgg):
    """
    A toolbar that also displays the selected tool and coordinates.

    Parameters
    ----------
    canvas : FigureCanvasWxAgg
        The canvas for the toolbar.
    figure_dpi : float, optional
        The dpi to use when saving the figure. Default is None, which will use
        the matplotlib.pyplot.rcParams['figure.dpi'] value.
    **kwargs
        Any additional keyword arguments to initialize NavigationToolbar2WxAgg.
        None until matplotlib v3.3.0, and then coordinates became a kwarg.
        However, this subclass defines its own set_message method, so coordinates
        will be forced to be False since matplotlib's implementation causes
        issues with user-added items.

    """

    def __init__(self, canvas, figure_dpi=None, **kwargs):
        if kwargs.get('coordinates', False):
            warnings.warn((
                'coordinates=True is not allowed for this Toolbar.'
                ' Setting coordinates=False'
            ))
        try:
            kwargs['coordinates'] = False
            super().__init__(canvas, **kwargs)
        except TypeError:  # matplotlib version < 3.3
            kwargs.pop('coordinates', None)
            super().__init__(canvas, **kwargs)

        if figure_dpi is None:
            self.figure_dpi = plt.rcParams['figure.dpi']
        else:
            self.figure_dpi = figure_dpi

        self.AddSeparator()
        self.message_output = wx.StaticText(self)
        self.AddControl(self.message_output)
        self.Realize()

    def set_message(self, s):
        """
        Sets the message on the toolbar.

        Overrides the super class's method since the behavior is inconsistent
        between matplotlib versions.

        Parameters
        ----------
        s : str
            The message to print on the toolbar.

        """
        current = self.message_output.GetLabel()
        # in matplotlib versions <3.3, message would be "tool, x=..y=.." but
        # in matplotlib v3.3, message became "x=..y=.." without the tool entry
        if current and s.startswith('x') and not current.startswith('x'):
            s = gui_utils.split_entry(current)[0] + ', ' + s
        self.message_output.SetLabel(s)

    def save_figure(self, *args, **kwargs):
        """
        Called when the Save button is pressed on the toolbar.

        Opens a custom dialog to select the output file and any possible
        compression options for the selected file type.

        Parameters
        ----------
        *args
            Arguments passed to save_figure by the toolbar. Not used in
            the super class's implementation, but added just to be safe.
        **kwargs
            Keyword arguments passed to save_figure by the toolbar. Not used
            in the super class's implementation, but added just to be safe.

        """
        with SaveFigureDialog(self, self._get_filetypes()) as dialog:
            response = dialog.ShowModal()
            if response in (wx.ID_OK, wx.ID_SAVE):
                file_path, pil_kwargs = dialog.get_value()
                if pil_kwargs:
                    kwargs = {'pil_kwargs': pil_kwargs}
                else:  # unused keyword arguments give warnings after matplotlib v3.3
                    kwargs = {}
                try:
                    self.canvas.figure.savefig(file_path, dpi=self.figure_dpi, **kwargs)
                except Exception:
                    with wx.MessageDialog(
                        self,
                        (f'Save Failed. The format "{Path(file_path).suffix}" may '
                         f'require additional setup.\n\n    {traceback.format_exc()}'),
                        'Save Failed', style=wx.OK | wx.ICON_ERROR
                    ) as dlg:
                        dlg.ShowModal()
                else:
                    with wx.MessageDialog(
                        self, f'Saved figure to {file_path}', 'Save Succeeded'
                    ) as dlg:
                        dlg.ShowModal()

    def _get_filetypes(self):
        """
        Returns the search terms for use with wxPython's file browse dialog.

        Also removes the extensions that are unavailable.

        """
        file_extensions = self.canvas.get_supported_filetypes_grouped()
        # extensions added by matplotlib.backends.backend_wx._FigureCanvasWxBase,
        # but are actually only valid for matplotlib.backends.backend_wx.FigureCanvasWx,
        # not matplotlib.backends.backend_wxagg.FigureCanvasWxAgg
        unused_extensions = ['PCX', 'Windows bitmap', 'X pixmap']
        if not utils.check_availability('PIL'):
            # FigureCanvasAgg only succports jpeg and tiff if Pillow is available
            unused_extensions.extend(['JPEG', 'Tagged Image Format File'])
        for extension in unused_extensions:
            file_extensions.pop(extension, None)

        # name is like "Tagged Image Format File" and file_exts are like ['tif', 'tiff']
        file_types = []
        for name, file_exts in sorted(file_extensions.items()):
            extension_list = [f'*.{extension}' for extension in file_exts]
            search_extensions = ';'.join(extension_list)
            shown_extensions = ', '.join(extension_list)
            file_types.append(f'{name} ({shown_extensions})|{search_extensions}')
        return '|'.join(file_types)


class SaveFigureDialog(wx.Dialog):
    """
    A dialog for selecting the file name and compression options for saving figures.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the dialog.
    file_types : str, optional
        The file extensions to allow. Input must be like
        'display_name_1|extension_1|display_name_2|extension_2', like
        'PNG File|*.png|JPEG File|*.jpg;*.jpeg'.

    """

    def __init__(self, parent, file_types):
        super().__init__(parent, title='Save Figure')

        self.path = None

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(h_sizer, 0, wx.EXPAND | wx.ALL, border=5)
        display = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        h_sizer.Add(display, 1, wx.ALL, border=3)
        self.save_as = gui_utils.FileSaveButton(
            self.panel, display, overwrite=True, file_types=file_types,
            id=wx.ID_SAVEAS
        )
        self.save_as.Bind(wx.EVT_BUTTON, self.on_saveas)
        h_sizer.Add(self.save_as, 0, wx.ALL, border=3)

        self.extra_panels = {}
        if utils.check_availability('PIL'):
            self.pane = wx.CollapsiblePane(self.panel, label='Additional Options')
            self.pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._on_pane)
            self.sizer.Add(self.pane, 0, wx.EXPAND | wx.ALL, 5)
            self._add_extra_panels(self.pane.GetPane())

        self.sizer.Add((10, 20), wx.ALL)
        btn_sizer = wx.StdDialogButtonSizer()
        self.sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        cancel_btn = wx.Button(self.panel, wx.ID_CANCEL)
        cancel_btn.SetDefault()
        btn_sizer.AddButton(cancel_btn)
        save_btn = wx.Button(self.panel, wx.ID_SAVE)
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sizer.AddButton(save_btn)
        btn_sizer.Realize()

        self.SetAffirmativeId(save_btn.GetId())
        self.SetEscapeId(cancel_btn.GetId())

        self.panel.SetSizer(self.sizer)
        self.sizer.SetMinSize((self.GetSize()[0], -1))
        for panel in self.extra_panels.values():
            panel.Show(False)

        self.sizer.Fit(self)

    def _add_extra_panels(self, pane):
        """Adds panels with additional save options to the collapsible pane."""
        pane_sizer = wx.BoxSizer(wx.VERTICAL)

        jpeg_panel = wx.Panel(pane)
        pane_sizer.Add(jpeg_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        jpeg_sizer = wx.BoxSizer(wx.VERTICAL)
        self.jpeg_check_1 = wx.CheckBox(jpeg_panel, label='Optimize')
        self.jpeg_check_1.SetValue(1)
        jpeg_sizer.Add(self.jpeg_check_1, 0, wx.ALL, 5)
        self.jpeg_check_2 = wx.CheckBox(jpeg_panel, label='Progressive')
        jpeg_sizer.Add(self.jpeg_check_2, 0, wx.ALL, 5)
        jpeg_text = wx.StaticText(jpeg_panel, label='Quality (1-95)')
        jpeg_sizer.Add(jpeg_text, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 5)
        self.jpeg_slider = wx.Slider(
            jpeg_panel, value=plt.rcParams['savefig.jpeg_quality'],
            minValue=1, maxValue=95, style=wx.SL_HORIZONTAL | wx.SL_LABELS
        )
        jpeg_sizer.Add(self.jpeg_slider, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        jpeg_panel.SetSizer(jpeg_sizer)
        self.extra_panels['jpeg'] = jpeg_panel

        png_panel = wx.Panel(pane)
        pane_sizer.Add(png_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        png_sizer = wx.BoxSizer(wx.VERTICAL)
        self.png_check_1 = wx.CheckBox(png_panel, label='Optimize')
        self.png_check_1.SetValue(1)
        png_sizer.Add(self.png_check_1, 0, wx.ALL, 5)
        png_text = wx.StaticText(png_panel, label='Compression Level')
        png_sizer.Add(png_text, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 5)
        self.png_slider = wx.Slider(
            png_panel, value=6, minValue=1, maxValue=9,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS
        )
        png_sizer.Add(self.png_slider, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        png_panel.SetSizer(png_sizer)
        self.extra_panels['png'] = png_panel

        tiff_panel = wx.Panel(pane)
        pane_sizer.Add(tiff_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        tiff_sizer = wx.BoxSizer(wx.VERTICAL)
        tiff_sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        tiff_sizer.Add(tiff_sizer_2, 0, wx.ALL, 5)
        tiff_text = wx.StaticText(tiff_panel, label='Compression')
        tiff_sizer_2.Add(tiff_text, 0, wx.ALL, 5)
        self.tiff_choice = wx.Choice(
            tiff_panel, choices=['None', 'Deflate', 'LZW', 'Pack Bits', 'JPEG']
        )
        self.tiff_choice.SetSelection(0)
        tiff_sizer_2.Add(self.tiff_choice, 0, wx.ALL, 5)
        self.tiff_choice.Bind(wx.EVT_CHOICE, self._on_tiff_choice)
        tiff_text_2 = wx.StaticText(
            tiff_panel, label='Quality (1-95) for JPEG Compression'
        )
        tiff_sizer.Add(tiff_text_2, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 5)
        self.tiff_slider = wx.Slider(
            tiff_panel, value=plt.rcParams['savefig.jpeg_quality'],
            minValue=1, maxValue=95, style=wx.SL_HORIZONTAL | wx.SL_LABELS
        )
        self.tiff_slider.Disable()
        tiff_sizer.Add(self.tiff_slider, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        tiff_panel.SetSizer(tiff_sizer)
        self.extra_panels['tiff'] = tiff_panel

        pane.SetSizer(pane_sizer)

    def _on_pane(self, event=None):
        """Resizes the dialog when the collapsible pane is folded or extended."""
        self.sizer.Fit(self)

    def _jpeg_kwargs(self):
        """Gives the kwargs for saving jpeg/jpg files."""
        return {
            'quality': self.jpeg_slider.GetValue(),
            'optimize': self.jpeg_check_1.GetValue(),
            'progressive': self.jpeg_check_2.GetValue()
        }

    def _png_kwargs(self):
        """Gives the kwargs for saving png files."""
        return {
            'compress_level': self.png_slider.GetValue(),
            'optimize': self.png_check_1.GetValue(),
        }

    def _tiff_kwargs(self):
        """Gives the kwargs for saving tiff/tif files."""
        kwargs = {
            'compression':
                {
                    'None': None, 'Deflate': 'tiff_deflate', 'LZW': 'tiff_lzw',
                    'Pack Bits': 'packbits', 'JPEG': 'jpeg'
                }[self.tiff_choice.GetStringSelection()]
        }
        if kwargs['compression'] == 'jpeg':
            kwargs['quality'] = self.tiff_slider.GetValue()

        return kwargs

    def _on_tiff_choice(self, event):
        """Enables/disables the jpeg slider depending on the selected compression type."""
        self.tiff_slider.Enable(event.GetString() == 'JPEG')

    def on_saveas(self, event):
        """Opens the file dialog to select the output file path."""
        self.save_as.on_click(event)
        old_path = self.path
        self.path = self.save_as.get_value()

        # update which panels are visible
        if self.extra_panels and old_path != self.path:
            suffix = Path(self.path).suffix.lower()
            if suffix.startswith('.'):
                suffix = suffix[1:]

            for file_type in (['jpeg', 'jpg'], ['png'], ['tiff', 'tif']):
                self.extra_panels[file_type[0]].Show(suffix in file_type)
            if self.pane.IsExpanded():
                self.pane.Collapse()
                self.pane.Collapse(False)
                self._on_pane()

    def on_save(self, event):
        """Exit the dialog if a file path has been selected."""
        if self.path is None:
            with wx.MessageDialog(self, 'Need to specify a file name.', 'Error') as dlg:
                dlg.ShowModal()
            return
        event.Skip()

    def get_value(self):
        """
        Returns the selected file path and any compression options to save the image.

        Returns
        -------
        self.path : str
            The selected file path.
        compression_options : dict
            A dictionary of compression options for the selected file extension
            to use as pil_kwargs in matplotlib.figure.Figure.savefig.

        """
        compression_options = {}
        for image_type, panel in self.extra_panels.items():
            if panel.IsShown():
                compression_options = getattr(self, f'_{image_type}_kwargs')()
                break
        return self.path, compression_options


class FixedSizeToolbar(Toolbar):
    """
    Custom toolbar without the subplots button that saves figures with a fixed size.

    The subplots button is removed so that the user does not mess with
    the plot layout since it is handled by using matplotlib's tight layout.

    Parameters
    ----------
    canvas : FigureCanvasWxAgg
        The canvas for the toolbar.
    figure_dpi : float, optional
        The dpi to use when saving the figure. Default is None, which will use
        the matplotlib.pyplot.rcParams['figure.dpi'] value.
    figure_size : tuple(float, float), optional
        The size, in inches, to set the figure to when saving. If None, will
        use the figure's size when this toolbar is initialized.
    **kwargs
        Any additional keyword arguments to pass to NavigationToolbar2Tk.

    """

    toolitems = tuple(
        ti for ti in NavigationToolbar2WxAgg.toolitems if ti[0] not in ('Subplots',)
    )

    def __init__(self, canvas, figure_dpi=None, figure_size=None, **kwargs):
        super().__init__(canvas, figure_dpi, **kwargs)

        if figure_size is None:
            self.figure_size = self.canvas.figure.get_size_inches()
        else:
            self.figure_size = figure_size

    def save_figure(self, *args, **kwargs):
        """
        Called when the Save button is pressed on the toolbar.

        Resizes the figure to self.figure_size, opens a custom dialog to
        select the output file and any possible compression options for
        the selected file type, and then resizes the figure back to its
        initial size.

        Parameters
        ----------
        *args
            Arguments passed to save_figure by the toolbar. Not used in
            the super class's implementation, but added just to be safe.
        **kwargs
            Keyword arguments passed to save_figure by the toolbar. Not used
            in the super class's implementation, but added just to be safe.

        Notes
        -----
        Use Freeze and Thaw on the canvas so that the resizing is not actually
        shown to the user.

        """
        start_size = self.canvas.figure.get_size_inches()
        self.canvas.Freeze()
        self.canvas.figure.set_size_inches(self.figure_size)
        super().save_figure(*args, **kwargs)
        self.canvas.figure.set_size_inches(start_size)
        self.canvas.draw_idle()
        self.canvas.Thaw()


class FigureCanvas(FigureCanvasWxAgg):
    """
    A figure canvas that has default event handlers attached.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the canvas.
    id : int, optional
        The id to assign to the canvas. Leave as is to use the default id
        assigned by wx.
    figure : matplotlib.figure.Figure, optional
        The figure that will be drawn on the canvas. If None, will create a
        new Figure.
    enable_events : bool, optional
        If True (default), will add the default events to self.events (default
        events are self._on_click, self._on_pick, and self._on_key)
        to canvas. If False, self.events will be an empty list.
    enable_keybinds : bool, optional
        If True (default), will add the matplotlib keybind events to
        the self.events.
    axis : plt.Axes, optional
        The axis on the figure which will be used by the default events. If
        None is given, defaults to the first axis of the figure (figure.axes[0]).
    selected_points : list, optional
        A list of selected points on the plot. Used by the default events to
        keep track of selected points.

    Notes
    -----
    To connect events to the canvas, must call the connect_events() method. This is
    done so that events can be alterred before they are connected to the canvas.

    The default events for this class will allow creating circles on a left-double-click,
    selecting created circles with a left or right click, and deleting selected circles
    with a right-double-click or pressing the delete key.

    """

    def __init__(self, parent, id=wx.ID_ANY, figure=None, enable_events=True, enable_keybinds=True,
                 selected_points=None, axis=None):
        if figure is None:
            figure = Figure()
        super().__init__(parent, id, figure)

        self.selected_points = selected_points if selected_points is not None else []
        if axis is not None:
            self._axis = axis
        elif figure.axes:
            self._axis = figure.axes[0]
        else:  # initialized from toolbar's configure subplot tool
            self._axis = None
        # set limits so that patches created by self are always the same
        # dimension and not dependent on the axis limits
        if self._axis is not None:
            self._xaxis_limits = self._axis.get_xlim()
            self._yaxis_limits = self._axis.get_ylim()
        else:
            self._xaxis_limits = (0, 1)
            self._yaxis_limits = (0, 1)
        self._cids = []  # references to connection ids for events
        self._picked_object = None  # used for pick events

        if not enable_events:
            self.events = []
        else:
            # some default events; can be alterred after init
            self.events = [
                ('button_press_event', 'on_click'),
                ('pick_event', 'on_pick'),
                ('key_press_event', 'on_key')
            ]
        if enable_keybinds:
            self.events.append(('key_press_event', 'on_keypress'))

    def connect_events(self):
        """
        Connects all events in self.events and disconnects any previous connections.

        Notes
        -----
        This is not done in __init__ so that the events can be alterred first.
        The callback in self.events can either be a callable, or a string
        corresponding to an attribute of self (the canvas).

        """
        for connection_id in self._cids:
            self.mpl_disconnect(connection_id)

        self._cids = []
        for (event_name, callback) in self.events:
            if callable(callback):
                function = callback
            else:
                function = getattr(self, callback)
            self._cids.append(self.mpl_connect(event_name, function))

    def on_keypress(self, event):
        """
        The keypress handler to use for Matplotlib's default keypress events.

        Parameters
        ----------
        event : matplotlib.backend_bases.KeyEvent
            The key_press_event event.

        """
        key_press_handler(event, canvas=self, toolbar=self.toolbar)

    def _update_plot(self):
        """Updates the plot after events on the matplotlib figure."""
        self.draw_idle()

    def _remove_circle(self):
        """Removes the selected circle from the axis."""
        coords = self._picked_object.get_center()
        for i, value in enumerate(self.selected_points):
            if all(np.isclose(value, coords)):
                del self.selected_points[i]
                break

        self._picked_object.remove()
        self._picked_object = None

    def on_click(self, event):
        """
        The function to be executed whenever this is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        1) If the button press is not within the self.axis, then nothing is done.
        2) If a double left click is done, then a circle is placed on self.axis.
        3) If a double right click is done and a circle is selected, then the circle
           is deleted from the self.axis.
        4) If a single left or right click is done, it deselects any selected circle
           if the click is not on the circle.

        """
        if event.inaxes == self._axis:
            if event.dblclick:  # a double click
                # left click
                if event.button == 1:
                    self.selected_points.append([event.xdata, event.ydata])
                    self._create_circle(event.xdata, event.ydata)
                    self._update_plot()

                # right click
                elif event.button == 3 and self._picked_object is not None:
                    self._remove_circle()
                    self._update_plot()

            # left or right single click
            elif (event.button in (1, 3) and self._picked_object is not None
                    and not self._picked_object.contains(event)[0]):
                self._picked_object.set_facecolor('green')
                self._picked_object = None
                self.draw_idle()

    def on_pick(self, event):
        """
        The function to be executed whenever there is a button press event.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The button_press_event event.

        Notes
        -----
        If a circle is selected, its color will change from green to red.
        It assigns the circle artist as the attribute self.picked_object.

        """
        if self._picked_object is not None and self._picked_object != event.artist:
            self._picked_object.set_facecolor('green')
            self._picked_object = None

        self._picked_object = event.artist
        self._picked_object.set_facecolor('red')
        self.draw_idle()

    def on_key(self, event):
        """
        The function to be executed if a key is pressed.

        Parameters
        ----------
        event : matplotlib.backend_bases.KeyEvent
            key_press_event event.

        Notes
        -----
        If the 'delete' key is pressed and a self.picked_object is not None,
        the selected artist will be removed from self.axis and the plot will
        be updated.

        """
        if event.key == 'delete' and self._picked_object is not None:
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
        circle_width = 0.04 * (self._xaxis_limits[1] - self._xaxis_limits[0])
        circle_height = 0.04 * (self._yaxis_limits[1] - self._yaxis_limits[0])
        # scale the height based on the axis width/height ratio to get perfect circles
        circle_height *= self._axis.bbox.width / self._axis.bbox.height

        self._axis.add_patch(
            Ellipse((x, y), circle_width, circle_height, edgecolor='black',
                    facecolor='green', picker=True, zorder=3, alpha=0.7)
        )


class EmbeddedFigure(wx.Dialog):
    """
    A simple dialog for displaying a plot and simple controls.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the frame.
    figure : matplotlib.figure.Figure
        The figure to place on the canvas.
    canvas_kwargs : dict, optional
        A dictionary of keyword arguments to use for creating FigureCanvas.
    toolbar_class : NavigationToolbar2WxAgg, optional
        The toolbar class to use. Default is Toolbar.
    toolbar_kwargs : dict, optional
        A dictionary of keyword arguments to use for creating the toolbar.
    **kwargs
        Any additional keyword arguments to use for initializing wx.Dialog.
    This class allows easy subclassing to create simple windows with
    embedded matplotlib figures.

    Notes
    -----
    A typical __init__ for a subclass would resemble the example
    below (note that plt designates matplotlib.pyplot)

    >>> class SimpleEmbeddedFigure(EmbeddedFigure):
            def __init__(x, y, parent=None, **kwargs):
                super().__init__(parent, **kwargs)
                self.figure, self.axis = plt.subplots()
                self.axis.plot(x, y)
                self.canvas_panel = wx.Panel(self)
                self.sizer = wx.BoxSizer(wx.VERTICAL)
                self.canvas_panel.SetSizer(self.sizer)
                self.create_canvas(self.figure, self.canvas_panel, self.sizer)
                self.finalize()

    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = None
        self.toolbar = None

    def create_canvas(self, figure, canvas_parent, sizer, canvas_kwargs=None,
                      toolbar_class=Toolbar, toolbar_kwargs=None, toolbar_on_top=True):
        """
        Creates the toolbar and canvas and places them onto the parent widget.

        figure : matplotlib.figure.Figure
            The figure to place on the canvas.
        canvas_parent : wx.Window
            The parent widget for the figure canvas.
        sizer : wx.Sizer
            The sizer item to use for placing the canvas and toolbar into the
            frame.
        canvas_kwargs : dict, optional
            A dictionary of keyword arguments to use for creating FigureCanvas.
        toolbar_class : NavigationToolbar2WxAgg, optional
            The toolbar class to use. Default is Toolbar. If None, then no toolbar
            will be created.
        toolbar_kwargs : dict, optional
            A dictionary of keyword arguments to use for creating the toolbar.
        toolbar_on_top : bool, optional
            If True (default), will place the toolbar above the figure canvas. If
            False, will place the toolbar below the figure canvas.

        """
        canvas_kwargs = canvas_kwargs if canvas_kwargs is not None else {}
        toolbar_kwargs = toolbar_kwargs if toolbar_kwargs is not None else {}

        self.canvas = FigureCanvas(canvas_parent, figure=figure, **canvas_kwargs)
        if toolbar_class is None:
            sizer.Add(self.canvas, 1, wx.EXPAND)
        else:
            self.toolbar = toolbar_class(self.canvas, **toolbar_kwargs)
            if toolbar_on_top:
                sizer.Add(self.toolbar, 0, wx.EXPAND)
                sizer.Add(self.canvas, 1, wx.EXPAND)
            else:
                sizer.Add(self.canvas, 1, wx.EXPAND)
                sizer.Add(self.toolbar, 0, wx.EXPAND)

    def finalize(self):
        """
        Connects events for the canvas and sets the size for the frame.

        Returns
        -------
        self : EmbeddedFigure
            Returns self so that it can be chained.

        Notes
        -----
        Need to set canvas's MinSize because
        matplotlib.backends.backend_wx._FigureCanvasWxBase will use the
        MinSize to limit how small the figure can get when resizing. If not
        set, the MinSize will be the initial size of the canvas, so the canvas
        would not be allowed to shrink properly. Also have to set MinSize
        after fitting the frame with the sizer; otherwise, the sizer would
        use the canvas's MinSize as its initial size.

        """
        if self.canvas is None:
            raise ValueError('Must initialize canvas with create_canvas().')

        self.canvas.connect_events()
        self.sizer.Fit(self)
        self.canvas.SetMinSize((200, 200))  # 200x200 px should be small enough

        return self


def get_dpi_correction(dpi):
    """
    Calculates the correction factor needed to create a figure with the desired dpi.

    Necessary because some matplotlib backends (namely qt5Agg) will adjust
    the dpi of the figure after creation. Only use if creating figures through
    matplotlib.pyplot.

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
    This function should only be used if creating figures through pyplot,
    since that scales the dpi based on the matplotlib backend. If directly
    creating figures through matplotlib.figure.Figure, then do not need this
    dpi correction.

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


def determine_dpi(fig_height, fig_width, dpi, canvas_size=CANVAS_SIZE):
    """
    Gives the correct dpi to fit the figure within the GUI canvas.

    Parameters
    ----------
    fig_height : float
        The figure height.
    fig_width : float
        The figure width.
    dpi : float
        The desired figure dpi.
    canvas_size : tuple(int, int), optional
        The size of the canvas that the figure will be placed on.
        Defaults to CANVAS_SIZE.

    Returns
    -------
    float
        The correct dpi to fit the figure onto the GUI canvas.

    Notes
    -----
    The dpi needs to be scaled to fit the figure on the GUI's canvas, and
    that scaling is called size_scale. For example, if the desired size was
    1600 x 1200 pixels with a dpi of 300, the figure would be scaled down to
    800 x 600 pixels to fit onto the canvas, so the dpi would be changed to
    150, with a size_scale of 0.5.

    The final dpi is equal to dpi * size_scale.

    """
    return dpi * min(canvas_size[0] / fig_width, canvas_size[1] / fig_height)


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
