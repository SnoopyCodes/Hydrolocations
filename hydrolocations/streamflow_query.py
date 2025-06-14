import httpx
import json
import pandas as pd
import numpy as np
import shapely
import geopandas as gpd
import pyproj

def _convert_radius(lat, long, radius):
    """
    converts radius to give a bounding box, returned as a list of 4 string-formatted floats
    to be more in-depth, converts radius to latitude and longitude offsets
    based on the curvature of the earth
    """

    to_meters = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)
    to_long_lat = pyproj.Transformer.from_crs("EPSG:5070", "EPSG:4326", always_xy=True)

    radius *= 1000
    x, y = to_meters.transform(long, lat)

    center = shapely.geometry.Point(x, y)
    circle = center.buffer(radius)
    b1_x, b1_y = to_long_lat.transform(circle.bounds[0], circle.bounds[1])
    b2_x, b2_y = to_long_lat.transform(circle.bounds[2], circle.bounds[3])

    bbox = [b1_x, b1_y, b2_x, b2_y]

    return [str(round(f, 5)) for f in bbox]

def main(lat, long, search_radius, start_date = "", end_date = ""):
    """
    takes in the parameters and will call the functions
    longitude, latitude, search_radius: float
    start_date, end dates are strings: YYYY-MM-DD
    """
    bBox = _convert_radius(lat, long, search_radius)
    check_args(bBox, start_date, end_date)
    sites_gdf = get_sites(bBox, start_date, end_date)
    sites_gdf = filter_sites(lat, long, search_radius, sites_gdf)
    ids = sites_gdf["site_no"]

    content = get_daily_values(ids, start_date, end_date)
    df = json_to_df(content)
    return df

def check_args(bBox, start_date, end_date):
    """
    check the validity of our arguments
    @TODO
    write own error statements?
    in any case we should be raising some kind of format exception
    we can probably import the 
    """
    bBox = [float(i) for i in bBox]
    if bBox[0] > 180 or bBox[0] < -180:
        raise ValueError
    if bBox[1] > 90 or bBox[1] < -90:
        raise ValueError
    if bBox[2] > 180 or bBox[2] < -180:
        raise ValueError
    if bBox[3] > 90 or bBox[3] < -90:
        raise ValueError
    
    if bBox[0] > bBox[2]:
        raise ValueError
    if bBox[1] > bBox[3]:
        raise ValueError

    if type(start_date) != type(end_date) != str:
        raise TypeError


    if len(start_date) != len(end_date) and (len(start_date) == 0 or len(start_date) == 10):
        raise ValueError
    # pygeoogc uses strftime for this, or something
    if len(start_date) == 10:
        for i in range(10):
            if i == 4 or i == 7:
                if not (start_date[i] == '-' and end_date[i] == start_date[i]):
                    raise ValueError
            else:
                if not start_date[i].isdigit() or not end_date[i].isdigit():
                    raise ValueError

def get_sites(bBox, start_date, end_date):
    base_url = "https://waterservices.usgs.gov/nwis/site/"
    """
    get the sites needed inside of our
    our params are: bBox, startDt, endDt, hasDataTypecd (=dv), and parameterCd
    """
    params = {
        "format":"rdb",
        "siteStatus":"all",
        "hasDataTypeCd":"dv",
        "parameterCd": "00060",
        "bBox": ",".join(bBox)
    }
    if (start_date != ""):
        params.update({ "startDt": start_date })
        params.update( { "endDt": end_date })
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = base_url + "?" + param_string
    response = httpx.get(full_url)
    response.raise_for_status()
    content = response.content.decode("utf-8")
    """
    the next thing we need to do is turn this into a dataframe
    and then a geodataframe
    this thing is tab split
    so we can split by \t
    first filter out all lines that are split
    """
    
    entries = [x.split("\t") for x in content.splitlines() if not (x.startswith("#") or x.startswith("5s"))]
    df = pd.DataFrame(entries[1:])
    df.columns = entries[0]
    """
    now we want to convert the date time correctly
    """
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["dec_long_va"], df["dec_lat_va"]),
        crs = 4326
    )
    return gdf

def filter_sites(lat, long, radius, gdf):
    gdf = gpd.GeoDataFrame(gdf)
    gdf = gdf.to_crs("EPSG:5070")
    to_meters = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)

    radius *= 1000
    x, y = to_meters.transform(long, lat)

    center = shapely.geometry.Point(x, y)
    circle = center.buffer(radius)
    circle_gdf = gpd.GeoDataFrame([{"geometry": circle}], crs = "EPSG:5070")
    
    gdf = gdf[gdf.within(circle_gdf.at[0, "geometry"])]
    gdf = gdf.to_crs("EPSG:4326")
    return gdf
    
def json_to_df(content):
    """
    takes a dict with all the information and converts it
    """
    
    def get_id(site_Code):
        #USGS may be guaranteed as the agency
        return site_Code["agencyCode"] + "-" + site_Code["value"]
    
    useful_info = {
        get_id(r["sourceInfo"]["siteCode"][0]) : r["values"][0]["value"]
        for r in content["value"]["timeSeries"]
    }

    def entry_to_df(col, vals):
        try:
            df = pd.DataFrame.from_records(vals, exclude = ["qualifiers"], index = ["dateTime"])
        except:
            return pd.DataFrame()
        df["value"] = pd.to_numeric(df["value"])
        tz = content["value"]["timeSeries"][0]["sourceInfo"]["timeZoneInfo"]
        time_zone = {
            "CST": "US/Central",
            "MST": "US/Mountain",
            "PST": "US/Pacific",
            "EST": "US/Eastern",
        }.get(
            tz["defaultTimeZone"]["zoneAbbreviation"],
            tz["defaultTimeZone"]["zoneAbbreviation"],
        )
        df.index = pd.to_datetime(df.index).tz_localize(time_zone).tz_convert("UTC")
        df.columns = [col]
        return df
    # format is in rows = dates, columns = sites, so we need to append by columns
    df = pd.concat([entry_to_df(k, v) for k, v in useful_info.items()], axis = 1)

    df[df.le(0)] = np.nan

    return df * np.float_power(0.3048, 3)

def get_daily_values(ids, start_date, end_date):
    base_url = "https://waterservices.usgs.gov/nwis/dv/"
    """
    return a dict containing information from daily values service
    """
    params = {
        "format":"json",
        "siteStatus":"all",
        "parameterCd":"00060",
        "statCd":"00003"
    }
    if (start_date != ""):
        params.update({ "startDt": start_date })
        params.update( { "endDt": end_date})
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    ids_string = "&" + "sites=" + ",".join(ids)
    full_url = base_url + "?" + param_string + ids_string
    response = httpx.get(full_url)
    response.raise_for_status()
    content = response.content.decode("utf-8")
    content = json.loads(content)
    return content

if __name__ == "__main__":
    date1 = "2024-05-28"
    date2 = "2024-06-01"
    rad = 80
    lat = 29
    long = -95
    print(main(lat, long, rad, date1, date2))