from Precipitation import Precipitation

# Uso de clase
p = Precipitation('../Datos/CHIRPS/')

# Calcular y obtener data
export_rain = p.run()

# Exportar a GeoJSON
p.export_rain()

from Slidding import Slidding

# Uso de clase
s = Slidding('../Datos/CHIRPS/')
# Calcular y obtener data
deslizamientos = s.run()

# Exportar a GeoJSON
s.export_to_geoJson()
