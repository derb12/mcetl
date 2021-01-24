====================
Creating DataSources
====================

:class:`.DataSource` objects are the main controlling object when using mcetl's main GUI.

DataSource Inputs
-----------------

This section groups the inputs for DataSource by their usage, and explains
possible inputs. The only necessary input for a DataSource is its ``name``, which
is displayed in the GUI when selecting which DataSource to use.

Note that most inputs for DataSource will supply defaults for entering information
into the GUIs, and can be overwritten when using the main GUI.

.. contents:: **Sections**
    :depth: 2
    :local:


Using Raw Data Files
~~~~~~~~~~~~~~~~~~~~

File Searching
^^^^^^^^^^^^^^

The keyword ``file_type`` should be a string of the file extension of data files for
the DataSource, such as 'csv' or 'txt'. When searching for files, either manually
or using a keyword search, the file extension is used to limit the number of
files to select.

The keyword ``num_files`` should be an interger telling how many files should
be associated for each sample for the DataSource. Only used if using a keyword
search for files.

Importing Data
^^^^^^^^^^^^^^

``column_numbers`` should be a list of integers telling which
columns to import from the raw data file. The order of columns
follows the ordering within column_numbers, so [0, 1, 2] would
import the first, second, and third columns from the data file
and keep their order, while [1, 2, 0] would still import the
three columns but rearrange them so that the first column is
now the third column.

``start_row`` and ``end_row`` should be integers telling which
row in the raw data file should be the first and last row, respectively.
Note that end_row counts up from the bottom of the data file, so
that end_row=0 would be the last row, end_row=1 would be the
second to last row, etc.

``separator`` should be a string designating the separator
used in the raw data file to separate columns. For example,
comma-separated files (csv) have ',' as the separator.

See the :doc:`Importing Data section <../importing_data>` of the tutorial
for more in depth discussion on importing data.

Processing Data
~~~~~~~~~~~~~~~

Functions
^^^^^^^^^

The keyword ``functions`` should be a list or tuple of all the PreprocessFunctions,
CalculationFunctions, and/or SummaryFunctions that are needed for processing data
for the DataSource. PreprocessFunctions will be performed first, followed by
CalculationFunctions and then SummaryFunctions. For each Function type, the order
in which the functions are performed is according to their ordering in the functions
input.

The keyword ``unique_variables`` should be a list of strings designating
the names to give to columns that contain necessary data. The Function objects of
the DataSource will then be able set their target_columns to those columns. For example,
in the previous tutorial section on creating Function objects, the example Function
objects had target_columns such as 'data' and 'diameter' from imported data. The
'data' and 'diameter' columns would be the DataSource's unique_variables.

``unique_variable_indices`` should be a list of intergers telling the indices
of the columns within column_numbers belong to the unique_variables. For
example, if column_numbers was [1, 2, 0], and Column 2 contained the data
for the unique variable, then unique_variable_indices would be [1] since
Column 2 is at index 1 within column_numbers.

Column Names
^^^^^^^^^^^^

The keyword ``column_labels`` should be a list of strings, designating the
default column labels for a single data entry. The column labels should
accomodate both the names of the imported data columns, and all of the columns
added by CalculationFunctions and SummaryFunctions.

To aid setting up the column_labels, a DataSource instance has the method
:meth:`~.DataSource.print_column_labels_template`, which will tell how
many labels belong to imported data, CalculationFunctions, sample-summary
SummaryFunctions, and dataset-summary SummaryFunctions, and give a template for the
column_labels input.

The example below shows creating a DataSource for tensile testing, and uses
the tensile_calc, stress_sample_summary, stress_dataset_summary Function objects
created in the previous tutorial section on creating Function objects.

.. code-block:: python

    import mcetl

    tensile = mcetl.DataSource(
        'Tensile Test',
        functions=[tensile_calc, stress_sample_summary, stress_dataset_summary],
        unique_variables=['stress', 'strain'],
        column_numbers=[4, 3, 0, 1, 2],
        unique_variable_indices=[1, 0],
        # column_labels only currently has labels for the imported data, not the Functions
        column_labels=['Strain (%)', 'Stress (MPa)', 'Time (s)', 'Extension (mm)', 'Load (kN)'],
    )

    tensile.print_column_labels_template()


The ``label_entries`` keyword can be set to True to append a number to the column labels of
each entry in a sample if there is more than one entry. For example, the
column label 'data' would become 'data, 1', 'data, 2', etc.

Figure Appearance
^^^^^^^^^^^^^^^^^

The ``figure_rcparams`` keyword can be used to set the style of figures for
fitting and plotting using
`Matplotlib's rcParams <https://matplotlib.org/tutorials/introductory/customizing.html#matplotlib-rcparams>`_.
The input should be a dictionary, like below:

.. code-block:: python

    example_rcparams = {
        'font.serif': 'Times New Roman',
        'font.family': 'serif',
        'font.size': 12,
        'xtick.direction': 'in',
        'ytick.direction': 'in'
    }


Excel Output
~~~~~~~~~~~~

Location within the Workbook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Where data is placed within the output Excel file is determined by the
``excel_column_offset`` and ``excel_row_offset`` keywords, which expect
integers. By default, data is placed in the workbook starting at cell A1.
To change the starting cell to D8, for example, the excel_column_offset
would be 3 and the excel_row_offset would be 7.

Spacing between Samples and Entries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To place empty columns in the Excel workbook to help visually separate the
various samples and entries, use ``entry_separation`` and ``sample_separation``.
For example, to place one empty columns between each entry in a sample, and two
empty columns between each sample in a dataset, use entry_separation=1 and
sample_separation=2, respectively.

Excel Plot Options
^^^^^^^^^^^^^^^^^^

The ``xy_plot_indices`` keyword should be a list with two integers, telling
the indices of the columns to use for the x- and y-axes when plotting each
entry in Excel.
Note that the the indices can refer to the columns from imported data or from
columns added by CalculationFunctions. For example, if three columns were imported,
and two additional columns were added by CalculationFunctions, then the total
column indices would be [0, 1, 2, 3, 4] and plot indices could be [0, 1] or [1, 4],
etc.

Sample SummaryFunctions and dataset SummaryFunctions are also allowed to be plotted
in Excel and will use the xy_plot_indices.

Specifying Excel Styles
^^^^^^^^^^^^^^^^^^^^^^^

The styles used in the output Excel file are described by using the
``excel_writer_styles`` keyword. See the
:ref:`Excel Styles section <excel-style-guide>` of the tutorial
for discussion on how to change the style of output Excel file.

Examples
--------

The examples below show creating DataSources using some of the keyword inputs
discussed above as well as the Function objects created in the previous
tutorial section on creating Function objects.

.. code-block:: python

    import mcetl

    xrd = mcetl.DataSource(
        'X-ray Diffraction',
        column_labels=['2\u03B8 (\u00B0)', 'Intensity (Counts)', 'Offset Intensity (a.u.)'],
        functions=[offset],
        column_numbers=[1, 2],
        unique_variables=['data'],
        unique_variable_indices=[1],
        start_row=1,
        end_row=0,
        separator=',',
        xy_plot_indices=[0, 2],
        file_type='csv',
        num_files=1,
        entry_separation=1,
        sample_separation=2,
    )

    tensile = mcetl.DataSource(
        'Tensile Test',
        functions=[tensile_calc, stress_sample_summary, stress_dataset_summary],
        column_numbers=[4, 3, 0, 1, 2],
        unique_variables=['stress', 'strain'],
        unique_variable_indices=[1, 0],
        xy_plot_indices=[0, 1],
        column_labels=[
            'Strain (%)', 'Stress (MPa)', 'Time (s)', 'Extension (mm)', 'Load (kN)', # imported data
            '', 'Elastic Modulus (GPa)', # CalculationFunction
            'Property', 'Average', 'Standard Deviation', # sample SummaryFunction
            'Sample', 'Elastic Modulus (GPa)', '' # dataset SummaryFunction
        ],
        start_row=6,
        separator=',',
        file_type='txt',
        num_files=3,
        entry_separation=2,
        sample_separation=3
    )
