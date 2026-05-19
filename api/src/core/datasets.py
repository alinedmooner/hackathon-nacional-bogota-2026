import os
from dotenv import load_dotenv

load_dotenv()


class ContratosDataset:
    ID = os.getenv("DATASET_CONTRATOS_ID", "jbjy-vk9h")

    # Entidad
    NOMBRE_ENTIDAD = "nombre_entidad"
    NIT_ENTIDAD = "nit_entidad"
    DEPARTAMENTO = "departamento"
    CIUDAD = "ciudad"
    LOCALIZACION = "localizaci_n"
    ORDEN = "orden"
    SECTOR = "sector"
    RAMA = "rama"
    ENTIDAD_CENTRALIZADA = "entidad_centralizada"
    CODIGO_ENTIDAD = "codigo_entidad"

    # Proceso
    PROCESO_DE_COMPRA = "proceso_de_compra"
    DESCRIPCION_DEL_PROCESO = "descripcion_del_proceso"
    MODALIDAD_DE_CONTRATACION = "modalidad_de_contratacion"
    JUSTIFICACION_MODALIDAD = "justificacion_modalidad_de"
    CODIGO_CATEGORIA_PRINCIPAL = "codigo_de_categoria_principal"
    URLPROCESO = "urlproceso"

    # Contrato
    ID_CONTRATO = "id_contrato"
    REFERENCIA_CONTRATO = "referencia_del_contrato"
    ESTADO_CONTRATO = "estado_contrato"
    TIPO_DE_CONTRATO = "tipo_de_contrato"
    OBJETO_DEL_CONTRATO = "objeto_del_contrato"
    DURACION_DEL_CONTRATO = "duraci_n_del_contrato"
    CONDICIONES_DE_ENTREGA = "condiciones_de_entrega"
    LIQUIDACION = "liquidaci_n"
    DIAS_ADICIONADOS = "dias_adicionados"
    EL_CONTRATO_PUEDE_SER_PRORROGADO = "el_contrato_puede_ser_prorrogado"

    # Fechas
    FECHA_DE_FIRMA = "fecha_de_firma"
    FECHA_INICIO_CONTRATO = "fecha_de_inicio_del_contrato"
    FECHA_FIN_CONTRATO = "fecha_de_fin_del_contrato"
    FECHA_INICIO_LIQUIDACION = "fecha_inicio_liquidacion"
    FECHA_FIN_LIQUIDACION = "fecha_fin_liquidacion"
    FECHA_NOTIFICACION_PRORROGACION = "fecha_de_notificaci_n_de_prorrogaci_n"
    ULTIMA_ACTUALIZACION = "ultima_actualizacion"

    # Proveedor
    DOCUMENTO_PROVEEDOR = "documento_proveedor"
    TIPODOCPROVEEDOR = "tipodocproveedor"
    PROVEEDOR_ADJUDICADO = "proveedor_adjudicado"
    CODIGO_PROVEEDOR = "codigo_proveedor"
    ES_GRUPO = "es_grupo"
    ES_PYME = "es_pyme"

    # Representante legal
    NOMBRE_REPRESENTANTE_LEGAL = "nombre_representante_legal"
    NACIONALIDAD_REPRESENTANTE_LEGAL = "nacionalidad_representante_legal"
    DOMICILIO_REPRESENTANTE_LEGAL = "domicilio_representante_legal"
    TIPO_ID_REPRESENTANTE_LEGAL = "tipo_de_identificaci_n_representante_legal"
    ID_REPRESENTANTE_LEGAL = "identificaci_n_representante_legal"
    GENERO_REPRESENTANTE_LEGAL = "g_nero_representante_legal"

    # Financiero
    VALOR_DEL_CONTRATO = "valor_del_contrato"
    VALOR_PAGO_ADELANTADO = "valor_de_pago_adelantado"
    VALOR_FACTURADO = "valor_facturado"
    VALOR_PENDIENTE_PAGO = "valor_pendiente_de_pago"
    VALOR_PAGADO = "valor_pagado"
    VALOR_AMORTIZADO = "valor_amortizado"
    VALOR_PENDIENTE_DE = "valor_pendiente_de"
    VALOR_PENDIENTE_EJECUCION = "valor_pendiente_de_ejecucion"
    SALDO_CDP = "saldo_cdp"
    SALDO_VIGENCIA = "saldo_vigencia"
    HABILITA_PAGO_ADELANTADO = "habilita_pago_adelantado"
    RECURSOS_PROPIOS = "recursos_propios_alcald_as_gobernaciones_y_resguardos_ind_genas_"
    ORIGEN_RECURSOS = "origen_de_los_recursos"
    DESTINO_GASTO = "destino_gasto"

    # Cuenta bancaria
    NOMBRE_DEL_BANCO = "nombre_del_banco"
    TIPO_DE_CUENTA = "tipo_de_cuenta"
    NUMERO_DE_CUENTA = "n_mero_de_cuenta"

    # Responsables
    NOMBRE_ORDENADOR_GASTO = "nombre_ordenador_del_gasto"
    TIPO_DOC_ORDENADOR_GASTO = "tipo_de_documento_ordenador_del_gasto"
    NUM_DOC_ORDENADOR_GASTO = "n_mero_de_documento_ordenador_del_gasto"
    NOMBRE_SUPERVISOR = "nombre_supervisor"
    TIPO_DOC_SUPERVISOR = "tipo_de_documento_supervisor"
    NUM_DOC_SUPERVISOR = "n_mero_de_documento_supervisor"
    NOMBRE_ORDENADOR_PAGO = "nombre_ordenador_de_pago"
    TIPO_DOC_ORDENADOR_PAGO = "tipo_de_documento_ordenador_de_pago"
    NUM_DOC_ORDENADOR_PAGO = "n_mero_de_documento_ordenador_de_pago"

    # Acuerdo de paz
    ESPOSTCONFLICTO = "espostconflicto"
    PUNTOS_DEL_ACUERDO = "puntos_del_acuerdo"
    PILARES_DEL_ACUERDO = "pilares_del_acuerdo"

    # Obligaciones
    OBLIGACION_AMBIENTAL = "obligaci_n_ambiental"
    OBLIGACIONES_POSTCONSUMO = "obligaciones_postconsumo"
    REVERSION = "reversion"

    # Documentos
    DOCUMENTOS_TIPO = "documentos_tipo"
    DESCRIPCION_DOCUMENTOS_TIPO = "descripcion_documentos_tipo"

    # Valores de estado_contrato
    class Estado:
        EN_EJECUCION = "En ejecución"
        CERRADO = "Cerrado"
        MODIFICADO = "Modificado"
        TERMINADO = "terminado"
        BORRADOR = "Borrador"
        APROBADO = "Aprobado"
        CANCELADO = "Cancelado"
        ENVIADO_PROVEEDOR = "enviado Proveedor"
        CEDIDO = "cedido"
        EN_APROBACION = "En aprobación"
        SUSPENDIDO = "Suspendido"
        PRORROGADO = "Prorrogado"


class ArchivosDataset:
    ID = os.getenv("DATASET_ARCHIVOS_ID", "dmgg-8hin")

    ID_DOCUMENTO = "id_documento"
    PROCESO = "proceso"
    NOMBRE_ARCHIVO = "nombre_archivo"
    TAMANNO_ARCHIVO = "tamanno_archivo"
    EXTENSION = "extensi_n"
    DESCRIPCION = "descripci_n"
    FECHA_CARGA = "fecha_carga"
    ENTIDAD = "entidad"
    NIT_ENTIDAD = "nit_entidad"
    URL_DESCARGA = "url_descarga_documento"


class SiriDataset:
    ID = "iaeu-rcn6"

    NUMERO_SIRI = "numero_siri"
    TIPO_INHABILIDAD = "tipo_inhabilidad"
    CALIDAD_PERSONA = "calidad_persona"
    TIPO_IDENTIFICACION = "tipo_identificacion"
    NUMERO_IDENTIFICACION = "numero_identificacion"
    PRIMER_APELLIDO = "primer_apellido"
    SEGUNDO_APELLIDO = "segundo_apellido"
    PRIMER_NOMBRE = "primer_nombre"
    SEGUNDO_NOMBRE = "segundo_nombre"
    CARGO = "cargo"
    SANCIONES = "sanciones"
    DURACION_ANOS = "duracion_anos"
    DURACION_MES = "duracion_mes"
    DURACION_DIAS = "duracion_dias"
    FECHA_EFECTOS_JURIDICOS = "fecha_efectos_juridicos"
    FECHA_FIN_SANCION = "fecha_fin_sancion"
    AUTORIDAD = "autoridad"
    ENTIDAD_SANCIONADO = "entidad_sancionado"


class MultasDataset:
    ID = "4n4q-k399"

    NOMBRE_ENTIDAD = "nombre_entidad"
    NIT_ENTIDAD = "nit_entidad"
    NIVEL = "nivel"
    ORDEN = "orden"
    MUNICIPIO = "municipio"
    NUMERO_DE_RESOLUCION = "numero_de_resolucion"
    DOCUMENTO_CONTRATISTA = "documento_contratista"
    NOMBRE_CONTRATISTA = "nombre_contratista"
    NUMERO_DE_CONTRATO = "numero_de_contrato"
    VALOR_SANCION = "valor_sancion"
    FECHA_DE_PUBLICACION = "fecha_de_publicacion"
    FECHA_DE_FIRMEZA = "fecha_de_firmeza"
    FECHA_DE_CARGUE = "fecha_de_cargue"
    RUTA_DE_PROCESO = "ruta_de_proceso"


class PatrimonioDataset:
    ID = "8tz7-h3eu"

    TIPO_DOCUMENTO = "tipo_documento"
    NUMERO_DOCUMENTO = "numero_documento"
    PRIMER_NOMBRE_DECLARANTE = "primer_nombre_declarante"
    SEGUNDO_NOMBRE_DECLARANTE = "segundo_nombre_declarante"
    PRIMER_APELLIDO_DECLARANTE = "primer_apellido_declarante"
    SEGUNDO_APELLIDO_DECLARANTE = "segundo_apellido_declarante"
    FECHA_PUBLICAC_DECLARAC = "fecha_publicac_declarac"
    ESTADO_DECLARACION = "estado_declaracion"
    TIPO_DECLARACION = "tipo_declaracion"
    NOMBRE_ENTIDAD = "nombre_entidad"
    DECLARANTE_ES_CONTRATISTA = "declarante_es_contratista"
    CARGO_DECLARANTE = "cargo_declarante"
    PARTICIP_CORP_SOCIED_ASOC = "particip_corp_socied_asoc"
    PARTICIP_JUNTAS_CONSEJOS = "particip_juntas_consejos"
    ACTIV_ECONOM_PRIVADAS = "activ_econom_privadas"
