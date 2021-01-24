Main GUI
========

The Main GUI for mcetl contains options for processing data, fitting data, plotting data,
writing data to Excel, and moving files. Before using the Main GUI, DataSource and Function
objects must be created.

Each :class:`.DataSource` object contains the information for reading files for that DataSource
(such as what separator to use, which rows and columns to use, labels for the columns, etc.),
the calculations that will be performed on the data, and the options for writing the data to
Excel (formatting, placement in the worksheet, etc.).

Function objects come in three types:

* :class:`.PreprocessFunction`: process each data entry as soon as it is imported from the files
* :class:`.CalculationFunction`: process each entry in each sample in each dataset
* :class:`.SummaryFunction`: process each sample or each dataset; performed last

**Naming Conventions**

Within the tutorials, data is sectioned into datasets, samples,
and entries. This is done to help understand the grouping of data. A dataset can be
considered a single, large grouping of data whose contents are all related somehow.
If writing to Excel, each dataset will occupy its own sheet. A sample is a grouping within
a dataset, and can contain multiple data entries. Each entry can be considered as
the contents of a single file, but could be broken down further if desired.

For example, consider a study of the effects of processing temperature and
carbon percentage on the mechanical properties of steel. If there are two
processing temperatures (700°C and 800°C) five different carbon
amounts (0 wt%, 1 wt%, 2 wt%, 3 wt%, and 4 wt%), and three measurements
per sample, then the following grouping could be made:

* Dataset 1 (700°C)

  * Sample 1 (0 wt% carbon)

    * Entry 1 (first measurement file)
    * Entry 2 (second measurement file)
    * Entry 3 (third measurement file)

  * Sample 2 (1 wt% carbon)

    * Entry 1 (first measurement file)
    * Entry 2 (second measurement file)
    * Entry 3 (third measurement file)

  * Sample 3 etc...

* Dataset 2 (800°C)

  * Sample 1 (0 wt% carbon)

    * Entry 1 (first measurement file)
    * Entry 2 (second measurement file)
    * Entry 3 (third measurement file)

  * Sample 2 etc...


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   creating_functions
   creating_datasources
   main_gui
