=========================
Creating Function Objects
=========================

Function objects are simple wrappers around functions that allow referencing the
function by a name, specifying which columns the function should act on, and other
relevant information about the function's behavior. Function objects come in three types:

* PreprocessFunctions: process each data entry as soon as it is imported from the files
* CalculationFunctions: process each entry in each sample in each dataset
* SummaryFunctions: process each sample or each dataset; performed last

Note that all functions will process
`pandas DataFrames <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_.
To speed up calculations within the functions, it is suggested to make use of
vectorization of the pandas DataFrame or Series or of the underlying numpy
arrays, since vectorization can be significantly faster than iterating over
each index using a for loop.

This tutorial will cover some basic examples for the three Function types.
To see more advanced examples, see the
`example programs <https://github.com/derb12/mcetl/tree/main/examples>`_ in the
GitHub respository. The use_main_gui.py example program shows many different
uses of the three Function objects, and the creating_functions.py example program
walks through the internals of how :func:`.launch_main_gui` calls the Functions so
that each individual step can be understood.

.. note::
   For functions of all three Function types, it is a good idea to add ``**kwargs`` to
   the function input. In later versions of mcetl, additional items may
   be passed to functions, but they will always be added as keyword arguments
   (ie. passed as ``name=value``). By adding ``**kwargs``, any unwanted keyword arguments
   for functions will be ignored and not cause issues when upgrading mcetl.

PreprocessFunctions
-------------------

A :class:`.PreprocessFunction` will perform its function on each data entry
individually. Example usage of a PreprocessFunction can be to split a single
data entry into multiple entries, collect information on all data entries in
each sample in each dataset for usage later, or just simple processes that are
easier to do per entry rather than when each dataset is grouped together.

The function for a PreprocessFunction must take at least two arguments: the
dataframe containing the data for the entry, and a list of indices that tell
which columns of the dataframe contain the data used by the function. **The function
must return a list of dataframes after processing**, even if only one dataframe
is used within the function.

A simple function to split dataframes based on the segment number, and then remove the
segment number column is shown below.

.. code-block:: python

    import mcetl
    import numpy as np

    def split_segments(df, target_indices, **kwargs):
        """
        Preprocess function that separates each entry based on the segment number.

        Also removes the segment column after processing since it is not needed
        in the final output.

        Parameters
        ----------
        df : pandas.DataFrame
            The dataframe of the entry.
        target_indices : list(int)
            The indices of the target columns.

        Returns
        -------
        output_dataframes : list(pandas.DataFrame)
            The list of dataframes after splitting by segment number.

        """

        segment_index = target_indices[0]
        segment_col = df[df.columns[segment_index]].to_numpy()
        mask = np.where(segment_col[:-1] != segment_col[1:])[0] + 1 # + 1 since mask loses one index

        output_dataframes = np.array_split(df, mask)

        for dataframe in output_dataframes:
            dataframe.drop(segment_index, 1, inplace=True)

        return output_dataframes

    # targets the 'segment' column from the imported data
    segment_separator = mcetl.PreprocessFunction(
        name='segment_separator', target_columns='segment',
        function=split_segments, deleted_columns=['segment']
    )

In addition, PreprocessFunctions can be used for procedures that are easier to perform
on each data entry separately, rather than when all of the data is collected together.
For example, sorting each entry based on the values in one of its columns.

.. code-block:: python

    def sort_columns(df, target_indices, **kwargs):
        """Sorts the dataframe based on the values of the target column."""
        return [df.sort_values(target_indices[0])]

    # targets the 'diameter' column from the imported data
    pore_preprocess = mcetl.PreprocessFunction('sort_data', 'diameter', sort_columns)

CalculationFunctions
--------------------

A :class:`.CalculationFunction` will perform its function on each merged dataset.
Each merged dataset is composed of all data entries for each sample concatenated
together, resembling how the dataset will look when written to an Excel sheet.
This makes the functions more difficult to create since target columns are given as
nested lists of lists for each sample, but allows access to all data
in a dataset, if required for complex calculations.

Each CalculationFunction can have two functions: one for performing the calculations
on data for Excel and one for performing calculations on data for Python. This way,
the Excel calculations can create strings to match Excel-specific functions, like
using '=SUM(A1:A3)' to make the data dynamic within the Excel workbook, while the
Python functions can calculate the actual numerical data (eg. sum(data[0:2]) to match
the previous Excel formula). If only a single, numerical calculation is desired, regardless of
whether the data is being output to Excel or Python, then only a single function needs
to be specified (an example of such a function is given below).

The functions for a CalculationFunction must take at least three arguments: the
dataframe containing the data for the dataset, a list of lists of integers that tell
which columns in the dataframe contain the data used by the function, and a list of
lists of integers that tell which columns in the dataframe are used for the output
of the function. Additionally,
two keyword arguments are passed to the function: ``excel_columns``, which is a list
of strings corresponding to the columns in Excel used by the dataset (eg. ['A',
'B', 'C', 'D']) if doing Excel functions and is None if doing Python functions,
and ``first_row``, which is an integer telling the first row in
Excel that the data will begin on (3 by default, since the first row is the sample
name and the second is the column name). **The functions must return a DataFrame
after processing**, even if all changes to the input DataFrame were done in place.

A simple function that adds a column of offset data is shown below.

.. code-block:: python

    import mcetl
    import numpy as np

    def offset_data_excel(df, target_indices, calc_indices, excel_columns,
                          first_row, offset, **kwargs):
        """Creates a string that will add an offset to data in Excel."""

        total_count = 0
        for i, sample in enumerate(calc_indices):
            for j, calc_col in enumerate(sample):
                y = df[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[0][i][j]]
                calc = [
                    f'= {y_col}{k + first_row} + {offset * total_count}' for k in range(len(y))
                ]
                # use np.where(~np.isnan(y)) so that the calculation works for unequally-sized
                # datasets
                df[calc_col] = np.where(~np.isnan(y), calc, None)
                total_count += 1

        return df

    def offset_data_python(df, target_indices, calc_indices, first_row, **kwargs):
        """Adds an offset to data."""

        total_count = 0
        for i, sample in enumerate(calc_indices):
            for j, calc_col in enumerate(sample):
                y = df[target_indices[0][i][j]]
                df[calc_col] = y + (kwargs['offset'] * total_count)
                total_count += 1

        return df

    # targets the 'data' column from the imported data
    offset = mcetl.CalculationFunction(
        name='offset', target_columns='data', functions=(offset_data_excel, offset_data_python),
        added_columns=1, function_kwargs={'offset': 10}
    )

Alternatively, the two functions could be combined into one, and the calculation
route could be decided by examining the value of the ``excel_columns`` input, which
is a list of strings if processing for Excel, and None when processing for Python.

.. code-block:: python

    import mcetl
    import numpy as np

    def offset_data(df, target_indices, calc_indices, excel_columns,
                    first_row, offset, **kwargs):
        """Adds an offset to data."""

        total_count = 0
        for i, sample in enumerate(calc_indices):
            for j, calc_col in enumerate(sample):
                if excel_columns is not None: # do Excel calculations
                    y = df[target_indices[0][i][j]]
                    y_col = excel_columns[target_indices[0][i][j]]
                    calc = [
                        f'= {y_col}{k + first_row} + {offset * total_count}' for k in range(len(y))
                    ]
                    df[calc_col] = np.where(~np.isnan(y), calc, None)

                else: # do Python calculations
                    y = df[target_indices[0][i][j]]
                    df[calc_col] = y + (offset * total_count)
                total_count += 1

        return df

    # targets the 'data' column from the imported data
    offset = mcetl.CalculationFunction(
        name='offset', target_columns='data', functions=offset_data,
        added_columns=1, function_kwargs={'offset': 10}
    )

To modify the contents of an existing column, the input for ``added_columns``
for CalculationFunction should be a string designating the target: either a
variable from the imported data, or the name of a CalculationFunction.

.. code-block:: python

    import mcetl
    import numpy as np

    def normalize(df, target_indices, calc_indices, excel_columns, first_row, **kwargs):
        """Performs a min-max normalization to bound values between 0 and 1."""

        for i, sample in enumerate(calc_indices):
            for j, calc_col in enumerate(sample):
                if excel_columns is not None:
                    y = df[target_indices[0][i][j]]
                    y_col = excel_columns[target_indices[0][i][j]]
                    end = y.count() + 2
                    calc = [
                        (f'=({y_col}{k + first_row} - MIN({y_col}$3:{y_col}${end})) / '
                         f'(MAX({y_col}$3:{y_col}${end}) - MIN({y_col}$3:{y_col}${end}))')
                        for k in range(len(y))
                    ]

                    df[calc_col] = np.where(~np.isnan(y), calc, None)

                else:
                    y_col = df.columns[target_indices[0][i][j]]
                    min_y = df[y_col].min()
                    max_y = df[y_col].max()

                    df[calc_col] = (df[y_col] - min_y) / (max_y - min_y)

        return df

    def offset_normalized(df, target_indices, calc_indices, excel_columns,
                          offset, **kwargs):
        """Adds an offset to normalized data."""

        total_count = 0
        for i, sample in enumerate(calc_indices):
            for j, calc_col in enumerate(sample):
                y_col = df[target_indices[0][i][j]]
                offset_amount = offset * total_count
                if excel_columns is not None:
                    df[calc_col] = y_col + f' + {offset_amount}'
                else:
                    df[calc_col] = y_col + offset_amount
                total_count += 1

        return df

    # targets the 'data' column from the imported data
    normalize_func = mcetl.CalculationFunction(
        name='normalize', target_columns='data',
        functions=normalize, added_columns=1
    )
    # targets the 'normalize' column from the the 'normalize' CalculationFunction
    # and also alters its contents
    offset_func = mcetl.CalculationFunction(
        name='offset', target_columns='normalize', functions=offset_normalized,
        added_columns='normalize', function_kwargs={'offset': 10}
    )

If the CalculationFunction does the same calculation, regardless of whether
the data is going to Excel or for later processing in Python, then a mutable
object, like a list, can be used in function_kwargs to signify that the calculation
has been performed to prevent processing twice.

.. code-block:: python

    import mcetl

    def offset_numerical(df, target_indices, calc_indices, excel_columns, **kwargs):
        """Adds a numerical offset to data."""

        # Add this section to prevent doing numerical calculations twice.
        if excel_columns is None and kwargs['processed'][0]:
            return df # return to prevent processing twice
        elif excel_columns is not None:
            kwargs['processed'][0] = True

        # Regular calculation section
        offset = kwargs['offset']
        total_count = 0
        for i, sample in enumerate(calc_indices):
            for j, calc_col in enumerate(sample):
                df[calc_col] = df[target_indices[0][i][j]] + (offset * total_count)
                total_count += 1

        return df

    # targets the 'data' column from the imported data
    numerical_offset = mcetl.CalculationFunction(
        name='numerical offset', target_columns='data', functions=offset_numerical,
        added_columns=1, function_kwargs={'offset': 10, 'processed': [False]}
    )

SummaryFunctions
----------------

A :class:`.SummaryFunction` is very similar to CalculationFunctions,
performing its functions on each merged dataset and requiring outputting a single
DataFrame. However, SummaryFunctions differ from CalculationFunctions in
that their added columns are not within the data entries themselves. Instead,
SummaryFunctions can either be a sample SummaryFunction (by using ``sample_summary=True``
when creating the object), which is equivalent to appending a data entry to
each sample in each dataset, or a dataset SummaryFunction (by using ``sample_summary=False``
when creating the object), which is equivalent to appending a sample to each dataset.

For example, consider calculating the elatic modulus from tensile tests. Each sample
in the dataset will have multiple measurements/entries, so a sample SummaryFunction
could be used to calculate the average elastic modulus for each sample, and a dataset
SummaryFunction could be used to create a table listing the average elastic modulus for
each sample in the dataset for easy referencing.

.. code-block:: python

    import mcetl
    import numpy as np
    import pandas as pd
    from scipy import optimize

    def stress_model(strain, modulus):
        """
        The linear estimate of the stress-strain curve using the strain and estimated modulus.

        Parameters
        ----------
        strain : array-like
            The array of experimental strain values, unitless (with cancelled
            units, such as mm/mm).
        modulus : float
            The estimated elastic modulus for the data, with units of GPa (Pa * 10**9).

        Returns
        -------
        array-like
            The estimated stress data following the linear model, with units of Pa.

        """
        return strain * modulus * 1e9


    def tensile_calculation(df, target_indices, calc_indices, excel_columns, **kwargs):
        """Calculates the elastic modulus from the stress-strain curve for each entry."""

        if excel_columns is None and kwargs['processed'][0]:
            return df # return to prevent processing twice
        elif excel_columns is not None:
            kwargs['processed'][0] = True

        num_columns = 2 # the number of calculation columns per entry
        for i, sample in enumerate(calc_indices):
            for j in range(len(sample) // num_columns):
                strain_index = target_indices[0][i][j]
                stress_index = target_indices[1][i][j]
                nan_mask = (~np.isnan(df[strain_index])) & (~np.isnan(df[stress_index]))

                # to convert strain from % to unitless
                strain = df[strain_index].to_numpy()[nan_mask] / 100
                 # to convert stress from MPa to Pa
                stress = df[stress_index].to_numpy()[nan_mask] * 1e6

                # only use data where stress varies linearly with respect to strain
                linear_mask = (
                    (strain >= kwargs['lower_limit']) & (strain <= kwargs['upper_limit'])
                )
                initial_guess = 80 # initial guess of the elastic modulus, in GPa

                modulus, covariance = optimize.curve_fit(
                    stress_model, strain[linear_mask], stress[linear_mask],
                    p0=[initial_guess]
                )

                df[sample[0 + (j * num_columns)]] = pd.Series(('Value', 'Standard Error'))
                df[sample[1 + (j * num_columns)]] = pd.Series(
                    (modulus[0], np.sqrt(np.diag(covariance)[0]))
                )

        return df


    def tensile_sample_summary(df, target_indices, calc_indices, excel_columns, **kwargs):
        """Summarizes the mechanical properties for each sample."""

        if excel_columns is None and kwargs['processed'][0]:
            return df # to prevent processing twice

        num_cols = 2 # the number of calculation columns per entry from tensile_calculation
        for i, sample in enumerate(calc_indices):
            if not sample: # skip empty lists
                continue

            entries = []
            for j in range(len(target_indices[0][i]) // num_cols):
                entries.append(target_indices[0][i][j * num_cols:(j + 1) * num_cols])

            df[sample[0]] = pd.Series(['Elastic Modulus (GPa)'])
            df[sample[1]] = pd.Series([np.mean([df[entry[1]][0] for entry in entries])])
            df[sample[2]] = pd.Series([np.std([df[entry[1]][0] for entry in entries])])

        return df


    def tensile_dataset_summary(df, target_indices, calc_indices, excel_columns, **kwargs):
        """Summarizes the mechanical properties for each dataset."""

        if excel_columns is None and kwargs['processed'][0]:
            return df # to prevent processing twice

        # the number of samples is the number of lists in calc_indices - 1
        num_samples = len(calc_indices[:-1])

        # calc index is -1 since only the last dataframe is the dataset summary dataframe
        df[calc_indices[-1][0]] = pd.Series(
            [''] + [f'Sample {num + 1}' for num in range(num_samples)]
        )
        df[calc_indices[-1][1]] = pd.Series(
            ['Average'] + [df[indices[1]][0] for indices in target_indices[0][:-1]]
        )
        df[calc_indices[-1][2]] = pd.Series(
            ['Standard Deviation'] + [df[indices[2]][0] for indices in target_indices[0][:-1]]
        )

        return df

    # share the keyword arguments between all function objects
    tensile_kwargs = {'lower_limit': 0.0015, 'upper_limit': 0.005, 'processed': [False]}

    # targets the 'data' column from the imported data
    tensile_calc = mcetl.CalculationFunction(
        name='tensile calc', target_columns=['strain', 'stress'],
        functions=tensile_calculation, added_columns=2,
        function_kwargs=tensile_kwargs
    )
    # targets the columns from the the 'tensile calc' CalculationFunction
    stress_sample_summary = mcetl.SummaryFunction(
        name='tensile sample summary', target_columns=['tensile calc'],
        functions=tensile_sample_summary, added_columns=3,
        function_kwargs=tensile_kwargs, sample_summary=True
    )
    # targets the columns from the the 'tensile sample summary' SummaryFunction
    stress_dataset_summary = mcetl.SummaryFunction(
        name='tensile dataset summary', target_columns=['tensile sample summary'],
        functions=tensile_dataset_summary, added_columns=3,
        function_kwargs=tensile_kwargs, sample_summary=False
    )
