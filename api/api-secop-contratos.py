import pandas as pd
from pathlib import Path
from api.soql_query import SoQLQuery

DATASET_ID = "jbjy-vk9h"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def descargar_datos() -> pd.DataFrame:
    """Descarga el dataset completo y lo guarda en parquet"""
    df = (
        SoQLQuery(DATASET_ID)
        .order_by(":id")
        .fetch_all()
    )

    print(f"✓ Total columnas: {len(df.columns)}")

    parquet_path = DATA_DIR / "contratos_secop.parquet"
    df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    print(f"✓ Guardado en: {parquet_path}")

    return df

def cargar_datos():
    """Carga los datos desde parquet local"""
    ruta = DATA_DIR / "contratos_secop.parquet"
    if ruta.exists():
        print(f"Cargando desde: {ruta}")
        return pd.read_parquet(ruta)
    print("Archivo no encontrado, descargando...")
    return descargar_datos()

def analizar_nulos(df):
    """Muestra qué variable tiene más valores nulos"""
    print("\n" + "="*60)
    print("ANÁLISIS DE VALORES NULOS")
    print("="*60)

    nulos = df.isnull().sum()
    pct_nulos = (nulos / len(df) * 100).round(2)

    resumen = pd.DataFrame({
        'nulos': nulos,
        'porcentaje': pct_nulos
    }).sort_values('nulos', ascending=False)

    print(resumen[resumen['nulos'] > 0].to_string())

    variable_max = resumen.index[0]
    max_nulos = resumen.iloc[0]['nulos']
    max_pct = resumen.iloc[0]['porcentaje']

    print("\n" + "="*60)
    print(f"Variable con MÁS nulos: '{variable_max}'")
    print(f"  Registros nulos: {max_nulos}")
    print(f"  Porcentaje:      {max_pct}%")
    print("="*60)

    return resumen

def obtener_rango_fecha_firma(df):
    """Valores mínimo y máximo de Fecha de Firma"""
    columnas = [c for c in df.columns if 'fecha' in c.lower() and 'firma' in c.lower()]

    if not columnas:
        print("No se encontró columna de Fecha de Firma")
        print("Columnas disponibles:", list(df.columns))
        return None

    col = columnas[0]
    df[col] = pd.to_datetime(df[col], errors='coerce')

    print("\n" + "="*60)
    print("RANGO DE FECHA DE FIRMA")
    print("="*60)
    print(f"Columna: {col}")
    print(f"Mínimo:  {df[col].min()}")
    print(f"Máximo:  {df[col].max()}")
    print(f"Rango:   {(df[col].max() - df[col].min()).days} días")
    print("="*60)

if __name__ == "__main__":
    df = descargar_datos()
    analizar_nulos(df)
    obtener_rango_fecha_firma(df)
