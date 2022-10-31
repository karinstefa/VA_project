import os
import rasterio
import pandas as pd
import geopandas as gp
from matplotlib import pyplot as plt
from functools import reduce
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point
from rasterio.features import shapes

class Precipitation:

	export_rain = pd.DataFrame()
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

	def get_municipios(self):
		self.municipios = gp.read_file('procesamiento/MGN_ANM_MPIOS.geojson')
		self.municipios = self.municipios[['DPTO_CCDGO', 'MPIO_CCDGO', 'geometry']]
		return self.municipios

	
	def run(self):
		self.get_rasters()
		self.get_municipios()

		precipitaciones = reduce(lambda left, right: pd.merge(left, right, on='geometry', how='outer'), self.rasters)
		print(precipitaciones.shape)
		precipitaciones.fillna(0, inplace=True)
		precipitaciones.head()


		rain = gp.sjoin(precipitaciones, self.municipios, how='left', predicate='intersects')
		rain = rain[rain['index_right'].notna()]
		rain = rain.drop(columns=['index_right'])
		print(rain.shape)
		rain.head()	

		self.export_rain = GeoDataFrame(rain[['geometry', 'DPTO_CCDGO', 'MPIO_CCDGO']])
		# Agrupar todas las precipitaciones por fecha en un solo campo
		self.export_rain['precipitation'] = rain.drop(columns=['geometry', 'DPTO_CCDGO', 'MPIO_CCDGO']).to_dict('records')
		return self.export_rain


	def export_to_geoJson(self):
		self.export_rain.to_file('precipitaciones.geojson', driver='GeoJSON')
		