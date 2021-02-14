# -*- coding: utf-8 -*-
"""Helper classes, functions, and constants for the GUI backend.

This file will contain all helper items for creating GUIs. This way,
if the GUI backend is changed again in the future, just replacing
the items in this module will ease the transition.

@author: Donald Erb
Created on Jan 25, 2021

"""

import base64
from collections.abc import Iterable
import functools
import io
import operator
from pathlib import Path
import re

import pandas as pd
import wx
import wx.grid


# the btyes representation of a png file used for the logo
_LOGO = (
    b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlz'
    b'AAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAYcSURB'
    b'VFiFvVZ7UFTXHf7uuXf33su+2OyyawABgRVBDCgLaEXxAfhOOjuhRZ12nDRp42Q6cSZpNDOpkzid'
    b'phOnTTLNaJva0am1nTqTTHR8xFSNhuADlcSJFXFRNCby2mWXx77u6/QPYAOLxDAhfH/d/X2/x/c7'
    b'e87vHAYo0fH5nhpNGfDJ3tcvAmC4/O1VrLHApWnhEAlebojd2tWKOHJ5feGvVjNJuWma3N0rB498'
    b'hLbDnfgW6DKeLmEdC4soaxJpuL1L6jvyKe6eaAcAhnVtWaOf8+YRrfezm1rHsZ+RlKo/Equ7AgwL'
    b'AKAxf1jrOvFn6dLGbfriXbWMvfJ3xFwwczg5jXzdpXYe3yY3PbN3TOHZO0qJo+YNYimuBOGZYbsW'
    b'6+rTes7vl8//eAtLbPNnss6VG6BGGJJcWsfwVrvmv7AboeYPqNynI8ZcFzHNWkiMeYVs+k9eplok'
    b'qPnPv01Dt06BwTSSlJXFiNOXEUU6qgYvxldCN/O3ReyMXxwlpoJCrd/7hRZseheBxv9o0c7rhOgy'
    b'WFvFSkTbG8C6tqwRPZSKHkqFFV6vbvaO0m96mK3nlzVdHeb5pRc+RtamacMsn73Jxa/u6BU9lOrL'
    b'D24f2T1fceo90UMpX9N8A6nr7aOWJmWJUV/2762YtirlGwFPRCiXsb5izDIuPPIn0UOpUP2/u7A/'
    b'bkrk+aXnTokeSvmKk3vixtQldmHVV/2ih1KubP/WcbYGAIDEv6gKJXTHl+jAyAP+QToWhe9wfyJP'
    b'NakHACjLWYZtrKG4nBHTjADA9l27/t0EjAtKH+4zGixnNw7FQu3z9nxPAROHSoPhwS8GxFzgnHoB'
    b'vouXabQjCgCwzHVPuQD46tvpQMt/AYDYyp/SuX5TPJLW5b3k5is/PcS5XljM/SACAGjtH21nDNll'
    b'jDjdyc588TRJq20AlTrAChmMIbeSYZP0aseh3RyjylEa61Ig9ytQo5ExiaReiUg9oFJP7IGVpIBE'
    b'5QAgBaWRZtn7+8/B6VcTR9WrjCF3OXmkdC0AUDkoY6D1ihK8vEdp2fnh8Hg0AdAAhMZpyAogDOBB'
    b'Irih+H4AygOjU5fYuaQ5s6ESvSJdbcbXZ74ap87Ug52KIhsyMqw/Tc+sLjAZzI2BwP2pqDkK/3SX'
    b'vUQ9tbRpWbU3kfthjmECGEKG9hplErnJEGCsr1za8kVVzd1teXnLJho8GXOAdxmNuU5eICLL2iZN'
    b'wM8zM+fOs1iyCVjmWl/g3rt37jQCSLyY0gDEZ/3tcNgOIHvoZzcGj+bEBLzz2Ny6BTb7iwVm0zyB'
    b'ZRkAkDUNm7Nd1y4F/X/4ZVPTAQBY63AU7Sktv6InhLVwOgDA23OKd705pwgAcCUYOFFd/8nKCQn4'
    b'+zz3lrrpGTsJwFwM9hy4FwmfFQmX5OCFReVWqyfPZNona0h67vOmv3UrSluD3783pqrCukdTNxo5'
    b'jjnZ1XmcMOgCgB5Jvvyw4qPw1IwZeR2r1/Vqnlr6l7klY14xB8sXvEU9tfR69cq2LEAYQdk61qxT'
    b'qaeWvlZQUPug3AfK5m8dPIZVrYlc/BSscUzb6BQE89VgoOXZz67sTHR858s7fw0pCp1lMmU96cpf'
    b'PqHuvgXxvyCFFx4DAJHVkXNLlu5KdJSpxkQ1TTIAfI5BTJ10AXqWWADArOMye1WyPtGRBcGt8EDs'
    b'Xpjt9sUibZMuQFW1EAB8GQqdmX/29IrJKvAwxPdAQJW8ACByXA4mdklplA7OBz3DTXiwxQU0+P0f'
    b'hFRFKTSbc3YXz9s2XsCPnE5Hginok2J+AEg3JGVMVEBc8es3bpwtMifvrk1L//WmzKwdRcnJ87ul'
    b'aH0wKvWaBcFoYdkcm45f1Kco0qLOzpIROWifojQDcCy3pTx/cvFiK1XB+mWJ1DVeeOE7CwCAusYL'
    b'z0fd7jZ3sm1zqfWRtRzDrB3mIqpKW0Mh771I6F+JSeoD/leset2+fKM551FR2AoAx9rb3x/mZU2j'
    b'AKANvrpGYcz1OASyOSu3rNBizhR0hO+OSIFzAd/Nw/fvt4zXyYL0dNEtCGWzTKbUuwNR3/ve5k9a'
    b'h55wNU6nId9sLgmoasc/bt++OTLu/zboYU40Aq2CAAAAAElFTkSuQmCC'
)


def bounds_error(min_value=None, max_value=None, equal_min=True, equal_max=True):
    """
    Formats the error message detailing the bounds that a value must be between.

    Parameters
    ----------
    min_value : int or float, optional
        The minimum value. If None or -inf, then is not included in the
        output message.
    max_value : int or float, optional
        The maximum value. If None or inf, then is not included in the
        output message.
    equal_min : bool, optional
        If True (default), the operator is value >= min_value, else value > min_value.
    equal_max : bool, optional
        If True (default), the operator is value <= max_value, else value < max_value.

    Returns
    -------
    str
        The correctly formatted error message.

    """
    if min_value is None:
        min_value = float('-inf')
    if max_value is None:
        max_value = float('inf')

    if min_value == float('-inf') and max_value != float('inf'):
        min_section = ''
    else:
        if equal_min:
            min_section = f'{min_value} <= '
        else:
            min_section = f'{min_value} < '
    if max_value == float('inf') and min_value != float('-inf'):
        max_section = ''
    else:
        if equal_max:
            max_section = f' >= {max_value}'
        else:
            max_section = f' > {max_value}'

    return f'value must satisfy the bounds: {min_section}value{max_section}'


def validate_bounds(value, min_value=None, max_value=None,
                    equal_min=True, equal_max=True):
    """
    Ensures that a value is within the specified bounds.

    Parameters
    ----------
    value : int or float
        The value to test.
    min_value : int or float, optional
        The minimum value. If None (default), is set to -inf.
    max_value : int or float, optional
        The maximum value. If None (default), is set to inf.
    equal_min : bool, optional
        If True (default), the operator is value >= min_value, else value > min_value.
    equal_max : bool, optional
        If True (default), the operator is value <= max_value, else value < max_value.

    Returns
    -------
    value : int or float
        The input value.

    Raises
    ------
    ValueError
        Raised if the value is not within the bounds.

    """
    min_value = min_value if min_value is not None else float('-inf')
    max_value = max_value if max_value is not None else float('inf')
    min_operator = operator.ge if equal_min else operator.gt
    max_operator = operator.le if equal_max else operator.lt
    # works even if value is nan
    if not (min_operator(value, min_value) and max_operator(value, max_value)):
        raise ValueError(bounds_error(min_value, max_value, equal_min, equal_max))
    return value


def split_entry(message, separator=','):
    """
    Splits the input string and returns only the segments with values.

    For example, split_entry('a, b,,d', separator=',') returns ['a', 'b', 'd'].

    Parameters
    ----------
    message : str
        The string to split.
    separator : str, optional
        The separator used to delimit values in the input message.
        Default is ','. Set to None to delimit any whitespace.

    Returns
    -------
    list(str)
        The list of values after splitting the input string.

    Notes
    -----
    Only returns segments that are non-empty, and strips any whitespace from
    the beginning and end of each segment.

    """
    return [entry.strip() for entry in message.split(separator) if entry.strip()]



def validate_sheet_name(sheet_name):
    r"""
    Ensures that the desired Excel sheet name is valid.

    Parameters
    ----------
    sheet_name : str
        The desired sheet name.

    Returns
    -------
    sheet_name : str
        The input sheet name. Only returned if it is valid.

    Raises
    ------
    ValueError
        Raised if the sheet name is greater than 31 characters or if it
        contains any of the following: ``\, /, ?, *, [, ], :``

    """
    forbidden_characters = ('\\', '/', '?', '*', '[', ']', ':')

    if len(sheet_name) > 31:
        raise ValueError('Sheet name must be less than 32 characters.')
    elif any(char in sheet_name for char in forbidden_characters):
        raise ValueError(
            f'Sheet name cannot have any of the following characters: {forbidden_characters}'
        )

    return sheet_name


def stringify_backslash(input_string):
    r"""
    Fixes strings containing backslash, such as ``'\n'``, so that they display properly in GUIs.

    Parameters
    ----------
    input_string : str
        The string that potentially contains a backslash character.

    Returns
    -------
    output_string : str
        The string after replacing various backslash characters with their
        double backslash versions.

    Notes
    -----
    It is necessary to replace multiple characters because things like ``'\n'`` are
    considered unique characters, so simply replacing the ``'\'`` would not work.

    """
    output_string = input_string
    replacements = (
        ('\\', '\\\\'), ('\f', '\\f'), ('\n', '\\n'), ('\t', '\\t'), ('\r', '\\r'),
    )
    for replacement in replacements:
        output_string = output_string.replace(*replacement)

    return output_string


def ensure_app(func):
    """
    Ensures a wxPython App is available for the wrapped function.

    Useful for basic, standalone functions that use dialogs or frames with a
    basic MainLoop so that each function does not need to check for and/or
    instantiate its own wx.App.

    Parameters
    ----------
    func : Callable
        The function to wrap.

    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        app = wx.App() if wx.GetApp() is None else None
        try:
            return func(*args, **kwargs)
        finally:
            if app:
                app.Destroy()
                app = None

    return wrapper


@ensure_app
def get_scale(widget=None):
    """
    Gets the DPI scale factor for the current screen.

    Parameters
    ----------
    widget : wx.Window, optional
        The widget to use for getting the dpi scale. Default is None, which
        will create a new wx.Frame.

    Returns
    -------
    scale : float
        The dpi scale factor to use to determine the correct size for displaying
        on the client screen.

    """
    if widget is None:
        wx_widget = wx.Frame(None)
        destroy_widget = True
    else:
        wx_widget = widget
        destroy_widget = False

    try:
        # FromDIP available in wx >= 4.1
        scale = wx_widget.FromDIP((100, 100))[0] / 100
    except AttributeError:
        # Divide by 96 since I program on Windows, which has a standard
        # dpi of 96 at 100% scaling.
        scale = wx.GetDisplayPPI() / 96
    finally:
        if destroy_widget:
            wx_widget.Destroy()
            wx_widget = None

    return scale


def get_size(width, height=None, widget=None):
    """
    Scales the input size(s) to correct for dpi differences.

    Parameters
    ----------
    width : int or float
        The dimension to scale.
    height : int or float, optional
        Another dimension to scale. Default is None.
    widget : wx.Window
        The widget to use for getting the dpi scale. Default is None, which
        will cause get_scale to create a new wx.Frame.

    Returns
    -------
    output : int or tuple(int, int)
        The scaled input size(s). If only width is input, then an integer is output.
        If both width and height are input, then returns a tuple of two integers.

    """
    scale = get_scale(widget)
    if height is not None:
        output = (round(scale * width), round(scale * height))
    else:
        output = round(scale * width)

    return output


class Controller:
    """
    An interface between the user interface and the code.

    The Controller is given the callback function to retrieve data for
    any widget in the user interface and the key to store the returned data.
    Its purpose is to validate data and ease the transition from GUI to code.

    Attributes
    ----------
    items : dict(str, dict(str, Any))
        The dictionary of items that the controller is in charge of. Each item
        is a dictionary with the following keys and values:

                'callback': Callable
                    The function used to get the value from the widget.
                'display_name': str, optional
                    The name displayed if there is an error getting
                    the value. If None, will use the item's key.
                'expected_type': type or None, optional
                    The type desired for the value. If the retrieved value
                    from the callback function is not the expected type, and
                    expected_type is not None, it will try to be converted.
                    Default is None.
                'none_values': Container, optional
                    A container (list, tuple, etc.) of items to consider
                    as none. Default is ('',).
                'allow_none': bool, optional
                    If False (default), will raise a ValueError if the retrieved
                    value is in none_values. If True, and the retrieved value is
                    in none_values, its value will be set to default_value.
                'default_value': Any, optional
                    The value to assign to the retrieved value if its value is in
                    none_values and allow_none is True. Default is None.
    subgroups : dict(str, dict(str, dict(str, Any)))
        A dictionary of subgroupings within Controller.items. This way, can
        validate only a partial group of widgets within Controller.items when
        performing minor tasks.

    """

    def __init__(self, controlled_items=None):
        self.items = {}
        self.subgroups = {}
        self._last_result = None
        if controlled_items is not None:
            self.add_items(controlled_items)

    def add_items(self, items):
        """
        Adds items to the Controller.

        Parameters
        ----------
        items : dict or Iterable(dict)
            A dictionary or an iterable of dictionaries with the following keys:

                'key': str
                    The desired key for the value.
                'callback': Callable
                    The function used to get the desired value.
                'display_name': str, optional
                    The name displayed if there is an error getting
                    the value. If None, will use 'key'.
                'expected_type': type or None, optional
                    The type desired for the value. If the retrieved value
                    from the callback function is not the expected type, and
                    expected_type is not None, it will try to be converted.
                    Default is None.
                'none_values': Container, optional
                    A container (list, tuple, etc.) of items to consider
                    as none. Default is ('',).
                'allow_none': bool, optional
                    If False (default), will raise a ValueError if the retrieved
                    value is in none_values. If True, and the retrieved value is
                    in none_values, its value will be set to default_value.
                'default_value': Any, optional
                    The value to assign to the retrieved value if its value is in
                    none_values and allow_none is True. Default is None.

        """
        if isinstance(items, dict):
            self._create_item(**items)
        else:
            for item in items:
                self._create_item(**item)

    def _create_item(self, key, callback, display_name=None, expected_type=None,
                     none_values=('',), allow_none=False, default_value=None):
        """
        Adds the given entry to self.items.

        Parameters
        ----------
        key : str
            The desired key for the value.
        callback : Callable
            The function used to get the desired value.
        display_name : str, optional
            The name displayed if there is an error getting
            the value. If None, will use 'key'.
        expected_type : type or None, optional
            The type desired for the value. If the retrieved value
            from the callback function is not the expected type, and
            expected_type is not None, it will try to be converted.
            Default is None.
        none_values : Container, optional
            A container (list, tuple, etc.) of items to consider
            as none. Default is ('',).
        allow_none : bool, optional
            If False (default), will raise a ValueError if the retrieved
            value is in none_values. If True, and the retrieved value is
            in none_values, its value will be set to default_value.
        default_value : Any, optional
            The value to assign to the retrieved value if its value is in
            none_values and allow_none is True. Default is None.

        """
        self.items[key] = {
            'callback': callback,
            'display_name': display_name if display_name is not None else key,
            'expected_type': expected_type,
            'none_values': none_values,
            'allow_none': allow_none,
            'default_value': default_value
        }

    def add_subgroup(self, subgroup_key, keys):
        """
        Adds a subgroup to validate only a subset of keys within self.items.

        Parameters
        ----------
        subgroup_key : str
            The key for the subgroup.
        keys : str or Iterable(str)
            The key(s) of items within self.items to include for the subgroup.

        """
        if isinstance(keys, str):
            keys = (keys,)
        self.subgroups[subgroup_key] = {key: self.items[key] for key in keys}

    def validate(self, subgroup_key=None):
        """
        Validates each item in either self.items or self.subgroups[subgroup_key].

        If there are errors during validation, a popup is shown describing the key
        and exception message for each error.

        Parameters
        ----------
        subgroup_key : str, optional
            The key of the subgroup to validate. If None, then will validate
            everything in self.items.

        Returns
        -------
        dict(str, Any) or None
            If validation is successful, returns the results dictionary containing
            each key and the returned value from the key's callback function. If
            validation failed, returns None.

        """
        if subgroup_key is not None:
            validation_dict = self.subgroups[subgroup_key]
        else:
            validation_dict = self.items

        output = {}
        failures = []
        for key, values in validation_dict.items():
            result = self._validate_item(
                values['callback'], values['expected_type'], values['none_values'],
                values['allow_none'], values['default_value']
            )
            if isinstance(result, Exception):
                failures.append((values['display_name'], str(result)))
            else:
                output[key] = result
        if failures:
            self._show_popup(failures)
            self._last_result = None
        else:
            self._last_result = output

        return self._last_result

    def _validate_item(self, callback, expected_type, none_values, allow_none, default_value):
        """Validates each individual item."""
        try:
            widget_value = callback()
            if widget_value in none_values:
                if allow_none:
                    widget_value = default_value
                else:
                    raise ValueError(f'Input must not be in {none_values}')
            elif expected_type is not None and not isinstance(widget_value, expected_type):
                if not isinstance(widget_value, str) and isinstance(widget_value, Iterable):
                    widget_value = [expected_type(val) for val in widget_value]
                else:
                    widget_value = expected_type(widget_value)

        except Exception as exception:
            return exception

        return widget_value

    @staticmethod
    @ensure_app
    def _show_popup(failures):
        """Displays all errors that occurred during validation."""
        msg = '\n'.join(
            [f'    {i + 1}) {failure[0]}: {failure[1]}' for i, failure in enumerate(failures)]
        )
        with wx.MessageDialog(
            None, 'Error with inputs\n\n' + msg, 'Errors', wx.OK | wx.ICON_WARNING
        ) as dialog:
            dialog.ShowModal()

    def reset(self):
        """
        Resets the Controller's last result to None.

        Should be used when frames are exited early to notify outer control logic
        that there is no result.

        """
        self._last_result = None

    def get_value(self):
        """
        Gives the last validation result for the Controller.

        Returns
        -------
        dict(str, Any) or None
            If the last validation wass successful, returns the results dictionary
            containing each key and the returned value from the key's callback
            function. If validation failed, or the Controller was reset, returns None.

        """
        return self._last_result


class BaseFrame(wx.Frame):
    """
    A wx.Frame with just the logo set.

    Parameters
    ----------
    parent : wx.Window, optional
        The parent widget for the frame. Default is None.
    confirm_close : bool, optional
        If True (default), will bind wx.EVT_CLOSE to the object's on_close method, which
        by default will show a popup asking for confirmation of closing the frame.
    controller : Controller, optional
        The Controller object for the frame, which is used to validate and
        collect inputs. If None, a new Controller will be created.
    **kwargs
        Keyword arguments for initializing wx.Frame.

    """

    def __init__(self, parent=None, confirm_close=True, controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.SetIcon(wx.Icon(wx.Image(io.BytesIO(base64.b64decode(_LOGO))).ConvertToBitmap()))
        self.controller = controller if controller is not None else Controller()
        if confirm_close:
            self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        """
        Asks the user for confirmation before closing the frame.

        Parameters
        ----------
        event : wx.Event
            The close event.

        """
        with wx.MessageDialog(
            self, 'Are you sure you want to exit?', 'Confirm Close',
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
        ) as dialog:
            if dialog.ShowModal() == wx.ID_YES:
                self.controller.reset()
                event.Skip()

    def safe_close(self, event=None):
        """
        Ensures that validation passes before closing the frame.

        Parameters
        ----------
        event : wx.Event, optional
            The close event.

        """
        if self.controller.validate():
            self.Destroy()


class BaseDialog(wx.Dialog):
    """
    A wx.Dialog that will set its logo if it has no parent.

    Parameters
    ----------
    parent : wx.Window, optional
        The parent widget for the frame. Default is None.
    *args
        Positional arguments for initializing wx.Dialog.
    **kwargs
        Keyword arguments for initializing wx.Dialog.

    """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        if parent is None:
            self.SetIcon(wx.Icon(wx.Image(io.BytesIO(base64.b64decode(_LOGO))).ConvertToBitmap()))


class UtilityButton(wx.Button):
    """
    The base class for Buttons that open dialogs when pressed.

    The buttons will have a target widget which will be updated with the
    dialog output, using either target.SetValue or target.Append/.Set.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the button.
    target : wx.Window
        The target widget that will be updated with information when this
        button is pressed.
    set_string : bool, optional
        If True (default), will use the target widget's SetValue method
        (or SetLabel method if no SetValue, such as for wx.StaticText)
        to update its value, even if the widget is an wx.ItemContainer
        which could use Set or Append instead.
    **kwargs
        Any additional keyword arguments for initializing wx.Button.

    Attributes
    ----------
    separator : str
        The string that will be used to delimit values when set_string and
        overwrite are both True. Default is ', '.

    Notes
    -----
    subclasses should use self.update_method(items) to update the target
    widget with the items from their on_click method.

    """

    def __init__(self, parent, target, set_string=True, overwrite=False, **kwargs):
        super().__init__(parent, **kwargs)
        self._value = None
        self._target = target
        self._overwrite = overwrite
        self.separator = ', '

        self.Bind(wx.EVT_BUTTON, self.on_click)

        if isinstance(target, wx.ItemContainer) and not set_string:
            self._set_string = False
            if overwrite:
                self.update_method = self._set
            else:
                self.update_method = target.Append
        else:
            self._set_string = True
            if hasattr(target, 'SetValue'):
                if overwrite:
                    self.update_method = target.SetValue
                else:
                    self.update_method = self._update_set_value
            else:
                if overwrite:
                    self.update_method = target.SetLabel
                else:
                    self.update_method = self._update_set_label

    def _set(self, item):
        """Ensures the update item is a list or tuple before using target.Set."""
        if isinstance(item, str) or not isinstance(item, Iterable):
            update_item = (item,)
        else:
            update_item = item
        self._target.Set(update_item)
        self._target.SetSelection(0)

    def _update_set_value(self, message):
        """Places a separator between values if the target already has a value."""
        if self._target.GetValue() != '':
            update_message = self._target.GetValue() + self.separator + message
        else:
            update_message = message
        self._target.SetValue(update_message)

    def _update_set_label(self, message):
        """Places a separator between values if the target already has a value."""
        if self._target.GetLabel() != '':
            update_message = self._target.GetLabel() + self.separator + message
        else:
            update_message = message
        self._target.SetLabel(update_message)

    def on_click(self, event):
        """Performs the event for when the button is clicked."""
        raise NotImplementedError('on_click must be set for each subclass.')

    def get_value(self):
        """Returns the value contained by the button."""
        return self._value


class FileSaveButton(UtilityButton):
    """
    Button that opens a FileDialog when pressed and updates its target with the chosen path.

    Used to select the filename for saving.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the button.
    target : wx.Window
        The target widget that will be updated using target.SetValue with the
        selected value from the FileDialog, in the desired output format.
    file_types : str, optional
        The file extensions to allow. Input must be like
        'display_name_1|extension_1|display_name_2|extension_2', like
        'PNG File|*.png|JPEG File|*.jpg;*.jpeg'. If not given, the
        defaults to allow all files, eg. 'All Files (*.*)|*.*'.
    full_path : bool, optional
        If False (default), will only update the target with the path's name
        (eg. C:/Users/file.txt would become file.txt). If True, will update the
        target with the entire file path.
    **kwargs
        Any additional keyword arguments for initializing wx.Button.

    """

    def __init__(self, parent, target, set_string=True, overwrite=False,
                 file_types=None, full_path=False, **kwargs):
        super().__init__(parent, target, set_string, overwrite, **kwargs)
        self._full_path = full_path
        self._file_types = file_types if file_types is not None else 'All Files (*.*)|*.*'

    def on_click(self, event):
        """Launches the dialog to select the file name and updates the target."""
        with wx.FileDialog(self, 'Save As...', wildcard=self._file_types,
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
            if self._value is not None:
                dialog.SetFilename(self._value.name)
                dialog.SetDirectory(str(self._value.parent))
                dialog.SetFilterIndex(self._suffix_index())

            if dialog.ShowModal() == wx.ID_OK:
                self._value = Path(dialog.GetPath())
                if self._full_path:
                    update_value = str(self._value)
                else:
                    update_value = self._value.name
                self.update_method(update_value)

    def _suffix_index(self):
        """Returns the index of the current extension within the total extensions."""
        extensions = [
            ext.replace('*', '').lower() for ext in self._file_types.split('|')[1::2]
        ]
        index = 0
        current_suffix = self._value.suffix.lower()
        for i, extension in enumerate(extensions):
            if current_suffix in extension.split(';'):
                index = i
                break
        return index

    def get_value(self):
        """
        Used to get the selected full path from the widget.

        Returns
        -------
        str or None
            The full file path of the selected file.

        """
        if self._value is None:
            return None
        else:
            return str(self._value)


class ColorButton(UtilityButton):
    """
    Button that opens a ColourDialog when pressed and updates its target with the chosen values.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the button.
    target : wx.Window
        The target widget that will be updated using target.SetValue with the
        selected value from the ColourDialog, in the desired output format.
    output_format : {'hex', 'rgb', 'rgba'}
        The output format to use when updating the target widget.
    **kwargs
        Any additional keyword arguments for initializing wx.Button.

    Attributes
    ----------
    formats : dict(str, str)
        A dictionary that gives the string format to use when updating
        the target with the selected color.

    """

    formats = {
        'hex': '#{0:02X}{1:02X}{2:02X}',
        'rgb': '{0}, {1}, {2}',
        'rgba': '{0}, {1}, {2}, 255'
    }

    def __init__(self, parent, target, set_string=True, overwrite=False, output_format='hex', **kwargs):
        super().__init__(parent, target, set_string, overwrite, **kwargs)
        if output_format.lower() in self.formats:
            self.output_format = self.formats[output_format.lower()]
        else:
            raise KeyError(f'output_format must be in {list(self.formats.keys())}')

    def on_click(self, event):
        """Launches the dialog to select the color and updates the target."""
        with wx.ColourDialog(self) as dialog:
            if self._value is not None:
                dialog.GetColourData().SetColour(self._value)
            # allows selecting custom colors
            dialog.GetColourData().SetChooseFull(True)

            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour().Get(includeAlpha=False)
                self.update_method(self.output_format.format(*color))
                self._value = color

    def get_value(self):
        """
        Used to get the last selected color from the widget, in the selected format.

        Returns
        -------
        str or None
            The last selected color.

        """
        if self._value is None:
            return None
        else:
            return self.output_format.format(*self._value)


class FileOpenButton(UtilityButton):
    """
    Button that opens a FileDialog when pressed and updates its target with the chosen paths.

    Used to select files to open.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the button.
    target : wx.Window
        The target widget that will be updated using target.SetValue with the
        selected value from the FileDialog, in the desired output format.
    file_types : str, optional
        The file extensions to allow. Input must be like
        'display_name_1|extension_1|display_name_2|extension_2'. If not
        given, then defaults to allow all files, eg. 'All Files (*.*)|*.*'.
    full_path : bool, optional
        If False (default), will only update the target with the path's name
        (eg. C:/Users/file.txt would become file.txt). If True, will update
        the target with the entire file path.
    multiple : bool, optional
        If True (default), will allow selecting multiple files.
    overwrite : bool, optional
        If False (default), will append the selected file(s) to the target.
        If True, will overwrite the target with the selected file(s).
    **kwargs
        Any additional keyword arguments for initializing wx.Button.

    Notes
    -----
    If the target is a subclass of wx.ItemContainer (like wx.ComboBox or
    wx.ListBox), will use target.Set or target.Append to add the paths.
    Otherwise, will use target.SetValue.

    """

    def __init__(self, parent, target, set_string=True, overwrite=False, file_types=None,
                 full_path=False, multiple=True, **kwargs):
        super().__init__(parent, target, set_string, overwrite, **kwargs)
        self._full_path = full_path
        self._multiple = multiple
        self._file_types = file_types if file_types is not None else 'All Files (*.*)|*.*'
        self._value = []

    def on_click(self, event):
        """Launches the dialog to select the color and updates the target."""
        style = wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST
        if self._multiple:
            style = style | wx.FD_MULTIPLE

        with wx.FileDialog(self, 'Select file(s)', wildcard=self._file_types, style=style) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                if self._multiple:
                    paths = dialog.GetPaths()
                else:
                    paths = [dialog.GetPath()]
                # maybe not necessary, but ensures paths are correct for all os
                paths = [str(Path(path)) for path in paths]

                if self._overwrite:
                    self._value = paths
                else:
                    self._value.extend(paths)

                if not self._full_path:
                    paths = [Path(path).name for path in paths]

                if not self._set_string:
                    update_value = paths
                else:
                    update_value = self.separator.join(paths)
                self.update_method(update_value)

    def get_value(self):
        """
        Used to get the selected full paths from the widget.

        Returns
        -------
        list(str)
            A list of the full file paths of the selected files.

        """
        return self._value


class FolderButton(UtilityButton):
    """
    Button that opens a DirDialog when pressed and updates its target with the chosen path.

    Used to select folders.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the button.
    target : wx.Window
        The target widget that will be updated using target.SetValue with the
        selected value from the DirDialog, in the desired output format.
    full_path : bool, optional
        If False (default), will only update the target with the path's name
        (eg. C:/Users/folder would become folder). If True, will update the
        target with the entire file path.
    **kwargs
        Any additional keyword arguments for initializing wx.Button.

    """

    def __init__(self, parent, target, set_string=True,
                 overwrite=False, full_path=False, **kwargs):
        super().__init__(parent, target, set_string, overwrite, **kwargs)
        self._full_path = full_path

    def on_click(self, event):
        """Launches the dialog to select the folder and updates the target."""
        with wx.DirDialog(self, 'Select a folder') as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self._value = Path(dialog.GetPath())
                if self._full_path:
                    update_value = str(self._value)
                else:
                    update_value = self._value.name
                self.update_method(update_value)

    def get_value(self):
        """
        Used to get the selected full path from the widget.

        Returns
        -------
        str or None
            The full file path of the selected folder.

        """
        if self._value is None:
            return None
        else:
            return str(self._value)


class BaseCtrl(wx.TextCtrl):
    """
    A base class for custom text controls that help users fill forms.

    The text control will validate itself once it loses focus, and if there
    is an incorrect input, the control will be highlighted and given a tooltip
    describing the error.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the text control.
    allow_empty : bool, optional
        If False (default), will highlight itself if there is no input
        in the control, even if it passed the higher level validations.
    **kwargs
        Keyword arguments for initializing wx.TextCtrl.

    Attributes
    ----------
    error_color : str
        The color to set the widget's background when validation fails.

    Notes
    -----
    Subclasses need to implement a validate method to validate the input,
    and should call self.on_success if validation passes and self.on_error
    if validation fails. The validate method **must** call event.Skip() at the
    end, or else the GUI will not process focus-losing events correctly.

    """

    error_color = 'pink'

    def __init__(self, parent, allow_empty=False, **kwargs):
        super().__init__(parent, **kwargs)
        self._tool_tip = None
        self._error = False
        self._allow_empty = allow_empty
        self.Bind(wx.EVT_KILL_FOCUS, self.validate)

    def validate(self, event):
        """The event called when the control widget loses focus."""
        raise NotImplementedError('Need to implement validate for each subclass.')

    def on_error(self, error_message=None):
        """
        Changes the control to inform the user that the input has an error.

        The default implementation changes the background color of the widget
        and optionally sets a tooltip.

        Parameters
        ----------
        error_message : str, optional
            The error message to set as the tooltip to inform the user of
            the expected input.

        """
        self._error = True
        self.SetBackgroundColour(self.error_color)
        if error_message is not None:
            if self._tool_tip is None and self.GetToolTip():
                self._tool_tip = self.GetToolTip().GetTip()
            elif not self._tool_tip:
                self._tool_tip = ''  # so it doesn't get set to another error message
            self.SetToolTip(error_message)
        self.Refresh()

    def on_success(self):
        """
        Changes the control to inform the user that the input is correct.

        The default implementation changes the background color of the widget
        back to the system default and sets it tooltip back to its original, if
        there is one.

        """
        if not super().GetValue() and not self._allow_empty:
            self.on_error('Input must not be empty')
        elif self._error:
            self._error = False
            self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            if self._tool_tip:
                self.SetToolTip(self._tool_tip)
                self._tool_tip = None
            else:
                self.UnsetToolTip()
            self.Refresh()


class UnicodeCtrl(BaseCtrl):
    r"""
    A text control that converts any input ascii Unicode to its symbol (eg. ``\u03b8`` -> θ).

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the text control.
    allow_empty : bool, optional
        If False (default), will highlight itself if there is no input
        in the control, even if it passed the higher level validations.
    **kwargs
        Keyword arguments for initializing wx.TextCtrl.

    """

    def __init__(self, parent, allow_empty=False, **kwargs):
        if kwargs.get('value', ''):
            kwargs['value'] = stringify_backslash(kwargs['value'])
        super().__init__(parent, allow_empty, **kwargs)

    def validate(self, event):
        """Validates the control's value and updates any Unicode."""
        try:
            converted_text = stringify_backslash(UnicodeCtrl.get_value(self))
        except (SyntaxError, UnicodeDecodeError):
            self.on_error('Incorrect Unicode')
        else:
            self.on_success()
            self.ChangeValue(converted_text)
        event.Skip()

    def get_value(self):
        """
        Returns the value of the control.

        Returns
        -------
        str
            The value in the entry.

        Raises
        ------
        UnicodeDecodeError
            Raised if the entry has invalid Unicode.

        """
        return string_to_unicode(self.GetValue())


class ExcelSheetCtrl(UnicodeCtrl):
    """
    A text control that ensures its input is a valid Excel sheet name.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the text control.
    allow_empty : bool, optional
        If False (default), will highlight itself if there is no input
        in the control, even if it passed the higher level validations.
    **kwargs
        Keyword arguments for initializing wx.TextCtrl.

    """

    def __init__(self, parent, allow_empty=False, **kwargs):
        super().__init__(parent, allow_empty, **kwargs)

    def validate(self, event):
        """Validates the control's value."""
        super().validate(event)
        if not self._error:
            try:
                validate_sheet_name(self.GetValue())
            except ValueError as exception:
                self.on_error(str(exception))
        event.Skip()

    def get_value(self):
        """
        Returns the value of the control.

        Returns
        -------
        str
            The value in the entry.

        Raises
        ------
        ValueError
            Raised if the entry is not a valid Excel sheet name.
        UnicodeDecodeError
            Raised if the entry has invalid Unicode.

        """
        return validate_sheet_name(super().get_value())


class _NumBase:
    """
    A base class for controls expecting numeric inputs with min and/or max values.

    Parameters
    ----------
    min_value : int or float, optional
        The minimum allowable value for the control. Default is None, which
        causes the minimum value to be -inf.
    max_value : int or float, optional
        The maximum allowable value for the control. Default is None, which
        causes the maximum value to be inf.
    equal_min : bool, optional
        If True (default), allows the input value to be equal to min_value. If False,
        the input value must be greater than min_value.
    equal_max : bool, optional
        If True (default), allows the input value to be equal to max_value. If False,
        the input value must be less than max_value.
    num_type : {int, float}, optional
        The type to cast the input value. Default is int.

    """

    def __init__(self, min_value=None, max_value=None, equal_min=True,
                 equal_max=True, num_type=int):
        self._min = min_value if min_value is not None else float('-inf')
        self._max = max_value if max_value is not None else float('inf')
        self._equal_min = equal_min
        self._equal_max = equal_max
        self._error_message = bounds_error(min_value, max_value, equal_min, equal_max)
        self._type = num_type

    @property
    def max_value(self):
        """
        The maximum value the input control can have.

        Returns
        -------
        int or float
            The maximum value.

        """
        return self._max

    @max_value.setter
    def max_value(self, value):
        """
        Updates the maximum value allowed for the control.

        If the input value is less than the current minimum value, the minimum
        value is also updated to the value.

        Parameters
        ----------
        value : int or float
            The value to set as the maximum allowable value for the input control.

        """
        if value < self._min:
            self._min = value
        self._max = value

    @property
    def min_value(self):
        """
        The minimum value the input control can have.

        Returns
        -------
        int or float
            The minimum value.

        """
        return self._min

    @min_value.setter
    def min_value(self, value):
        """
        Updates the minimum value allowed for the control.

        If the input value is greater than the current maximum value, the maximum
        value is also updated to the value.

        Parameters
        ----------
        value : int or float
            The value to set as the minimum allowable value for the input control.

        """
        self._min = value
        if value > self._max:
            self._max = value


class NumCtrl(BaseCtrl, _NumBase):
    """
    A wx.TextCtrl that converts input strings into numeric values.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the text control.
    allow_empty : bool, optional
        If False (default), will highlight itself if there is no input
        in the control, even if it passed the higher level validations.
    min_value : int or float, optional
        The minimum allowable value for the control. Default is None, which
        causes the minimum value to be -inf.
    max_value : int or float, optional
        The maximum allowable value for the control. Default is None, which
        causes the maximum value to be inf.
    equal_min : bool, optional
        If True (default), allows the input value to be equal to min_value. If False,
        the input value must be greater than min_value.
    equal_max : bool, optional
        If True (default), allows the input value to be equal to max_value. If False,
        the input value must be less than max_value.
    num_type : {int, float}, optional
        The type to cast the input value. Default is int.
    **kwargs
        Keyword arguments for initializing wx.TextCtrl.

    """

    def __init__(self, parent, allow_empty=False, min_value=None, max_value=None,
                 equal_min=True, equal_max=True, num_type=int, **kwargs):
        BaseCtrl.__init__(self, parent, allow_empty, **kwargs)
        _NumBase.__init__(self, min_value, max_value, equal_min, equal_max, num_type)
        error_prefix = {int: 'an integer', float: 'a float'}[self._type]
        self._error_message = f'must be {error_prefix} and ' + self._error_message

    def validate(self, event):
        """Validates the control's value."""
        if not self.GetValue():
            self.on_success()
        else:
            try:
                self.get_value()
            except ValueError:
                self.on_error(self._error_message)
            else:
                self.on_success()
        event.Skip()

    def get_value(self):
        """
        Returns the value of the control.

        Returns
        -------
        int or float or None
            The value in the entry, after converting to either int or float. If
            the entry is blank and allow_empty is True, then None is returned.

        Raises
        ------
        ValueError
            Raised if there is an issue converting the control's string to a
            float or int, or if the value is not within the bounds.

        """
        value = self.GetValue()
        if not value and self._allow_empty:
            return None
        return validate_bounds(self._type(value), self._min, self._max, self._equal_min, self._equal_max)


class IterCtrl(BaseCtrl):
    """
    A text control whose value is an iterable of items.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the text control.
    allow_empty : bool, optional
        If False (default), will highlight itself if there is no input
        in the control, even if it passed the higher level validations.
    separator : str, optional
        The separator to use for splitting text into lists. Default is ', '.
    **kwargs
        Keyword arguments for initializing wx.TextCtrl.

    """

    def __init__(self, parent, allow_empty=False, separator=', ', **kwargs):
        self._separator = separator
        if kwargs.get('value', None):
            kwargs['value'] = self._convert_iterable(kwargs['value'])
        super().__init__(parent, allow_empty, **kwargs)

    def _convert_iterable(self, value):
        """
        Converts iterables to strings for use in wx.TextCtrl.

        Parameters
        ----------
        value : Any
            The value to place into the control. If the value is an Iterable
            and not a string, then all the values in the Iterable are converted
            to string and joined by self._separator. Otherwise, the value is just
            converted to string.

        Returns
        -------
        output : str
            The value to place into the control.

        """
        if not isinstance(value, str) and isinstance(value, Iterable):
            separator = self._separator if self._separator is not None else ' '
            output = separator.join(str(val) for val in value)
        else:
            output = str(value)
        return output

    def SetValue(self, value):
        """
        Ensures that the value is a string before placing into the control.

        Parameters
        ----------
        value : Any
            The value to place into the control. If the value is an Iterable
            and not a string, then all the values in the Iterable are converted
            to string and joined by self._separator. Otherwise, the value is just
            converted to string.

        """
        super().SetValue(self._convert_iterable(value))

    def validate(self, event):
        """Validates the control's value."""
        try:
            IterCtrl.get_value(self)
        except Exception as exc:
            # there should never be a case where this fails, since it is just
            # getting its string.
            self.on_error(f'Issue with input: {repr(exc)}')
        else:
            self.on_success()
        event.Skip()

    def get_value(self):
        """
        Returns the value of the control.

        Returns
        -------
        list(str)
            The value in the entry after separating using self._separator.

        """
        if self._separator is None:
            separator = self._separator
        else:
            separator = self._separator.strip()
        return split_entry(super().GetValue(), separator)


class IterNumCtrl(IterCtrl, _NumBase):
    """
    A text control whose value is an iterable of numeric values.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the text control.
    allow_empty : bool, optional
        If False (default), will highlight itself if there is no input
        in the control, even if it passed the higher level validations.
    separator : str, optional
        The separator to use for splitting text into lists. Default is ', '.
    min_value : int or float, optional
        The minimum allowable value for the control. Default is None, which
        causes the minimum value to be -inf.
    max_value : int or float, optional
        The maximum allowable value for the control. Default is None, which
        causes the maximum value to be inf.
    equal_min : bool, optional
        If True (default), allows the input value to be equal to min_value. If False,
        the input value must be greater than min_value.
    equal_max : bool, optional
        If True (default), allows the input value to be equal to max_value. If False,
        the input value must be less than max_value.
    num_type : {int, float}, optional
        The type to cast the input value. Default is int.
    **kwargs
        Keyword arguments for initializing wx.TextCtrl.

    """

    def __init__(self, parent, allow_empty=False, separator=', ', min_value=None,
                 max_value=None, equal_min=True, equal_max=True, num_type=int, **kwargs):
        IterCtrl.__init__(self, parent, allow_empty, separator, **kwargs)
        _NumBase.__init__(self, min_value, max_value, equal_min, equal_max, num_type)
        error_prefix = {int: 'an integer', float: 'a float'}[self._type]
        self._error_message = f'each value must be {error_prefix} and each ' + self._error_message

    def validate(self, event):
        """Validates the control's value."""
        if not self.GetValue():
            self.on_success()
        else:
            try:
                self.get_value()
            except ValueError:
                self.on_error(self._error_message)
            else:
                self.on_success()
        event.Skip()

    def get_value(self):
        """
        Returns the value of the control.

        Returns
        -------
        list(int) or list(float) or list
            The value in the entry after separating using self._separator and
            converting to int or float. If the entry is empty and allow_empty
            is True, then an empty list is returned.

        Raises
        ------
        ValueError
            Raised if there is an issue converting the any string to a
            float or int, or if any value is not within the bounds.

        """
        value = super().get_value()
        if value == [''] and self._allow_empty:
            return []
        return [
            validate_bounds(self._type(val), self._min, self._max, self._equal_min, self._equal_max)
            for val in value
        ]


class DataFrameTable(wx.grid.GridTableBase):
    """
    A table for displaying the contents of a pandas DataFrame.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The pandas DataFrame for the table.

    Attributes
    ----------
    EVEN_COLOR : str
        The color of even rows. The default is '#ADD8E6', which is a light blue.
    ODD_COLOR : str
        The color of odd rows. The default is '#FFFACD', which is lemon chiffon
        (a light yellow).

    Notes
    -----
    The columns and indices of the dataframe are set to numerical values
    while used by the table, for two reasons. First, it allows using
    dataframe.at rather than dataframe.iloc, which is faster. Second,
    using dataframe.at to set a value preserves the column's dtype, unlike
    using dataframe.iloc. The columns and indices are reset once the
    table is destroyed, leaving the dataframe unchanged.

    Some base methods are set to ensure that the Table works correctly.
    Not sure if all base methods are necessary.

    The table allows only loading data from the DataFrame that is visible
    in the GUI, so it is much faster than placing the data from the DataFrame
    directly into a wx.Grid, and can allow viewing extremely large DataFrames.

    """

    EVEN_COLOR = '#ADD8E6'  # 'light blue'
    ODD_COLOR = '#FFFACD'  # 'lemon chiffon'

    def __init__(self, dataframe):
        super().__init__()

        self._num_cols = len(dataframe.columns)
        self._num_rows = len(dataframe.index)
        self._index = dataframe.index
        self._columns = dataframe.columns

        # set columns and indices to ascending numerical values
        dataframe.columns = range(len(dataframe.columns))
        dataframe.index = range(len(dataframe.index))
        self.dataframe = dataframe

        # sets the row background color to alternating colors
        self.odd = wx.grid.GridCellAttr()
        self.odd.SetBackgroundColour(self.ODD_COLOR)
        self.even = wx.grid.GridCellAttr()
        self.even.SetBackgroundColour(self.EVEN_COLOR)

    def __del__(self):
        """Resets the DataFrame's columns and indices when table is destroyed."""
        self.dataframe.columns = self._columns
        self.dataframe.index = self._index

    def GetColLabelValue(self, col):
        """
        Gives the label for the given column.

        Parameters
        ----------
        col : int
            The column index.

        Returns
        -------
        str
            The label for the given column.

        """
        return str(self._columns[col])

    def GetRowLabelValue(self, row):
        """
        Gives the label for the given row.

        Parameters
        ----------
        row : int
            The row index.

        Returns
        -------
        str
            The label for the given row.

        """
        return str(self._index[row])

    def GetAttr(self, row, col, kind):
        """
        Determines the cell Attr (the cell formatting) to use.

        Parameters
        ----------
        row : int
            The row index.
        col : int
            The column index.
        kind : wx.grid.AttrKind
            Not sure what this is. But not really necessary in this case.

        Returns
        -------
        wx.grid.GridCellAttr
            The attribute/formatting of the given cell.

        """
        attr = (self.even, self.odd)[row % 2]
        attr.IncRef()
        return attr

    def GetNumberRows(self):
        """
        Gets the number of rows in the table.

        Returns
        -------
        int
            The number of rows in the table.

        """
        return self._num_rows

    def GetNumberCols(self):
        """
        Gets the number of columns in the table.

        Returns
        -------
        int
            The number of columns in the table.

        """
        return self._num_cols

    def GetValue(self, row, col):
        """
        Gets the value of the DataFrame cell.

        Parameters
        ----------
        row : int
            The row index.
        col : int
            The column index.

        Returns
        -------
        str
            The string value of the DataFrame cell.

        """
        return str(self.dataframe.at[row, col])

    def SetValue(self, row, col, value):
        """
        Sets the value in the DataFrame, if possible.

        If the value cannot be coerced to match the DataFrame column's dtype,
        then it is ignored.

        Parameters
        ----------
        row : int
            The row index.
        col : int
            The column index.
        value : Any
            The value to set in the DataFrame.

        """
        try:
            self.dataframe.at[row, col] = value
        except ValueError:
            pass  # the dataframe's column typing does not allow conversion


class DataFrameGrid(wx.grid.Grid):
    """
    A grid for displaying a pandas DataFrame.

    Uses a Table rather than setting its own cells since using a
    Table is significantly faster.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the grid.
    dataframe : pandas.DataFrame
        The dataframe to display.
    allow_edit : bool, optional
        If True, will allow editing the values in the grid.

    """

    def __init__(self, parent, dataframe, allow_edit=False):
        super().__init__(parent)

        table = DataFrameTable(dataframe)
        # takeOwnership=True means table will be cleaned when Grid is destoyed
        self.SetTable(table, takeOwnership=True)
        self.EnableEditing(allow_edit)


class DataFrameViewer(BaseDialog):
    """
    A Frame for displaying and potentially editing pandas DataFrames.

    If a list or list of lists of DataFrames is given, then each grouping
    of DataFrames is put within a wx.Notebook.

    Parameters
    ----------
    parent : wx.Window
        The parent widget for the frame.
    dataframes : pandas.DataFrame or list(pandas.DataFrame) or list(list(pandas.DataFrame))
        The data to display. If a list or list of lists is given, then each
        list is grouped within its own wx.Notebook.
    allow_edit : bool, optional
        If True, will add a checkbox to the frame to toggle editing the values
        in the dataframes.
    **kwargs
        Additional keyword arguments for initializing wx.Dialog.

    """

    def __init__(self, parent, dataframes, allow_edit=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.grids = []

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        if allow_edit:
            self.check_box = wx.CheckBox(self.panel, label='Allow Editing')
            self.sizer.Add(self.check_box, 0, wx.ALL, 10)
            self.check_box.Bind(wx.EVT_CHECKBOX, self.toggle_edit)

        if isinstance(dataframes, pd.DataFrame):
            self.notebook = None
            self.grids.append(DataFrameGrid(self.panel, dataframes))
            self.sizer.Add(self.grids[-1], 0, wx.EXPAND)
        else:
            self.notebook = wx.Notebook(self.panel)
            if isinstance(dataframes[0], pd.DataFrame):
                for i, dataframe in enumerate(dataframes):
                    self.grids.append(DataFrameGrid(self.notebook, dataframe))
                    self.notebook.AddPage(self.grids[-1], f'Dataset {i + 1}')
            else:
                pages = []
                for i, dataframe_list in enumerate(dataframes):
                    pages.append(wx.Notebook(self.notebook))
                    for j, dataframe in enumerate(dataframe_list):
                        self.grids.append(DataFrameGrid(pages[-1], dataframe))
                        pages[-1].AddPage(self.grids[-1], f'Entry {j + 1}')
                    self.notebook.AddPage(pages[-1], f'Dataset {i + 1}')
            self.sizer.Add(self.notebook, 0, wx.EXPAND)
        self.panel.SetSizer(self.sizer)

    def toggle_edit(self, event):
        """
        Allows editing the grids if the checkbox is selected.

        If checked, first warns the user that all changes will be final.

        Parameters
        ----------
        event : wx.Event
            The wxEVT_CHECKBOX event.

        """
        if not self.check_box.GetValue():
            enable_edit = False
        else:
            with wx.MessageDialog(
                self,
                ('Are you sure you want to enable editing?\n'
                 'All changes to the data will be final.'),
                'Enable Editing?',
                style=wx.YES_NO | wx.ICON_WARNING
            ) as dialog:
                response = dialog.ShowModal()
                if response == wx.ID_YES:
                    enable_edit = True
                else:
                    enable_edit = None
                    self.check_box.SetValue(0)

        if enable_edit is not None:
            for grid in self.grids:
                grid.EnableEditing(enable_edit)
