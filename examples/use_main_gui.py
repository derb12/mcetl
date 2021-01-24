# -*- coding: utf-8 -*-
"""Example script to show how to use mcetl.launch_main_gui with defined DataSource objects.

@author: Donald Erb
Created on Aug 22, 2020

"""


import itertools

import mcetl
import numpy as np
import pandas as pd
from scipy import optimize


def offset_data(df, target_indices, calc_indices, excel_columns,
                first_row, offset=None, **kwargs):
    """Example CalculationFunction with named kwargs"""

    total_count = 0
    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            if excel_columns is not None:
                y = df[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[0][i][j]]
                calc = [
                    f'= {y_col}{k + first_row} + {offset * total_count}' for k in range(len(y))
                ]
                # use np.where(~np.isnan(y)) so that the calculation works for unequally-sized
                # datasets
                df[calc_col] = np.where(~np.isnan(y), calc, None)

            else:
                y_col = df[df.columns[target_indices[0][i][j]]]
                df[df.columns[calc_col]] = y_col + (offset * total_count)
            total_count += 1

    return df


def offset_normalized_data(df, target_indices, calc_indices, excel_columns,
                           offset=None, **kwargs):
    """Adds an offset to normalized data"""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            y_col = df[df.columns[target_indices[0][i][j]]]

            if excel_columns is not None:
                df[calc_col] = y_col + f' + {offset * i}'
            else:
                df[calc_col] = y_col + (offset * i)

    return df


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


def split(df, target_indices, **kwargs):
    """Preprocess function that separates each entry where delta-x changes sign."""

    x_col = df[df.columns[target_indices[0]]].to_numpy()
    diff = np.diff(x_col)
    mask = np.where(np.sign(diff[1:]) != np.sign(diff[:-1]))[0] + 2 # +2 b/c diff is one less, and mask is one less than diff

    if len(mask) > 1:
        mask = np.array([mask[0], *mask[np.where(mask[1:] - mask[:-1] != 1)[0] + 1]]) # in case x[i] - x[i+1] = 0

    return np.array_split(df, mask)


def split_segments(df, target_indices, **kwargs):
    """
    Preprocess function that separates each entry based on the segment number.

    Also removes the segment column after processing since it is not needed
    in the final output.

    """

    segment_index = target_indices[0]
    segment_col = df[df.columns[segment_index]].to_numpy()
    mask = np.where(segment_col[:-1] != segment_col[1:])[0] + 1 # + 1 since mask loses one index

    output_dataframes = np.array_split(df, mask)

    for dataframe in output_dataframes:
        dataframe.drop(segment_index, 1, inplace=True)

    return output_dataframes


def derivative(df, target_indices, calc_indices, excel_columns, first_row, **kwargs):
    """Calculates the derivative."""

    for i, sample in enumerate(calc_indices):
        for j, calc_col in enumerate(sample):
            if excel_columns is not None:
                y = df[target_indices[1][i][j]]
                x_col = excel_columns[target_indices[0][i][j]]
                y_col = excel_columns[target_indices[1][i][j]]
                calc = [
                    f'= ({y_col}{k + first_row} - {y_col}{k + first_row - 1}) / ({x_col}{k + first_row} - {x_col}{k + first_row - 1})' for k in range(len(y))
                ]
                calc[0] = 0

                df[calc_col] = np.where(~np.isnan(y), calc, None)

            else:
                x = df[target_indices[0][i][j]].to_numpy()
                y = df[target_indices[1][i][j]].to_numpy()

                derivative = np.zeros(x.size)
                derivative[1:] = (y[1:] - y[0:-1]) / (x[1:] - x[0:-1])
                df[calc_col] = derivative

    return df


def pore_preprocessor(df, target_indices, **kwargs):
    """
    Sorts the dataframe according to the diameter.

    Easier to do for each individual data file rather than when each
    dataset is combined together.

    """

    return [df.sort_values(target_indices[0])]


def pore_analysis(df, target_indices, calc_indices, excel_columns, **kwargs):
    """
    Creates a histogram of pore sizes weighted by the pore area for each entry.

    Also computes the average pore diameter and the standard deviation of pore size.

    """

    if excel_columns is None and kwargs['processed'][0]:
        return df # to prevent processing twice
    elif excel_columns is not None:
        kwargs['processed'][0] = True

    max_pore_size = df[itertools.chain.from_iterable(target_indices[0])].max(numeric_only=True).max()
    pore_bins = np.arange(-kwargs['bin_size'][0], max_pore_size + kwargs['bin_size'][0],
                          kwargs['bin_size'][0])
    # in case the number of measured pores is less than the number of bins
    if pore_bins[1:].size > len(df):
        df = pd.concat((df, pd.DataFrame({'temp': pore_bins})), axis=1).drop('temp', axis=1)

    for i, sample in enumerate(calc_indices):
        for j in range(len(sample) // 10): # 10 calc columns per entry in each sample

            # d designates diameters, a designates areas
            d_index = target_indices[0][i][j]
            a_index = target_indices[1][i][j]

            nan_mask = (~np.isnan(df[d_index])) & (~np.isnan(df[a_index]))
            avg_pore_size = np.average(df[d_index][nan_mask], weights=df[a_index][nan_mask])
            area_histogram = np.histogram(df[d_index], pore_bins, weights=df[a_index])[0]
            norm_area_histogram = np.histogram(df[d_index], pore_bins,
                                               weights=df[a_index], density=True)[0] * kwargs['bin_size'][0]

            df[sample[1 + (j * 10)]] = pd.Series(pore_bins[1:])
            df[sample[2 + (j * 10)]] = pd.Series(np.histogram(df[d_index], pore_bins)[0])
            df[sample[3 + (j * 10)]] = pd.Series(area_histogram)
            df[sample[4 + (j * 10)]] = pd.Series(np.cumsum(area_histogram))
            df[sample[5 + (j * 10)]] = df[sample[3 + (j * 10)]] / kwargs['bin_size'][0]
            df[sample[6 + (j * 10)]] = pd.Series(np.cumsum(norm_area_histogram))
            df[sample[7 + (j * 10)]] = pd.Series(norm_area_histogram / kwargs['bin_size'][0])
            df[sample[8 + (j * 10)]] = pd.Series((
                'non-weighted', np.average(df[d_index][nan_mask]),
                'Area-weighted', avg_pore_size
            ))
            df[sample[9 + (j * 10)]] = pd.Series((
                '', np.std(df[d_index][nan_mask]),
                '', np.sqrt(np.average((df[d_index][nan_mask] - avg_pore_size)**2,
                                       weights=df[a_index][nan_mask]))
            ))

    return df


def pore_sample_summary(df, target_indices, calc_indices, excel_columns, **kwargs):
    """
    Creates a histogram of pore sizes weighted by the pore area for each sample.

    Also computes the average pore diameter and the standard deviation of pore size.

    """

    if excel_columns is None and kwargs['processed'][0]:
        return df # to prevent processing twice

    max_pore_size = df[itertools.chain.from_iterable(target_indices[0])].max(numeric_only=True).max()
    pore_bins = np.arange(-kwargs['bin_size'][0], max_pore_size + kwargs['bin_size'][0],
                          kwargs['bin_size'][0])

    for i, sample in enumerate(calc_indices):
        if not sample: # skip empty lists
            continue

        diameters = np.hstack([df[num][~np.isnan(df[num])] for num in target_indices[0][i]])
        areas = np.hstack([df[num][~np.isnan(df[num])] for num in target_indices[1][i]])

        avg_pore_size = np.average(diameters, weights=areas)
        area_histogram = np.histogram(diameters, pore_bins, weights=areas)[0]
        norm_area_histogram = np.histogram(diameters, pore_bins,
                                           weights=areas, density=True)[0] * kwargs['bin_size'][0]

        df[sample[0]] = pd.Series(pore_bins[1:])
        df[sample[1]] = pd.Series(np.histogram(diameters, pore_bins)[0])
        df[sample[2]] = pd.Series(area_histogram)
        df[sample[3]] = pd.Series(np.cumsum(area_histogram))
        df[sample[4]] = df[sample[2]] / kwargs['bin_size'][0]
        df[sample[5]] = pd.Series(np.cumsum(norm_area_histogram))
        df[sample[6]] = pd.Series(norm_area_histogram / kwargs['bin_size'][0])
        df[sample[7]] = pd.Series(('non-weighted', np.average(diameters),
                                   'Area-weighted', avg_pore_size))
        df[sample[8]] = pd.Series(('', np.std(diameters),
                                   '', np.sqrt(np.average((diameters - avg_pore_size)**2, weights=areas))))

    return df


def pore_dataset_summary(df, target_indices, calc_indices, excel_columns, **kwargs):
    """
    Summarizes the average pore size for each sample and its standard deviation.

    """

    if excel_columns is None and kwargs['processed'][0]:
        return df # to prevent processing twice

    # calc index is -1 since only the last dataframe is the dataset summary dataframe
    df[calc_indices[-1][0]] = pd.Series((f'Sample {num + 1}' for num in range(len(calc_indices[:-1]))))
    df[calc_indices[-1][1]] = pd.Series((df[indices[-2]][1] for indices in target_indices[0][:-1]))
    df[calc_indices[-1][2]] = pd.Series((df[indices[-1]][1] for indices in target_indices[0][:-1]))
    df[calc_indices[-1][3]] = pd.Series((df[indices[-2]][3] for indices in target_indices[0][:-1]))
    df[calc_indices[-1][4]] = pd.Series((df[indices[-1]][3] for indices in target_indices[0][:-1]))

    return df


def stress_model(strain, modulus):
    """
    Returns the linear estimate of the stress-strain curve using the strain and estimated modulus.

    Used for fitting data with scipy.

    Parameters
    ----------
    strain : array-like
        The array of experimental strain values, unitless (or with cancelled
        units, such as mm/mm).
    modulus : float
        The estimated elastic modulus for the data, with units of GPa (Pa * 10^9).

    Returns
    -------
    array-like
        The estimated stress data following the linear model, with units of Pa.

    """

    return strain * modulus * 1e9


def stress_strain_analysis(df, target_indices, calc_indices, excel_columns, **kwargs):
    """
    Calculates the mechanical properties from the stress-strain curve for each entry.

    Calculated properties include elastic modulus, 0.2% offset yield stress,
    ultimate tensile strength, and fracture strain.

    """

    if excel_columns is None and kwargs['processed'][0]:
        return df # to prevent processing twice

    empty_filler = 'N/A' if excel_columns is not None else None
    num_columns = 7 # the number of calculation columns per entry
    for i, sample in enumerate(calc_indices):
        for j in range(len(sample) // num_columns):
            strain_index = target_indices[0][i][j]
            stress_index = target_indices[1][i][j]
            nan_mask = (~np.isnan(df[strain_index])) & (~np.isnan(df[stress_index]))

            strain = df[strain_index].to_numpy()[nan_mask] / 100 # to convert from % to unitless
            stress = df[stress_index].to_numpy()[nan_mask] * 1e6 # to convert from MPa to Pa

            line_mask = (strain >= kwargs['lower_limit'][0]) & (strain <= kwargs['upper_limit'][0])
            modulus, covar = optimize.curve_fit(
                stress_model, strain[line_mask], stress[line_mask], p0=[80],
                method='trf', loss='soft_l1'
            )

            predicted_ultimate = np.nanmax(stress)
            uts_index = np.abs(stress - predicted_ultimate).argmin() + 1

            offset = stress - ((strain - 0.002) * modulus * 1e9) # 0.2% strain offset
            # using linear interpolation to get the exact crossing point of the offset and measured curves
            y0, y1 = (offset[offset > 0][-1], offset[offset <= 0][0])
            x0, x1 = (strain[offset > 0][-1], strain[offset <= 0][0])
            x_intercept = x0 - ((y0 * (x1 - x0)) / (y1 - y0))
            predicted_yield = float((x_intercept - 0.002) * modulus * 1e9)

            # predict fracture where stress[i] - stress[i + 1] is > 50 MPa
            try:
                predicted_fracture = 100 * strain[np.where(stress[:-1] - stress[1:] > 50e6)[0][0]]
            except IndexError: # fracture condition never reached
                predicted_fracture = 'N/A'

            df[sample[0 + (j * num_columns)]] = pd.Series(100 * np.log(1 + strain[:uts_index]))
            df[sample[1 + (j * num_columns)]] = pd.Series(stress[:uts_index] * (1 + strain[:uts_index]) / 1e6)
            df[sample[2 + (j * num_columns)]] = pd.Series(('Value', 'Standard Error'))
            df[sample[3 + (j * num_columns)]] = pd.Series((modulus[0], np.sqrt(np.diag(covar)[0])))
            df[sample[4 + (j * num_columns)]] = pd.Series((predicted_yield / 1e6, empty_filler))
            df[sample[5 + (j * num_columns)]] = pd.Series((predicted_ultimate / 1e6, empty_filler))
            df[sample[6 + (j * num_columns)]] = pd.Series((predicted_fracture, empty_filler))

    # prevents reprocessing the data
    kwargs['processed'][0] = True if excel_columns is not None else False

    return df


def tensile_sample_summary(df, target_indices, calc_indices, excel_columns, **kwargs):
    """
    Summarizes the mechanical properties for each sample.

    """

    if excel_columns is None and kwargs['processed'][0]:
        return df # to prevent processing twice

    num_cols = 7 # the number of calculation columns per entry from stress_strain_analysis
    for i, sample in enumerate(calc_indices):
        if not sample: # skip empty lists
            continue

        entries = [
            target_indices[0][i][j * num_cols:(j + 1) * num_cols] for j in range(len(target_indices[0][i]) // num_cols)
        ]

        df[sample[0]] = pd.Series(('Elastic Modulus (GPa)', 'Offset Yield Stress (MPa)',
                                   'Ultimate Tensile Strength (MPa)', 'Fracture Strain (%)'))
        df[sample[1]] = pd.Series(
            [np.mean([df[entry[3 + j]][0] for entry in entries if df[entry[3 + j]][0] != 'N/A']) for j in range(4)]
        )
        df[sample[2]] = pd.Series(
            [np.std([df[entry[3 + j]][0] for entry in entries if df[entry[3 + j]][0] != 'N/A']) for j in range(4)]
        )

    return df


def tensile_dataset_summary(df, target_indices, calc_indices, excel_columns, **kwargs):
    """
    Summarizes the mechanical properties for each dataset.

    """

    if excel_columns is None and kwargs['processed'][0]:
        return df # to prevent processing twice

    # calc index is -1 since only the last dataframe is the dataset summary dataframe
    df[calc_indices[-1][0]] = pd.Series([''] + [f'Sample {num + 1}' for num in range(len(calc_indices[:-1]))])
    df[calc_indices[-1][1]] = pd.Series(['Average'] + [df[indices[1]][0] for indices in target_indices[0][:-1]])
    df[calc_indices[-1][2]] = pd.Series(
        ['Standard Deviation'] + [df[indices[2]][0] for indices in target_indices[0][:-1]]
    )
    df[calc_indices[-1][3]] = pd.Series(['Average'] + [df[indices[1]][1] for indices in target_indices[0][:-1]])
    df[calc_indices[-1][4]] = pd.Series(
        ['Standard Deviation'] + [df[indices[2]][1] for indices in target_indices[0][:-1]]
    )
    df[calc_indices[-1][5]] = pd.Series(['Average'] + [df[indices[1]][2] for indices in target_indices[0][:-1]])
    df[calc_indices[-1][6]] = pd.Series(
        ['Standard Deviation'] + [df[indices[2]][2] for indices in target_indices[0][:-1]]
    )
    df[calc_indices[-1][7]] = pd.Series(['Average'] + [df[indices[1]][3] for indices in target_indices[0][:-1]])
    df[calc_indices[-1][8]] = pd.Series(
        ['Standard Deviation'] + [df[indices[2]][3] for indices in target_indices[0][:-1]]
    )

    return df


def carreau_model(shear_rate, mu_0, mu_inf, lambda_, n):
    """
    Estimates the Carreau model for viscosity.

    Used for fitting data using scipy.

    Parameters
    ----------
    shear_rate : array-like
        The experimental shear rate data, with units of 1/s.
    mu_0 : float
        The estimated viscosity at a shear rate of 0 1/s; units of Pa*s.
    mu_inf : float
        The estimated viscosity at infinite shear rate; units of Pa*s.
    lambda_ : float
        The reciprocal of the shear rate at which the material begins
        to flow in a non-Newtonian way; units of s.
    n : float
        The power law index for the material (1-n defines the slope of the
        curve of the non-Newtonian section of the log(viscosity) vs log(shear rate)
        curve); unitless.

    Returns
    -------
    array-like
        The estimated viscosity following the Carreau model, with units of Pa*s.

    """

    return mu_inf + (mu_0 - mu_inf) * (1 + (lambda_ * shear_rate)**2)**((n - 1) / 2)


def rheometry_analysis(df, target_indices, calc_indices, excel_columns, **kwargs):
    """
    Fits each data entry to the Carreau model and tabulates the results.

    """

    if excel_columns is None and kwargs['processed'][0]:
        return df # to prevent processing twice

    num_columns = 5 # the number of calculation columns per entry
    for i, sample in enumerate(calc_indices):
        for j in range(len(sample) // num_columns):
            shear_index = target_indices[0][i][j]
            viscosity_index = target_indices[1][i][j]
            nan_mask = (~np.isnan(df[shear_index])) & (~np.isnan(df[viscosity_index]))

            shear_rate = df[shear_index].to_numpy()[nan_mask]
            viscosity = df[viscosity_index].to_numpy()[nan_mask]

            # mu_0, mu_inf, lambda_, n
            initial_guess = (viscosity[0], viscosity[-1], 1, 0.2)
            bounds = ((1e-10, 1e-10, 1e-5, 1e-5), (1e10, 1e10, 1e5, 5))
            params, covariance = optimize.curve_fit(
                carreau_model, shear_rate, viscosity, p0=initial_guess,
                bounds=bounds, method='trf', loss='soft_l1'
            )
            # need to catch the following errors: ValueError('x0 is infeasible')
            predicted_viscosity = carreau_model(shear_rate, *params)
            r_sq = mcetl.fitting.r_squared(viscosity, predicted_viscosity, 4)[1]

            df[sample[1 + (j * num_columns)]] = pd.Series(predicted_viscosity)
            df[sample[2 + (j * num_columns)]] = pd.Series(
                ('\u03bc_0 (Pa*s)', '\u03bc_inf (Pa*s)',
                 '\u03bb, relaxation time (s)', 'n, power law index (unitless)',
                 '', 'Fit R\u00b2')
            )
            df[sample[3 + (j * num_columns)]] = pd.Series(list(params) + ['', r_sq])
            df[sample[4 + (j * num_columns)]] = pd.Series(np.sqrt(np.diag(covariance)))

    # prevents reprocessing the data
    kwargs['processed'][0] = True if excel_columns is not None else False

    return df


if __name__ == '__main__':

    # the kwargs for some functions; make a variable so it can be shared between Function objects;
    # uses lists as the values so that they can be permanently alterred
    pore_kwargs = {'bin_size': [5], 'processed': [False]}
    tensile_kwargs = {'lower_limit': [0.0015], 'upper_limit': [0.005], 'processed': [False]}

    # Definitions for the Function objects
    offset = mcetl.CalculationFunction(
        name='offset', target_columns='y', functions=offset_data,
        added_columns=1, function_kwargs={'offset': 1000}
    )
    normalize = mcetl.CalculationFunction('normalize', 'y', normalize, 1)
    offset_normalized = mcetl.CalculationFunction(
        'offset_normalized', 'normalize', offset_normalized_data, 'normalize', {'offset': 1}
    )
    delta_x_separator = mcetl.PreprocessFunction('delta_x_sep', 'temperature', split)
    segment_separator = mcetl.PreprocessFunction('segment_sep', 'segment', split_segments,
                                                 deleted_columns=['segment'])
    derivative_calc = mcetl.CalculationFunction('derivative', ['time', 'mass'], derivative, 1)
    pore_preprocess = mcetl.PreprocessFunction('pore_preprocess', 'diameter', pore_preprocessor)
    pore_histogram = mcetl.CalculationFunction(
        'pore_hist', ['diameter', 'area'], pore_analysis, 10, pore_kwargs
    )
    pore_sample_summation = mcetl.SummaryFunction(
        'pore_sample_sum', ['diameter', 'area'], pore_sample_summary, 9, pore_kwargs
    )
    pore_dataset_summation = mcetl.SummaryFunction(
        'pore_dataset_sum', ['pore_sample_sum'], pore_dataset_summary, 5,
        pore_kwargs, False
    )
    stress_analysis = mcetl.CalculationFunction(
        'tensile_test', ['strain', 'stress'], stress_strain_analysis, 7, tensile_kwargs
    )
    stress_sample_summary = mcetl.SummaryFunction(
        'tensile_sample_summary', ['tensile_test'], tensile_sample_summary, 3, tensile_kwargs
    )
    stress_dataset_summary = mcetl.SummaryFunction(
        'tensile_dataset_summary', ['tensile_sample_summary'], tensile_dataset_summary, 9,
        tensile_kwargs, False
    )
    rheometry_calc = mcetl.CalculationFunction(
        'rheology', ['shear rate', 'viscosity'], rheometry_analysis, 5, {'processed': [False]}
    )

    # Definitions for each data source
    xrd = mcetl.DataSource(
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
        sample_separation=2,
    )

    ftir = mcetl.DataSource(
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

    raman = mcetl.DataSource(
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

    tga = mcetl.DataSource(
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

    dsc = mcetl.DataSource(
        name='DSC',
        column_labels=['Temperature (\u00B0C)', 'Time (min)', 'Heat Flow, exo up (mW/mg)'],
        functions=[segment_separator],
        column_numbers=[0, 1, 2, 3],
        start_row=34,
        end_row=0,
        separator=';',
        xy_plot_indices=[1, 2],
        file_type='txt',
        num_files=1,
        unique_variables=['segment'],
        unique_variable_indices=[3],
        entry_separation=1,
        sample_separation=2
    )

    rheometry = mcetl.DataSource(
        name='Rheometry',
        column_labels=['Shear Stress (Pa)', 'Shear Rate (1/s)', 'Viscosity (Pa*s)',
                       'Time (s)', 'Temperature (\u00B0C)', '',
                       'Carreau Model Viscosity (Pa*s)', 'Carreau Model Variable',
                       'Value', 'Standard Error'],
        functions=[rheometry_calc],
        column_numbers=[0, 1, 2, 3, 4],
        start_row=167,
        end_row=0,
        separator='\t',
        xy_plot_indices=[1, 2],
        file_type='txt',
        num_files=1,
        unique_variables=['shear rate', 'viscosity'],
        unique_variable_indices=[1, 2],
        entry_separation=1,
        sample_separation=2
    )

    tensile = mcetl.DataSource(
        name='Tensile Test',
        column_labels=['Strain (%)', 'Stress (MPa)', 'Time (s)', 'Extension (mm)', 'Load (kN)',
                       'True Strain (%)', 'True Stress (MPa)',
                       '', 'Elastic Modulus (GPa)', 'Offset Yield Stress (MPa)',
                       'Ultimate Tensile Strength (MPa)', 'Fracture Strain (%)',
                       'Property', 'Average', 'Standard Deviation',
                       'Sample', 'Elastic Modulus (GPa)', '',
                       'Offset Yield Stress (MPa)', '',
                       'Ultimate Tensile Strength (MPa)', '',
                       'Fracture Strain (%)', ''],
        functions=[stress_analysis, stress_sample_summary, stress_dataset_summary],
        column_numbers=[4, 3, 0, 1, 2],
        start_row=6,
        end_row=0,
        separator=',',
        xy_plot_indices=[0, 1],
        file_type='txt',
        num_files=3,
        unique_variables=['stress', 'strain'],
        unique_variable_indices=[1, 0],
        entry_separation=2,
        sample_separation=3
    )

    pore_size = mcetl.DataSource(
        name='Pore Size Analysis',
        column_labels=['Measured Feret Diameters (\u03bcm)', 'Measured Areas (\u03bcm\u00b2)',
                       '', 'Histogram Diameter, D (\u03bcm)',
                       'Pore Count (#)', 'Area (\u03bcm\u00b2)',
                       'Cumulative Area, A (\u03bcm\u00b2)',
                       'Pore Size Distribution, dA/dD (\u03bcm\u00b2/\u03bcm)',
                       'Normalized Cumulative Area (\u03bcm\u00b2)',
                       'Normalized PSD, dA/dD (\u03bcm\u00b2/\u03bcm)',
                       'Average Diameter (\u03bcm)', 'Diameter Standard Deviation (\u03bcm)',
                       'Summarized Histogram Diameter, D (\u03bcm)',
                       'Summarized Pore Count (#)',
                       'Summarized Area (\u03bcm\u00b2)',
                       'Summarized Cumulative Area, A (\u03bcm\u00b2)',
                       'Summarized Pore Size Distribution, dA/dD (\u03bcm\u00b2/\u03bcm)',
                       'Summarized Normalized Cumulative Area (\u03bcm\u00b2)',
                       'Summarized Normalized PSD, dA/dD (\u03bcm\u00b2/\u03bcm)',
                       'Summarized Average Diameter (\u03bcm)',
                       'Summarized Diameter Standard Deviation (\u03bcm)',
                       'Sample', 'Average Diameter, non-weighted (\u03bcm)',
                       'Diameter Standard Deviation, non-weighted (\u03bcm)',
                       'Average Diameter, area-weighted (\u03bcm)',
                       'Diameter Standard Deviation, area-weighted (\u03bcm)'],
        functions=[pore_preprocess, pore_histogram,
                   pore_sample_summation, pore_dataset_summation],
        column_numbers=[4, 1],
        start_row=1,
        end_row=0,
        separator=',',
        xy_plot_indices=[3, 7],
        file_type='csv',
        num_files=3,
        unique_variables=['diameter', 'area'],
        unique_variable_indices=[0, 1],
        entry_separation=1,
        sample_separation=2
    )

    # For use in case you need to open arbitrary files without processing
    other = mcetl.DataSource('Other')

    # Put all DataSource objects in this tuple in order to use them
    data_sources = (xrd, ftir, raman, tga, dsc, rheometry, tensile, pore_size, other)

    #set dpi awareness so GUI is not blurry on Windows os
    mcetl.set_dpi_awareness()

    # Call the launch_main_gui function with data_sources as the input
    output = mcetl.launch_main_gui(data_sources)
