=========
Changelog
=========


0.1.2 (2020-09-15)
------------------

This is a minor patch with a critical bug fix.

* FIX: Fixed issue using sorted() with a dictionary causing the plotting gui to fail with python 3.7. Used sorted(list(dictionary.keys())) instead.


0.1.1 (2020-09-14)
------------------

This is a minor patch with bug fixes, new features, and documentation improvements.

* FIX: Fixed how the plotting gui handles twin axes. Now, the main axis is plotted after the twin axes
  so that the bounds, tick params, and grid lines work correctly for all axes.

* FIX: Fixed an error that occurred when a DataSource object would define Excel plot indices that
  were larger than the number of imported and calculation columns.

* FIX: New DataSource objects that do not provide a unique_variables input will simply have no
  unique variables, rather than default 'x' and 'y' variables.

* FIX: Fixed an error where column labels were assigned before performing separation functions, which
  potentially creates labels for less data entries than there actually are.

* FEATURE: Extended the unicode conversion to cover any input with '\\\'. This mainly helps with text
  in the plotting gui, allowing multiline text using '\\n' while still giving the correct behavior when
  using mathtext with matplotlib.

* EXAMPLES: Added DataSource objects with correct calculations to the example program use_main_gui.py for
  each of the characterization techniques covered by mcetl's raw_data.generate_raw_data function.

* DOC: Added a more in-depth summary for the package, more explanation on the usage of the package, and
  screenshots of some of the guis and program outputs.


0.1.0 (2020-09-12)
------------------

* First release on PyPI.

