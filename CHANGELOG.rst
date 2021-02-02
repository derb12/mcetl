=========
Changelog
=========

Version 0.4.2 (2021-02-02)
--------------------------

This is a minor patch with a critical bug fix.

Bug Fixes
~~~~~~~~~

* Fixed a crash when merging styled cells due to a change in openpyxl v3.0.6. Now
  cells are merged first, and then styled. The fix is fully compatible with all
  covered versions of openpyxl (any >= v2.4).

Version 0.4.1 (2021-01-26)
--------------------------

This is a minor patch with critical bug fixes.

Bug Fixes
~~~~~~~~~

* Fixed grouping of column labels for the main GUI when there are more than
  9 entries for a sample.
* Fixed processing of regex separators, such as ``\s+`` when importing data.

Version 0.4.0 (2021-01-24)
--------------------------

This is a minor version with new features, bug fixes, deprecations,
and documentation improvements.

New Features
~~~~~~~~~~~~

* The data import window extended the support of importing from spreadsheet-like
  files beyond just xlsx and now supports importing from any spreadsheet-like
  file format supported by pandas.read_excel (eg. xls, xlsm, xlsb, ods, etc). For
  spreadsheet formats not supported by openpyxl, and thus not supported by the default
  mcetl installation, it will require installing the appropriate library. For
  example, to read xls files, the xlrd library would need to be installed.
* Greatly improved load time of spreadsheets when using the data import window.
  Now, only one sheet is loaded into memory at a time (if supported by the engine
  used for reading the spreadsheet).
* The data import window now supports importing from fixed-width files.
* Column labels and Excel plot indices are now specified individually when using
  the main GUI. This allows processing uneven-sized data and working with already
  processed data.
* Column labels are now added to the dataframes in launch_main_gui if any processing
  step is specified besides moving files.
* Excel styles no longer have to be NamedStyles, allowing not adding styles to the
  output Excel workbook. Also, non-named styles are ~50% faster for writing to Excel.
* Added test_excel_styles method to DataSource, to allow testing whether the
  input styles will create valid Excel styles.
* Added a more usable window for manual file selection, which is used for launch_main_gui
  launch_fitting_gui, and launch_plotting_gui.
* The main GUI will now save the previous search for each DataSource separately,
  with a filename of previous_files_(DataSource.name).json (eg. prevous_files_XRD.json).
* Allow using all models available from lmfit and mcetl to use as the background for
  fitting. The few models that need kwargs during initialization now allow selecting them in the GUI.
* Added several functions to mcetl.fitting.fitting_utils to allow using the lmfit model names
  within code while displaying shortened versions in GUIs. Also, a full list of
  models available through lmfit and mcetl are generated at runtime, so that the
  available models match for different versions.
* Created an ExcelWriterHandler class, which is used to correctly handle opening and
  saving existing Excel files and to apply styles to the Excel workbook.
* Allow specifying changes to Matplotlib's rcParams for fitting when using launch_main_gui.
  If None are specified, will use the selected DataSource's figure_rcparams attribute.
* Allow columns to be removed by PreprocessFunctions, which also correctly updates
  the unique variable references.
* When importing data, columns of the imported data are now sorted following the user-input
  column numbers (eg. if the user-specified columns were 1, 0, 2, then the data would first
  be imported with columns ordered as 0, 1, 2 and then the columns are rearranged to 1, 0, 2.
  Note that column names are still specified as ascending numbers, so even though the data
  corresponds to columns 1, 0, 2 in the data file, the column names in the pandas DataFrame
  are still 0, 1, 2). Note that this feature was already implemented when importing from
  spreadsheets, but is now extended to all other formats.
* Allow using Matplotlib keybindings for most embedded figures, such as within the fitting GUI.
  This allows doing things like switching axis scales from linear to log.
* Added more fit descriptors to the saved Excel file from fitting, such as whether the
  fit converged and the number of independant variables.
* Added numerical calculations for area, extremum, mode, and full-width-at-half-maximum
  when doing data fitting. These calculations are performed on the peak models after
  fitting, and are included to at least give an estimate of their values for models
  that do not have analytical solutions, like Breit-Wigner-Fano, Moffat, and skewed Gaussian/Voigt.
* Made the file import options more flexible by allowing user to select whether or not
  to use same import options for all files (option is ignored for spreadsheet-like files).
  Also allow inputting previous inputs for the file import function, so that any changes
  to the defaults can be maintained, especially helpful when manually opening files for
  fitting or plotting.
* Added a modified Breit-Wigner-Fano peak model for fitting.
* The fitting GUI now allows confirmation of the fit results before proceeding. A plot of
  the fit results and a printed out fit report are given, and the user can select to go
  back and redo the fit.
* Allow inputting Excel styles in launch_fitting_gui so that custom styles can be used
  when writing fit results to Excel when using launch_fitting_gui directly.
* Created a EmbeddedFigure class in plot_utils for easily creating windows with
  embedded Matplotlib figures that optionally have events. Is easily subclassed to
  create custom windows with embedded figures and event loops.

Bug Fixes
~~~~~~~~~

* DPI awareness is no longer set immediately upon importing mcetl on Windows
  operating systems. That way, users can decide whether or not to set dpi
  awareness. To set dpi awareness, users must call mcetl.set_dpi_awareness()
  before opening any GUIs.
* Correctly handle PermissionError for the main GUI when deciding which folder
  to save file searches to and when writing file searches to file. PermissionError
  is still raised if read access is not granted, so that user is made aware that
  they need to set the folder to something that grants access.
* Added a function in utils for converting pandas series to numpy with a specific
  dtype to reduce the chance of error occuring during conversion.
* Fixed an issue when plotting in Excel with a log scale if one of the specified bounds was <= 0.
* The data import window will only attempt to assign indices for a DataSource's
  unique variables if processing.
* The entry and sample separation columns that are added when using the main GUI if
  processing and writing to Excel are now removed when splitting the merged dataframes
  back into individual entries, so that the returned DataFrames contain only the
  actual data.
* Ensured that Excel sheet names are valid.
* Simplified writing to csv for plotting GUI. Removed the column indices when reading/writing
  csv data within the plotting GUI. Now, columns are just directly taken from the data.
* Switched to using df.iloc[:, col_number] rather than df[col_number] to get columns
  by their indices so that dataframes with repeated column names will not produce errors.
* Made it so that '.' is removed from the user-input file extension when doing file searching
  only if the '.' is the first character in the string. This way, file types with multiple
  extensions, like tar.gz, are now possible to use.
* The raw data generated for Raman was accidently being saved as a csv
  rather than as a tab-separated txt file.
* Fixed issue when using lmfit.models.ConstantModel for fitting, which
  gives a single value rather than an array. Now, replace the single value
  with an array with the same size as the data being fit so that it does not
  cause errors when plotting.
* Fixed IndexError that occurred when using the fitting GUI and trying
  to fit residuals.
* Fixed issue where Voigt models with manual peak selection and vary gamma parameter
  set to True would not set an initial value for gamma.

Other Changes
~~~~~~~~~~~~~

* Reduced import time of mcetl. On my machine, the import time for version 0.4.0
  is ~80% less than version 0.3.0.
* Replaced sympy with asteval for parsing user expressions when creating secondary
  axes for the plotting GUI. This requires the user to input forward and backward
  expressions, but otherwise requires no changes. Also, it technically drops a requirement
  for mcetl, since asteval is already required for lmfit.
* Reordered package layout. Moved all fitting related files to a mcetl.fitting,
  and moved all plotting related files to mcetl.plotting. This will allow expansion
  of the fitting and plotting sections without burdening the main folder.
* Renamed peak_fitting_gui to fitting_gui since I intend to extend the fitting
  beyond just peak fitting.
* Made all of the methods that are only internally used private for DataSource and
  the Function objects, so that users do not use them.
* Updated required versions for several dependencies.
* Added Python 3.9 to the supported Python versions.
* Created mcetl.fitting.models, which can be filled later with any additional models.
  Put the modified Breit-Wigner-Fano function in fitting.models.
* Created mcetl.plot_utils that contains all helper functions and classes for plotting.
* The plotting GUI switched back to using "utf-8" encoding when saving data to a csv file
  (was made to use "raw_unicode_escape" in v0.3.0).

Deprecations/Breaking Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Renamed SeparationFunction to PreprocessFunction to make its usage more clear.
* Changed the file extension for the theme files for the plotting GUI from ".figtheme"
  to ".figjson" to make it more clear that it is just a json file. Converting existing
  files should be easy, just change the extension.
* mcetl.launch_peak_fitting_gui() and mcetl.launch_plotting_gui() are no longer valid.
  Instead, use 'from mcetl import fitting, plotting; fitting.launch_fitting_gui();
  plotting.launch_plotting_gui()'.
* The keyword arguments 'excel_writer_formats' and 'figure_rcParams' for DataSource
  were changed to 'excel_writer_styles' and 'figure_rcparams', respectively.
* DataSource only accepts keyword arguments besides the first argmument, which
  is the DataSource's name.
* The keyword argument 'peaks_dataframe' for mcetl.fitting.fit_to_excel was changed to
  'values_dataframe' to make its usage more clear.
* mcetl.fitting.peak_fitting.fit_peaks no longer takes the keyword 'poly_n' as an argument. Instead, the
  function takes the keyword 'background_kwargs' which is a dictionary for background keyword
  arguments, allowing any model to be used as the background. For example, to get the same behavior
  as with the old 'poly_n' keyword, the new input would be background_kwargs={'degree': 1}.
* Renamed datasource.py to data_source.py. This should have little effect on user code
  since the DataSource object is available through the main mcetl namespace.
* Renamed the keyword argmument vary_Voigt for mcetl.fitting.peak_fitting.fit_peaks to vary_voigt.
* The constants mcetl.main_gui.SAVE_FOLDER and mcetl.fitting.peak_fitting._PEAK_TRANSFORMS
  are used instead of the functions mcetl.main_gui.get_save_location (now _get_save_location)
  and mcetl.fitting.peak_fitting.peak_transformer (now _peak_transformer), respectively.
  This way, do not need to repeatedly call the functions, and their contents can be alterred
  by users, if desired.

Documentation/Examples
~~~~~~~~~~~~~~~~~~~~~~

* Improved the api documentation, added tutorials, and improved the overall documentation.
* Updated example programs for all of the new changes in version 0.4.0.
* Added an example program showing how to use just mcetl.fitting.fit_peaks to do
  peak fitting instead of using the fitting GUI.
* Changed the readthedocs config to create static htmlzip files in addition
  to pdf files each time the documentation is built.


Version 0.3.0 (2020-11-08)
--------------------------

This is a minor version with new features, bug fixes, deprecations, and documentation improvements.

New Features
~~~~~~~~~~~~

* Added functions to generate_raw_data.py to create data for pore size analysis (emulating
  the output of the ImageJ software when analyzing images), uniaxial tensile tests,
  and rheometry.
* The plotting GUI now uses "raw_unicode_escape" encoding when saving data to a csv file.
  This has no impact on the data after reloading, but it makes any Unicode more readable
  in the csv file. The module still uses "utf-8" encoding as the default when loading csv
  files, but will fall back to "raw_unicode_escape" in the event "utf-8" encoding errors.
* Validation of user-input in the GUIs now converts the string inputs into the desired
  data type during validation, rather than requiring further processing after validation.
  Updated all modules for this new change.
* Added the ability to use constraints in the data validation function for user-inputs,
  allowing user-inputs to be bounded between two values.

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
  This allows access to the Excel file in Python after running the launch_main_gui function, in
  case further processing is desired.
* The peak_fitting_gui module now includes full coverage for the data validation of user-inputs
  for all events.

Deprecations/Breaking Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The output of the launch_main_gui function was changed from a tuple of items to a single, dictionary output.

Documentation/Examples
~~~~~~~~~~~~~~~~~~~~~~

* Added DataSource objects to the use_main_gui.py example program for the three new raw data types.
  These analyses are more in-depth than the existing DataSource objects, and involve both
  CalculationFunction and SummaryFunction objects.
* Changed the Changelog to group changes into categories rather than labelling each change with
  FEATURE, BUG, etc.


Version 0.2.0 (2020-10-05)
--------------------------

This is a minor version with new features, bug fixes, deprecations, and documentation improvements.

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

Deprecations/Breaking Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Figure theme (.figtheme) files saved with the plotting GUI in versions < 0.2.0
  will not be compatible with versions >= 0.2.0.

Documentation/Examples
~~~~~~~~~~~~~~~~~~~~~~

* Switched from using plt.pause and a while loop to using plt.show(block=True)
  to keep the peak_fitting and generate_raw_data example programs running while the plots
  are open.

* Made all the documentation figures have the same file extension, and made
  them wider so they look better in the README where their dimensions cannot be modified.


Version 0.1.2 (2020-09-15)
--------------------------

This is a minor patch with a critical bug fix.

Bug Fixes
~~~~~~~~~

* Fixed issue using reversed() with a dictionary causing the plotting GUI to fail with Python 3.7.
  Used reversed(list(dictionary.keys())) instead.


Version 0.1.1 (2020-09-14)
--------------------------

This is a minor patch with new features, bug fixes, and documentation improvements.

New Features
~~~~~~~~~~~~

* Extended the Unicode conversion to cover any input with ``"\"``. This mainly helps with text
  in the plotting GUI, such as allowing multiline text using ``"\n"``, while still giving the
  correct behavior when using mathtext with Matplotlib.

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


Version 0.1.0 (2020-09-12)
--------------------------

* First release on PyPI.
