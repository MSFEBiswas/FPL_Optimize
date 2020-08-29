# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 19:51:55 2020

@author: noahk
"""
import lib.FPL as fpl

if __name__ == "__main__":
    fpl_data, stats_data = fpl.api_init()
    all_data = fpl.program_init()