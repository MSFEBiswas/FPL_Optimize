# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 17:24:46 2020

@author: Ankan Biswas
"""
import lib.FPL as fpl

if __name__ == "__main__":
    fpl_data, stats_data = fpl.api_init()
    all_data = fpl.program_init()