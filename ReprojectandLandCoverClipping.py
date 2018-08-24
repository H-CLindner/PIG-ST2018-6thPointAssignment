from matplotlib import pyplot as plt
import ogr
import os
import osr
import gdal
from qgis.utils import iface
from qgis.core import QgsVectorDataProvider, QgsField, QgsProject
from PyQt5.QtCore import QVariant

def reprojectandGetLandCoverType(rasterPath, shpPath, shpOutput):
    #opening the land cover raster
    rast_data_source = gdal.Open(rasterPath)
    src_band = rast_data_source.GetRasterBand(1)
    gt = rast_data_source.GetGeoTransform()
    cols = rast_data_source.RasterXSize
    rows = rast_data_source.RasterYSize

    #do the reprojection of the shapefile to the reference system of the raster
    rast_spatial_ref = rast_data_source.GetProjection()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    vect_data_source = driver.Open(shpPath, 0)
    layer = vect_data_source.GetLayer(0)
    vect_spatial_ref = layer.GetSpatialRef()
    sr = osr.SpatialReference(rast_spatial_ref)
    transform = osr.CoordinateTransformation(vect_spatial_ref, sr)
    if os.path.exists(shpOutput):
        print('exists, deleting')
        driver.DeleteDataSource(shpOutput)
    out_ds = driver.CreateDataSource(shpOutput)
    if out_ds is None:
        print('Could not create %s' % (shpOutput))

    out_lyr = out_ds.CreateLayer('track_points', sr, ogr.wkbPoint)
    out_lyr.CreateFields(layer.schema)
    out_defn = out_lyr.GetLayerDefn()
    out_feat = ogr.Feature(out_defn)
    # Loop over all features and change their spatial ref
    for in_feat in layer:
        geom = in_feat.geometry()
        geom.Transform(transform)
        out_feat.SetGeometry(geom)
        # Make sure to also include the attributes in the new file
        for i in range(in_feat.GetFieldCount()):
            value = in_feat.GetField(i)
            out_feat.SetField(i, value)
        out_lyr.CreateFeature(out_feat)

    land_cover_types = []
    elevDifference = []
    #get the land cover type for every point in the shapefile
    for feat in out_lyr:
        geom = feat.GetGeometryRef()
        mx = geom.GetX()
        my = geom.GetY()
        px = int((mx - gt[0]) / gt[1]) #x pixel
        py = int((my - gt[3]) / gt[5]) #y pixel
        intval=src_band.ReadAsArray(px, py,1,1)
        elevDiff = feat['ele'] - float(feat['dem_elev'])
        elevDiff2 = abs(elevDiff)
        elevDifference.append(elevDiff2)
        land_cover_types.append(intval[0][0])
        
    del out_ds
    
    # load the shapefile
    shape_layer = iface.addVectorLayer(shpOutput, "shape:", "ogr")
    if not shape_layer:
        print("Shapefile failed to load!")
    else: print("Shapefile loaded!")
        
    caps = shape_layer.dataProvider().capabilities()
    if caps & QgsVectorDataProvider.AddAttributes:
        # We require a String field
        res = shape_layer.dataProvider().addAttributes(
            [QgsField("land_cover", QVariant.String),QgsField("elev_diff", QVariant.String)])
            
    shape_layer.updateFields()
    field_name_i_search = 'land_cover'
    index = 0
    for field in shape_layer.fields():
        if field.name() == field_name_i_search:
            break
        index += 1

    updates = {}
    for feat in shape_layer.getFeatures():
        # Update the empty field in the shapefile
        updates[feat.id()] = {index: str(land_cover_types[feat.id()])}

    # Use the created dictionary to update the field for all features
    shape_layer.dataProvider().changeAttributeValues(updates)
    # Update to propagate the changes
    shape_layer.updateFields()

    field_name_i_search2 = 'elev_diff'
    index2 = 0
    for field in shape_layer.fields():
        if field.name() == field_name_i_search2:
            break
        index2 += 1

    updates2 = {}
    for feat in shape_layer.getFeatures():
        # Update the empty field in the shapefile
        updates2[feat.id()] = {index2: str(elevDifference[feat.id()])}

    # Use the created dictionary to update the field for all features
    shape_layer.dataProvider().changeAttributeValues(updates2)
    # Update to propagate the changes
    shape_layer.updateFields()
    #optional for removing the shapefile after laoding it in
    QgsProject.instance().removeMapLayer(shape_layer.id())