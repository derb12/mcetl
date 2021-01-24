===========
Fitting GUI
===========

The fitting submodule of mcetl provides functions and GUIs for fitting data.
mcetl uses the `lmfit`_ library for fitting data using non-linear least-squares
minimization. For in-depth discussion on the theory and available methods/models for
curve fitting, the `lmfit`_ documentation is highly recommended.

Please note that the fitting submodule is included in mcetl to allow a fairly basic
curve fitting option. If other curve fitting software is available, such as
`fityk <https://fityk.nieto.pl>`_ or `Origin <https://originlab.com>`_, the
author highly recommends their usage instead of mcetl.

Basic Usage
-----------

To use the fitting GUI in mcetl, simply do:

.. code-block:: python

    from mcetl import fitting
    fitting.launch_fitting_gui()


A window will then appear to select the data file(s) to be fit and the
Excel file for saving the results. No other setup is required.

Usage of the fitting GUI is fairly straightforward, and the GUI should
notify the user if any issues occur and allow correction without terminating
the program.

After doing the fitting, the fit results and plots will be saved to Excel.

.. note::
   Currently, mcetl only provides functions and a GUI for performing peak
   fitting. A later release of mcetl (v0.5 or v0.6) is slated to add
   general fitting routines, to allow fitting arbitrary models to data.
   Further, that release should also add the option to save the fitting
   options from the GUI to a file so that the options can be reused for
   fitting other data, similar to how the plotting GUI does it.


Advanced Usage
--------------

To be added.


.. _lmfit: https://lmfit.github.io/lmfit-py/
