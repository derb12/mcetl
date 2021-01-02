===================
Changing GUI Colors
===================

All user interfaces are created using PySimpleGUI, which allows easily changing the theme of the GUIs.
For example, the following code will change the GUI theme to use PySimpleGUI's 'darkblue10' theme:

.. code-block:: python

    import PySimpleGUI as sg
    sg.theme('darkblue10')


Additionally, mcetl uses a unique coloring for the button that advances to the next window.
To change this button's colors (for example to use white text on a green background), do:

.. code-block:: python

    from mcetl import utils
    utils.PROCEED_COLOR = ('white', 'green')


Valid inputs for PROCEED_COLOR are color strings supported by PySimpleGUI, such as 'green',
or hex colors such as '#F9B381'.

Changes to the GUI colors must be done before creating the GUIs, so the overall sequence
would look something like this:

.. code-block:: python

    from mcetl import fitting, utils
    import PySimpleGUI as sg

    sg.theme('darkblue10')
    utils.PROCEED_COLOR = ('green', '#F9B381')

    fitting.launch_fitting_gui()
