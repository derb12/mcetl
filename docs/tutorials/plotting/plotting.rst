===========
Basic Usage
===========


Plotting
~~~~~~~~

To use the plotting module in mcetl, simply do:

.. code-block:: python

    from mcetl import plotting
    plotting.launch_plotting_gui()


Similar to fitting, a window will then appear to select the data file(s) to be plotted,
and no other setup is required for doing plotting.


When plotting, the image of the plots can be saved to all formats supported by matplotlib,
including tiff, jpg, png, svg, and pdf.


In addition, the layout of the plots can be saved to apply to other figures later, and the data
for the plots can be saved so that the entire plot can be recreated.


To reopen a figure saved through mcetl, do:

.. code-block:: python

    plotting.load_previous_figure()
