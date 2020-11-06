=========
Changelog
=========


0.3.0 (2020-11-06)
------------------

This is a minor version with new features, bug fixes, and documentation improvements.

Note: The output of the launch_main_gui function was changed to a single, dictionary output.

New Features
~~~~~~~~~~~~

* Validation of user-input in the GUIs now converts the string inputs into the desired
  data type during validation, rather than requiring further processing after validation.
  Updated all modules for this new change.
* Added the ability to use constraints in the data validation function for user-inputs,
  allowing user-inputs to be bounded between two values.
* Added functions to generate_raw_data.py to create data for pore size analysis (emulating
  the output of the ImageJ software when analyzing images), uniaxial tensile tests,
  and rheometry.
* The plotting GUI now uses "raw_unicode_escape" encoding when saving data to a csv file.
  This has no impact on the data after reloading, but it makes any Unicode more readable
  in the csv file. The module still uses "utf-8" encoding as the default when loading csv
  files, but will fall back to "raw_unicode_escape" in the event "utf-8" encoding errors.

Bug Fixes
~~~~~~~~~

* Fixed issue where an additional set of data entry column labels was erroneously created
  when using a SummaryCalculation object for summarizing data for a sample.
* Fixed issue using sorted() with strings rather than integers when sorting the indices
  of datasets to be deleted when using the plotting GUI.
* Fixed the naming of the standard error for parameters from peak fitting in the output
  Excel file from "standard deviation" to "standard error".

Other Changes
~~~~~~~~~~~~~

* The output of the launch_main_gui function is now a single dictionary. This will allow potential
  changes to the output in later versions to not cause breaking changes.
* The output of launch_main_gui now includes the ExcelWriter object used when saving to Excel.
  This allows access to the Excel file in python after running the launch_main_gui function, in
  case further processing is desired.
* The peak_fitting_gui module now includes full coverage for the data validation of user-inputs
  for all events.

Documentation/Examples
~~~~~~~~~~~~~~~~~~~~~~

* Added DataSource objects to the use_main_gui.py example program for the three new raw data types.
  These analyses are more in-depth than the existing DataSource objects, and involve both
  CalculationFunction and SummaryFunction objects.
* Changed the Changelog to group changes into categories rather than labelling each change with
  FEATURE, BUG, etc.


0.2.0 (2020-10-05)
------------------

This is a minor version with new features, bug fixes, and documentation improvements.

Note: Figure theme (.figtheme) files saved with the plotting GUI in versions < 0.2.0
will not be compatible with versions >= 0.2.0.

New Features
~~~~~~~~~~~~

* Allow marking and labelling peaks in the plotting GUI.

* File searching is more flexible, allowing for different numbers of samples
  and files for each dataset.

* The window location for the plotting GUI is maintained when reopening the window.

* The json files (previous_search.json and the figure theme files saved
  by the plotting GUI) now have indentation, making them more easily read and edited.

* Figure theme files for the plotting GUI now contain a single
  dictionary with all relevant sections as keys. This allows expanding the data
  saved to the file in later versions without making breaking changes.

* Allow selecting which characterization techniques are used when generating raw data.

Bug Fixes
~~~~~~~~~

* Changed save location for previous_search.json to an OS-dependant location, so that
  the file is not overwritten when updating the package.

* Allow doing peak fitting without saving to Excel.

Other Changes
~~~~~~~~~~~~~

* Changed the Excel start row sent to user-defined functions by adding 2 to account
  for the header and subheader rows. Now formulas can directly use the start row variable,
  rather than having to manually add 2 each time. Changed the use_main_gui.py example program
  to reflect this change.

Documentation/Examples
~~~~~~~~~~~~~~~~~~~~~~

* Switched from using plt.pause and a while loop to using plt.show(block=True)
  to keep the peak_fitting and generate_raw_data example programs running while the plots
  are open.

* Made all the documentation figures have the same file extension, and made
  them wider so they look better in the README where their dimensions cannot be modified.


0.1.2 (2020-09-15)
------------------

This is a minor patch with a critical bug fix.

Bug Fixes
~~~~~~~~~

* Fixed issue using sorted() with a dictionary causing the plotting GUI to fail with python 3.7.
  Used sorted(list(dictionary.keys())) instead.


0.1.1 (2020-09-14)
------------------

This is a minor patch with new features, bug fixes, and documentation improvements.

New Features
~~~~~~~~~~~~

* Extended the Unicode conversion to cover any input with "\\" (backslash). This mainly helps with text
  in the plotting GUI, allowing multiline text using "\\n" while still giving the correct behavior when
  using mathtext with matplotlib.

Bug Fixes
~~~~~~~~~

* Fixed how the plotting GUI handles twin axes. Now, the main axis is plotted after the twin axes
  so that the bounds, tick params, and grid lines work correctly for all axes.

* Fixed an error that occurred when a DataSource object would define Excel plot indices that
  were larger than the number of imported and calculation columns.

* New DataSource objects that do not provide a unique_variables input will simply have no
  unique variables, rather than default "x" and "y" variables.

* Fixed an error where column labels were assigned before performing separation functions, which
  potentially creates labels for less data entries than there actually are.

Documentation/Examples
~~~~~~~~~~~~~~~~~~~~~~

* Added a more in-depth summary for the package, more explanation on the usage of the package, and
  screenshots of some of the guis and program outputs to the documentation.

* Added DataSource objects with correct calculations to the example program use_main_gui.py for
  each of the characterization techniques covered by mcetl's raw_data.generate_raw_data function.


0.1.0 (2020-09-12)
------------------

* First release on PyPI.
