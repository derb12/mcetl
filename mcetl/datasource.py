# -*- coding: utf-8 -*-
"""Contains the DataSource class.

@author: Donald Erb
Created on Fri Jul 31 16:22:51 2020

"""


import pandas as pd
import numpy as np
from .utils import optimize_memory
from .functions import SeparationFunction, CalculationFunction, SummaryFunction


class DataSource:
    """
    Used to give default settings for importing data and various functions based on the source.

    Attributes
    ----------
    lengths : list
        A list of lists of lists of integers, corresponding to the number of columns
        in each individual measurement in the total dataframes for the DataSource.
        Used to split the concatted dataframe back into individual dataframes for
        each dataset.
    references : list
        A list of dictionaries, with each dictionary containing the column numbers
        for each unique variable and calculation for the merged dataframe of each
        dataset.

    """

    def __init__(
            self, name, column_names=None, functions=None,
            column_numbers=None, start_row=0, end_row=0, separator=None,
            unique_variables=None, unique_variable_indices=None,
            xy_plot_indices=None, file_type=None, num_files=1,
            figure_rcParams=None, excel_writer_kwargs=None,
            sample_separation=0, measurement_separation=0,
            excel_row_offset=0, excel_column_offset=0
        ):
        """


        Parameters
        ----------
        name : TYPE
            DESCRIPTION.
        column_names : TYPE, optional
            DESCRIPTION. The default is None.
        functions : TYPE, optional
            DESCRIPTION. The default is None.
        column_numbers : TYPE, optional
            DESCRIPTION. The default is None.
        start_row : TYPE, optional
            DESCRIPTION. The default is 0.
        end_row : TYPE, optional
            DESCRIPTION. The default is 0.
        separator : TYPE, optional
            DESCRIPTION. The default is None.
        unique_variable_indices : TYPE, optional
            DESCRIPTION. The default is None.
        xy_plot_indices : TYPE, optional
            DESCRIPTION. The default is None.
        file_type : TYPE, optional
            DESCRIPTION. The default is None.
        num_files : TYPE, optional
            DESCRIPTION. The default is 1.
        unique_variables : TYPE, optional
            DESCRIPTION. The default is None.
        figure_rcParams : dict, optional
            A dictionary containing any changes to matplotlib's rcParams.
            The default is None.
        excel_writer_kwargs : TYPE, optional
            DESCRIPTION. The default is None.
        sample_separation : TYPE, optional
            DESCRIPTION. The default is 0.
        measurement_separation : TYPE, optional
            DESCRIPTION. The default is 0.

        Raises
        ------
        TypeError
            DESCRIPTION.

        """

        column_names = column_names if column_names is not None else []

        self.lengths = None
        self.name = name
        self.column_numbers = column_numbers if column_numbers is not None else [0, 1]
        self.start_row = start_row
        self.end_row = end_row
        self.separator = separator
        self.file_type = file_type
        self.num_files = num_files
        self.sample_separation = sample_separation
        self.measurement_separation = measurement_separation
        self.excel_row_offset = excel_row_offset
        self.excel_column_offset = excel_column_offset
        self.column_names = column_names if column_names is not None else []
        self.figure_rcParams = figure_rcParams if figure_rcParams is not None else {}

        if unique_variables is None:
            self.unique_variables = ['x', 'y']
        elif isinstance(unique_variables, str):
            self.unique_variables = [unique_variables]
        else:
            self.unique_variables = unique_variables

        self.separation_functions = []
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
                elif isinstance(function, SeparationFunction):
                    self.separation_functions.append(function)
                else:
                    raise TypeError(f'{function} is not a valid Function object.')

        self._validate_target_columns()

        #indices for each unique variable for data processing
        if (isinstance(unique_variable_indices, (list, tuple))
            and len(unique_variable_indices) == len(unique_variables)):

            self.unique_variable_indices = unique_variable_indices
        else:
            self.unique_variable_indices = [*range(len(self.unique_variables))]

        #x and y indices for plotting
        if isinstance(xy_plot_indices, (list, tuple)) and len(xy_plot_indices) >= 2:
            self.x_plot_index = xy_plot_indices[0]
            self.y_plot_index = xy_plot_indices[1]
        else:
            self.x_plot_index = 0
            self.y_plot_index = 1

        self._create_excel_writer_formats(excel_writer_kwargs)


    def _create_excel_writer_formats(self, format_kwargs):
        """

        Sets the excel_formats attribute for the DataSource.

        Parameters
        ----------
        format_kwargs : TYPE
            DESCRIPTION.

        """

        format_kwargs = format_kwargs if format_kwargs is not None else {}
        #TODO rename the keys to make more sense
        self.excel_formats = {
            'odd_header_format': {
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2,
                'bold':True,'bg_color':'DBEDFF', 'font_size':12, 'bottom': True
            },
            'even_header_format': {
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2,
                'bold':True, 'bg_color':'FFEAD6', 'font_size':12, 'bottom': True
            },
            'odd_col_num_format': {
                'num_format': '0.00', 'bg_color':'DBEDFF', 'text_v_align': 2,
                'text_h_align': 2
            },
            'even_col_num_format': {
                'num_format': '0.00', 'bg_color':'FFEAD6', 'text_v_align': 2,
                'text_h_align': 2
            },
            'odd_fit_header_format': {
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
                'bg_color':'73A2DB', 'font_size':12, 'bottom': True
            },
            'even_fit_header_format': {
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
                'bg_color':'F9B381', 'font_size':12, 'bottom': True
            },
            'odd_bold_format': {
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
                'bg_color':'DBEDFF', 'font_size':11, 'num_format': '0.000'
            },
            'even_bold_format': {
                'text_wrap': True, 'text_v_align': 2, 'text_h_align': 2, 'bold':True,
                'bg_color':'FFEAD6', 'font_size':11, 'num_format': '0.000'
            }
        }

        for key in self.excel_formats:
            if key in format_kwargs:
                self.excel_formats[key].update(format_kwargs[key])


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

        unique_keys = [*self.unique_variables]

        for function in (self.separation_functions + self.calculation_functions
                         + self.sample_summary_functions + self.dataset_summary_functions):
            #ensure function names are unique
            if function.name in unique_keys:
                raise ValueError(
                    f'The name "{function.name}" is associated with two different '\
                    f'Function objects in the DataSource "{self.name}", which is not allowed.'
                )
            #ensure targets exist
            for target in function.target_columns:
                if target not in unique_keys:
                    raise ValueError(
                        f'"{target}" is not an available target for Function '\
                        f'"{function.name}". Check that the function order is correct.'
                    )
            #ensure columns exist if function modifies columns
            if (not isinstance(function, SeparationFunction)
                and not isinstance(function.added_columns, int)):

                for target in function.added_columns:
                    if target not in unique_keys:
                        raise ValueError(
                            f'"{target}" is not an available column for Function '\
                            f'"{function.name}" to modify. Check that the function order is correct.'
                        )
            #ensure summary functions either add columns or modify other summary columns
            if (isinstance(function, SummaryFunction)
                and not isinstance(function.added_columns, int)):

                if function.sample_summary:
                    sum_funcs = [function.name for function in self.sample_summary_functions]
                else:
                    sum_funcs = [function.name for function in self.dataset_summary_functions]

                if any(column not in sum_funcs for column in function.added_columns):
                    raise ValueError(
                        f'Error with "{function.name}". SummaryFunctions can only modify '\
                        'other SummaryFunction columns.'
                    )

            unique_keys.append(function.name)


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
                        references[i][-1][function.name] = [*range(start_index, end_index)]
                        for num in range(start_index, end_index):
                            data[num] = np.nan
                        start_index = end_index
                    else:
                        references[i][-1][function.name] = []
                        for target in function.added_columns:
                            references[i][-1][function.name].extend(references[i][-1][target])

                sample.append(pd.DataFrame(data, index=[0], dtype=np.float32))

        if self.dataset_summary_functions:
            references.append([{}])
            start_index = 0
            data = {}
            for function in self.dataset_summary_functions:
                if isinstance(function.added_columns, int):
                    end_index = start_index + function.added_columns
                    references[-1][-1][function.name] = [*range(start_index, end_index)]
                    for num in range(start_index, end_index):
                        data[num] = np.nan
                    start_index = end_index
                else:
                    references[-1][-1][function.name] = []
                    for target in function.added_columns:
                        references[-1][-1][function.name].extend(references[-1][-1][target])

            dataset.append([pd.DataFrame(data, index=[0], dtype=np.float32)])


    def _create_references(self, dataset, import_values):
        """
        """

        references = [[] for sample in dataset]
        for i, sample in enumerate(dataset):
            for j, dataframe in enumerate(sample):
                reference = {
                    variable: [int(import_values[i][j][f'index_{variable}'])] for variable in self.unique_variables
                }
                start_index = len(dataframe.columns)

                for function in self.calculation_functions:
                    if isinstance(function.added_columns, int):
                        end_index = start_index + function.added_columns
                        reference[function.name] = [*range(start_index, end_index)]

                        for num in range(start_index, end_index):
                            dataframe[num] = pd.Series(np.nan, dtype=np.float32)

                        start_index = end_index
                    else:
                        reference[function.name] = []
                        for target in function.added_columns:
                            reference[function.name].extend(reference[target])

                references[i].append(reference)

        return references


    def merge_datasets(self, dataframes):
        """
        Merges all measurements and samples into one dataframe for each dataset.

        Also sets the length attribute, which will later be used to separate each
        dataframes back into individual dataframes for each measurement.

        Parameters
        ----------
        dataframes : list
            A nested list of list of lists of dataframes.

        Returns
        -------
        merged_dataframes : list
            A list of dataframes.

        """

        merged_dataframes = []
        #length of each individual measurement for splitting later
        lengths = [[[] for sample in dataset] for dataset in dataframes]
        for i, dataset in enumerate(dataframes):
            for j, sample in enumerate(dataset):
                lengths[i][j] = [len(measurement.columns) for measurement in sample]
            #merges all dataframes in the dataset using generators
            dataset_dataframe = pd.concat(
                (pd.concat(
                    (measurement for measurement in sample), axis=1) for sample in dataset),
                axis=1
            )
            dataset_dataframe.columns = [*range(len(dataset_dataframe.columns))]
            merged_dataframes.append(dataset_dataframe)

        self.lengths = lengths

        return merged_dataframes


    def _merge_references(self, dataframes, references):
        """
        Merges all the references for the merged dataframe.

        """

        functions = (self.calculation_functions
                     + self.sample_summary_functions
                     + self.dataset_summary_functions)

        merged_references = []
        for i, dataset in enumerate(dataframes):
            start_index = 0
            merged_reference = {
                key: [] for key in (self.unique_variables
                                    + [func.name for func in functions])
            }
            for j, sample in enumerate(dataset):
                for key in merged_reference:
                    merged_reference[key].append([])
                for k, measurement in enumerate(sample):
                    for key in references[i][j][k]:
                        merged_reference[key][j].extend([
                            index + start_index for index in references[i][j][k][key]
                        ])

                    start_index += len(measurement.columns)

            merged_references.append(merged_reference)

        return merged_references


    def create_formula_headers(self):
        """


        Returns
        -------
        headers : TYPE
            DESCRIPTION.

        """

        #TODO split this in two, one to do just formulas, the other to populate with names
        headers = []
        for function in self.calculation_functions:
            headers.extend(['' for _ in range(function.added_columns)])
        for function in self.summary_functions:
            headers.extend(['' for _ in range(function.added_columns)])

        max_index = min(len(headers), len(self.column_names))
        headers[:max_index] = self.column_names[:max_index]

        return headers


    def set_references(self, dataframes, import_values):
        """
        Creates a dictionary to reference the column indices for calculations.

        Also adds the necessary columns to the input dataframes for all calculations,
        creates dataframes for the SummaryCalculations, and adds spacing between
        samples and measurements.

        Assigns the merged references to the attribute references.

        Parameters
        ----------
        dataframes : list
            A list of lists of lists of dataframes.
        import_values : list
            A list of lists of dictionaries containing the values used to import the data
            from files. The relevant keys are the DataSource's unique variables

        """

        #create references, add summary dataframes, and add in empty spacing columns
        references = []
        for i, dataset in enumerate(dataframes):
            reference = self._create_references(dataset, import_values[i])
            self._add_summary_dataframes(dataset, reference)
            references.append(reference)

            #add measurement spacings
            for j, sample in enumerate(dataset):
                for k, measurement in enumerate(sample):
                    if k < len(sample) - 1:
                        start_index = len(measurement.columns)
                        for num in range(start_index,
                                         start_index + self.measurement_separation):
                            measurement[num] = pd.Series(np.nan, dtype=np.float16)

                #add sample spacings
                start_index = len(sample[-1].columns)
                for num in range(start_index, self.sample_separation + start_index):
                    sample[-1][num] = pd.Series(np.nan, dtype=np.float16)

        #merges the references into one for each dataset
        self.references = self._merge_references(dataframes, references)


    def separate_data(self, dataframes, import_values):
        """
        """

        for i, dataset in enumerate(dataframes):
            for function in self.separation_functions:
                function.separate_dataframes(dataset, import_values[i])


    def _do_functions(self, dataframes, index):
        """
        Performs each function for all CalculationFunctions and SummaryFunctions.

        Parameters
        ----------
        dataframes : list
            A list of dataframes, one per dataset.
        index : int
            If index is 0, will perform the Excel functions; if index is 1, will
            perform the python functions.

        """

        functions = (self.calculation_functions + self.sample_summary_functions
                     + self.dataset_summary_functions)

        for i, dataset in enumerate(dataframes):
            for function in functions:
                dataframes[i] = function.do_function(
                    dataset, self.references[i], index,
                    self.excel_column_offset, self.excel_row_offset
                )

            #optimizes memory usage after calculations
            dataframes[i] = optimize_memory(dataset)


    def do_excel_functions(self, dataframes):
        """
        Will perform the Excel function for each CalculationFunctions and SummaryFunctions.

        Convenience wrapper for the internal method _do_functions.

        Parameters
        ----------
        dataframes : list
            A list of dataframes, one for each dataset.

        """

        self._do_functions(dataframes, 0)


    def do_python_functions(self, dataframes):
        """
        Will perform the python function for each CalculationFunctions and SummaryFunctions.

        Convenience wrapper for the internal method _do_functions.

        Parameters
        ----------
        dataframes : list
            A list of dataframes, one for each dataset.

        """

        self._do_functions(dataframes, 1)


    def split_into_measurements(self, merged_dataframes):
        """
        Splits the merged dataset dataframes back into dataframes for each measurement.

        Parameters
        ----------
        merged_dataframes : list
            A list of dataframes. Each dataframe will be split into lists of lists
            of dataframes.

        Returns
        -------
        split_dataframes : list
            A list of lists of lists of dataframes, corresponding to measurements
            and samples within each dataset.

        """

        sample_lengths = [
            np.cumsum(
                [np.sum(measurement) for measurement in sample]
            ) for sample in self.lengths
        ]

        split_dataframes = [[[] for sample in dataset] for dataset in self.lengths]
        dataset_dtypes = []
        for i, dataset in enumerate(merged_dataframes):
            dataset_dtypes.append(iter(dataset.dtypes.values))
            split_samples = np.array_split(dataset, sample_lengths[i], axis=1)[:-1]

            for j, sample in enumerate(split_samples):
                split_dataframes[i][j].extend(
                    np.array_split(sample, np.cumsum(self.lengths[i][j]), axis=1)[:-1]
                )

        #renames columns back to individual indices and reassigns dtypes
        for i, dataset in enumerate(split_dataframes):
            for sample in dataset:
                for j, measurement in enumerate(sample):
                    measurement.columns = [*range(len(measurement.columns))]
                    dtypes = {
                        col: next(dataset_dtypes[i]) for col in measurement.columns
                    }
                    sample[j] = measurement.astype(dtypes)

        return split_dataframes


    def print_label_template(self):
        """
        Convenience function that will print a template for all the column headers.

        Column headers account for all of the columns imported from raw data, the
        columns added by CalculationFunctions, and the columns added by
        SummaryFunctions.

        """

        calculation_columns = 0
        for function in self.calculation_functions:
            if isinstance(function.added_columns, int):
                calculation_columns += function.added_columns

        sample_summary_columns = 0
        for function in self.sample_summary_functions:
            if isinstance(function.added_columns, int):
                sample_summary_columns += function.added_columns

        dataset_summary_columns = 0
        for function in self.dataset_summary_functions:
            if isinstance(function.added_columns, int):
                dataset_summary_columns += function.added_columns

        total_labels = (len(self.column_numbers) + calculation_columns
                        +sample_summary_columns + dataset_summary_columns)
        print((
            f'\nImported data labels: {len(self.column_numbers)}\n'
            f'Calculation labels: {calculation_columns}\n'
            f'Sample summary labels: {sample_summary_columns}\n'
            f'Dataset summary labels: {dataset_summary_columns}\n\n'
            f'label template = {[""] * total_labels}'
        ))
