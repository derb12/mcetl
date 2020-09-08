# -*- coding: utf-8 -*-
"""Example script to show how to use mcetl.launch_main_gui with defined DataSource objects.

@author: Donald Erb
Created on Sat Aug 22 13:01:37 2020

"""

if __name__ == '__main__':

    import numpy as np
    from mcetl import CalculationFunction, SummaryFunction, DataSource, launch_main_gui

    def offset_func(df, target_indices, calc_indices, excel_columns=None, start_row=0, offset=None):
        """Example CalculationFunction with named kwargs"""

        for i, sample in enumerate(calc_indices):
            for j, calc_col in enumerate(sample):
                if excel_columns is not None:
                    y = df[target_indices[0][i][j]]
                    y_col = excel_columns[target_indices[0][i][j]]
                    calc = [
                        f'= {y_col}{k + 3 + start_row} + {offset}' for k in range(len(y))
                    ]

                    df[calc_col] = np.where(~np.isnan(y), calc, '')
                else:
                    y_col = df[df.columns[target_indices[0][i][j]]]
                    df[df.columns[calc_col]] = y_col + offset

            offset += offset

        return df

    def summarize(df, *args, **kwargs):
        return df
    def summarize2(df, *args, **kwargs):
        return df

    offset = CalculationFunction('offset', 'Intensity', offset_func, 1, {'offset': 1000})
    summary = SummaryFunction('summarize', 'Intensity', summarize, 1, None, False)
    summary2 = SummaryFunction('summarize2', 'Intensity', summarize2, 1, None, True) 
   
    # Definitions for each data source
    xrd = DataSource(
        name='XRD',
        column_labels=['2\u03B8 (\u00B0)', 'Intensity (Counts)', 'Offset Intensity (a.u.)'],
        functions=[offset, summary, summary2], column_numbers=[1, 2],
        start_row=1, end_row=0, separator=',',
        xy_plot_indices=[0, 2], file_type='csv', num_files=1,
        unique_variables=['2\u03B8', 'Intensity']
    )

    """
    ftir = DataSource('FTIR', ['Wavenumber (1/cm)','Absorbance (a.u.)',
                                     'Offset Absorbance (a.u.)'],
                                     ['offset', 'normalize', 'fit_peaks'], [0, 1],
                                     1, 0, 0, ',', [0, 1], [0, 2], 'csv')
    raman = DataSource('Raman', ['Raman Shift (1/cm)','Intensity (a.u.)',
                                      'Offset Intensity (a.u.)'],
                                      ['offset', 'normalize', 'fit_peaks'], [0, 1],
                                      1, 0, 0, '\\t', [0, 1], [0, 2], 'txt')
    tga = DataSource('TGA', ['Temperature (\u00B0C)', 'Time (min)',
                                    'Mass (%)', 'Mass Loss Rate (%/\u00B0C)',
                                    'Fraction Mass Lost'],
                                    ['negative_derivative', 'max_x', 'fit_peaks',
                                     'fractional_change'],
                                    [0, 1, 2], None, 34, 0, ';', [0, 2], [0, 2], 'txt')
    """

    other = DataSource('Other')

    #Put all DataSource objects in this tuple in order to use them
    data_sources = (xrd, other)

    #call the main function with data_sources as the input
    dataframes, fit_results, plot_results = launch_main_gui(data_sources)
