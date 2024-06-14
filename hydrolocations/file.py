import math, httpx, pandas

#longitude, latitude, searchradius (in km)
def convert_radius(lat, long, radius):
    """
    converts radius to give a bounding box, returned as a list of 4 floats to the nearest thousandth degree
    to be more in-depth, converts radius to latitude and longitude offsets
    based on the curvature of the earth
    """
    lat_offset = radius / 111
    long_offset = radius / (111 * math.cos(math.radians(lat)))
    print(lat_offset)
    print(long_offset)
    bBox = [long - long_offset, lat - lat_offset, long + long_offset, lat + lat_offset]
    bBox = [round(i, 3) for i in bBox]
    return [str(i) for i in bBox]
def main(lat, long, search_radius = 1, start_date = "", end_date = ""):
    """
    control function. it takes in the parameters and will call the functions
    longitude, latitude, search_radius: float
    start_date, end dates are strings: YYYY-MM-DD
    """
    bBox = convert_radius(lat, long, search_radius)
    ids = get_sites(bBox, start_date, end_date)
def check_args(longitude, latitude, search_radius, start_date, end_date):
    """
    check the validity of our arguments
    """
    if (type(longitude) != type(latitude) != type(search_radius) != float): #this code is wrong
        raise TypeError
"""
the next order of business is to make our initial call to the site service
we first need to query for a list of sites that we may pass in to daily values
"""
def get_sites(bBox, start_date, end_date):
    base_url = "https://waterservices.usgs.gov/nwis/site/"
    """
    our params are: bBox, startDt, endDt, hasDataTypecd (=dv)
    """
    #required parameters
    params = {
        "format":"rdb",
        "siteStatus":"all",
        "hasDataTypeCd":"dv"
    }
    print(bBox)
    if (start_date != ""):
        params.update({ "startDt": start_date })
        params.update( { "endDt": end_date})
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    bBox_string = "&" + "bBox=" + ",".join(bBox)
    full_url = base_url + "?" + param_string + bBox_string
    print(full_url)
    response = httpx.get(full_url)
    response.raise_for_status()
    content = response.content.decode("utf-8").split()
    ids = []
    for i in range(len(content)):
        if content[i] == "USGS":
            ids.append(content[i+1])
    return ids
main(29, -95, 200, "2024-05-28", "2024-06-14")