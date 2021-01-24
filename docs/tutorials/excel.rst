================
Writing to Excel
================

mcetl gives the option to write results to Excel when using either
:func:`mcetl.launch_main_gui() <mcetl.main_gui.launch_main_gui>` or
:func:`fitting.launch_fitting_gui() <mcetl.fitting.fitting_gui.launch_fitting_gui>`
from :mod:`mcetl.fitting`. This section covers some information that is good
to know when writing to Excel.

Appending to Existing File
--------------------------

mcetl allows appending to existing Excel files, but it should be used with caution,
namely for two reasons: high memory usage, and potentially losing Excel objects.

Memory Usage
~~~~~~~~~~~~

When appending to an existing Excel file, mcetl loads the Excel workbook using
the Python library `openpyxl <https://openpyxl.readthedocs.io/en/stable/>`_;
however, the conversion from Excel to Python
can increase the necessary memory by more than an order of magnitude. For example,
an Excel file that is 10 MB on disk will require several hundred MB of RAM when
opened in Python. Users should to be aware of this fact, so that a MemoryError
does not occur when loading existing files. If in doubt, write to a new file
using mcetl, and then copy the sheets to the desired file within Excel.

Losing Excel Objects
~~~~~~~~~~~~~~~~~~~~

openpyxl can convert the majority of objects within an Excel file, such as cell
values and styles, defined styles for the workbook, and charts. If the existing
Excel file is simply tabulated data and charts, then it should have no issues.
However, there are some Excel objects which openpyxl cannot read, such as shapes
and inserted equations, so these non-convertable objects will be lost when
appending to a file.

If there is any doubt whether openpyxl can read an object within an Excel file, it
is a good idea to create a copy of the file before appending to it with mcetl to
test whether all objects are transferred, or use mcetl to write to a new file and
then copy its contents to the existing file using Excel.

.. _excel-style-guide:

Excel Styles
------------

When writing to Excel, using either
:func:`mcetl.launch_main_gui() <mcetl.main_gui.launch_main_gui>` (using a
:class:`.DataSource` to set the style) or
:func:`fitting.launch_fitting_gui() <mcetl.fitting.fitting_gui.launch_fitting_gui>`,
the style of the cells in the Excel workbook can be customized.
The :doc:`gallery section <../gallery>` of the documentation shows two
spreadsheets showing the default styles used for both the launch_main_gui function
and the launch_fitting_gui function.

There are seven different styles that can be specified, each with an even and odd variant
(eg. 'header_even' and 'header_odd'), allowing for fourteen total styles to be
specified, making the Excel output visually distinct. The base names for
the seven styles are:

* 'header': The style used for the headers.
* 'subheader': The style used for the subheaders.
* 'columns': The style for all of the data columns.
* 'fitting_header': The style used for the headers when writing results from fitting.
* 'fitting_subheader':The style used for the subheaders when writing fit results.
* 'fitting_columns': The style for the data and parameter columns for fit results.
* 'fitting_descriptors': The style for the two columns specifying descriptions about
  the fit (whether it was successful, the goodness of fit, etc.).

The styles with the 'fitting' prefix are only used if writing results from fitting
to Excel.

The styles are specified using a dictionary containing
the above base names with '_even' or '_odd' appended (eg. 'header_even') as keys, and either
a nested dictionary or an openpyxl :class:`~openpyxl.styles.named_styles.NamedStyle` object as values.

Using Named Styles
~~~~~~~~~~~~~~~~~~

To make the styles usable in the output Excel file, there are two options.
The first is to use openpyxl :class:`~openpyxl.styles.named_styles.NamedStyle`
objects in the dictionary. The second is to use a dictionary, and include the
'name' key in the dictionary to set the NamedStyle's name.

.. note::
   Once a Named Style is added to an Excel workbook, it cannot be overwritten using mcetl.
   That means that if appending to an existing workbook and trying to set a Named Style to
   the name of an existing style in the workbook, the format of the existing style will be used
   rather than the input style. To fix this, just delete or rename any styles that need
   to be changed within the Excel workbook before writing more data using mcetl.

Some examples of valid inputs that create NamedStyles are shown below:

.. code-block:: python

    from openpyxl.styles import (
        Alignment, Border, Font, NamedStyle, PatternFill, Side
    )

    partial_styles = {
        # can use an openpyxl NamedStyle
        'header_even': NamedStyle(
            name='Even Header',
            font=Font(size=12, bold=True),
            fill=PatternFill(fill_type='solid', start_color='F9B381', end_color='F9B381'),
            border=Border(bottom=Side(style='thin')),
            alignment=Alignment(horizontal='center', vertical='center', wrap_text=True),
            number_format='0.00'
        ),
        # or use a dictionary with a 'name' key
        'header_odd': {
            'name': 'Odd Header',
            'font': Font(size=12, bold=True),
            'fill': PatternFill(fill_type='solid', start_color='73A2DB', end_color='73A2DB'),
            'border': Border(bottom=Side(style='thin')),
            'alignment': Alignment(horizontal='center', vertical='center', wrap_text=True),
            'number_format': '0.00'
        },
        # can replace all openpyxl objects with dict to not even need to import openpyxl
        'subheader_odd': {
            'name': 'Odd Subheader',
            'font': dict(size=12, bold=True),
            'fill': dict(fill_type='solid', start_color='73A2DB', end_color='73A2DB'),
            'border': dict(bottom=dict(style='thin')),
            'alignment': dict(horizontal='center', vertical='center', wrap_text=True),
            'number_format': '0.00'
        },
        # can also reference already created NamedStyles
        'subheader_even': 'Odd Subheader'
    }

Using Anonymous Styles
~~~~~~~~~~~~~~~~~~~~~~

Anonymous styles will properly format the cells in the output Excel file,
but their names will not be available styles in the Excel file. In addition,
anonymous styles also have a much faster write time than Named Styles, taking
~ 50% less time to write. So if processing speed is a concern, using anonymous
styles is a good choice.

An easy way to create anonymous styles is to first create the NamedStyle, like
above, and then replace NamedStyle with dict and remove the 'name' key. Doing
so with the styles from the previous section gives:

.. code-block:: python

    partial_styles = {
        # replace NamedStyle with dict and remove name=''
        'header_even': dict(
            font=Font(size=12, bold=True),
            fill=PatternFill(fill_type='solid', start_color='F9B381', end_color='F9B381'),
            border=Border(bottom=Side(style='thin')),
            alignment=Alignment(horizontal='center', vertical='center', wrap_text=True),
            number_format='0.00'
        ),
        # remove the 'name' key
        'header_odd': {
            'font': Font(size=12, bold=True),
            'fill': PatternFill(fill_type='solid', start_color='73A2DB', end_color='73A2DB'),
            'border': Border(bottom=Side(style='thin')),
            'alignment': Alignment(horizontal='center', vertical='center', wrap_text=True),
            'number_format': '0.00'
        },
        # remove 'name' and replace all openpyxl objects with dict to not even need to import openpyxl
        'subheader_odd': {
            'font': dict(size=12, bold=True),
            'fill': dict(fill_type='solid', start_color='73A2DB', end_color='73A2DB'),
            'border': dict(bottom=dict(style='thin')),
            'alignment': dict(horizontal='center', vertical='center', wrap_text=True),
            'number_format': '0.00'
        }
    }

Using Unformatted Styles
~~~~~~~~~~~~~~~~~~~~~~~~

To make a style unformatted (use the Excel default format), simply set its value
to either None or an empty dictionary.

.. code-block:: python

    # both produces same, default style in the output Excel file
    partial_styles = {'header_even': {}, 'header_odd': None}

To make all styles unformatted, do one of the following dictionary comprehensions:

.. code-block:: python

    from mcetl import DataSource

    unformatted_styles = {style: {} for style in DataSource.excel_styles.keys()}
    unformatted_styles2 = {style: None for style in DataSource.excel_styles.keys()}

Validate Styles
~~~~~~~~~~~~~~~

To ensure that the input style dictionary is valid, DataSource provides the
:meth:`~mcetl.data_source.DataSource.test_excel_styles` static method, which will
indicate the keys of all of the styles are not valid and their error tracebacks:

.. code-block:: python

    from mcetl import DataSource
    from openpyxl.styles import Font, NamedStyle

    good_styles = {
        'header_even': NamedStyle(
                name='header_even',
                font=Font(size=12, bold=True),
            ),
        'header_odd': {
            'font': dict(size=12, bold=True),
        }
    }

    bad_styles = {
        'header_even': dict(
                name='Header',
                font=Font(size=12, bold=True),
                number_format=1 # wrong since number_format must be a string or None
            ),
        'header_odd': {
            'font': dict(size='string'), # wrong since font size must be a float
        }
    }

    DataSource.test_excel_styles(good_styles) # returns True
    DataSource.test_excel_styles(bad_styles) # returns False
