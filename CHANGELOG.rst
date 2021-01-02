=========
Changelog
=========


Version 0.4.0 (2021-01-04)
--------------------------

This is a minor version with new features, bug fixes, deprecations, and documentation improvements.

New Features
~~~~~~~~~~~~

* Column labels now specified individually
  Column labels and Excel plot indices are now specified individually. This allows processing uneven-sized data and working with already processed data. HUGE update.
* Added manual file selection to launch_main_gui
  Changed the file selection in the main menu of the main gui to use either manual selection of files, keyword search for files, or previous files. Cleaned up the file selection/import in utils.
* Added/improved manual file selection
  Added a much more usable manual file selection for use in utils.select_multiple_files. Also added manual file selection in file_organizer.py that allows selecting files for all datasets and samples within one window.
* Improve usability of multiple GUIs
  Improved multiple GUIs: 1) the first window of the main gui now uses textwrap for the DataSources in case their names are too long, and includes a scrollbar; 2) the results window for fitting now uses expand_x/y to fill the entire tab rather than guessing using character width/height; 3) the peak selector window now aligns the buttons and checks correctly.
* Each DataSource keeps a previous search
  The main GUI will now save the previous search for each DataSource separately, with a filename of previous_search_(DataSource.name).json (eg. prevous_search_XRD.json).
* Pass kwargs for background for fitting
  For peak fitting, all models in lmfit and mcetl are available to use as the background. The few models that need kwargs during initialization now allow selecting them in the GUI.
* Simplified the use of model names for fitting
  Added several functions to fitting_utils to allow using the lmfit model names within code while displaying shortened versions in GUIs. Also, a full list of models available through lmfit and mcetl are generated at runtime, so that the available models match for different versions.
* Reduce import time by lazy importing openpyxl
  Placed openpyxl imports within the functions that write to Excel since it is not needed otherwise. Wrote a function for converting 1-index numbers to column letters to replace openpyxl's implementation. Due to this commit and the previous one with ExcelWriterHandler, the import time of mcetl is reduced ~35%, bringing the total import time reduction since v0.3.0 to ~75%.
* Created ExcelWriterHandler class
  Created an ExcelWriterHandler class, which is used to correctly handle opening and saving existing Excel files and to apply openpyxl NamedStyles to the Excel workbook. The new class allows removing openpyxl imports in several other modules and removes repeated code for creating pd.ExcelWriter objects.
* Improved fit confirmation window
  The confirmation window for fitting now includes a separate tab with the fit report for the fitting. Also improved the plot by adding residuals, and allowing the background to be subtracted, if the model has a background.
* Allow specifying fitting rcparams for main gui
  The launch_main_gui function now allows inputting a dictionary of changes for matplotlib's rcparams to apply only when doing fitting.
* Selecting Excel plot columns updates labels
  Selecting the Excel columns to use for plotting automatically updates the axis label corresponding to the selected column. Also made the column labels line up a little better and increased the input space for column labels.
* Allow PreprocessingFunctions to delete columns
  Renamed SeparationFunction to PreprocessingFunction to give it a more general meaning. Allow columns to be removed by PreprocessingFunctions, which update the unique variable references. If not processing, the column numbers for the deleted columns are removed from the DataSource before showing the import window. Made the string representation for DataSource and Function objects better and removed their repr. Added doc strings for everything in mcetl.functions.
* Allow sorting columns during import
  Columns of the imported data are now sorted following the user-input column numbers. Note that this feature was already implemented for Excel formats, but is now extended to all other formats.
* Allow using matplotlib keybindings
  Added the ability to use matplotlib keybindings to trigger events within embedded figures. Use the default toolbar for the fitting figures, since the subplot tool is sometimes needed when tight layout fails.
* Added more fit descriptions to Excel output
  Added additional fit descriptors to the saved Excel file, such as whether the fit converged and the number of independant variables.
* Added numerical calculations for peak params
  Added numerical calculations for area, max/min, mode, and fwhm. These calculations are performed on the peak models after fitting, and are included to at least give an estimate for their values for models that do not have analytical solutions, like BWF and skewed Gaussian/Voigt.
* File import options are more flexible
  Made the file import options more flexible when used from the main gui by allowing user to select whether or not to use same import options for all files (option is disabled for Excel files). Also allow inputting previous inputs for the file import function, so that any changes to the defaults can be maintained, especially helpful when manually opening files for fitting or plotting.
* Added numerical integration for peaks
  Added numerical integration as an added parameter for all peak models after fitting in order to estimate the area for models that don't have amplitude=area (such as BWF, Moffat). Removed the code in fitting_gui that changed the 'amplitude' parameter to 'area' since amplitude is not always area.
* Added BWF function for peak fitting
  Added a modified Breit-Wigner-Fano peak model for fitting. Fixed issue where Voigt models with manual peak selection and vary gamma parameter set to True would not set an initial value for gamma.
* Allow redoing fitting
  The fitting gui now allows confirmation of the fit results before proceeding. Divided the fit_dataframe function into several smaller functions to make it easier to read and change.
* Allow inputting excel styles in launch_fitting_gui
  Added the ability to input custom styles to use when writing fit results to Excel when using launch_fitting_gui directly.
* Reordered module layout
  Moved all fitting related files to a new "fitting" folder and moved all plotting related files to a new "plotting" folder. This will allow expansion of the fitting and plotting sections without burdening the main folder. Renamed peak_fitting_gui to fitting_gui since I intend to extend the fitting beyond just peak fitting.
* Reduced module import timing
  Reduced the time it takes to import mcetl by ~ 60% by removing the peak fitting and plotting guis from the main namespace. Also moved the sympy import in the plotting gui to within its own function since it will rarely be called and takes a significant time to import.
* Added validations for plotting gui
  Added validations for some windows for the plotting gui. The main window still needs its validations corrected.
* Made draw_figure_on_canvas more flexible
  Made the draw_figure_on_canvas function more flexible by allowing kwargs for packing the figure on the window, and allow using the same canvas for both the figure and the toolbar.
* Created class for embedded figures
  Created a class in plotting_utils for easily creating windows with embedded matplotlib figures that optionally have events. Created subclasses in peak_fitting for selecting peaks and selecting background points for doing peak fitting, and a subclass in peak_fitting_gui for a simple embedded figure in a window with no events.
* Allow using data from .xls, .xlsm, and fixed-width files
  Added the ability to read raw data from .xls and .xlsm files.

Bug Fixes
~~~~~~~~~

* Improved conversion from pandas to numpy
  Added a function in utils for converting pandas series to numpy to reduce the change of error occuring during conversion. Improved handling of nan data in fitting gui and all embedded figures.
* Fixed error with Excel plot options when not plotting
  Fixed error with Excel plot options when not plotting. Column labels are now added to the dataframes.
* Fix issue using log scale with values <= 0
  Fixed an issue when plotting in Excel with a log scale if one of the specified bounds was <= 0.
* Fixed matplotlib toolbar size and packing
  In matplotlib version 3.3, the toolbar size was increased, so all toolbars in mcetl are likewise incrased in size. Likewise, a pack_toolbar keyword was added for NavigationToolbarTK, so try using that key when creating toolbars. Otherwise, use pack_forget to unpack the toolbar and then pack with the desired keys.
* Improve data import window
  The data import window will only attempt to assign indices for DataSource variables if processing. Also improved the layout of the import window.
* Separation columns are removed before returning dataframes
  The entry and sample separation columns that are added if processing and writing to Excel are now removed when splitting the merged dataframes back into individual entries. This only affects the dataframes output by the launch_main_gui function.
* Ensure that Excel sheet name is valid
  Added a function in utils for ensuring that input strings are valid Excel sheet names. Added to validations in fitting_gui and main_gui.
* Simplified writing to csv for plotting gui
  Removed the column indices when reading/writing csv data within the plotting gui. Now, columns are just directly taken from the data.
* Use df.iloc to get columns by index
  Switched to using df.iloc[:, col_number] to get columns by their indices so that dataframes with repeated column names will not produce errors. Further, use df.astype(float).to_numpy() to create numpy arrays from dataframes, since in later pandas versions, converting dirrectly using np.array(df[col], float) would cause issues if the series was an IntegerArray and contained pd.NA, which cannot be converted to float by numpy.
* Only remove first '.' for file search extension
  Made it so that '.' is removed from the user-input file extension when doing file searching only if the '.' is the first character in the string. This way, file types with multiple extensions, like tar.gz, are now possible to use.
* Fixed Raman raw data file extension
  The raw data generated for Raman was accidently being saved as a csv rather than a tab-separated txt file.
* Ensure Excel file is closed before overwriting
  Added create_excel_writer to utils that ensures a current Excel file is closed if appending to the file before creating the pandas ExcelWriter object. This is because any changes to the file after creating the ExcelWriter object will be lost.
* Fixed issue when using ConstantModel
  Ensured that the background model for peak fitting is always an array with the same size as the data being fit so that it does not cause errors when plotting. Made the plotting convenience functions in peak_fitting take just the fit result, since the x and y values are within the result. Renamed the peak_fitting function to fit_peaks because it was causing a namespace issue.
* Fixed issue from input conversion
  Fixed an inssue in the plotting gui caused by the auto-dtype-conversion during input validation.

Other Changes
~~~~~~~~~~~~~

* Replace sympy with asteval
  Use asteval instead of sympy to parse user expressions when creating secondary axes for the plotting gui. This requires the user to input forward and backward expressions, but otherwise requires no changes. Also, it now drops a requirement for mcetl, since asteval is already required for lmfit. Updated requirements in setup.py and requirements.txt.
* Made internal methods private
  Made all of the methods that are only internally used private for DataSource and the Function objects. Updated the doc string for DataSource.
* Update required PySimpleGUI version
  Bumped the required version of PySimpleGUI to v4.29 in setup.py.
* Added Excel style test to DataSource
  Added a wrapper for ExcelWriterHandler's test_excel_styles method to DataSource, since DataSource is the main user-facing object. Removed ExcelWriterHandler from __init__.
* Update python version in setup.py
  Added python 3.9 to the supported python versions.
* Added function to compute min element size
  Added a function to utils.py to compute the minimum allowable dimensions for scalable elements. This improves usage on smaller screens.
* Update requirements
  Rearranged modules in requirements_development and requirements_documentation. Added version numbers for all modules.
* Made canvas packing more flexible
  The function for placing figures on tkinter canvases is more flexible and now works in the case where the figure canvas and the toolbar canvas are the same. Also handles exceptions better, and allows different kwargs for packing the figure and the toolbar.
* Created mcetl.fitting.models
  Created a new file in mcetl.fitting called models, which can be filled later with any additional models. Put the modified BWF function in fitting.models.
* Simplified data import code in main gui
  When opening multiple files, use the same logic for both Excel files and other files since there is no longer a need to differentiate. Also renamed peak fitting to just fitting or data fitting. Fixed issue in fitting_gui where user_inputs is not None but does not contain the desired key.
* Improved manual peak initialization
  Simplified manual peak initialization by including all relevant parameters for a peak model in the peak_transformer dictionary. Improved the guess function for the modified BWF model.
* plotting gui uses canvas size from plot_utils
  Changed all references in the plotting_gui from CANVAS_SIZE to plot_utils.CANVAS_SIZE because the constant would not change once the file was imported.
* Reduce namespace for mcetl.fitting
  Took out several functions and classes from mcetl.fitting.__init__ since they are not needed.
* Made utils function for fixing backslash
  Made the stringify_backslash function in utils to help displaying strings with backslashes in GUIs. Removed the code in other files that can now use stringify_backslash.
* Simplified initialization for peak models
  Created functions for estimating sigma and amplitude for lognormal, which allowed deleting a lot of repeated code in peak_fitting.py. Cleaned up the code for initializing peak models.
* Created an additional module called plot_utils that contains all helper functions and classes for plotting.
  Moved some functions from plotting_gui and utils to plot_utils.

Deprecations/Breaking Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Renamed SeparationFunction to PreprocessingFunction to make its usage more clear.
* The peak_fitting function no longer takes the keyword 'poly_n' as an argument. Instead, the
  function takes the keyword 'background_kwargs' which is a dictionary for background keyword
  arguments, allowing any model to be used as the background. For example, to get the same behavior
  as with the old 'poly_n' keyword, the new input would be background_kwargs = {'degree': 1}.
* Renamed datasource.py to data_source.py. This should have little effect on user code
  since the DataSource object is available through the main mcetl namespace.

Documentation/Examples
~~~~~~~~~~~~~~~~~~~~~~

* Improved the api documentation, added tutorials, and improved the overall documentation.
* Updated examples for previous two commits
  Renamed SeparationFunctions to PreprocessingFunctions in the examples, wrote new examples for preprocessing and reordered the import column indices in use_main_gui. Other minor changes in the other files, just wanted to commit their changes.
* Create epub and htmlzip files with docs
  Used the 'all' key for the formats to build during documentation, so that pdf, epub, and htmlzip files are all created when the documentation is made by readthedocs.
* Added peak fitting example
  Added an example program using just mcetl.fitting.fit_peaks rather than the GUI.
* Updated example programs
  Updated the example programs to account for the new module layout from the last commit.


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
  This allows access to the Excel file in python after running the launch_main_gui function, in
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

* Fixed issue using reversed() with a dictionary causing the plotting GUI to fail with python 3.7.
  Used reversed(list(dictionary.keys())) instead.


Version 0.1.1 (2020-09-14)
--------------------------

This is a minor patch with new features, bug fixes, and documentation improvements.

New Features
~~~~~~~~~~~~

* Extended the Unicode conversion to cover any input with backslash. This mainly helps with text
  in the plotting GUI, such as allowing multiline text using "\\n", while still giving the correct behavior
  when using mathtext with matplotlib.

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
