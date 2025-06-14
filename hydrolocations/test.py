import pandas as pd
import numpy as np
import pygeohydro as pgh
import streamflow_query
import json
nwis = pgh.NWIS()
date1 = "2024-05-28"
date2 = "2024-06-01"
lat = 29
long = -95
rad = 200
# df = nwis.get_streamflow(ids, (date1, date2))
print()
res = streamflow_query.main(lat, long, rad, date1, date2)
# res is supposed to be a dict[string, any]
print(res.head())
# print(df.head())
# print(df.head(30))
# print(type(df))
# print(df.loc[df.index[0]])