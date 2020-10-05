=========
Changelog
=========


0.2.0 (2020-10-05)
------------------

This is a minor version with bug fixes, new features, and documentation improvements.

Note: Figure theme (.figtheme) files saved with the plotting gui in versions < 0.2.0
will not be compatible with versions >= 0.2.0.

* FEATURE: Allow marking and labelling peaks in the plotting gui.

* FEATURE: File searching is more flexible, allowing for different numbers
  of samples and files for each dataset.

* FEATURE: The window location for the plotting gui is maintained when
  reopening the window.

* FEATURE: The json files (previous_search.json and the figure theme files saved
  by the plotting gui) now have indentation, making them more easily read and edited.

* FEATURE: Figure theme files for the plotting gui now contain a single
  dictionary with all relevant sections as keys. This allows expanding the data
  saved to the file in later versions without making breaking changes.

* FEATURE: Allow selecting which characterization techniques are used when
  generating raw data.

* FIX: Changed the Excel start row sent to user-defined functions by adding 2 (to allow
  for the header and subheader rows). Now formulas can directly use the start row variable,
  rather than having to manually add 2 each time. Changed the use_main_gui.py example program
  to reflect this change.

* FIX: Changed save location for previous_search.json to an OS-dependant location, so that
  the file is not overwritten when updating the package.

* FIX: Allow doing peak fitting without saving to Excel.

* EXAMPLES: Switched from using plt.pause and a while loop to using plt.show(block=True)
  to keep the peak_fitting and generate_raw_data example programs running while the plots
  are open.

* DOC: Made all the documentation figures have the same file extension, and made
  them wider so they look better in the README where their dimensions cannot be modified.


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

