import pandas as pd
import rasterio
import numpy as np
import os
from datetime import datetime, timedelta

def calcular_kc_desde_ndvi(ndvi_array, nodata_ndvi=-9999.0):
    kc_array = 1.4 * ndvi_array - 0.1
    kc_array = np.clip(kc_array, 0.15, 1.15)
    kc_array[ndvi_array == nodata_ndvi] = nodata_ndvi
    return kc_array

def calcular_etc_mapa(ruta_ndvi_tif, et0_valor_diario, ruta_salida_etc_tif, nodata_val=-9999.0):
    try:
        with rasterio.open(ruta_ndvi_tif) as src_ndvi:
            ndvi_map = src_ndvi.read(1).astype('float32')
            profile_ndvi = src_ndvi.profile
            nodata_ndvi_original = src_ndvi.nodata if src_ndvi.nodata is not None else nodata_val

        ndvi_map_proc = np.where(ndvi_map == nodata_ndvi_original, nodata_val, ndvi_map)
        kc_map = calcular_kc_desde_ndvi(ndvi_map_proc, nodata_val)
        
        etc_map = kc_map * et0_valor_diario
        etc_map[kc_map == nodata_val] = nodata_val

        profile_etc = profile_ndvi.copy()
        profile_etc.update(dtype='float32', nodata=nodata_val, compress='lzw')

        with rasterio.open(ruta_salida_etc_tif, 'w', **profile_etc) as dst:
            dst.write(etc_map.astype(rasterio.float32), 1)
        print(f"Mapa ETc guardado en: {ruta_salida_etc_tif}")
        return etc_map # Devuelve el mapa para posible análisis
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo NDVI: {ruta_ndvi_tif}")
    except Exception as e:
        print(f"Ocurrió un error al calcular el mapa de ETc: {e}")
    return None

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    et0_csv_path = os.path.join(base_dir, '..', 'results', 'et0_calculada', 'datos_meteorologicos_con_et0.csv')
    ndvi_maps_dir = os.path.join(base_dir, '..', 'results', 'ndvi_maps')
    etc_maps_dir = os.path.join(base_dir, '..', 'results', 'etc_maps')
    
    os.makedirs(etc_maps_dir, exist_ok=True)

    try:
        df_et0 = pd.read_csv(et0_csv_path)
        df_et0['fecha'] = pd.to_datetime(df_et0['fecha'])
        print(f"Datos de ET0 cargados desde: {et0_csv_path}")
    except FileNotFoundError:
        print(f"Error: Archivo ET0 '{et0_csv_path}' no encontrado. Ejecuta primero 'calcular_et0.py'.")
        exit()
    except Exception as e:
        print(f"Error cargando ET0: {e}")
        exit()

    # Fechas para las que se generaron NDVI dummies
    fechas_imagenes_ndvi = [
        "20230915", "20231015", "20231115", "20231215",
        "20240115", "20240215", "20240315", "20240415"
    ]
    
    # Simular ETc para cada día de la temporada usando Kc interpolado
    start_date = datetime(2023, 9, 1)
    end_date = datetime(2024, 4, 30)
    current_date = start_date

    # Cargar todos los NDVI y sus fechas
    ndvis_disponibles = {}
    for fecha_str_ndvi in fechas_imagenes_ndvi:
        ruta_ndvi = os.path.join(ndvi_maps_dir, f'NDVI_dummy_{fecha_str_ndvi}.tif')
        if os.path.exists(ruta_ndvi):
            ndvis_disponibles[datetime.strptime(fecha_str_ndvi, '%Y%m%d')] = ruta_ndvi
        else:
            print(f"Advertencia: Archivo NDVI no encontrado para {fecha_str_ndvi}, se omitirá.")

    if not ndvis_disponibles:
        print("Error: No se encontraron archivos NDVI. Ejecuta 'calcular_ndvi.py' primero.")
        exit()

    fechas_ndvi_sorted = sorted(ndvis_disponibles.keys())
    
    # Crear un DataFrame para ETc acumulada por píxel (simulado)
    # Tomar el perfil de un NDVI para saber dimensiones
    with rasterio.open(ndvis_disponibles[fechas_ndvi_sorted]) as src:
        profile_base = src.profile
        etc_acumulada_mapa = np.zeros((profile_base['height'], profile_base['width']), dtype='float32')


    while current_date <= end_date:
        fecha_actual_str = current_date.strftime('%Y-%m-%d')
        
        # Obtener ET0 para el día actual
        et0_hoy_serie = df_et0[df_et0['fecha'] == pd.Timestamp(current_date)]['et0_mm_day']
        if et0_hoy_serie.empty:
            # print(f"No hay ET0 para {fecha_actual_str}, usando valor del día anterior o 0.")
            # Podrías interpolar ET0 o manejarlo de otra forma. Aquí usamos 0 si no hay dato.
            et0_valor_hoy = 0 
            # O buscar el más cercano si el CSV no es completo:
            # et0_valor_hoy = df_et0.iloc[(df_et0['fecha']-pd.Timestamp(current_date)).abs().argsort()[:1]]['et0_mm_day'].values

        else:
            et0_valor_hoy = et0_hoy_serie.iloc

        # Interpolar Kc a partir de los NDVI mensuales
        # Encontrar los dos NDVI más cercanos (anterior y posterior)
        ndvi_anterior_fecha = None
        ndvi_posterior_fecha = None

        for fecha_ndvi in fechas_ndvi_sorted:
            if fecha_ndvi <= current_date:
                ndvi_anterior_fecha = fecha_ndvi
            if fecha_ndvi >= current_date:
                ndvi_posterior_fecha = fecha_ndvi
                break # Ya encontramos el siguiente o igual

        if ndvi_anterior_fecha is None and ndvi_posterior_fecha is not None: # Antes del primer NDVI
            ruta_ndvi_usar = ndvis_disponibles[ndvi_posterior_fecha]
        elif ndvi_anterior_fecha is not None and ndvi_posterior_fecha is None: # Después del último NDVI
            ruta_ndvi_usar = ndvis_disponibles[ndvi_anterior_fecha]
        elif ndvi_anterior_fecha == ndvi_posterior_fecha: # Exactamente en una fecha de NDVI
             ruta_ndvi_usar = ndvis_disponibles[ndvi_anterior_fecha]
        elif ndvi_anterior_fecha is not None and ndvi_posterior_fecha is not None:
            # Interpolar (simplificado: usamos el más cercano o el anterior si está entre dos)
            # Una interpolación real de mapas NDVI sería más compleja.
            # Aquí, para simplificar, si estamos entre dos fechas NDVI,
            # usamos el NDVI de la fecha anterior hasta llegar a la siguiente.
            # O podrías implementar una interpolación lineal píxel a píxel si el tiempo lo permite.
            ruta_ndvi_usar = ndvis_disponibles[ndvi_anterior_fecha]
        else: # No debería ocurrir si hay NDVIs
            print(f"No se pudo determinar NDVI para {fecha_actual_str}. Omitiendo ETc.")
            current_date += timedelta(days=1)
            continue
            
        # Generar mapa de ETc para el día actual
        nombre_archivo_etc = f'ETc_dummy_{current_date.strftime("%Y%m%d")}.tif'
        ruta_salida_etc_diaria = os.path.join(etc_maps_dir, nombre_archivo_etc)
        
        print(f"\nCalculando ETc para: {fecha_actual_str} usando NDVI de {ruta_ndvi_usar} y ET0={et0_valor_hoy:.2f}")
        mapa_etc_diario = calcular_etc_mapa(ruta_ndvi_usar, et0_valor_hoy, ruta_salida_etc_diaria)
        
        if mapa_etc_diario is not None:
             # Acumular ETc (donde no sea NoData)
            valid_pixels_etc = (mapa_etc_diario!= (profile_base.get('nodata', -9999.0)))
            etc_acumulada_mapa[valid_pixels_etc] += mapa_etc_diario[valid_pixels_etc]

        current_date += timedelta(days=1)

    # Guardar el mapa de ETc acumulada total para la temporada
    ruta_etc_acumulada_total = os.path.join(etc_maps_dir, 'ETc_acumulada_total_temporada_dummy.tif')
    profile_acumulada = profile_base.copy()
    profile_acumulada.update(dtype='float32', nodata=-9999.0, compress='lzw')
    with rasterio.open(ruta_etc_acumulada_total, 'w', **profile_acumulada) as dst:
        dst.write(etc_acumulada_mapa.astype(rasterio.float32), 1)
    print(f"\nMapa de ETc acumulada total de la temporada guardado en: {ruta_etc_acumulada_total}")

    print("\nProceso de cálculo de Kc y ETc completado.")
