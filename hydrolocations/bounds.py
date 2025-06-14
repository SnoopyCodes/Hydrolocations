import shapely, geopandas, pyproj, streamflow_query
import matplotlib.pyplot as plt
from pygeohydro import NWIS

rad = 200 #km
lat = 29.5984
long = -95.6226
bBox = streamflow_query._convert_radius(lat, long, rad)
nwis = NWIS()
date1 = "2024-05-28"
date2 = "2024-06-01"
params = {
    "startDt": date1,
    "endDt": date2,
    "format":"rdb",
    "siteStatus":"all",
    "hasDataTypeCd":"dv",
    "parameterCd": "00060",
    "bBox": ",".join(bBox)
}
gdf = nwis.get_info(params, fix_names=True) #geodataframe
my_gdf = streamflow_query.get_sites(
    streamflow_query._convert_radius(lat, long, rad),
    date1,
    date2
)
my_gdf = streamflow_query.filter_sites(lat, long, rad, my_gdf)
to_meters = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)
to_long_lat = pyproj.Transformer.from_crs("EPSG:5070", "EPSG:4326", always_xy=True)
x, y = to_meters.transform(long, lat)
center = shapely.geometry.Point(x, y)
circle = center.buffer(rad * 1000)
circle_gdf = geopandas.GeoDataFrame([{"geometry":circle}], crs="EPSG:5070")
circle_gdf = circle_gdf.to_crs(gdf.crs)
print(gdf)
print(my_gdf)
ax = gdf.plot(color='blue', marker='o', markersize=40, label='nwis')
erm = my_gdf.plot(ax=ax, color='yellow', marker='x', markersize = 30, label='Mine')
circle_gdf.boundary.plot(ax=ax, edgecolor='red', linewidth=2, label='Circle')

# Add a legend and show the plot
ax.legend()
plt.show()