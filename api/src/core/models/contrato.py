import math
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Contrato(BaseModel):
    # Entidad
    nombre_entidad: Optional[str] = None
    nit_entidad: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: Optional[str] = None
    localizacion: Optional[str] = Field(None, alias="localizaci_n")
    orden: Optional[str] = None
    sector: Optional[str] = None
    rama: Optional[str] = None
    entidad_centralizada: Optional[str] = None
    codigo_entidad: Optional[str] = None

    # Proceso
    proceso_de_compra: Optional[str] = None
    descripcion_del_proceso: Optional[str] = None
    modalidad_de_contratacion: Optional[str] = None
    justificacion_modalidad_de: Optional[str] = None
    codigo_de_categoria_principal: Optional[str] = None
    urlproceso: Optional[str] = None

    # Contrato
    id_contrato: Optional[str] = None
    referencia_del_contrato: Optional[str] = None
    estado_contrato: Optional[str] = None
    tipo_de_contrato: Optional[str] = None
    objeto_del_contrato: Optional[str] = None
    duracion_del_contrato: Optional[str] = Field(None, alias="duraci_n_del_contrato")
    condiciones_de_entrega: Optional[str] = None
    liquidacion: Optional[str] = Field(None, alias="liquidaci_n")
    dias_adicionados: Optional[str] = None
    el_contrato_puede_ser_prorrogado: Optional[str] = None

    # Fechas
    fecha_de_firma: Optional[str] = None
    fecha_de_inicio_del_contrato: Optional[str] = None
    fecha_de_fin_del_contrato: Optional[str] = None
    fecha_inicio_liquidacion: Optional[str] = None
    fecha_fin_liquidacion: Optional[str] = None
    fecha_de_notificacion_de_prorrogacion: Optional[str] = Field(None, alias="fecha_de_notificaci_n_de_prorrogaci_n")
    ultima_actualizacion: Optional[str] = None

    # Proveedor
    tipodocproveedor: Optional[str] = None
    documento_proveedor: Optional[str] = None
    proveedor_adjudicado: Optional[str] = None
    codigo_proveedor: Optional[str] = None
    es_grupo: Optional[str] = None
    es_pyme: Optional[str] = None

    # Financiero
    valor_del_contrato: Optional[str] = None
    valor_de_pago_adelantado: Optional[str] = None
    valor_facturado: Optional[str] = None
    valor_pendiente_de_pago: Optional[str] = None
    valor_pagado: Optional[str] = None
    valor_amortizado: Optional[str] = None
    valor_pendiente_de: Optional[str] = None
    valor_pendiente_de_ejecucion: Optional[str] = None
    saldo_cdp: Optional[str] = None
    saldo_vigencia: Optional[str] = None
    habilita_pago_adelantado: Optional[str] = None
    origen_de_los_recursos: Optional[str] = None
    destino_gasto: Optional[str] = None

    # Responsables
    nombre_ordenador_del_gasto: Optional[str] = None
    nombre_supervisor: Optional[str] = None
    nombre_ordenador_de_pago: Optional[str] = None

    # Representante legal
    nombre_representante_legal: Optional[str] = None
    genero_representante_legal: Optional[str] = Field(None, alias="g_nero_representante_legal")

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def sanitize_nan(cls, data: dict) -> dict:
        return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in data.items()}

    @field_validator("urlproceso", mode="before")
    @classmethod
    def extract_url(cls, v: Any) -> Optional[str]:
        if isinstance(v, dict):
            return v.get("url")
        return v
