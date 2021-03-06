# -*- coding: utf-8 -*-
"""This is a program that shows the internals of what occurs during function processing for DataSources.

The steps for processing are more clearly broken down so that each step can be understood.


@author: Donald Erb
Created on Aug 22, 2020

"""

import numpy as np
import pandas as pd
from mcetl import (DataSource, PreprocessFunction, CalculationFunction,
                   SummaryFunction, utils)


def f(df, target_indices, calc_indices, excel_columns, first_row, **kwargs):
    """Example sample summary function."""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            if excel_columns is not None:
                cols = [excel_columns[col] for col in target_indices[0][i]]
                df[calc_col] = [
                    f'= SUM({f"{index + first_row}, ".join(cols) + str(index + first_row)})' for index in range(len(df))
                ]

            else:
                df[calc_col] = df[target_indices[0][i]].sum(axis=1)

    return df


def f2(df, target_indices, calc_indices, excel_columns, first_row, **kwargs):
    """Example dataset summary function."""

    targets = []
    for i, sample in enumerate(calc_indices):
        targets.extend([target for target in target_indices[0][i]])

    #only use the last list since that is the dataset summary list
    for calc_col in calc_indices[-1]:
        if excel_columns is not None:
            cols = [excel_columns[col] for col in targets]
            df[calc_col] = [
                f'= SUM({f"{index + first_row}, ".join(cols) + str(index + first_row)})' for index in range(len(df))
            ]

        else:
            df[calc_col] = df[targets].sum(axis=1)

    return df


def split(df, target_indices, **kwargs):
    """Example separation function."""

    x_col = df[df.columns[target_indices[0]]].to_numpy()
    diff = np.diff(x_col)
    mask = np.where(np.sign(diff[1:]) != np.sign(diff[:-1]))[0] + 2 # +2 b/c diff is one less, and mask is one less than diff

    if len(mask) > 1:
        mask = np.array([mask[0], *mask[np.where(mask[1:] - mask[:-1] != 1)[0] + 1]]) #in case x[i] - x[i+1] = 0

    return np.array_split(df, mask)


def func(df, target_indices, calc_indices, excel_columns=None, first_row=0, offset=None):
    """Example CalculationFunction with named kwargs"""

    for i, sample in enumerate(calc_indices):
        for j in range(len(sample) // 2): # 2 calc columns per entry in each sample
            calc_col = sample[j * 2]
            if excel_columns is not None:
                x = df[target_indices[0][i][j]]
                x_col = excel_columns[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[1][i][j]]
                calc = [
                    f'= {x_col}{k + first_row} + {y_col}{k + first_row} + {offset}' for k in range(len(x))
                ]

                df[calc_col] = np.where(~np.isnan(x), calc, '')
            else:
                x_col = df[df.columns[target_indices[0][i][j]]]
                y_col = df[df.columns[target_indices[1][i][j]]]

                df[df.columns[calc_col]] = x_col + y_col + offset

        offset += offset

    return df


def func2(df, target_indices, calc_indices, excel_columns=None, first_row=0, offset=None):
    """Example CalculationFunction with named kwargs"""
    print('target columns', target_indices)
    print('calculation columns', calc_indices)
    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            if excel_columns is not None:
                x = df[target_indices[0][i][j]]
                x_col = excel_columns[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[1][i][j]]
                calc = [
                    f'= {x_col}{k + first_row} + {y_col}{k + first_row} + {offset}' for k in range(len(x))
                ]

                df[calc_col] = np.where(~np.isnan(x), calc, '')
            else:
                x_col = df[df.columns[target_indices[0][i][j]]]
                y_col = df[df.columns[target_indices[1][i][j]]]

                df[df.columns[calc_col]] = x_col + y_col + offset

        offset += offset

    return df


def func3(df, target_indices, calc_indices, excel_columns=None, **kwargs):
    """Example CalculationFunction using *args and **kwargs to swallow additional keyword arguments."""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            x_col = df.columns[target_indices[0][i][j]]
            x = df[x_col].to_numpy()

            if excel_columns is not None:
                df[df.columns[calc_col]] = np.where(
                    x, x + f' + {kwargs["offset"]}', None
                )
            else:
                df[df.columns[calc_col]] = x + kwargs['offset']

            kwargs['offset'] += kwargs['offset']

    return df


#Functions
calculation = CalculationFunction('calc', ['x', 'y'], func, 2, {'offset': 10})
calculation2 = CalculationFunction('calc2', ['x', 'y'], func2, 1, {'offset': 5})
calculation3 = CalculationFunction('calc3', ['calc2'], func3, 'calc2', {'offset': 1})
separator = PreprocessFunction('sep', 'x', split, None)
sum1 = SummaryFunction('sum', 'x', f, added_columns=2)
sum3 = SummaryFunction('sum3', 'x', f2, 1, sample_summary=False)

#Data Source
xrd = DataSource(
    'xrd', functions=[calculation, calculation2, calculation3, separator, sum1, sum3],
    unique_variables=['x', 'y'], sample_separation=3, entry_separation=1,
    excel_row_offset=1, excel_column_offset=1
)
data_source = xrd

x = np.array([*np.linspace(0, 10), *np.linspace(10, 0, 40)])
x2 = np.linspace(0, 20, 600)
data = {0: x, 1: 2 * x, 2: np.zeros(x.size)}
data2 = {0: x2, 1: 4 * x2, 2: np.zeros(x2.size)}

#load data from files and assign indices for unique variables, would be done at same time in actual program
#headers will be unique integer for each df, eg. 0, 1, 2
#structure is: [ [ [file1, file2], [file3, file4] ](one dataset), [[], []]]
dataframes = [
    [[pd.DataFrame(data), pd.DataFrame(data)], [pd.DataFrame(data2)]],
    [[pd.DataFrame(data)], [pd.DataFrame(data2)]]
]

#emulates importing the data as done in mcetl.launch_main_gui
import_vals = [[[] for sample in dataset] for dataset in dataframes]
for i, dataset in enumerate(dataframes):
    for j, sample in enumerate(dataset):
        for k, measurement in enumerate(sample):
            import_vals[i][j].append({'x': 1, 'y': 0})
            sample[k] = utils.optimize_memory(measurement)

#perform separation calcs
dataframes, import_vals = data_source._do_preprocessing(
    dataframes, import_vals
)
#assign reference indices for all relevant columns
data_source._set_references(dataframes, import_vals)
references = data_source.references

#merge dfs for each dataset
merged_dataframes = data_source.merge_datasets(dataframes)

#to compare excel vs python formulas
merged_dataframes2 = [df.copy() for df in merged_dataframes]

#doing excel formulas
merged_dataframes = data_source._do_excel_functions(merged_dataframes)

#doing python formulas
merged_dataframes2 = data_source._do_python_functions(merged_dataframes2)

lengths = data_source.lengths.copy()
#split data back into individual dataframes
output_dfs = data_source.split_into_entries(merged_dataframes)

# manually set some DataSource attributes in order to split the other copied dataframe
# since the attributes are reset after splitting a merged dataframe
data_source._added_separators = True
data_source.lengths = lengths

#split data back into individual dataframes
output_dfs2 = data_source.split_into_entries(merged_dataframes2)
