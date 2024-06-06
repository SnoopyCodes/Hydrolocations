import httpx

"""
@TODO
implement the function to accept input latitude, longitude, searchRadius

Approach: approximate search radius as bounding box
problems: the earth is round
"""
def query(*urls):
    url = ""
    for item in urls:
        url += item
    response = httpx.get(url)
    print(url)
    return response.content
#Houston
latitude = 29.7604
longitude = -95.3698
searchRadius = 2

#what format are the dates in?
#put them in yyyy-mm-dd

url = "https://waterservices.usgs.gov/nwis/"
service = "site/"
#arguments
format = "?format=rdb"
boundingBox = "&bBox="+ str(longitude - searchRadius) + ","+ str(latitude - searchRadius) + ","+ str(longitude + searchRadius) + ","+ str(latitude + searchRadius)
#figure out a format for the dates
startDate = "&startDT=2024-05-28"
endDate = "&endDT=2024-06-06"
status = "&siteStatus=all"
datatype = "&hasDataTypeCd=dv"
data = query(url, service, format, boundingBox, startDate, endDate, status, datatype).decode("utf-8")
print(data)