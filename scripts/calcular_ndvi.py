import rasterio
from rasterio.transform import from_origin
import numpy as np
import os

def crear_dummy_geotiff(ruta_archivo, ancho=100, alto=100, num_bandas=1, dtype='uint16', crs_epsg=32719, resolucion=10):
    """Crea un GeoTIFF dummy con valores aleatorios si no existe."""
    if not os.path.exists(ruta_archivo):
        print(f"Creando GeoTIFF dummy en: {ruta_archivo}")
        transform = from_origin(-70, -33, resolucion, resolucion) # Origen y resolución de ejemplo
        profile = {
            'driver': 'GTiff',
            'dtype': dtype,
            'nodata': None,
            'width': ancho,
            'height': alto,
            'count': num_bandas,
            'crs': rasterio.crs.CRS.from_epsg(crs_epsg),
            'transform': transform,
            'compress': 'lzw'
        }
        # Generar datos aleatorios apropiados para bandas satelitales (reflectancia)
        if dtype == 'uint16':
            array_datos = np.random.randint(100, 3000, (num_bandas, alto, ancho)).astype(dtype)
        else: # float32 para NDVI
            array_datos = (np.random.rand(num_bandas, alto, ancho) * 2 - 1).astype(dtype) # Rango -1 a 1

        with rasterio.open(ruta_archivo, 'w', **profile) as dst:
            if num_bandas == 1:
                dst.write(array_datos, 1)
            else:
                for i in range(num_bandas):
                    dst.write(array_datos[i], i + 1)
        print(f"GeoTIFF dummy creado: {ruta_archivo}")

def calcular_ndvi(ruta_banda_roja, ruta_banda_nir, ruta_salida_ndvi):
    try:
        with rasterio.open(ruta_banda_roja) as src_red:
            red = src_red.read(1).astype('float32') / 10000.0 # Escalar a reflectancia (0-1)
            profile = src_red.profile
            profile.update(dtype=rasterio.float32, count=1, compress='lzw', nodata=-9999.0)

        with rasterio.open(ruta_banda_nir) as src_nir:
            nir = src_nir.read(1).astype('float32') / 10000.0 # Escalar a reflectancia (0-1)

        np.seterr(divide='ignore', invalid='ignore')
        ndvi_numerator = nir - red
        ndvi_denominator = nir + red
        ndvi = np.full_like(red, profile['nodata'], dtype='float32')
        
        valid_pixels = ndvi_denominator!= 0
        ndvi[valid_pixels] = ndvi_numerator[valid_pixels] / ndvi_denominator[valid_pixels]
        ndvi = np.clip(ndvi, -1, 1)
        ndvi[~valid_pixels] = profile['nodata']

        with rasterio.open(ruta_salida_ndvi, 'w', **profile) as dst:
            dst.write(ndvi.astype(rasterio.float32), 1)
        print(f"NDVI calculado y guardado en: {ruta_salida_ndvi}")

    except FileNotFoundError:
        print(f"Error: No se encontró uno o ambos archivos de banda: {ruta_banda_roja}, {ruta_banda_nir}")
    except Exception as e:
        print(f"Ocurrió un error al calcular el NDVI: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Rutas para los dummies de entrada y la salida del NDVI
    dummy_satellite_dir = os.path.join(base_dir, '..', 'data', 'satellite_raw_dummy')
    results_ndvi_dir = os.path.join(base_dir, '..', 'results', 'ndvi_maps')
    
    os.makedirs(dummy_satellite_dir, exist_ok=True)
    os.makedirs(results_ndvi_dir, exist_ok=True)

    # Crear dummies para bandas si no existen (simulando imágenes mensuales)
    fechas_simuladas = [
        "20230915", "20231015", "20231115", "20231215",
        "20240115", "20240215", "20240315", "20240415"
    ]

    for fecha_str in fechas_simuladas:
        ruta_b4_dummy = os.path.join(dummy_satellite_dir, f'S2_dummy_{fecha_str}_B04.tif')
        ruta_b8_dummy = os.path.join(dummy_satellite_dir, f'S2_dummy_{fecha_str}_B08.tif')
        ruta_ndvi_salida = os.path.join(results_ndvi_dir, f'NDVI_dummy_{fecha_str}.tif')

        crear_dummy_geotiff(ruta_b4_dummy, dtype='uint16') # Simula DN de Sentinel-2
        crear_dummy_geotiff(ruta_b8_dummy, dtype='uint16') # Simula DN de Sentinel-2
        
        print(f"\nProcesando para fecha: {fecha_str}")
        calcular_ndvi(ruta_b4_dummy, ruta_b8_dummy, ruta_ndvi_salida)
