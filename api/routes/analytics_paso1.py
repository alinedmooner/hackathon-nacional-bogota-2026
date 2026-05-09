from fastapi import APIRouter, Depends
from security import get_current_user
from services import analytics_paso1_service as svc

router = APIRouter(prefix="/paso1/analytics", tags=["paso1-analytics"])


@router.get("/total-registros")
def total_registros(current_user: dict = Depends(get_current_user)):
    return svc.total_registros()


@router.get("/total-columnas")
def total_columnas(current_user: dict = Depends(get_current_user)):
    return svc.total_columnas()


@router.get("/nulos-descripcion")
def nulos_descripcion(current_user: dict = Depends(get_current_user)):
    return svc.nulos_descripcion()


@router.get("/nulos-proceso")
def nulos_proceso(current_user: dict = Depends(get_current_user)):
    return svc.nulos_proceso()


@router.get("/tipos-columnas")
def tipos_columnas(current_user: dict = Depends(get_current_user)):
    return svc.tipos_columnas()


@router.get("/stats-id-documento")
def stats_id_documento(current_user: dict = Depends(get_current_user)):
    return svc.stats_id_documento()


@router.get("/stats-tamano-archivo")
def stats_tamano_archivo(current_user: dict = Depends(get_current_user)):
    return svc.stats_tamano_archivo()


@router.get("/stats-nit-entidad")
def stats_nit_entidad(current_user: dict = Depends(get_current_user)):
    return svc.stats_nit_entidad()


@router.get("/rango-fecha-carga")
def rango_fecha_carga(current_user: dict = Depends(get_current_user)):
    return svc.rango_fecha_carga()


@router.get("/documento-por-id")
def documento_por_id(
    id_documento: int = 756926574,
    current_user: dict = Depends(get_current_user),
):
    return svc.documento_por_id(id_documento)
