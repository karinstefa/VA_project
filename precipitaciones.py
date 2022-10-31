import os
import rasterio
import pandas as pd
import geopandas as gp
from matplotlib import pyplot as plt
from functools import reduce
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point
from rasterio.features import shapes

def get_date(tiff_path):
    tiff_name = tiff_path.split('/')[-1]
    date = '-'.join(tiff_name.split('.')[:-1])
    return date

def open_tiff(src, date, mask = None):
    results = []
    for s, v in shapes(src.read(), mask=mask, transform=src.meta['transform']):
        data = {
            'properties': {date: v}, 
            'geometry': Polygon(s['coordinates'][0]).centroid
        }
        results.append(data)
    return results

def get_raster(path):
    src = rasterio.open(path)
    crs = src.read_crs()
    date = get_date(path)
    tiff = open_tiff(src, date)
    src.close()
    raster = GeoDataFrame.from_features(tiff, crs=crs)
    raster['geometry'] = raster['geometry'].to_crs(crs)
    return raster

folder = '../Datos/CHIRPS/'
rasters = []
for file in os.listdir(folder):
    if file.endswith('.tif'):
        path = os.path.join(folder, file)
        raster = get_raster(path)
        rasters.append(raster)

precipitaciones = reduce(lambda left, right: pd.merge(left, right, on='geometry', how='outer'), rasters)
print(precipitaciones.shape)
precipitaciones.fillna(0, inplace=True)
precipitaciones.head()

municipios = gp.read_file('procesamiento/MGN_ANM_MPIOS.geojson')
municipios = municipios[['DPTO_CCDGO', 'MPIO_CCDGO', 'geometry']]
print(municipios.shape)
municipios.head()

rain = gp.sjoin(precipitaciones, municipios, how='left', predicate='intersects')
rain = rain[rain['index_right'].notna()]
rain = rain.drop(columns=['index_right'])
print(rain.shape)
rain.head()	

export_rain = GeoDataFrame(rain[['geometry', 'DPTO_CCDGO', 'MPIO_CCDGO']])
# Agrupar todas las precipitaciones por fecha en un solo campo
export_rain['precipitation'] = rain.drop(columns=['geometry', 'DPTO_CCDGO', 'MPIO_CCDGO']).to_dict('records')
# Exportar a GeoJSON
export_rain.to_file('precipitaciones.geojson', driver='GeoJSON')
export_rain.head()