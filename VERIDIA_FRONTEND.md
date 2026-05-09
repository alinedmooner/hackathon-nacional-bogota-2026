# Veridia · Guía de integración para el equipo frontend

> **Audiencia:** desarrolladores Angular del módulo Veridia.
> **Complementa (no reemplaza):** `FRONTEND.md` — que cubre el chat IA general.
> **Stack base:** Angular 17, Tailwind, JWT interceptor ya existente.

---

## Índice

1. [Configuración base](#1-configuración-base)
2. [Autenticación](#2-autenticación)
3. [Interfaces TypeScript](#3-interfaces-typescript)
4. [Endpoints Veridia REST](#4-endpoints-veridia-rest)
5. [Chat IA — SSE Streaming (formato real)](#5-chat-ia--sse-streaming-formato-real)
6. [Servicio Angular — VeridiaService](#6-servicio-angular--veridiaservice)
7. [Cytoscape.js — Grafo de entidad](#7-cytoscapejs--grafo-de-entidad)
8. [Notas de compatibilidad](#8-notas-de-compatibilidad)

---

## 1. Configuración base

### Variables de entorno Angular

```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
};
```

En producción Docker, el frontend corre detrás del mismo nginx que proxifica `/api` → `:8000`.
Usa `window.__env.BACKEND_URL` si ya existe ese mecanismo en el proyecto, o el `proxy.conf.json` de development.

### Prefijos de rutas

| Módulo         | Prefijo      |
|----------------|--------------|
| Autenticación  | `/auth`      |
| Agente IA      | `/ai`        |
| Veridia alertas| `/veridia`   |

Todos los endpoints **requieren** `Authorization: Bearer <token>` — el interceptor existente ya lo agrega.

---

## 2. Autenticación

```
POST /auth/login
Content-Type: application/json

{ "username": "admin", "password": "admin123" }
```

**Respuesta:**
```json
{ "access_token": "eyJhbGci...", "token_type": "bearer" }
```

Guardar el token en `localStorage`. El interceptor JWT del proyecto ya lo toma de ahí. No tocar.

---

## 3. Interfaces TypeScript

Pega esto en `src/app/models/veridia.models.ts`:

```typescript
// ── Alertas ──────────────────────────────────────────────────────────────────

export interface AlertaResumen {
  total_personas?: number;
  total_contratistas?: number;
  total_contratos: number;
  valor_total_cop: number;
}

export interface Dashboard {
  sancionados_activos: AlertaResumen & { interpretacion: string };
  multados_activos:    AlertaResumen & { interpretacion: string };
  puerta_giratoria:    AlertaResumen & { interpretacion: string; nota: string };
  disponibilidad_datasets: Record<string, boolean>;
}

export interface Hallazgo {
  documento:           string;
  nombre_sancionado?:  string;
  nombre_contratista?: string;
  nombre_declarante?:  string;
  sanciones?:          string;
  valor_sancion?:      number;
  fecha_inicio_sancion?: string;
  fecha_fin_sancion?:    string;
  url_evidencia?:        string;
  id_contrato:           string;
  fecha_de_firma:        string;
  valor_contrato:        number;
  nombre_entidad:        string;
  nit_entidad:           string;
  confianza:             'alta' | 'media';
}

export interface ListaHallazgos {
  hallazgos:   Hallazgo[];
  limit:       number;
  offset:      number;
  total_pagina: number;
}

export interface Perfil {
  documento:      string;
  nivel_alerta:   'rojo' | 'naranja' | 'amarillo' | 'verde';
  secop?: {
    total_contratos: number;
    valor_total_cop: number;
    contratos: any[];
  };
  siri:       any[];
  multas:     any[];
  patrimonio: any[];
}

// ── Grafo (Cytoscape) ────────────────────────────────────────────────────────

export type NodeGroup =
  | 'entidad'
  | 'contratista'
  | 'sancionado'
  | 'multado'
  | 'alto_riesgo';

export interface GrafoNode {
  id:    string;
  label: string;
  group: NodeGroup;
  value: number;   // tamaño del nodo / número de contratos
  title: string;   // HTML tooltip
}

export interface GrafoEdge {
  from:  string;
  to:    string;
  value: number;   // grosor de arista
  title: string;
}

export interface GrafoResponse {
  nodes: GrafoNode[];
  edges: GrafoEdge[];
  meta: {
    entidad:           string;
    nit:               string;
    total_contratistas: number;
    alertas_rojo:      number;
    alertas_naranja:   number;
  };
}

// ── Chat / SSE ────────────────────────────────────────────────────────────────

export interface ChatRequest {
  message:         string;
  conversation_id: string | null;
}

export type SseEventType =
  | 'init'
  | 'thinking'
  | 'tool_call'
  | 'tool_result'
  | 'chart'
  | 'answer'
  | 'done'
  | 'error';

export interface SseEvent {
  type:            SseEventType;
  // init
  conversation_id?: string;
  // thinking
  iteration?:      number;
  // tool_call
  tool?:           string;
  args?:           Record<string, any>;
  // tool_result
  summary?:        string;
  // chart
  chart?: {
    id:           string;
    title:        string;
    chart_js_spec: any;
  };
  // answer
  text?:           string;
  // done
  usage?:          { input_tokens: number; output_tokens: number };
  latency_ms?:     number;
  // error
  detail?:         string;
}
```

---

## 4. Endpoints Veridia REST

Base: `GET /veridia/...` — todos requieren JWT.

### 4.1 Dashboard global

```
GET /veridia/dashboard
```

Devuelve KPIs de los tres tipos de alerta. Llamar una vez al montar el módulo.

```typescript
this.http.get<Dashboard>(`${apiUrl}/veridia/dashboard`).subscribe(...)
```

### 4.2 Sancionados activos (inhabilitados SIRI contratando)

```
GET /veridia/alertas/sancionados/resumen
GET /veridia/alertas/sancionados?limit=50&offset=0
```

### 4.3 Multados activos (multa SECOP I + contratos posteriores)

```
GET /veridia/alertas/multados/resumen
GET /veridia/alertas/multados?limit=50&offset=0
```

Cada hallazgo incluye `url_evidencia` con el link al expediente oficial — muéstralo como chip clickeable.

### 4.4 Puerta giratoria

```
GET /veridia/alertas/puerta-giratoria/resumen
GET /veridia/alertas/puerta-giratoria?limit=50&offset=0&confianza=alta
```

El query param `confianza=alta` filtra solo los casos con entidad coincidente exacta (más fiables para la demo).

### 4.5 Perfil de persona/empresa

```
GET /veridia/perfil/{documento}
```

Donde `documento` es la cédula o NIT (solo dígitos, sin puntos ni guiones).

```typescript
this.http.get<Perfil>(`${apiUrl}/veridia/perfil/900005502`).subscribe(...)
```

### 4.6 Grafo de entidad

```
GET /veridia/grafo/entidad/{nit}?limit=40
```

Devuelve `GrafoResponse` con nodos y aristas. Ver sección 7 para integración Cytoscape.

---

## 5. Chat IA — SSE Streaming (formato real)

> El `FRONTEND.md` anterior describe un formato de eventos **diferente al implementado**.
> Este es el formato correcto del endpoint `POST /ai/chat/stream`.

### Secuencia de eventos real

```
data: {"type":"init","conversation_id":"abc-123"}

data: {"type":"thinking","iteration":1}

data: {"type":"tool_call","tool":"get_alert_summary","args":{}}

data: {"type":"tool_result","tool":"get_alert_summary","summary":"resumen global: 42 sancionados activos"}

data: {"type":"thinking","iteration":2}

data: {"type":"tool_call","tool":"check_active_sanctions","args":{"limit":5}}

data: {"type":"tool_result","tool":"check_active_sanctions","summary":"ALERTA_ROJA: 5 contratos detectados"}

data: {"type":"answer","text":"He encontrado 42 personas inhabilitadas..."}

data: {"type":"done","conversation_id":"abc-123","usage":{"input_tokens":1200,"output_tokens":340},"latency_ms":4800}
```

### Consumo con `fetch` + `ReadableStream` (sin librería externa)

```typescript
// src/app/services/veridia-stream.service.ts
import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';
import { SseEvent } from '../models/veridia.models';

@Injectable({ providedIn: 'root' })
export class VeridiaStreamService {
  private readonly auth = inject(AuthService);

  async *streamChat(
    message: string,
    conversationId: string | null = null
  ): AsyncGenerator<SseEvent> {
    const response = await fetch(`${environment.apiUrl}/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.auth.getToken()}`,
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Los eventos SSE se separan por línea doble \n\n
      const parts = buffer.split('\n\n');
      buffer = parts.pop()!; // último fragmento incompleto

      for (const part of parts) {
        const line = part.trim();
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6)) as SseEvent;
          } catch {
            // ignorar líneas mal formadas
          }
        }
      }
    }
  }
}
```

### Uso en un componente Angular

```typescript
// En el componente de chat
async sendMessage(text: string) {
  this.isStreaming = true;
  this.currentAnswer = '';
  this.activeTools = [];

  try {
    for await (const event of this.streamSvc.streamChat(text, this.conversationId)) {
      switch (event.type) {
        case 'init':
          this.conversationId = event.conversation_id!;
          break;

        case 'thinking':
          this.thinkingLabel = `Analizando (paso ${event.iteration})...`;
          break;

        case 'tool_call':
          this.activeTools.push({ tool: event.tool!, status: 'running', summary: '' });
          break;

        case 'tool_result':
          const t = this.activeTools.findLast(t => t.tool === event.tool);
          if (t) { t.status = 'done'; t.summary = event.summary!; }
          break;

        case 'chart':
          this.charts.push(event.chart!);
          break;

        case 'answer':
          this.currentAnswer = event.text!;
          break;

        case 'done':
          this.isStreaming = false;
          break;

        case 'error':
          this.errorMsg = event.detail!;
          this.isStreaming = false;
          break;
      }

      // Forzar detección de cambios si usas OnPush
      this.cdr.markForCheck();
    }
  } catch (err) {
    this.errorMsg = 'Error de conexión';
    this.isStreaming = false;
  }
}
```

---

## 6. Servicio Angular — VeridiaService

```typescript
// src/app/services/veridia.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Dashboard, ListaHallazgos, AlertaResumen,
  Perfil, GrafoResponse
} from '../models/veridia.models';

@Injectable({ providedIn: 'root' })
export class VeridiaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/veridia`;

  getDashboard(): Observable<Dashboard> {
    return this.http.get<Dashboard>(`${this.base}/dashboard`);
  }

  getSancionadosResumen(): Observable<AlertaResumen> {
    return this.http.get<AlertaResumen>(`${this.base}/alertas/sancionados/resumen`);
  }

  getSancionados(limit = 50, offset = 0): Observable<ListaHallazgos> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<ListaHallazgos>(`${this.base}/alertas/sancionados`, { params });
  }

  getMultadosResumen(): Observable<AlertaResumen> {
    return this.http.get<AlertaResumen>(`${this.base}/alertas/multados/resumen`);
  }

  getMultados(limit = 50, offset = 0): Observable<ListaHallazgos> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<ListaHallazgos>(`${this.base}/alertas/multados`, { params });
  }

  getPuertaGiratoria(limit = 50, offset = 0, confianza?: 'alta' | 'media'): Observable<ListaHallazgos> {
    let params = new HttpParams().set('limit', limit).set('offset', offset);
    if (confianza) params = params.set('confianza', confianza);
    return this.http.get<ListaHallazgos>(`${this.base}/alertas/puerta-giratoria`, { params });
  }

  getPerfil(documento: string): Observable<Perfil> {
    return this.http.get<Perfil>(`${this.base}/perfil/${documento}`);
  }

  getGrafo(nit: string, limit = 40): Observable<GrafoResponse> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<GrafoResponse>(`${this.base}/grafo/entidad/${nit}`, { params });
  }
}
```

---

## 7. Cytoscape.js — Grafo de entidad

### Instalación

```bash
npm install cytoscape
npm install --save-dev @types/cytoscape
# Layout force-directed (opcional pero recomendado)
npm install cytoscape-fcose
npm install --save-dev @types/cytoscape-fcose
```

### Mapeo de la respuesta API → formato Cytoscape

La API devuelve formato vis-network (`from`/`to`). Cytoscape usa `source`/`target`.
El adaptador es una función de una línea por tipo:

```typescript
import { GrafoResponse } from '../models/veridia.models';
import cytoscape from 'cytoscape';

function toCytoscapeElements(grafo: GrafoResponse): cytoscape.ElementDefinition[] {
  const nodes = grafo.nodes.map(n => ({
    data: { id: n.id, label: n.label, group: n.group, value: n.value, title: n.title },
  }));

  const edges = grafo.edges.map((e, i) => ({
    data: {
      id:     `edge_${i}`,
      source: e.from,
      target: e.to,
      value:  e.value,
      title:  e.title,
    },
  }));

  return [...nodes, ...edges];
}
```

### Componente Angular completo

```typescript
// src/app/components/grafo-entidad/grafo-entidad.component.ts
import {
  Component, ElementRef, Input, OnChanges,
  OnDestroy, ViewChild, inject
} from '@angular/core';
import { VeridiaService } from '../../services/veridia.service';
import { GrafoResponse } from '../../models/veridia.models';
import cytoscape from 'cytoscape';
// @ts-ignore — fcose no tiene tipos oficiales completos
import fcose from 'cytoscape-fcose';

cytoscape.use(fcose);

@Component({
  selector: 'app-grafo-entidad',
  standalone: true,
  template: `
    <div class="relative w-full h-full">
      <div #cytoscapeContainer class="w-full h-full rounded-lg bg-gray-900"></div>

      <div *ngIf="meta" class="absolute top-3 left-3 bg-white/90 rounded p-2 text-xs shadow">
        <p class="font-semibold">{{ meta.entidad }}</p>
        <p class="text-gray-500">{{ meta.total_contratistas }} proveedores</p>
        <p class="text-red-600" *ngIf="meta.alertas_rojo">
          🔴 {{ meta.alertas_rojo }} inhabilitados
        </p>
        <p class="text-orange-500" *ngIf="meta.alertas_naranja">
          🟠 {{ meta.alertas_naranja }} multados
        </p>
      </div>

      <div *ngIf="loading" class="absolute inset-0 flex items-center justify-center">
        <span class="text-white animate-pulse">Cargando grafo...</span>
      </div>
    </div>
  `,
})
export class GrafoEntidadComponent implements OnChanges, OnDestroy {
  @Input() nit!: string;
  @Input() limit = 40;
  @ViewChild('cytoscapeContainer', { static: true }) container!: ElementRef<HTMLDivElement>;

  private readonly svc = inject(VeridiaService);
  private cy?: cytoscape.Core;

  loading = false;
  meta?: GrafoResponse['meta'];

  ngOnChanges() {
    if (this.nit) this.loadGraph();
  }

  ngOnDestroy() {
    this.cy?.destroy();
  }

  private loadGraph() {
    this.loading = true;
    this.svc.getGrafo(this.nit, this.limit).subscribe({
      next: (grafo) => {
        this.meta = grafo.meta;
        this.renderCytoscape(grafo);
        this.loading = false;
      },
      error: () => { this.loading = false; },
    });
  }

  private renderCytoscape(grafo: GrafoResponse) {
    this.cy?.destroy();

    this.cy = cytoscape({
      container: this.container.nativeElement,
      elements:  toCytoscapeElements(grafo),

      style: CYTOSCAPE_STYLE,

      layout: {
        name:          'fcose',
        animate:       true,
        animationDuration: 600,
        nodeRepulsion: 8000,
        idealEdgeLength: 120,
      } as any,
    });

    // Tooltip al hacer hover
    this.cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      const tip = document.getElementById('cy-tooltip')!;
      tip.innerHTML = node.data('title');
      tip.style.display = 'block';
    });

    this.cy.on('mouseout', 'node', () => {
      const tip = document.getElementById('cy-tooltip');
      if (tip) tip.style.display = 'none';
    });

    // Click en nodo contratista → navegar al perfil
    this.cy.on('tap', 'node[group != "entidad"]', (evt) => {
      const doc = evt.target.id().replace('c_', '');
      // this.router.navigate(['/veridia/perfil', doc]);
    });
  }
}

// ── Estilos Cytoscape ─────────────────────────────────────────────────────────

const NODE_SIZE = 'mapData(value, 1, 100, 30, 80)';

const CYTOSCAPE_STYLE: cytoscape.Stylesheet[] = [
  {
    selector: 'node',
    style: {
      label:           'data(label)',
      'font-size':     10,
      'text-valign':   'bottom',
      'text-margin-y': 4,
      color:           '#fff',
      'text-outline-width': 2,
      'text-outline-color': '#00000088',
      width:           NODE_SIZE,
      height:          NODE_SIZE,
    },
  },
  {
    selector: 'node[group = "entidad"]',
    style: { 'background-color': '#2980b9', shape: 'diamond', width: 80, height: 80 },
  },
  {
    selector: 'node[group = "contratista"]',
    style: { 'background-color': '#27ae60' },
  },
  {
    selector: 'node[group = "sancionado"]',
    style: { 'background-color': '#c0392b' },
  },
  {
    selector: 'node[group = "multado"]',
    style: { 'background-color': '#e67e22' },
  },
  {
    selector: 'node[group = "alto_riesgo"]',
    style: { 'background-color': '#7b241c', 'border-width': 3, 'border-color': '#f1c40f' },
  },
  {
    selector: 'edge',
    style: {
      width:              'mapData(value, 1, 20, 1, 6)',
      'line-color':       '#4a5568',
      'target-arrow-color': '#4a5568',
      'target-arrow-shape': 'triangle',
      'curve-style':      'bezier',
      opacity:            0.6,
    },
  },
  {
    selector: 'node:selected',
    style: { 'border-width': 3, 'border-color': '#f1c40f' },
  },
];

// ── Adaptador API → Cytoscape ─────────────────────────────────────────────────

function toCytoscapeElements(grafo: GrafoResponse): cytoscape.ElementDefinition[] {
  return [
    ...grafo.nodes.map(n => ({
      data: { id: n.id, label: n.label, group: n.group, value: n.value, title: n.title },
    })),
    ...grafo.edges.map((e, i) => ({
      data: { id: `edge_${i}`, source: e.from, target: e.to, value: e.value, title: e.title },
    })),
  ];
}
```

### Uso del componente

```html
<!-- En el template del módulo Veridia -->
<div class="h-[600px] w-full">
  <app-grafo-entidad
    [nit]="entidadSeleccionada.nit"
    [limit]="50">
  </app-grafo-entidad>
</div>
```

### Leyenda de colores

| Color | Grupo Cytoscape | Significado |
|---|---|---|
| Azul diamante | `entidad` | La entidad pública consultada |
| Verde | `contratista` | Proveedor sin alertas |
| Rojo | `sancionado` | Inhabilitado por la Procuraduría (SIRI) |
| Naranja | `multado` | Multado en SECOP I |
| Granate + borde amarillo | `alto_riesgo` | Inhabilitado **y** multado |

---

## 8. Notas de compatibilidad

### Por qué Cytoscape y no vis-network

- `vis-network` no tiene tipos TypeScript oficiales y el bundle es más pesado.
- `cytoscape` + `fcose` layout es más fluido para grafos de 50-100 nodos.
- Estilos más controlables con CSS-like selectors.

### Corrección al FRONTEND.md anterior

El `FRONTEND.md` describe eventos SSE que **no existen** en la implementación actual:

| Evento en doc antigua | Estado real |
|---|---|
| `text_delta`  | ❌ No existe — el texto llega completo en `answer` |
| `table`       | ❌ No existe |
| `tool_call`   | ✅ Existe, mismo nombre |
| `tool_result` | ✅ Existe, mismo nombre |
| `chart`       | ✅ Existe, mismo nombre |
| `done`        | ✅ Existe, campos distintos — ver sección 5 |

El agente actual no hace streaming de texto carácter por carácter (no hay `text_delta`).
El texto final llega completo en el evento `answer`. Si se necesita streaming de texto, coordinarlo con backend.

### Tooltip en Cytoscape

El campo `title` de cada nodo contiene HTML (etiquetas `<b>`, `<span style="color:...">` generado por el backend).
Necesitas un div flotante externo, no el tooltip nativo del browser:

```html
<!-- En el template del componente padre -->
<div id="cy-tooltip"
     class="hidden fixed z-50 bg-white shadow rounded p-2 text-xs max-w-xs pointer-events-none"
     [innerHTML]="tooltipHtml | safeHtml">
</div>
```

Usar `DomSanitizer` con pipe `safeHtml` para evitar XSS — el contenido viene de tu propio backend, pero es buena práctica.

### `fcose` en SSR / Angular Universal

Si el proyecto usa SSR, importa Cytoscape solo en el browser:

```typescript
if (isPlatformBrowser(this.platformId)) {
  const { default: cytoscape } = await import('cytoscape');
  const { default: fcose } = await import('cytoscape-fcose');
  cytoscape.use(fcose);
  // ... renderizar
}
```

---

*Generado: 2026-05-09 · Backend branch: `feature/architecture`*
