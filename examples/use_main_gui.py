# -*- coding: utf-8 -*-
"""Example script to show how to use mcetl.launch_main_gui with defined DataSource objects.

@author: Donald Erb
Created on Sat Aug 22 13:01:37 2020

"""


from mcetl import CalculationFunction, SeparationFunction, DataSource, launch_main_gui
import numpy as np


def offset_data(df, target_indices, calc_indices, excel_columns=None,
                start_row=0, offset=None):
    """Example CalculationFunction with named kwargs"""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            if excel_columns is not None:
                y = df[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[0][i][j]]
                calc = [
                    f'= {y_col}{k + 3 + start_row} + {offset * i}' for k in range(len(y))
                ]

                df[calc_col] = np.where(~np.isnan(y), calc, None)

            else:
                y_col = df[df.columns[target_indices[0][i][j]]]
                df[df.columns[calc_col]] = y_col + (offset * i)

    return df


def offset_normalized_data(df, target_indices, calc_indices, excel_columns=None,
                           start_row=0, offset=None):
    """Adds an offset to normalized data"""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            y_col = df[df.columns[target_indices[0][i][j]]]
            
            if excel_columns is not None:
                df[calc_col] = y_col + f' + {offset * i}'
            else:
                df[calc_col] = y_col + (offset * i)

    return df


def normalize(df, target_indices, calc_indices, excel_columns=None, start_row=0, **kwargs):
    """Performs a min-max normalization to bound values between 0 and 1."""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            if excel_columns is not None:
                y = df[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[0][i][j]]
                start = 3 + start_row
                end = y.count() + 2
                calc = [
                    f'=({y_col}{k + start} - MIN({y_col}$3:{y_col}${end})) / (MAX({y_col}$3:{y_col}${end}) - MIN({y_col}$3:{y_col}${end}))' for k in range(len(y))
                ]

                df[calc_col] = np.where(~np.isnan(y), calc, None)
    
            else:
                y_col = df.columns[target_indices[0][i][j]]
                min_y = df[y_col].min()
                max_y = df[y_col].max()

                df[calc_col] = (df[y_col] - min_y) / (max_y - min_y)
    
    return df


def split(df, target_indices, **kwargs):
    """Separation function that separates each entry once delta-x changes sign."""

    x_col = df[df.columns[target_indices[0]]].to_numpy()
    diff = np.diff(x_col)
    mask = np.where(np.sign(diff[1:]) != np.sign(diff[:-1]))[0] + 2 # +2 b/c diff is one less, and mask is one less than diff

    if len(mask) > 1:
        mask = np.array([mask[0], *mask[np.where(mask[1:] - mask[:-1] != 1)[0] + 1]]) # in case x[i] - x[i+1] = 0

    return np.array_split(df, mask)



def derivative(df, target_indices, calc_indices, excel_columns=None, start_row=0, **kwargs):
    """Calculates the derivative."""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            if excel_columns is not None:
                y = df[target_indices[1][i][j]]
                x_col = excel_columns[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[1][i][j]]
                start = 3 + start_row
                calc = [
                    f'= ({y_col}{k + start} - {y_col}{k + start - 1}) / ({x_col}{k + start} - {x_col}{k + start - 1})' for k in range(len(y))
                ]
                calc[0] = 0

                df[calc_col] = np.where(~np.isnan(y), calc, None)

            else:
                x = df[target_indices[0][i][j]].to_numpy()
                y = df[target_indices[1][i][j]].to_numpy()

                derivative = np.zeros(len(x))
                derivative[1:] = (y[1:] - y[0:-1]) / (x[1:] - x[0:-1])
                df[calc_col] = derivative

    return df


if __name__ == '__main__':

    # Definitions for the Function objects
    offset = CalculationFunction('offset', 'y', offset_data, 1, {'offset': 1000})
    normalize = CalculationFunction('normalize', 'y', normalize, 1)
    offset_normalized = CalculationFunction(
        'offset_normalized', 'normalize', offset_normalized_data, 'normalize', {'offset': 1}
    )
    delta_x_separator = SeparationFunction('delta_x_sep', 'temperature', split, None)
    derivative_calc = CalculationFunction('derivative', ['time', 'mass'], derivative, 1)

    # Definitions for each data source
    xrd = DataSource(
        name='XRD',
        column_labels=['2\u03B8 (\u00B0)', 'Intensity (Counts)', 'Offset Intensity (a.u.)'],
        functions=[offset],
        column_numbers=[1, 2],
        start_row=1,
        end_row=0,
        separator=',',
        xy_plot_indices=[0, 2],
        file_type='csv',
        num_files=1,
        unique_variables=['x', 'y'],
        entry_separation=1,
        sample_separation=2
    )

    ftir = DataSource(
        name='FTIR',
        column_labels=['Wavenumber (1/cm)', 'Absorbance (a.u.)', 'Normalized Absorbance (a.u.)'],
        functions=[normalize, offset_normalized],
        column_numbers=[0, 1],
        start_row=1,
        end_row=0,
        separator=',',
        xy_plot_indices=[0, 2],
        file_type='csv',
        num_files=1,
        unique_variables=['x', 'y'],
        entry_separation=1,
        sample_separation=2
    )

    raman = DataSource(
        name='Raman',
        column_labels=['Raman Shift (1/cm)', 'Intensity (a.u.)', 'Normalized Intensity (a.u.)'],
        functions=[normalize, offset_normalized],
        column_numbers=[0, 1],
        start_row=0,
        end_row=0,
        separator='\t',
        xy_plot_indices=[0, 2],
        file_type='txt',
        num_files=1,
        unique_variables=['x', 'y'],
        entry_separation=1,
        sample_separation=2
    )

    tga = DataSource(
        name='TGA',
        column_labels=['Temperature (\u00B0C)', 'Time (min)',
                       'Mass (%)', 'Mass Loss Rate (%/min)'],
        functions=[delta_x_separator, derivative_calc],
        column_numbers=[0, 1, 2],
        start_row=34,
        end_row=0,
        separator=';',
        xy_plot_indices=[0, 2],
        file_type='txt',
        num_files=1,
        unique_variables=['temperature', 'time', 'mass'],
        unique_variable_indices=[0, 1, 2],
        entry_separation=1,
        sample_separation=2
    )

    dsc = DataSource(
        name='DSC',
        column_labels=['Temperature (\u00B0C)', 'Time (min)', 'Heat Flow, exo up (mW/mg)'],
        functions=[delta_x_separator],
        column_numbers=[0, 1, 2],
        start_row=34,
        end_row=0,
        separator=';',
        xy_plot_indices=[0, 2],
        file_type='txt',
        num_files=1,
        unique_variables=['temperature'],
        entry_separation=1,
        sample_separation=2
    )

    other = DataSource('Other') # For use in case you need to open arbitrary files without processing

    # Put all DataSource objects in this tuple in order to use them
    data_sources = (xrd, ftir, raman, tga, dsc, other)

    # Call the main function with data_sources as the input
    dataframes, fit_results, plot_results = launch_main_gui(data_sources)
