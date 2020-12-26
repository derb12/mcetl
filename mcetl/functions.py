# -*- coding: utf-8 -*-
"""Contains the classes for Functions objects.

There are three main types of Functions:
    1) PreprocessFunction: preprocesses the imported data entry; for example, can
                           separate into multiple data entries or remove data columns.
    2) CalculationFunction: performs a calculation on each of the entries within
                            each sample within each dataset.
    3) SummaryFunction: performs a calculation once per sample or once per
                        dataset.

@author: Donald Erb
Created on Jul 31, 2020

"""


import itertools

from .utils import excel_column_name


class FunctionBase:
    """
    Base class for all other Function classes.

    Used to ensure that function names and target_columns are correct,
    and defines the string representation for all Function classes.

    Parameters
    ----------
    name : str
        The string representation for this object.
    target_columns : str or (list(str), tuple(str))
        A string or list/tuple of strings designating the target columns
        for this object.

    """

    def __init__(self, name, target_columns):
        """
        Raises
        ------
        ValueError
            Raised if there is an issue with the input name or target_columns.

        """

        if name:
            self.name = name
        else:
            raise ValueError('Function name cannot be a blank string.')

        if not target_columns:
            raise ValueError(f'target_columns must be specified for {self}.')
        elif isinstance(target_columns, str):
            self.target_columns = [target_columns]
        else:
            self.target_columns = target_columns


    def __str__(self):
        return f'{self.__class__.__name__}(name={self.name})'


class PreprocessFunction(FunctionBase):
    """
    Function for processing data before performing any calculations.

    For example, can separate a single data entry into multiple entries
    depending on a criteria or delete unneeded columns.

    Parameters
    ----------
    name : str
        The string representation for this object.
    target_columns : str or (list(str), tuple(str))
        A string or list/tuple of strings designating the target columns
        for this object.
    function : function
        The function that this object uses to process data. The function
        should take args of dataframe and target indices (a list of numbers,
        corresponding to the column index in the dataframe for each of the
        target columns), and should return a list of dataframes.
    function_kwargs : dict, optional
        A dictionary of keywords and values to be passed to the function.
        The default is None.
    deleted_columns : str or list(str) or tuple(str), optional
        The names of columns that will be deleted by this object's function.

    """

    def __init__(self, name, target_columns, function, function_kwargs=None,
                 deleted_columns=None):

        super().__init__(name, target_columns)
        self.function = function
        self.function_kwargs = function_kwargs if function_kwargs is not None else {}

        if isinstance(deleted_columns, str):
            self.deleted_columns = (deleted_columns,)
        elif deleted_columns is not None:
            self.deleted_columns = deleted_columns
        else:
            self.deleted_columns = ()


    def _preprocess_data(self, dataset, column_reference):
        """
        Calls self.function to process each dataframe for each sample in the dataset.

        Parameters
        ----------
        dataset : list(list(pd.DataFrame))
            The list of samples, each composed of lists of dataframes.
        column_reference : list(list(dict))
            A nested list of lists of dictionaries. Each dictionary has
            the target columns as keys and their column indices in the
            dataframe as values.

        Returns
        -------
        new_datasets : list(list(pd.DataFrame))
            The list of samples, each composed of lists of dataframes.
            There may be additional dataframes for each sample compared
            to the input dataset.
        new_column_reference : list(list(dict))
            The input column reference, with new references for any
            additional dataframes created by self.function.

        Notes
        -----
        The returned list of dataframes from self.function must all have
        the same number of columns.

        """

        new_datasets = []
        new_column_reference = []
        for i, sample in enumerate(dataset):
            new_samples = []
            new_references = []
            for j, dataframe in enumerate(sample):
                old_columns = list(range(len(dataframe.columns)))
                target_columns = [column_reference[i][j][column] for column in self.target_columns]
                new_dataframes = self.function(dataframe, target_columns, **self.function_kwargs)
                new_columns = list(range(len(new_dataframes[0].columns)))
                for df in new_dataframes:
                    # ensures that indices and column names are correct
                    df.reset_index(drop=True, inplace=True)
                    df.columns = new_columns # all dfs should have same # of columns
                new_samples.extend(new_dataframes)
                new_reference = self._reassign_indices(column_reference[i][j], old_columns)
                new_references.extend([new_reference] * len(new_dataframes))

            new_datasets.append(new_samples)
            new_column_reference.append(new_references)

        return new_datasets, new_column_reference


    def _reassign_indices(self, reference, columns):
        """
        Removes and reorders column references based on self.deleted_columns.

        Parameters
        ----------
        reference : dict
            A dictionary with keys being target variable names, and values
            being their indices within the dataframe columns.
        columns : list
            The original list of column indices (output by list(range(df.columns))),
            Will be used to track the indices for the reference dictionary after
            removing any columns.

        Returns
        -------
        dict
            The updated reference after taking into account the columns removed
            by self.function, as described by self.deleted_columns.

        """

        for column_name in self.deleted_columns:
            columns.pop(columns.index(reference[column_name]))

        return {key: columns.index(val) for key, val in reference.items() if val in columns}


class CalculationFunction(FunctionBase):
    """
    Function that performs a calculation for every entry in each sample.

    Parameters
    ----------
    name : str
        The string representation for this object.
    target_columns : str or (list(str), tuple(str))
        A string or list/tuple of strings designating the target columns
        for this object.
    functions : function or (list(function)/tuple(function))
        The functions that this object uses to process data. If only one function
        is given, it is assumed that the same function is used for both calculations
        for the data to be written to Excel and the data to be used in python.
        If a list/tuple of functions are given, it is assumed that the first
        function is used for processing the data to write to Excel, and the second
        function is used for processing the data to be used in python. The function
        should take args of list(list(pd.DataFrame)), target indices (a list
        of lists of lists of numbers, corresponding to the column index in each
        dataframe for each of the target columns), added columns (a list of lists
        of numbers, corresponding to the column index in the dataframe for each
        added column), the Excel columns (a list of column names corresponding
        to the column in Excel for each added column, eg 'A', 'B', if doing
        the Excel calculations, otherwise None), the first row (the row number
        of the first row of data in Excel, eg 3). The function should output
        a list of lists of pd.DataFrames. The Excel columns and first row values
        are meant to ease the writing of formulas for Excel.
    added_columns : int or str/list(str)/tuple(str)
        The columns that will be acted upon by this object's functions. If
        the input is an integer, then it denotes that the functions act on
        columns that are currently empty, with the number of columns affected
        by the functions being equal to the input integer. If the input is a string
        or list/tuple of strings, it denotes that the functions will change the
        contents of an existing column(s), whose column names are the inputs.
    function_kwargs : dict, optional
        A dictionary of keywords and values to be passed to the function.
        The default is None.

    """

    def __init__(self, name, target_columns, functions,
                 added_columns, function_kwargs=None):
        """
        Raises
        ------
        ValueError
            Raised if there is an issue with added_columns or target_columns.

        """

        super().__init__(name, target_columns)

        if not added_columns:
            raise ValueError(f'Added columns for {self} must be specified and not equal to 0.')
        elif isinstance(added_columns, int):
            if added_columns <= 0:
                raise ValueError(f'Added columns for {self} must be > 0.')
            else:
                self.added_columns = added_columns
        elif isinstance(added_columns, str):
            self.added_columns = [added_columns]
        else:
            self.added_columns = added_columns

        if isinstance(functions, type(lambda _: _)): # is a function
            self.functions = (functions, functions)
        else:
            self.functions = functions

        if function_kwargs is None:
            self.function_kwargs = ({}, {})
        elif isinstance(function_kwargs, dict):
            self.function_kwargs = (function_kwargs, function_kwargs)
        else:
            self.function_kwargs = function_kwargs


    def _do_function(self, dataset, reference, index, excel_columns, first_row):
        """
        Calls self.functions[index] to process each dataframe for each sample in the dataset.

        If index is 0, performs Excel function; if index is 1, performs python functions.

        Parameters
        ----------
        dataset : list(list(pd.DataFrame))
            The list of samples, each composed of lists of dataframes.
        reference : list(list(dict))
            A nested list of lists of dictionaries. Each dictionary has
            the target columns as keys and their column indices in the
            dataframe as values.
        index : int
            Either 0 or 1. If 0, do Excel formulas; if 1, do python formulas.
        excel_columns : list(str) or None
            A list of the Excel column names (eg. ['A', 'B', 'C']) that cover
            the columns of the dataset if index is 0. Is None if index is 1.
        first_row : int
            The first Excel row to use; corresponds to the actual row number
            in Excel (ie is 1-based rather than 0-based), so 1 denotes the
            Excel row 1 and is the first row in the Excel workbook.

        Returns
        -------
        dataset : pd.DataFrame
            The input dataframe modified by the function.

        """

        target_columns = [reference[target] for target in self.target_columns]
        added_columns = reference[self.name]

        dataset = self.functions[index](
            dataset, target_columns, added_columns, excel_columns, first_row,
            **self.function_kwargs[index]
        )

        return dataset


class SummaryFunction(CalculationFunction):
    """
    Calculation that is only performed once per sample or once per dataset.

    Parameters
    ----------
    name : str
        The string representation for this object.
    target_columns : str or (list(str), tuple(str))
        A string or list/tuple of strings designating the target columns
        for this object.
    functions : function or (list(function)/tuple(function))
        The functions that this object uses to process data. If only one function
        is given, it is assumed that the same function is used for both calculations
        for the data to be written to Excel and the data to be used in python.
        If a list/tuple of functions are given, it is assumed that the first
        function is used for processing the data to write to Excel, and the second
        function is used for processing the data to be used in python. The function
        should take args of list(list(pd.DataFrame)), target indices (a list
        of lists of lists of numbers, corresponding to the column index in each
        dataframe for each of the target columns), added columns (a list of lists
        of numbers, corresponding to the column index in the dataframe for each
        added column), the Excel columns (a list of column names corresponding
        to the column in Excel for each added column, eg 'A', 'B', if doing
        the Excel calculations, otherwise None), the first row (the row number
        of the first row of data in Excel, eg 3). The function should output
        a list of lists of pd.DataFrames. The Excel columns and first row values
        are meant to ease the writing of formulas for Excel.
    added_columns : int or str/list(str)/tuple(str)
        The columns that will be acted upon by this object's functions. If
        the input is an integer, then it denotes that the functions act on
        columns that are currently empty, with the number of columns affected
        by the functions being equal to the input integer. If the input is a string
        or list/tuple of strings, it denotes that the functions will change the
        contents of an existing column(s), whose column names are the inputs. Further,
        SummaryFunctions can only modify other SummaryFunction columns with matching
        sample_summary attributes.
    function_kwargs : dict, optional
        A dictionary of keywords and values to be passed to the function.
        The default is None.
    sample_summary : bool, optional
        If True (default), denotes that the SummaryFunction summarizes a sample;
        if False, denotes that the SummaryFunction summarizes a dataset.

    """

    def __init__(self, name, target_columns, functions, added_columns,
                 function_kwargs=None, sample_summary=True):

        super().__init__(name, target_columns, functions, added_columns, function_kwargs)
        self.sample_summary = sample_summary
