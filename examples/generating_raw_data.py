# -*- coding: utf-8 -*-
"""This is an example program to show how to generate example raw data using mcetl.

@author: Donald Erb
Created on Aug 22, 2020

"""

import matplotlib.pyplot as plt
from mcetl import raw_data, set_dpi_awareness

#set dpi awareness so GUI is not blurry on Windows os
set_dpi_awareness()

raw_data.generate_raw_data()

# Ensures program will not end until all plots are closed
if plt.get_fignums():
    plt.show(block=True)
