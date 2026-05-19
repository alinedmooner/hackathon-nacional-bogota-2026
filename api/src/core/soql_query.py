import copy
import json
import urllib.request
from urllib.parse import urlencode

BASE_URL = "https://www.datos.gov.co/resource/{dataset_id}.json"


class SoQLQuery:
    """Builder para construir y ejecutar queries SoQL contra la API Socrata."""

    def __init__(self, dataset_id: str):
        self._dataset_id = dataset_id
        self._select: list[str] = []
        self._where: list[str] = []
        self._group: list[str] = []
        self._order: list[str] = []
        self._having: list[str] = []
        self._limit: int | None = None
        self._offset: int | None = None

    # ------------------------------------------------------------------ #
    # Builder methods                                                       #
    # ------------------------------------------------------------------ #

    def select(self, *columns: str) -> "SoQLQuery":
        self._select.extend(columns)
        return self

    def where(self, condition: str) -> "SoQLQuery":
        self._where.append(condition)
        return self

    def group_by(self, *columns: str) -> "SoQLQuery":
        self._group.extend(columns)
        return self

    def order_by(self, column: str, desc: bool = False) -> "SoQLQuery":
        self._order.append(f"{column} DESC" if desc else column)
        return self

    def having(self, condition: str) -> "SoQLQuery":
        self._having.append(condition)
        return self

    def limit(self, n: int) -> "SoQLQuery":
        self._limit = n
        return self

    def offset(self, n: int) -> "SoQLQuery":
        self._offset = n
        return self

    def copy(self) -> "SoQLQuery":
        """Retorna una copia independiente del query."""
        return copy.deepcopy(self)

    # ------------------------------------------------------------------ #
    # Build                                                                 #
    # ------------------------------------------------------------------ #

    def build(self) -> dict:
        """Retorna los parámetros de la query como diccionario."""
        params = {}

        if self._select:
            params["$select"] = ", ".join(self._select)
        if self._where:
            params["$where"] = " AND ".join(f"({c})" for c in self._where)
        if self._group:
            params["$group"] = ", ".join(self._group)
        if self._order:
            params["$order"] = ", ".join(self._order)
        if self._having:
            params["$having"] = " AND ".join(f"({c})" for c in self._having)
        if self._limit is not None:
            params["$limit"] = self._limit
        if self._offset is not None:
            params["$offset"] = self._offset

        return params

    def url(self) -> str:
        """Retorna la URL completa lista para pegar en el navegador."""
        base = BASE_URL.format(dataset_id=self._dataset_id)
        params = self.build()
        return f"{base}?{urlencode(params)}" if params else base

    # ------------------------------------------------------------------ #
    # Execute                                                               #
    # ------------------------------------------------------------------ #

    def fetch(self, app_token: str = "") -> list[dict]:
        """Ejecuta la query y retorna una lista de dicts."""
        params = self.build()
        base = BASE_URL.format(dataset_id=self._dataset_id)
        full_url = f"{base}?{urlencode(params)}" if params else base

        req = urllib.request.Request(full_url)
        if app_token:
            req.add_header("X-App-Token", app_token)

        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    def fetch_count(self, app_token: str = "") -> int:
        """Ejecuta un COUNT(*) y retorna el total."""
        q = self.copy()
        q._select = ["COUNT(*) AS total"]
        q._order = []
        q._limit = None
        q._offset = None
        rows = q.fetch(app_token)
        if rows and isinstance(rows, list) and len(rows) > 0:
            return int(rows[0].get("total", 0))
        return 0

    def __repr__(self) -> str:
        return f"SoQLQuery(url={self.url()!r})"
