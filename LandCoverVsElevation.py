import sys, os
sysPath = os.path.join('C:\\', 'Users', 'hans-', \
'Documents', 'Master', '2.Semester', 'PythonInGIS', '6thPointAssignment', 'Scripts')
sys.path.append(sysPath)
from matplotlib import pyplot as plt
import ogr
import osr
import gdal
import numpy as np
import GPXtoSHP
import ReprojectingandDEMClipping
import ReprojectandLandCoverClipping

# the gpx file to analyze (please provide your path)
in_gpx = os.path.join('C:\\', 'Users', 'hans-', \
'Documents', 'Master', '2.Semester', 'PythonInGIS', '6thPointAssignment', 'test', 'Shg-ruhr-2018-08Rhein-runde.gpx')

GPXtoSHP.convertGPXtoSHP(in_gpx, sysPath)

# the DEM to get the correct elevation (please provide path)
in_dem = os.path.join('C:\\', 'Users', 'hans-', \
'Documents', 'Master', '2.Semester', 'PythonInGIS', 'GermanyDGM1', 'GermanyDGM1', 'dgm1_5meter.img')

# the input shapefile for the elevation computation
in_shp = os.path.join(os.path.dirname(sysPath), os.path.basename(sysPath), 'output', 'track_points.shp')

# the output shapefile with the correct elevation
out_shapefile = os.path.join(os.path.dirname(sysPath), os.path.basename(sysPath), 'output', 'reprojected_with_dem.shp')

ReprojectingandDEMClipping.reprojectandGetElevFromDEM(in_dem, in_shp, out_shapefile)

# the copernicus land cover raster (please provide path)
in_land_cover = os.path.join('C:\\', 'Users', 'hans-', \
'Documents', 'Master', '2.Semester', 'PythonInGIS', '6thPointAssignment', 'Code', 'g100_clc12_V18_5.tif')

# Path to output shapefile (reprojected)
out_shapefile2 = os.path.join(os.path.dirname(sysPath), os.path.basename(sysPath),'output', 'reprojected_with_lc_and_diff.shp')

ReprojectandLandCoverClipping.reprojectandGetLandCoverType(in_land_cover, out_shapefile, out_shapefile2)

#create a dictionary for the land cover classes and the differences
land_cover_elevation_differences = {}
driver = ogr.GetDriverByName('ESRI Shapefile')
new_layer = driver.Open(out_shapefile2, 0)
prepared_layer = new_layer.GetLayer(0)
for feat in prepared_layer:
    lc = feat.GetField('land_cover')
    elevdiff = feat.GetField('elev_diff')
    land_cover_elevation_differences.setdefault(lc, []).append(elevdiff)

shortLCTypes = []
for key in land_cover_elevation_differences:
    if len(land_cover_elevation_differences[key]) <= 4:
        shortLCTypes.append(key)
      
for type in shortLCTypes:
    del land_cover_elevation_differences[type]        

#compute averages for the land cover types
land_cover_averages = {}
averageList = []
for key in land_cover_elevation_differences:
    floatList = list(map(float, land_cover_elevation_differences[key]))
    sumKeys = sum(floatList)
    stdKeys = np.std(floatList)
    minKeys = np.amin(floatList)
    maxKeys = np.amax(floatList)
    averageKeys = sumKeys/len(land_cover_elevation_differences[key])
    averageList.append((key, averageKeys))
    land_cover_averages.setdefault(key, []).append({'mean': averageKeys,'standard_deviation': stdKeys, 'min': minKeys, 'max': maxKeys})
print(land_cover_averages)
maxMean = max(averageList,key=lambda item:item[1])
minMean = min(averageList,key=lambda item:item[1])
print(maxMean)
print(minMean)

#create the boxplots
fig = plt.figure(1, figsize=(9, 6))
ax = fig.add_subplot(111)
ax.set_ylim(0,25)
ax.set_title('Boxplot of maximum elevation difference, land cover class ' + maxMean[0])
maxFloat = list(map(float, land_cover_elevation_differences[maxMean[0]]))
bp = ax.boxplot(maxFloat)
savePath = os.path.join(os.path.dirname(sysPath), os.path.basename(sysPath),'plots')
fig.savefig(os.path.join(savePath, 'maxMeanPlot.png'), bbox_inches='tight')

fig2 = plt.figure(2, figsize=(9, 6))
ax2 = fig2.add_subplot(111)
ax2.set_ylim(0,25)
ax2.set_title('Boxplot of minimum elevation difference, land cover class ' + minMean[0])
minFloat = list(map(float, land_cover_elevation_differences[minMean[0]]))
bp2 = ax2.boxplot(minFloat)
fig2.savefig(os.path.join(savePath, 'minMeanPlot.png'), bbox_inches='tight')
