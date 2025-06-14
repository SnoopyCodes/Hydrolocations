from pygeoogc import ArcGISRESTful, WFS, WMS, ServiceURL
import pygeoutils as geoutils
from pynhd import NLDI

basin_geom = NLDI().get_basins("01031500").geometry[0]

hr = ArcGISRESTful(ServiceURL().restful.nhdplushr, 2, outformat="json")

oids = hr.oids_bygeom(basin_geom, geo_crs=4326, sql_clause="AREASQKM > 0.5")
resp = hr.get_features(oids)
catchments = geoutils.json2geodf(resp)