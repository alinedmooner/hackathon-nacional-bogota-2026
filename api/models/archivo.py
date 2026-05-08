from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class Archivo(BaseModel):
    id_documento: Optional[str] = None
    proceso: Optional[str] = None
    nombre_archivo: Optional[str] = None
    tamanno_archivo: Optional[str] = None
    extension: Optional[str] = Field(None, alias="extensi_n")
    descripcion: Optional[str] = Field(None, alias="descripci_n")
    fecha_carga: Optional[str] = None
    entidad: Optional[str] = None
    nit_entidad: Optional[str] = None
    url_descarga: Optional[str] = Field(None, alias="url_descarga_documento")

    model_config = {"populate_by_name": True}

    @field_validator("url_descarga", mode="before")
    @classmethod
    def extract_url(cls, v: Any) -> Optional[str]:
        if isinstance(v, dict):
            return v.get("url")
        return v
