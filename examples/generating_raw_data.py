# -*- coding: utf-8 -*-
"""This is an example program to show how to generate example raw data using mcetl.



@author: Donald Erb
Created on Sat Aug 22 13:49:50 2020

"""

import matplotlib.pyplot as plt
from mcetl import raw_data

raw_data.generate_raw_data()

while plt.get_fignums():
    plt.pause(5) # ensures the program continues while the plots are open
    #TODO use some other waiting method, because it is quite buggy using plt.pause
