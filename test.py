#%%
from Precipitation import *
#%% Uso de clase
p = Precipitation('Datos/CHIRPS/')
#%%
# Calcular y obtener data, y exportar a GeoJSON
export_rain = p.run()

#%% ------------------------------------------------------------
from Slidding import Slidding

#%%
# Uso de clase
s = Slidding('Datos/CHIRPS/')

#%%
# Calcular y obtener data
deslizamientos = s.run()
#%%
# Exportar a GeoJSON
s.export_to_geoJson()

# %%
