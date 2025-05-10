import pandas as pd
from pyeto import fao_penman_monteith, deg_to_rad
from datetime import datetime
import os

def calcular_et0_diaria(df_meteo, latitud_grados, altitud_metros):
    lat_rad = deg_to_rad(latitud_grados)
    resultados_et0 = []

    for index, row in df_meteo.iterrows():
        try:
            fecha_dt = datetime.strptime(str(row['fecha']), '%Y-%m-%d')
            day_of_year = fecha_dt.timetuple().tm_yday
            
            # Asegurar que los datos sean numéricos
            tmin = float(row['tmin'])
            tmax = float(row['tmax'])
            rh_mean = float(row['rh_mean'])
            wind_speed_2m = float(row['wind_speed_2m'])
            sol_rad_mj_m2_day = float(row['sol_rad_mj_m2_day'])

            et0 = fao_penman_monteith(
                tmin=tmin,
                tmax=tmax,
                rh_mean=rh_mean,
                wind_speed=wind_speed_2m,
                sol_rad=sol_rad_mj_m2_day,
                elevation=altitud_metros,
                lat=lat_rad,
                J=day_of_year,
                t_mean=(tmin + tmax) / 2
            )
            resultados_et0.append(et0)
        except Exception as e:
            print(f"Error calculando ET0 para la fecha {row['fecha']}: {e}")
            resultados_et0.append(None)

    df_meteo['et0_mm_day'] = resultados_et0
    return df_meteo

if __name__ == "__main__":
    # Rutas relativas al script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_input_path = os.path.join(base_dir, '..', 'data', 'meteorological', 'datos_meteorologicos_lujan_2023_2024.csv')
    results_output_dir = os.path.join(base_dir, '..', 'results', 'et0_calculada')
    output_csv_path = os.path.join(results_output_dir, 'datos_meteorologicos_con_et0.csv')

    os.makedirs(results_output_dir, exist_ok=True)

    # Parámetros de la estación (ejemplo para Luján de Cuyo)
    latitud_lujan = -33.0 # Aproximado
    altitud_lujan = 950  # Aproximado

    try:
        df_meteo_real = pd.read_csv(data_input_path)
        df_meteo_real['fecha'] = pd.to_datetime(df_meteo_real['fecha']).dt.strftime('%Y-%m-%d')
        
        print(f"Cargando datos desde: {data_input_path}")
        print("Primeras filas de los datos meteorológicos:")
        print(df_meteo_real.head())

        df_con_et0 = calcular_et0_diaria(df_meteo_real, latitud_lujan, altitud_lujan)
        
        print("\nDataFrame con ET0 calculada:")
        print(df_con_et0.head())
        
        df_con_et0.to_csv(output_csv_path, index=False)
        print(f"\nDatos con ET0 guardados en: {output_csv_path}")

    except FileNotFoundError:
        print(f"Error: Archivo '{data_input_path}' no encontrado.")
        print("Asegúrate de haber creado el archivo CSV con los datos meteorológicos simulados en la ruta correcta.")
    except Exception as e:
        print(f"Ocurrió un error general: {e}")
