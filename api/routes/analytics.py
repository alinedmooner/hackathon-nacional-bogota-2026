from fastapi import APIRouter, Depends
from security import get_current_user
from services import analytics_paso2_service as svc
from services import cache_service

router = APIRouter(prefix="/paso2/analytics", tags=["paso2-analytics"])


@router.get("/total-registros")
def total_registros(current_user: dict = Depends(get_current_user)):
    return svc.total_registros()


@router.get("/total-variables")
def total_variables(current_user: dict = Depends(get_current_user)):
    return svc.total_variables()


@router.get("/registros-2025")
def registros_2025(current_user: dict = Depends(get_current_user)):
    return svc.registros_2025()


@router.get("/pymes")
def pymes(current_user: dict = Depends(get_current_user)):
    return svc.pymes()


@router.get("/top-departamentos")
def top_departamentos(current_user: dict = Depends(get_current_user)):
    return svc.top_departamentos()


@router.get("/modalidad-preferida")
def modalidad_preferida(current_user: dict = Depends(get_current_user)):
    return svc.modalidad_preferida()


@router.get("/top-entidades-dinero")
def top_entidades_dinero(current_user: dict = Depends(get_current_user)):
    return svc.top_entidades_dinero()


@router.get("/tipos-contrato")
def tipos_contrato(current_user: dict = Depends(get_current_user)):
    return svc.tipos_contrato()


@router.get("/anomalias-financieras")
def anomalias_financieras(current_user: dict = Depends(get_current_user)):
    return svc.anomalias_financieras()


@router.get("/pagos-adelantados")
def pagos_adelantados(current_user: dict = Depends(get_current_user)):
    return svc.pagos_adelantados()


@router.get("/obligaciones-ambientales")
def obligaciones_ambientales(current_user: dict = Depends(get_current_user)):
    return svc.obligaciones_ambientales()


@router.get("/pareto")
def pareto(current_user: dict = Depends(get_current_user)):
    return svc.pareto()


@router.get("/brecha-genero")
def brecha_genero(current_user: dict = Depends(get_current_user)):
    return svc.brecha_genero()


@router.get("/anomalias-tipos-datos")
def anomalias_tipos_datos(current_user: dict = Depends(get_current_user)):
    return svc.anomalias_tipos_datos()


@router.get("/api-doc")
def api_doc(current_user: dict = Depends(get_current_user)):
    return svc.api_doc()


@router.delete("/cache")
def clear_cache(current_user: dict = Depends(get_current_user)):
    deleted = cache_service.clear_all()
    return {"mensaje": f"Cache limpiado: {deleted} entradas eliminadas"}
