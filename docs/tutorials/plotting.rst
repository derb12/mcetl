============
Plotting GUI
============

The plotting module of mcetl provides a GUI for plotting data. mcetl uses
the `Matplotlib`_ library for plotting, which allows for saving high quality
images in several formats.

Please note that the plotting submodule is included in mcetl to allow a fairly basic
plotting option. Further, its development will be slower than the main GUI or the
fitting submoduule since it requires covering many more options and is not a priority
of the author. If other plotting software is available, such as
`SciDAVis <https://scidavis.sourceforge.net/>`_, `Veusz <https://veusz.github.io>`_,
or `Origin <https://originlab.com>`_, the author highly recommends their usage
instead of mcetl.

Summary of Features
-------------------

The plotting GUI has the following features:

* plot data using line and/or scatter plots, and allow
  customization of the colors, style, and size of the markers/lines.
* specify complex layouts composed of multiple rows and/or columns of axes
  and inset axes
* add twin axes to plot multiple dependent responses (such as
  viscosity and density as functions of temperature)
* add secondary axes to plot the same data on different scales,
  using user-specified conversions (such as plotting temperature
  in both Fahrenheit and Celsius)
* specify figure dimensions and dots per inch (dpi)
* add formatted annotations (text, arrows, and lines) anywhere on the figure
* allow specifying peak positions, which will optionally place markers
  and/or labels above each peak position on each dataset.

In addition, changes to
`Matplotlib's rcParams <https://matplotlib.org/tutorials/introductory/customizing.html#matplotlib-rcparams>`_
can be specified, which allows additional control over the style and formatting
of the figures.


Basic Usage
-----------

To use the plotting GUI in mcetl, simply do:

.. code-block:: python

    from mcetl import plotting

    # add some changes to Matplotlib's rcparams
    changes = {
        'font.serif': 'Times New Roman',
        'font.family': 'serif',
        'font.size': 12,
        'xtick.direction': 'in',
        'ytick.direction': 'in'
    }
    plotting.launch_plotting_gui(mpl_changes=changes)


Similar to fitting, a window will then appear to select the data file(s) to be plotted,
and no other setup is required for doing plotting.

When plotting, the image of the plots can be saved to all formats supported by `Matplotlib`_,
including tiff, jpg, png, svg, and pdf. If the `Pillow <https://python-pillow.org/>`_
library is installed, additional options are given to allow saving compressed files for
some formats, such as tiff, in order to reduce the file size.


Advanced Usage
--------------

To be added.

Saving/Reopening Plots
----------------------

Using the GUI, the layout of the plots can be saved to apply to other figures later,
which is referred to in the GUI as saving the Figure Theme. The necessary data will
be saved with the file extension ".figjson", which is just a json file.

Further, the data for the plots can be saved to a csv file so that the entire plot can
be recreated.

To reopen a figure saved through mcetl, do:

.. code-block:: python

    plotting.load_previous_figure()


which will open a window to select the csv and (optionally) figjson files to use.


.. _Matplotlib: https://matplotlib.org
