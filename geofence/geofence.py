import shapely.speedups
from shapely.geometry import Point
import geopandas as gpd
import matplotlib.pyplot as plt

def geofence_find(polys, nums, data):
    for i in range(nums):
        if(polys.loc[i, 'geometry'].contains(data)):
            poly_name = polys.loc[i, 'Name']
            return poly_name
    return False

def allocation(lat,lng):
    gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw' # Enables respective driver to read KML file
    fp = "geofence/Base.kml" # Retrieve KML file
    polys = gpd.read_file(fp, driver='KML') # Converts KML file into a dataframe
    shapely.speedups.enable() # Faster spatial queries
    data = Point(lng, lat)
    num_polys = len(polys)
    res = geofence_find(polys, num_polys, data)
    if not res:
        return "0"
    else:
        return res

    # fig, ax = plt.subplots()
    # polys.plot(ax=ax, facecolor='gray')
    # plt.plot(lat,lng,'ro')
    # plt.tight_layout()
    # plt.show()

