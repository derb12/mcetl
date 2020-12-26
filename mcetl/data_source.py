# -*- coding: utf-8 -*-
"""The DataSource class contains all needed information for importing, processing, and saving data.

@author: Donald Erb
Created on Jul 31, 2020

"""


import itertools

import numpy as np
import pandas as pd

from . import utils
from .excel_writer import ExcelWriterHandler
from .functions import CalculationFunction, PreprocessFunction, SummaryFunction


class DataSource:
    """
    Used to give default settings for importing data and various functions based on the source.

    Parameters
    ----------
    name : str
        The name of the DataSource. Used when displaying the DataSource in a GUI.
    functions : list/tuple of CalculationFunction, PreprocessFunction, and SummaryFunction, optional
        The list/tuple of Function objects that will be used to process data for
        the DataSource. The order the Functions are performed in is as follows:
        PreprocessFunctions, CalculationFunctions, SummaryFunctions, with functions
        of the same type being performed in the same order as input.
    column_labels : tuple(str) or list(str), optional
        A list/tuple of strings that will be used to label columns in the
        Excel output, and to label the pandas DataFrame columns for the data.
    column_numbers : tuple(int) or list(int), optional
        The indices of the columns to import from raw data files.
    start_row : int, optional
        The first row of data to use when importing from raw data files.
    end_row : int, optional
        The last row of data to use when importing from raw data files.
        Counts up from the last row, so the last row is 0, the second
        to last row is 1, etc.
    separator : str, optional
        The separator to use when importing from raw data files.
    file_type : str, optional
        The file extension associated with the data files for the DataSource.
        For example, 'txt' or 'csv'.
    num_files : int, optional
        The number of data files per sample for the DataSource. Only used
        when using keyword search for files.
    unique_variables : list(str) or tuple(str), optional
        The names of all columns from the imported raw data that are
        needed for calculations. For example, if importing thermogravimetric
        analysis (TGA) data, the unique_variables could be ['temperature', 'mass'].
    unique_variable_indices : list(int) or tuple(int), optional
        The indices of the columns within column_numbers that correspond with
        each of the input unique_variables.
    xy_plot_indices : list(int, int) or tuple(int, int), optional
        The indices of the columns after processing that will be the default
        columns for plotting in Excel.
    figure_rcParams : dict, optional
        A dictionary containing any changes to matplotlib's rcParams.
        Used if plotting in python through the launch_main_gui function.
    excel_writer_formats : dict(dict or openpyxl.style.NamedStyle), optional
        A dictionary of styles used to format the output Excel workbook.
        The following keys are used when writing data from files to Excel:
            'header_even', 'header_odd', 'subheader_even', 'subheader_odd',
            'columns_even', 'columns_odd'
        The following keys are used when writing data fit results to Excel:
            'fitting_header_even', 'fitting_header_odd', 'fitting_subheader_even',
            'fitting_subheader_odd', 'fitting_columns_even', 'fitting_columns_odd',
            'fitting_descriptors_even', 'fitting_descriptors_odd'
        The values for the dictionaries must be either dictionaries, with
        keys corresponding to keyword inputs for openpyxl's NamedStyle, or NamedStyle
        objects.
    excel_row_offset : int, optional
        The first row to use when writing to Excel. A value of 0 would start
        at row 1 in Excel, 1 would start at row 2, etc.
    excel_column_offset : int, optional
        The first column to use when writing to Excel. A value of 0 would
        start at column 'A' in Excel, 1 would start at column 'B', etc.
    entry_separation : int, optional
        The number of blank columns to insert between data entries when writing
        to Excel.
    sample_separation : int, optional
        The number of blank columns to insert between samples when writing
        to Excel.
    label_entries : bool, optional
        If True, will add a number to the column labels for each
        entry in a sample if there is more than one entry. For example, the
        column label 'data' would become 'data, 1', 'data, 2', etc.

    Attributes
    ----------
    lengths : list
        A list of lists of lists of integers, corresponding to the number of columns
        in each individual entry in the total dataframes for the DataSource.
        Used to split the concatted dataframe back into individual dataframes for
        each dataset.
    references : list
        A list of dictionaries, with each dictionary containing the column numbers
        for each unique variable and calculation for the merged dataframe of each
        dataset.

    """

    excel_formats = {
        'header_even': {
            'font': dict(size=12, bold=True),
            'fill': dict(fill_type='solid', start_color='F9B381', end_color='F9B381'),
            'border': dict(bottom=dict(style='thin')),
            'alignment': dict(horizontal='center', vertical='center', wrap_text=True)
        },
        'header_odd': {
            'font': dict(size=12, bold=True),
            'fill': dict(fill_type='solid', start_color='73A2DB', end_color='73A2DB'),
            'border': dict(bottom=dict(style='thin')),
            'alignment': dict(horizontal='center', vertical='center', wrap_text=True)
        },
        'subheader_even': {
            'font': dict(bold=True),
            'fill': dict(fill_type='solid', start_color='FFEAD6', end_color='FFEAD6'),
            'border': dict(bottom=dict(style='thin')),
            'alignment': dict(horizontal='center', vertical='center', wrap_text=True)
        },
        'subheader_odd': {
            'font': dict(bold=True),
            'fill': dict(fill_type='solid', start_color='DBEDFF', end_color='DBEDFF'),
            'border': dict(bottom=dict(style='thin')),
            'alignment': dict(horizontal='center', vertical='center', wrap_text=True)
        },
        'columns_even': {
            'fill': dict(fill_type='solid', start_color='FFEAD6', end_color='FFEAD6'),
            'alignment': dict(horizontal='center', vertical='center'),
            'number_format': '0.00'
        },
        'columns_odd': {
            'fill': dict(fill_type='solid', start_color='DBEDFF', end_color='DBEDFF'),
            'alignment': dict(horizontal='center', vertical='center'),
            'number_format': '0.00'
        }
    }

    def __init__(
            self,
            name,
            functions=None,
            column_labels=None,
            column_numbers=None,
            start_row=0,
            end_row=0,
            separator=None,
            file_type=None,
            num_files=1,
            unique_variables=None,
            unique_variable_indices=None,
            xy_plot_indices=None,
            figure_rcParams=None,
            excel_writer_formats=None,
            excel_row_offset=0,
            excel_column_offset=0,
            entry_separation=0,
            sample_separation=0,
            label_entries=True):
        """
        Raises
        ------
        ValueError
            Raised if the input name is a blank string, or if either excel_row_offset
            or excel_column_offset is < 0.
        TypeError
            Raised if one of the input functions is not a valid mcetl.FunctionBase
            object.
        IndexError
            Raised if the number of data columns is less than the number of unique
            variables.

        """

        if name:
            self.name = name
        else:
            raise ValueError('DataSource name cannot be a blank string.')

        # attributes that will be set later
        self.lengths = None # used for splitting merged datasets
        self.references = None # used to reference columns within a dataframe
        # _added_separators signifies that entry and sample separation columns were added
        # to the merged dataset and will need to be removed in split_into_entries method
        self._added_separators = False

        self.start_row = start_row
        self.end_row = end_row
        self.file_type = file_type
        self.num_files = num_files
        self.sample_separation = sample_separation
        self.entry_separation = entry_separation
        self.label_entries = label_entries
        self.column_labels = column_labels if column_labels is not None else []
        self.figure_rcParams = figure_rcParams if figure_rcParams is not None else {}
        self.separator = separator

        # Ensures excel_row_offset and excel_column_offset are >= 0
        if any(value < 0 for value in (excel_column_offset, excel_row_offset)):
            raise ValueError('excel_column_offset and excel_row_offset must be >= 0.')
        else:
            self.excel_row_offset = excel_row_offset
            self.excel_column_offset = excel_column_offset

        if unique_variables is None:
            self.unique_variables = []
        elif isinstance(unique_variables, str):
            self.unique_variables = [unique_variables]
        else:
            self.unique_variables = list(unique_variables)

        if column_numbers is not None:
            self.column_numbers = column_numbers
        else:
            self.column_numbers = list(range(len(self.unique_variables)))

        # ensures the number of imported columns can accomodate all variables
        if len(self.column_numbers) < len(self.unique_variables):
            raise IndexError((
                f'The number of columns specified for {self} '
                'must be greater or equal to the number of unique variables.'
            ))

        # sorts the functions by their usage
        self.preprocess_functions = []
        self.calculation_functions = []
        self.sample_summary_functions = []
        self.dataset_summary_functions = []
        if functions is not None:
            if not isinstance(functions, (list, tuple)):
                functions = (functions,)
            for function in functions:
                if isinstance(function, SummaryFunction):
                    if function.sample_summary:
                        self.sample_summary_functions.append(function)
                    else:
                        self.dataset_summary_functions.append(function)
                elif isinstance(function, CalculationFunction):
                    self.calculation_functions.append(function)
                elif isinstance(function, PreprocessFunction):
                    self.preprocess_functions.append(function)
                else:
                    raise TypeError(f'{function} is not a valid Function object.')

        self._validate_target_columns()

        # self._deleted_columns tracks how many columns will be deleted after
        # preprocessing so the number of needed column labels can be adjusted
        self._deleted_columns = sum(
            len(cols) for func in self.preprocess_functions for cols in func.deleted_columns
        )

        # indices for each unique variable for data processing
        if unique_variable_indices is None:
            self.unique_variable_indices = list(range(len(self.unique_variables)))
        elif isinstance(unique_variable_indices, (str, int)):
            self.unique_variable_indices = [unique_variable_indices]
        else:
            self.unique_variable_indices = unique_variable_indices

        # ensure all unique variables have a unique column index
        unused_indices = (i for i in range(len(self.unique_variables)) if i not in self.unique_variable_indices)
        for i in range(len(self.unique_variables)):
            if i > len(self.unique_variable_indices) - 1:
                self.unique_variable_indices.append(next(unused_indices))

        # x and y indices for plotting
        if isinstance(xy_plot_indices, (list, tuple)) and len(xy_plot_indices) >= 2:
            self.x_plot_index = xy_plot_indices[0]
            self.y_plot_index = xy_plot_indices[1]
        else:
            self.x_plot_index = 0
            self.y_plot_index = 1

        # sets styles for writing to Excel
        self.excel_formats = self._create_excel_writer_formats(excel_writer_formats)


    def __str__(self):
        return f'{self.__class__.__name__}(name={self.name})'


    @classmethod
    def _create_excel_writer_formats(cls, styles=None):
        """
        Sets the excel_formats attribute for the DataSource.

        Parameters
        ----------
        styles : dict, optional
            The input dictionary to override the default formats.

        Returns
        -------
        format_kwargs : dict
            The input styles dictionary with any missing keys from
            DataSource.excel_formats added.

        """

        format_kwargs = styles if styles is not None else {}
        for key, value in cls.excel_formats.items():
            if key not in format_kwargs:
                format_kwargs[key] = value

        return format_kwargs


    def _validate_target_columns(self):
        """
        Ensures that the target columns and function names for each Function are valid.

        Raises
        ------
        ValueError
            Raises ValueError if the target column for a Function does not exist, or if
            two Function objects have the same name. If the target column does not
            exist, it can either be due to that target not existing, or that the
            functions are calculated in the wrong order.

        """

        target_error = ('"{target}" is not an available column for {function} to modify. '
                        'Check that {self} a) has the correct function order and/or b) has '
                        'the correct unique_variables specified.')

        unique_keys = set(self.unique_variables)
        for function in (self.preprocess_functions
                         + self.calculation_functions
                         + self.sample_summary_functions
                         + self.dataset_summary_functions):
            # ensure function names are unique
            if function.name in unique_keys:
                raise ValueError((
                    f'The name "{function.name}" is associated with two '
                    f'different objects for {self}, which is not allowed.'
                ))
            # ensure targets exist
            for target in function.target_columns:
                if target not in unique_keys:
                    raise ValueError(target_error.format(target=target, self=self,
                                                         function=function))

            # remove keys for columns removed by PreprocessFunction
            if isinstance(function, PreprocessFunction):
                for key in function.deleted_columns:
                    if key in unique_keys:
                        unique_keys.remove(key)
                    else:
                        raise ValueError(target_error.format(target=key, self=self,
                                                             function=function))

            # ensure columns exist if function modifies columns
            elif not isinstance(function.added_columns, int):
                for target in function.added_columns:
                    if target not in unique_keys:
                        raise ValueError(target_error.format(target=target, self=self,
                                                             function=function))
            # ensure summary functions either add columns or modify other summary columns
            if (isinstance(function, SummaryFunction)
                    and not isinstance(function.added_columns, int)):

                if function.sample_summary:
                    sum_funcs = [function.name for function in self.sample_summary_functions]
                else:
                    sum_funcs = [function.name for function in self.dataset_summary_functions]

                if any(column not in sum_funcs for column in function.added_columns):
                    raise ValueError((
                        f'Error with {function}. SummaryFunctions can only modify columns '
                        'for other SummaryFunctions with matching sample_summary attributes.'
                    ))

            unique_keys.add(function.name)


    def _create_references(self, dataset, import_values):
        """Creates a dictionary to reference the column indices."""

        references = [[] for sample in dataset]
        for i, sample in enumerate(dataset):
            for j, dataframe in enumerate(sample):
                reference = {key: [value] for key, value in import_values[i][j].items()}
                start_index = len(dataframe.columns)

                for function in self.calculation_functions:
                    if isinstance(function.added_columns, int):
                        end_index = start_index + function.added_columns
                        reference[function.name] = list(range(start_index, end_index))

                        for num in range(start_index, end_index):
                            dataframe[num] = pd.Series(np.nan, dtype=np.float32)

                        start_index = end_index
                    else:
                        reference[function.name] = []
                        for target in function.added_columns:
                            reference[function.name].extend(reference[target])

                references[i].append(reference)

        return references


    def _add_summary_dataframes(self, dataset, references):
        """Adds the dataframes for summary functions and creates references for them."""

        if self.sample_summary_functions:
            for reference in references:
                reference.append({})

            for i, sample in enumerate(dataset):
                start_index = 0
                data = {}
                for function in self.sample_summary_functions:
                    if isinstance(function.added_columns, int):
                        end_index = start_index + function.added_columns
                        references[i][-1][function.name] = list(range(start_index, end_index))
                        for num in range(start_index, end_index):
                            data[num] = np.nan
                        start_index = end_index

                    else:
                        references[i][-1][function.name] = []
                        for target in function.added_columns:
                            references[i][-1][function.name].extend(
                                references[i][-1][target]
                            )

                sample.append(pd.DataFrame(data, index=[0], dtype=np.float32))

        if self.dataset_summary_functions:
            references.append([{}])
            start_index = 0
            data = {}
            for function in self.dataset_summary_functions:
                if isinstance(function.added_columns, int):
                    end_index = start_index + function.added_columns
                    references[-1][-1][function.name] = list(
                        range(start_index, end_index)
                    )
                    for num in range(start_index, end_index):
                        data[num] = np.nan
                    start_index = end_index

                else:
                    references[-1][-1][function.name] = []
                    for target in function.added_columns:
                        references[-1][-1][function.name].extend(
                            references[-1][-1][target]
                        )

            dataset.append([pd.DataFrame(data, index=[0], dtype=np.float32)])


    def _merge_references(self, dataframes, references):
        """Merges all the references for the merged dataframe."""

        functions = (self.calculation_functions
                     + self.sample_summary_functions
                     + self.dataset_summary_functions)

        merged_references = []
        for i, dataset in enumerate(dataframes):
            start_index = 0
            merged_reference = {
                key: [] for key in (self.unique_variables + [func.name for func in functions])
            }
            for j, sample in enumerate(dataset):
                for key in merged_reference:
                    merged_reference[key].append([])
                for k, entry in enumerate(sample):
                    for key, value in references[i][j][k].items():
                        merged_reference[key][j].extend([index + start_index for index in value])

                    start_index += len(entry.columns)

            merged_references.append(merged_reference)

        return merged_references


    def _set_references(self, dataframes, import_values):
        """
        Creates a dictionary to reference the column indices for calculations.

        Also adds the necessary columns to the input dataframes for all calculations,
        creates dataframes for the SummaryCalculations, and adds spacing between
        samples and entries.

        Assigns the merged references to the references attribute.

        Parameters
        ----------
        dataframes : list(list(list(pd.DataFrame)))
            A list of lists of lists of dataframes.
        import_values : list
            A list of lists of dictionaries containing the values used to import the data
            from files. The relevant keys are the DataSource's unique variables

        """

        # create references, add summary dataframes, and add in empty spacing columns
        references = []
        for i, dataset in enumerate(dataframes):
            reference = self._create_references(dataset, import_values[i])
            self._add_summary_dataframes(dataset, reference)
            references.append(reference)

            # add entry spacings
            for sample in dataset:
                for k, entry in enumerate(sample):
                    if k < len(sample) - 1:
                        start_index = len(entry.columns)
                        for num in range(start_index, start_index + self.entry_separation):
                            entry[num] = pd.Series(np.nan, dtype=np.float16)

                # add sample spacings
                start_index = len(sample[-1].columns)
                for num in range(start_index, start_index + self.sample_separation):
                    sample[-1][num] = pd.Series(np.nan, dtype=np.float16)

        # merges the references into one for each dataset
        self.references = self._merge_references(dataframes, references)
        self._added_separators = True


    def _do_preprocessing(self, dataframes, import_values):
        """
        Performs the function for all PreprocessFunctions.

        Parameters
        ----------
        dataframes : list(list(list(pd.DataFrame)))
            A list of lists of lists of dataframes.
        import_values : list
            A list of lists of dictionaries containing the values used to import the data
            from files. The relevant keys are the DataSource's unique variables

        Returns
        -------
        new_dataframes : list(list(list(pd.DataFrame)))
            The list of lists of lists of dataframes, after performing the
            preprocessing.
        new_import_values : list
            The list of lists of dictionaries containing the values used to
            import the data from files, after performing the
            preprocessing.

        """

        new_dataframes = []
        new_import_values = []
        for i, dataset in enumerate(dataframes):
            for function in self.preprocess_functions:
                dataset, import_values[i] = function._preprocess_data(
                    dataset, import_values[i]
                )
            new_dataframes.append(dataset)
            new_import_values.append(import_values[i])

        self._remove_unneeded_variables()

        return new_dataframes, new_import_values


    def _remove_unneeded_variables(self):
        """Removes unique variables that are not needed for processing."""

        for function in self.preprocess_functions:
            for variable in function.deleted_columns:
                if variable in self.unique_variables:
                    variable_index = self.unique_variables.index(variable)
                    column_index = self.unique_variable_indices[variable_index]
                    for i, col_num in enumerate(self.unique_variable_indices):
                        if col_num > column_index:
                            self.unique_variable_indices[i] -= 1
                    self.unique_variables.pop(variable_index)
                    self.unique_variable_indices.pop(variable_index)
                    self.column_numbers.pop(column_index)

        self._deleted_columns = 0


    def merge_datasets(self, dataframes):
        """
        Merges all entries and samples into one dataframe for each dataset.

        Also sets the length attribute, which will later be used to separate each
        dataframes back into individual dataframes for each entry.

        Parameters
        ----------
        dataframes : list(list(list(pd.DataFrame)))
            A nested list of list of lists of dataframes.

        Returns
        -------
        merged_dataframes : list(pd.DataFrame)
            A list of dataframes.

        """

        merged_dataframes = []
        # length of each individual entry for splitting later
        lengths = [[[] for sample in dataset] for dataset in dataframes]
        for i, dataset in enumerate(dataframes):
            for j, sample in enumerate(dataset):
                lengths[i][j] = [len(entry.columns) for entry in sample]
            # merges all dataframes in the dataset using generators
            dataset_dataframe = pd.concat(
                (pd.concat((entry for entry in sample), axis=1) for sample in dataset),
                axis=1
            )
            dataset_dataframe.columns = list(range(len(dataset_dataframe.columns)))
            merged_dataframes.append(dataset_dataframe)

        self.lengths = lengths

        return merged_dataframes


    def _do_functions(self, dataframes, index):
        """
        Performs the function for all CalculationFunctions and SummaryFunctions.

        Parameters
        ----------
        dataframes : list(pd.DataFrame)
            A list of dataframes, one per dataset.
        index : int
            If index is 0, will perform the Excel functions; if index is 1, will
            perform the python functions.

        Returns
        -------
        processed_dataframes : list(pd.DataFrame)
            The list of dataframes after processing.

        Notes
        -----
        The start row is set to self.excel_row_offset + 3 since openpyxl is 1-based
        and there are two header rows. The start column is also set to
        self.excel_column_offset + 1 since openpyxl is 1-based.

        """

        functions = (self.calculation_functions + self.sample_summary_functions
                     + self.dataset_summary_functions)
        first_column = self.excel_column_offset + 1

        processed_dataframes = []
        for i, dataset in enumerate(dataframes):
            if index == 1:
                excel_columns = None
            else:
                excel_columns = [
                    utils.excel_column_name(num) for num in range(first_column, len(dataset.columns) + first_column)
                ]

            for function in functions:
                dataset = function._do_function(
                    dataset, self.references[i], index, excel_columns, self.excel_row_offset + 3
                )

            # Optimizes memory usage after calculations
            processed_dataframes.append(utils.optimize_memory(dataset, bool(index)))

        return processed_dataframes


    def _do_excel_functions(self, dataframes):
        """
        Will perform the Excel function for each CalculationFunctions and SummaryFunctions.

        Convenience wrapper for the internal method _do_functions.

        Parameters
        ----------
        dataframes : list(pd.DataFrame)
            A list of dataframes, one for each dataset.

        Returns
        -------
        list(pd.DataFrame)
            The list of dataframes after processing.

        """

        return self._do_functions(dataframes, 0)


    def _do_python_functions(self, dataframes):
        """
        Will perform the python function for each CalculationFunctions and SummaryFunctions.

        Convenience wrapper for the internal method _do_functions.

        Parameters
        ----------
        dataframes : list(pd.DataFrame)
            A list of dataframes, one for each dataset.

        Returns
        -------
        list(pd.DataFrame)
            The list of dataframes after processing.

        """

        return self._do_functions(dataframes, 1)


    def split_into_entries(self, merged_dataframes):
        """
        Splits the merged dataset dataframes back into dataframes for each entry.

        Parameters
        ----------
        merged_dataframes : list(pd.DataFrame)
            A list of dataframes. Each dataframe will be split into lists of lists
            of dataframes.

        Returns
        -------
        split_dataframes : list(list(list(pd.DataFrame)))
            A list of lists of lists of dataframes, corresponding to entries
            and samples within each dataset.

        """

        sample_lengths = [
            np.cumsum([np.sum(sample) for sample in dataset]) for dataset in self.lengths
        ]

        split_dataframes = [[[] for sample in dataset] for dataset in self.lengths]
        dataset_dtypes = []
        for i, dataset in enumerate(merged_dataframes):
            dataset_dtypes.append(iter(dataset.dtypes.values))
            split_samples = np.array_split(dataset, sample_lengths[i], axis=1)[:-1]

            for j, sample in enumerate(split_samples):
                split_dataframes[i][j].extend(
                    np.array_split(sample, np.cumsum(self.lengths[i][j]), axis=1)[:-1])

        # renames columns back to individual indices, reassigns dtypes, and removes
        # the separation columns, if they were added
        for i, dataset in enumerate(split_dataframes):
            for sample in dataset:
                for j, entry in enumerate(sample):
                    entry.columns = list(range(len(entry.columns)))
                    dtypes = {col: next(dataset_dtypes[i]) for col in entry.columns}
                    if self._added_separators:
                        separation_cols = self.sample_separation if j == len(sample) - 1 else self.entry_separation
                    else:
                        separation_cols = 0

                    sample[j] = entry.astype(dtypes
                        ).drop(range(len(entry.columns) - separation_cols, len(entry.columns)), axis=1)

        # reset internal attributes
        self._added_separators = False
        self.lengths = None

        return split_dataframes


    def _create_imported_data_labels(self, df_length=None):
        """
        Calculates the necessary column labels for imported data.

        Also fills in as many labels as possible using self.column_labels.

        Parameters
        ----------
        df_length : int, optional
            The number of columns in the imported dataframe.

        Returns
        -------
        imported_data_labels : list(str)
            A list of strings

        """

        specified_labels = itertools.chain(self.column_labels, itertools.cycle(['']))
        imported_data_labels = [
            next(specified_labels) for _ in range(len(self.column_numbers) - self._deleted_columns)
        ]
        if df_length is not None:
            if df_length <= len(self.column_numbers) - self._deleted_columns:
                imported_data_labels = imported_data_labels[:df_length]
            else:
                imported_data_labels.extend(
                    '' for _ in range(df_length - len(self.column_numbers) + self._deleted_columns)
                )

        return imported_data_labels


    def _create_calculation_labels(self):
        """
        Calculates the necessary column labels for the DataSource's Functions.

        Also fills in as many labels as possible using self.column_labels.

        Returns
        ----------
        calculation_labels : list(list(str))
            A list with three lists, containing all the needed column labels
            for functions: index 0 is for CalculationFunctions labels, index 1
            is for sample SummaryFunctions labels, and index 2 is for dataset
            SummaryFunctions labels.

        """

        specified_labels = itertools.chain(self.column_labels, itertools.cycle(['']))
        # discard the column labels that correspond to imported data
        unneeded = [next(specified_labels) for _ in range(len(self.column_numbers) - self._deleted_columns)]

        calculation_labels = [[], [], []]
        functions = (self.calculation_functions, self.sample_summary_functions, self.dataset_summary_functions)
        for i, function_type in enumerate(functions):
            for function in function_type:
                if isinstance(function.added_columns, int):
                    calculation_labels[i].extend(next(specified_labels) for _ in range(function.added_columns))

        return calculation_labels


    def print_column_labels_template(self):
        """
        Convenience function that will print a template for all the column headers.

        Column headers account for all of the columns imported from raw data, the
        columns added by CalculationFunctions, and the columns added by
        SummaryFunctions.

        """

        labels = [self._create_imported_data_labels(), *self._create_calculation_labels()]
        label_template = list(itertools.chain.from_iterable(labels))

        print((
            f'\nImported data labels: {len(labels[0])}\n'
            f'Calculation labels: {len(labels[1])}\n'
            f'Sample summary labels: {len(labels[2])}\n'
            f'Dataset summary labels: {len(labels[3])}\n\n'
            f'column_labels template for {self} = {label_template}'
        ))


    @staticmethod
    def test_excel_styles(styles):
        """
        Tests whether the input styles create valid Excel styles with openpyxl.

        Parameters
        ----------
        styles : dict(str : dict or openpyxl.styles.NamedStyle)
            The dictionary of styles to test. Values in the dictionary can
            either be nested dictionaries with the necessary keys and values
            to create an openpyxl NamedStyle, or openpyxl.styles.NamedStyle
            objects.

        Returns
        -------
        bool
            Returns True if all input styles successfully create openpyxl
            NamedStyle objects; otherwise, returns False.

        Notes
        -----
        This is just a wrapper of ExcelWriterHandler.test_excel_styles,
        and is included because DataSource is the main-facing object of
        mcetl and will be used more often.

        """
        return ExcelWriterHandler.test_excel_styles(styles)
