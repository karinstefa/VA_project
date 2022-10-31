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

deslizamientos = gp.read_file('procesamiento/INVENTARIO_FINAL_MM.csv')
deslizamientos.columns = ['movimiento', 'fecha', 'municipio', 'latitud', 'longitud', 'fuente', 'geometry']
deslizamientos.geometry = deslizamientos.apply(lambda row: Point(float(row['longitud']), float(row['latitud'])), axis=1)
print(deslizamientos.shape)

deslizamientos = deslizamientos[['geometry', 'movimiento', 'fecha', 'fuente']]
deslizamientos.fecha = pd.to_datetime(deslizamientos.fecha, format='%d/%m/%Y')
deslizamientos.set_crs(epsg=4326, inplace=True)
print(deslizamientos.shape)

deslizamientos = deslizamientos[deslizamientos.fecha >= '2010-01-01']
print(deslizamientos.shape)
deslizamientos.head()

municipios = gp.read_file('procesamiento/MGN_ANM_MPIOS.geojson')
municipios = municipios[['DPTO_CCDGO', 'MPIO_CCDGO', 'geometry']]
print(municipios.shape)
municipios.head()

# Obtener los municipios que contienen deslizamientos
geodata = gp.sjoin(deslizamientos, municipios, how='left', predicate='intersects')
geodata = geodata[geodata['index_right'].notna()]
geodata = geodata.drop(columns=['index_right'])
print(geodata.shape)

# Exportar a GeoJSON
geodata.to_file('deslizamientos.geojson', driver='GeoJSON')
geodata.head()