"""Endpoints Veridia — alertas de integridad en contratación pública."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from security import get_current_user
from services import cache_service
from services import radar_service as svc

router = APIRouter(prefix="/veridia", tags=["veridia"])


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user)):
    """Resumen global de alertas: KPIs de los tres tipos de detección."""
    return svc.dashboard()


# ── UC-01: Sancionados activos ────────────────────────────────────────────────

@router.get("/alertas/sancionados/resumen")
def sancionados_resumen(current_user: dict = Depends(get_current_user)):
    """Total de personas inhabilitadas con contratos vigentes y valor total."""
    return svc.sancionados_resumen()


@router.get("/alertas/sancionados")
def sancionados_lista(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Lista paginada de contratistas con inhabilitación vigente en SIRI."""
    return svc.sancionados_lista(limit=limit, offset=offset)


# ── UC-02: Multados activos ───────────────────────────────────────────────────

@router.get("/alertas/multados/resumen")
def multados_resumen(current_user: dict = Depends(get_current_user)):
    """Total de contratistas multados que siguieron recibiendo contratos."""
    return svc.multados_resumen()


@router.get("/alertas/multados")
def multados_lista(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Lista paginada de contratistas multados con contratos posteriores a la multa."""
    return svc.multados_lista(limit=limit, offset=offset)


# ── UC-03: Puerta giratoria ───────────────────────────────────────────────────

@router.get("/alertas/puerta-giratoria/resumen")
def puerta_giratoria_resumen(current_user: dict = Depends(get_current_user)):
    """Total de posibles casos de puerta giratoria detectados."""
    return svc.puerta_giratoria_resumen()


@router.get("/alertas/puerta-giratoria")
def puerta_giratoria_lista(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    confianza: str = Query(default=None, description="Filtrar por nivel: alta | media"),
    current_user: dict = Depends(get_current_user),
):
    """Lista paginada de posibles casos puerta giratoria (declarantes → contratistas)."""
    result = svc.puerta_giratoria_lista(limit=limit, offset=offset)
    if confianza in ("alta", "media"):
        result["hallazgos"] = [h for h in result["hallazgos"] if h.get("confianza") == confianza]
    return result


# ── UC-05: Perfil unificado ───────────────────────────────────────────────────

@router.get("/perfil/{documento}")
def perfil_documento(
    documento: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Perfil unificado de un contratista o persona por documento (cédula o NIT).
    Agrega datos de SECOP, SIRI, Multas y Declaraciones patrimoniales.
    Incluye nivel_alerta: rojo | naranja | amarillo | verde.
    """
    return svc.perfil(documento)


# ── Grafo relacional ─────────────────────────────────────────────────────────

@router.get("/grafo/entidad/{nit}")
def grafo_entidad(
    nit: str,
    limit: int = Query(default=40, ge=5, le=100, description="Máximo de proveedores a incluir"),
    current_user: dict = Depends(get_current_user),
):
    """
    Grafo vis-network de una entidad pública: nodo central + top proveedores.

    Grupos de nodo (para colorear en el frontend):
      - entidad     → azul   (la entidad consultada)
      - contratista → verde  (proveedor sin alertas)
      - sancionado  → rojo   (inhabilitado SIRI con contratos durante la sanción)
      - multado     → naranja (multa SECOP I con contratos posteriores)
      - alto_riesgo → granate (inhabilitado + multado)

    Cada nodo tiene `title` con HTML para tooltip de vis-network.
    Cada arista tiene `value` proporcional al número de contratos.
    """
    result = svc.grafo_entidad(nit=nit, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


# ── Cache ─────────────────────────────────────────────────────────────────────

@router.delete("/cache")
def clear_cache(current_user: dict = Depends(get_current_user)):
    """Invalida todas las entradas del cache de Veridia."""
    deleted = cache_service.clear_prefix("radar_")
    return {"mensaje": f"Cache Veridia limpiado: {deleted} entradas eliminadas"}


@router.delete("/cache/{cache_id}")
def delete_cache_entry(cache_id: str, current_user: dict = Depends(get_current_user)):
    """Invalida una entrada específica del cache por su cache_id."""
    eliminado = cache_service.delete_one(f"radar_{cache_id}")
    if eliminado:
        return {"mensaje": f"Entrada 'radar_{cache_id}' eliminada"}
    return {"mensaje": f"No se encontró 'radar_{cache_id}'"}
