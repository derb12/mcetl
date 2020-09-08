=====
Usage
=====

To use mcetl in a project::

    import mcetl


To use the peak fitting or plotting modules in mcetl, simply do::

    mcetl.launch_peak_fitting_gui()
    mcetl.launch_plotting_gui()


A window will then appear to select the data file(s) to be fitted or plotted.

Files for example data from characterization techniques can be created using::

    mcetl.raw_data.generate_raw_data()


The characterization techniques produced by that function include:

* X-ray diffraction (XRD)
* Fourier-transform infrared spectroscopy (FTIR)
* Raman spectroscopy
* Thermogravimetric analysis (TGA)
* Differential scanning calorimetry (DSC)


Example python programs showing the use of mcetl are located at https://github.com/derb12/mcetl/tree/master/examples

The examples include:

* Generating raw data
* Using the main GUI
* Using the peak fitting GUI
* Using the plotting GUI
* Reopening a figure saved with the plotting GUI