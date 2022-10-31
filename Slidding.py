import os
import rasterio
import pandas as pd
import geopandas as gp
from matplotlib import pyplot as plt
from functools import reduce
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point
from rasterio.features import shapes

class Slidding:

	export_rain = pd.DataFrame()
	deslizamientos = pd.DataFrame()	
	municipios = pd.DataFrame()
	folder = '../Datos/CHIRPS/'
	rasters = []

	def __init__(self, folder =  '../Datos/CHIRPS/') -> None:
		self.folder = folder

	def get_date(self, tiff_path):
		tiff_name = tiff_path.split('/')[-1]
		date = '-'.join(tiff_name.split('.')[:-1])
		return date

	def open_tiff(self, src, date, mask = None):
		results = []
		for s, v in shapes(src.read(), mask=mask, transform=src.meta['transform']):
			data = {
				'properties': {date: v}, 
				'geometry': Polygon(s['coordinates'][0]).centroid
			}
			results.append(data)
		return results

	def get_raster(self, path):
		src = rasterio.open(path)
		crs = src.read_crs()
		date = self.get_date(path)
		tiff = self.open_tiff(src, date)
		src.close()
		raster = GeoDataFrame.from_features(tiff, crs=crs)
		raster['geometry'] = raster['geometry'].to_crs(crs)
		return raster

	def get_rasters(self):
		for file in os.listdir(self.folder):
			if file.endswith('.tif'):
				path = os.path.join(self.folder, file)
				raster = self.get_raster(path)
				self.rasters.append(raster)
		return self.rasters

	

	def run(self):
		self.get_rasters()
		self.get_municipios()
		
		self.deslizamientos = gp.read_file('INVENTARIO_FINAL_MM.csv')
		self.deslizamientos.columns = ['movimiento', 'fecha', 'municipio', 'latitud', 'longitud', 'fuente', 'geometry']
		self.deslizamientos.geometry = self.deslizamientos.apply(lambda row: Point(float(row['longitud']), float(row['latitud'])), axis=1)
		# print(deslizamientos.shape)

		self.deslizamientos = self.deslizamientos[['geometry', 'movimiento', 'fecha', 'fuente']]
		self.deslizamientos.fecha = pd.to_datetime(self.deslizamientos.fecha, format='%d/%m/%Y')
		self.deslizamientos.set_crs(epsg=4326, inplace=True)
		# print(deslizamientos.shape)

		self.deslizamientos = self.deslizamientos[self.deslizamientos.fecha >= '2010-01-01']
		# print(deslizamientos.shape)
		# deslizamientos.head()

		return self.deslizamientos

	def export_to_geoJson(self):
		# Obtener los municipios que contienen deslizamientos
		geodata = gp.sjoin(self.deslizamientos, municipios, how='left', predicate='intersects')
		geodata = geodata[geodata['index_right'].notna()]
		geodata = geodata.drop(columns=['index_right'])
		# print(geodata.shape)
		# Exportar a GeoJSON
		geodata.to_file('deslizamientos.geojson', driver='GeoJSON')
		# geodata.head()