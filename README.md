# Proyecto: Optimización del Riego en Viñedos de Luján de Cuyo, Mendoza (Simulación)
Este repositorio contiene los datos simulados, scripts de Python y una simulación de resultados para un proyecto de análisis de datos enfocado en la optimización del manejo del agua en viñedos de Luján de Cuyo, Mendoza, para la temporada 2023-2024.
El objetivo principal de un proyecto real sería estimar la variabilidad espacial y temporal de las necesidades hídricas (Evapotranspiración del Cultivo, ETc​) para proponer estrategias de riego más eficientes. Esta simulación demuestra la metodología.

## Metodología General (Simulada)

1. Datos de Entrada:
   *  Meteorológicos: Archivo CSV con datos diarios simulados (`data/meteorological/datos_meteorologicos_lujan_2023_2024.csv`).
   *  Suelo: Referencias a fuentes como SIAT Mendoza y estudios del INTA (uso cualitativo en esta simulación).
   *  Satélites: Se utilizan archivos GeoTIFF dummy generados por los scripts para representar bandas de Sentinel-2 (en `data/satellite_raw_dummy/`).
2. Cálculo de ET0​: Método FAO Penman-Monteith (usando `pyeto` en `scripts/calcular_et0.py`).
3. Cálculo de NDVI: A partir de las bandas dummy Roja y NIR (usando `rasterio` en `scripts/calcular_ndvi.py`).
4. Estimación de Kc​: Relación lineal Kc​=1.4×NDVI−0.1.
5. Cálculo de ETc​: ETc​=Kc​×ET0​ (en `scripts/calcular_kc_etc.py`), generando mapas dummy de ETc​.

## Estructura del Repositorio
* `/data/`: Contiene los datos de entrada simulados.
  * `meteorological/`: Datos climáticos.
  * `satellite_raw_dummy/`: Los scripts de NDVI crearán aquí los GeoTIFFs dummy de las bandas si no existen.
* `/scripts/`: Scripts de Python para cada etapa del análisis.
* `/results/`: Almacena los resultados generados por los scripts (CSVs, GeoTIFFs dummy).
* `/informe/`: Contiene el informe detallado del proyecto simulado.
* `requirements.txt`: Lista de las librerías de Python necesarias.
## Cómo Ejecutar la Simulación
1. Clonar el repositorio:
```bash git clone
https://tu_usuario/proyecto_optimizacion_riego_mendoza.git cd proyecto_optimizacion_riego_mendoza
```
2. Crear un entorno virtual e instalar dependencias:
```bash
python -m venv venv
# En Linux/macOS:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate
pip install -r requirements.txt
```
3. Preparar datos de entrada:
Asegúrate que el archivo `data/meteorological/datos_meteorologicos_lujan_2023_2024.csv` exista con el contenido proporcionado.
La carpeta `data/satellite_raw_dummy`/ se puede dejar vacía inicialmente; el script `calcular_ndvi.py` creará los TIFFs dummy necesarios.

4. Ejecutar los scripts en orden desde la raíz del proyecto:
```bash
python scripts/calcular_et0.py
python scripts/calcular_ndvi.py
python scripts/calcular_kc_etc.py
```

5. Verificar Resultados:
  * Los resultados se guardarán en las subcarpetas dentro de `/results/`.
  * Puedes abrir los archivos GeoTIFF generados (ej. `results/ndvi_maps/NDVI_dummy_20240115.tif` o `results/etc_maps/ETc_acumulada_total_temporada_dummy.tif`) con un software GIS como QGIS para visualizarlos (serán mapas con valores simulados/aleatorios pero con la estructura correcta).

### Nota Importante
  * Esta es una simulación para demostrar el flujo de trabajo. Para un proyecto real, necesitarás:
  * Obtener datos meteorológicos reales y actualizados.
  * Descargar imágenes satelitales Sentinel-2 reales (archivos GeoTIFF grandes) del Copernicus Data Space Ecosystem u otra fuente.
  * Adaptar las rutas de los archivos en los scripts para que apunten a tus datos reales.
  * Realizar una validación a campo de los resultados.

### Contacto
