# Veridia · Guía de integración frontend (documento único)

> **Reemplaza a:** `FRONTEND.md` — este es el único documento de referencia.
> **Audiencia:** equipo frontend Angular del proyecto.
> **Última actualización:** 2026-05-09 · branch `feature/architecture`

---

## Índice

1. [Stack existente y restricciones](#1-stack-existente-y-restricciones)
2. [Configuración base](#2-configuración-base)
3. [Autenticación](#3-autenticación)
4. [Interfaces TypeScript](#4-interfaces-typescript)
5. [Módulo Veridia — endpoints REST](#5-módulo-veridia--endpoints-rest)
6. [Módulo IA — Chat y conversaciones](#6-módulo-ia--chat-y-conversaciones)
7. [Servicios Angular](#7-servicios-angular)
8. [Componentes a implementar](#8-componentes-a-implementar)
9. [Cytoscape.js — Grafo de entidad](#9-cytoscapejs--grafo-de-entidad)
10. [Layout y comportamiento](#10-layout-y-comportamiento)
11. [Patrones de UI](#11-patrones-de-ui)
12. [Estados de UI a manejar](#12-estados-de-ui-a-manejar)
13. [Notas técnicas](#13-notas-técnicas)
14. [Criterios de aceptación](#14-criterios-de-aceptación)
15. [Lo que NO debes hacer](#15-lo-que-no-debes-hacer)

---

## 1. Stack existente y restricciones

El frontend ya está en `hackathon5.0/frontend/` con:

- **Angular 17.2** — standalone components
- **Tailwind CSS 3.4**
- **Chart.js 4.4** vía **ng2-charts 5.0** — no cambiar a Plotly
- **JWT auth** con interceptor existente (`auth.interceptor.ts`)
- **Layout** armado: login + dashboard con tabs `records` / `analytics`
- **Runtime config** vía `window.__env.BACKEND_URL` (default: `/api`)

**No cambies el stack.** Los nuevos módulos se integran dentro de este proyecto.

**Dependencias nuevas a instalar:**

```bash
# Grafo relacional
npm install cytoscape cytoscape-fcose
npm install --save-dev @types/cytoscape

# Markdown en respuestas del agente (opcional pero recomendado)
npm install ngx-markdown marked
```

No se necesita `@microsoft/fetch-event-source` — el streaming SSE se implementa con `fetch` nativo.

---

## 2. Configuración base

```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
};

// src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: (window as any).__env?.BACKEND_URL ?? 'https://gludsitohackathon5back.glud.org',
};
```

### Prefijos de rutas

| Módulo          | Prefijo    | Auth |
|-----------------|------------|------|
| Autenticación   | `/auth`    | ❌   |
| Agente IA       | `/ai`      | ✅   |
| Veridia alertas | `/veridia` | ✅   |

El interceptor JWT existente añade `Authorization: Bearer <token>` automáticamente a todas las rutas. No es necesario código extra en ningún servicio.

### proxy.conf.json (dev)

No requiere cambio — el proxy `/api → :8000` ya cubre `/ai/*` y `/veridia/*`.

---

## 3. Autenticación

```http
POST /auth/login
Content-Type: application/json

{ "username": "admin", "password": "admin123" }
```

**Respuesta 200:**
```json
{ "access_token": "eyJhbGci...", "token_type": "bearer" }
```

Guardar `access_token` en `localStorage`. El interceptor ya lo lee de ahí.

**Persistencia de sesión recomendada:**
```typescript
localStorage.setItem('token', data.access_token);
localStorage.setItem('conversation_id', convId); // para retomar entre recargas
```

---

## 4. Interfaces TypeScript

Crea `src/app/models/veridia.models.ts`:

```typescript
// ── Auth ──────────────────────────────────────────────────────────────────────

export interface LoginRequest  { username: string; password: string; }
export interface LoginResponse { access_token: string; token_type: string; }

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface AlertaResumen {
  total_personas?:     number;
  total_contratistas?: number;
  total_contratos:     number;
  valor_total_cop:     number;
  interpretacion?:     string;
}

export interface Dashboard {
  sancionados_activos: AlertaResumen & { interpretacion: string };
  multados_activos:    AlertaResumen & { interpretacion: string };
  puerta_giratoria:    AlertaResumen & { interpretacion: string; nota: string };
  disponibilidad_datasets: Record<'contratos'|'siri'|'multas'|'patrimonio', boolean>;
}

// ── Hallazgos ─────────────────────────────────────────────────────────────────

export interface HallazgoSancionado {
  documento:            string;
  nombre_sancionado:    string;
  sanciones:            string;
  entidad_sancionado:   string;
  autoridad:            string;
  fecha_inicio_sancion: string;
  fecha_fin_sancion:    string | null;
  duracion_anos:        number;
  id_contrato:          string;
  fecha_de_firma:       string;
  valor_contrato:       number;
  proveedor_adjudicado: string;
  nombre_entidad:       string;
  nit_entidad:          string;
  tipo_de_contrato:     string;
  estado_contrato:      string;
  confianza:            'alta' | 'media';
  url_secop:            string; // enlace verificable a datos.gov.co
}

export interface HallazgoMultado {
  documento:           string;
  nombre_contratista:  string;
  valor_sancion:       number;
  entidad_que_multo:   string;
  numero_de_resolucion: string;
  fecha_multa:         string;
  url_evidencia:       string; // enlace al expediente de la multa
  id_contrato:         string;
  fecha_de_firma:      string;
  valor_contrato:      number;
  entidad_contratante: string;
  nit_entidad:         string;
  tipo_de_contrato:    string;
  estado_contrato:     string;
  confianza:           'alta';
}

export interface HallazgoPuerta {
  documento:                 string;
  nombre_declarante:         string;
  cargo_declarante:          string;
  entidad_donde_trabaja:     string;
  tipo_declaracion:          string;
  fecha_declaracion:         string;
  participa_en_sociedades:   string;
  id_contrato:               string;
  fecha_de_firma:            string;
  valor_contrato:            number;
  entidad_contratante:       string;
  nit_entidad:               string;
  tipo_de_contrato:          string;
  modalidad_de_contratacion: string;
  confianza:                 'alta' | 'media';
}

export interface ListaHallazgos<T> {
  hallazgos:    T[];
  limit:        number;
  offset:       number;
  total_pagina: number;
}

// ── Perfil ────────────────────────────────────────────────────────────────────

export type NivelAlerta = 'rojo' | 'naranja' | 'amarillo' | 'verde';

export interface Perfil {
  documento:    string;
  nivel_alerta: NivelAlerta;
  secop?: {
    total_contratos: number;
    valor_total_cop: number;
    contratos: {
      id_contrato: string; nombre_entidad: string; nit_entidad: string;
      fecha_de_firma: string; valor: number; tipo_de_contrato: string;
      estado_contrato: string; proveedor_adjudicado: string;
    }[];
  };
  siri:       any[];
  multas:     any[];
  patrimonio: any[];
}

// ── Grafo ─────────────────────────────────────────────────────────────────────

export type NodeGroup = 'entidad'|'contratista'|'sancionado'|'multado'|'alto_riesgo';

export interface GrafoNode  { id: string; label: string; group: NodeGroup; value: number; title: string; }
export interface GrafoEdge  { from: string; to: string; value: number; title: string; }
export interface GrafoResponse {
  nodes: GrafoNode[];
  edges: GrafoEdge[];
  meta:  { entidad: string; nit: string; total_contratistas: number; alertas_rojo: number; alertas_naranja: number; };
}

// ── Chat / IA ─────────────────────────────────────────────────────────────────

export interface ChatRequest  { message: string; conversation_id: string | null; }

export interface ToolCallLog  { tool: string; input: Record<string,any>; result_summary: string; soql_url?: string; }
export interface ChartItem    { id: string; title: string; chart_js_spec: any; }
export interface ChatUsage    { input_tokens: number; output_tokens: number; }

export interface ChatResponse {
  conversation_id: string;
  answer:          string;
  tool_calls:      ToolCallLog[];
  charts:          ChartItem[];
  usage:           ChatUsage;
  latency_ms:      number;
}

export interface ConversationSummary {
  conversation_id: string;
  title:           string;
  created_at?:     string;
  updated_at?:     string;
}

export interface ConversationDetail {
  conversation_id: string;
  title:           string;
  messages:        { role: string; content: string; tool_calls?: ToolCallLog[]; charts?: ChartItem[]; }[];
  created_at?:     string;
  updated_at?:     string;
}

export interface DatasetField { name: string; type: string; }
export interface DatasetInfo  { id: string; name: string; fields: DatasetField[]; }

// ── SSE ───────────────────────────────────────────────────────────────────────

export type SseEventType = 'init'|'thinking'|'tool_call'|'tool_result'|'chart'|'answer'|'done'|'error';

export interface SseEvent {
  type:             SseEventType;
  conversation_id?: string;          // init, done
  iteration?:       number;          // thinking
  tool?:            string;          // tool_call, tool_result
  args?:            Record<string,any>; // tool_call
  summary?:         string;          // tool_result
  chart?:           ChartItem;       // chart
  text?:            string;          // answer
  usage?:           ChatUsage;       // done
  latency_ms?:      number;          // done
  detail?:          string;          // error
}
```

---

## 5. Módulo Veridia — endpoints REST

### 5.1 Dashboard global

```
GET /veridia/dashboard
```

KPIs de los tres tipos de alerta + disponibilidad de datasets. Llamar al montar el módulo.

**Respuesta:**
```json
{
  "sancionados_activos": {
    "total_personas": 14, "total_contratos": 27, "valor_total_cop": 1234567890,
    "interpretacion": "14 personas con inhabilitación vigente firmaron 27 contratos..."
  },
  "multados_activos": {
    "total_contratistas": 8, "total_contratos": 19, "valor_total_cop": 987654321,
    "interpretacion": "8 contratistas sancionados siguieron recibiendo 19 contratos..."
  },
  "puerta_giratoria": {
    "total_personas": 312, "total_contratos": 580, "valor_total_cop": 45678901234,
    "interpretacion": "312 personas con declaración patrimonial aparecen como contratistas...",
    "nota": "Filtrar por confianza='alta' para casos verificados."
  },
  "disponibilidad_datasets": { "contratos": true, "siri": true, "multas": true, "patrimonio": true }
}
```

### 5.2 Sancionados activos (🔴 Rojo)

Personas con **inhabilitación SIRI vigente** que firmaron contratos durante ese período.

```
GET /veridia/alertas/sancionados/resumen
GET /veridia/alertas/sancionados?limit=50&offset=0
```

**Hallazgo de ejemplo:**
```json
{
  "documento": "12345678",
  "nombre_sancionado": "JUAN CARLOS PÉREZ GÓMEZ",
  "sanciones": "INHABILIDAD GENERAL",
  "fecha_inicio_sancion": "2023-03-15",
  "fecha_fin_sancion": "2033-03-15",
  "duracion_anos": 10,
  "id_contrato": "CO1.BDOS.123456",
  "fecha_de_firma": "01/20/2025",
  "valor_contrato": 48000000,
  "nombre_entidad": "GOBERNACIÓN DE LA GUAJIRA",
  "nit_entidad": "800099780",
  "confianza": "alta",
  "url_secop": "https://www.datos.gov.co/resource/jbjy-vk9h.json?$where=id_contrato='CO1.BDOS.123456'"
}
```

**UI:** mostrar `url_secop` como botón **"Verificar en SECOP"** que abre en nueva pestaña.

### 5.3 Multados activos (🟠 Naranja)

Contratistas con **multa SECOP I** que continuaron contratando después.

```
GET /veridia/alertas/multados/resumen
GET /veridia/alertas/multados?limit=50&offset=0
```

**Hallazgo de ejemplo:**
```json
{
  "documento": "900123456",
  "nombre_contratista": "EMPRESA XYZ S.A.S",
  "valor_sancion": 15000000,
  "entidad_que_multo": "INVIAS",
  "fecha_multa": "2022-06-10",
  "url_evidencia": "https://www.datos.gov.co/...",
  "valor_contrato": 250000000,
  "entidad_contratante": "MINISTERIO DE TRANSPORTE",
  "confianza": "alta"
}
```

**UI:** mostrar `url_evidencia` como **"Ver expediente de multa"**.

### 5.4 Puerta giratoria (🟡 Amarillo)

Funcionarios que declaran patrimonio en una entidad y luego aparecen como contratistas de esa misma entidad.

```
GET /veridia/alertas/puerta-giratoria/resumen
GET /veridia/alertas/puerta-giratoria?limit=50&offset=0&confianza=alta
```

`confianza=alta` → entidad coincide exactamente (recomendado para la vista por defecto).

**Hallazgo de ejemplo:**
```json
{
  "documento": "52456789",
  "nombre_declarante": "MARÍA ANDREA TORRES SILVA",
  "cargo_declarante": "Directora de Contratación",
  "entidad_donde_trabaja": "ALCALDÍA DE BOGOTÁ",
  "fecha_declaracion": "2024-08-01",
  "valor_contrato": 180000000,
  "entidad_contratante": "ALCALDÍA DE BOGOTÁ",
  "modalidad_de_contratacion": "Contratación Directa",
  "confianza": "alta"
}
```

### 5.5 Perfil unificado

Toda la información de una persona o empresa en un solo llamado.

```
GET /veridia/perfil/{documento}
```

`documento` = solo dígitos, sin puntos ni guiones.

**Respuesta:**
```json
{
  "documento": "12345678",
  "nivel_alerta": "rojo",
  "secop": {
    "total_contratos": 5,
    "valor_total_cop": 320000000,
    "contratos": [{ "id_contrato": "...", "nombre_entidad": "...", "valor": 48000000 }]
  },
  "siri": [{ "sanciones": "INHABILIDAD GENERAL", "fecha_inicio": "2023-03-15", "fecha_fin": "2033-03-15", "duracion_anos": 10 }],
  "multas": [],
  "patrimonio": []
}
```

**`nivel_alerta`:**

| Valor | Color | Significado |
|-------|-------|-------------|
| `rojo` | `#c0392b` | Inhabilitado Procuraduría |
| `naranja` | `#e67e22` | Multado SECOP I |
| `amarillo` | `#f39c12` | Posible puerta giratoria |
| `verde` | `#27ae60` | Sin alertas |

### 5.6 Grafo de entidad

Red de proveedores de una entidad coloreada por nivel de alerta.

```
GET /veridia/grafo/entidad/{nit}?limit=40
```

**Respuesta:**
```json
{
  "nodes": [
    { "id": "e_800099780", "label": "GOBERNACIÓN DE LA GUAJIRA", "group": "entidad", "value": 312, "title": "<b>...</b>" },
    { "id": "c_12345678",  "label": "JUAN CARLOS PÉREZ",         "group": "sancionado", "value": 4, "title": "...<span style='color:#c0392b'>⚠ INHABILITADO SIRI</span>" }
  ],
  "edges": [
    { "from": "e_800099780", "to": "c_12345678", "value": 4, "title": "4 contratos · $192,000,000 COP" }
  ],
  "meta": { "entidad": "GOBERNACIÓN DE LA GUAJIRA", "nit": "800099780", "total_contratistas": 40, "alertas_rojo": 2, "alertas_naranja": 1 }
}
```

> Los edges usan `from`/`to`. Para Cytoscape.js mapear a `source`/`target`. Ver sección 9.

---

## 6. Módulo IA — Chat y conversaciones

### 6.1 POST /ai/chat — respuesta bloqueante

```http
POST /ai/chat
Content-Type: application/json

{ "message": "Analiza los contratos de la Gobernación de La Guajira", "conversation_id": null }
```

**Respuesta 200:**
```json
{
  "conversation_id": "abc-123",
  "answer": "Encontré 2 personas con inhabilitación vigente que firmaron 4 contratos...",
  "tool_calls": [
    { "tool": "check_active_sanctions", "input": {"entity_name": "Guajira"}, "result_summary": "4 contratos detectados", "soql_url": null }
  ],
  "charts": [
    { "id": "chart_1", "title": "Contratos irregulares", "chart_js_spec": { "type": "bar", "data": {...}, "options": {...} } }
  ],
  "usage": { "input_tokens": 1800, "output_tokens": 420 },
  "latency_ms": 38000
}
```

> `soql_url` es `null` para las tools Veridia. Solo se rellena para `query_secop`.

### 6.2 POST /ai/chat/stream — SSE (modo recomendado para la demo)

Mismo body que `/ai/chat`. Responde con `Content-Type: text/event-stream`.

#### Herramientas del agente — qué verás en `tool_call`

| `tool` | Qué hace | Alerta |
|--------|----------|--------|
| `get_alert_summary` | KPIs globales | — |
| `check_active_sanctions` | Inhabilitados SIRI | 🔴 |
| `check_fines` | Multados SECOP I | 🟠 |
| `check_revolving_door` | Puerta giratoria | 🟡 |
| `get_person_profile` | Perfil unificado | Según nivel |
| `query_secop` | SoQL sobre contratos | — |
| `render_chart` | Genera Chart.js spec | — |

#### Secuencia real de eventos

```
data: {"type":"init","conversation_id":"abc-123"}

data: {"type":"thinking","iteration":1}

data: {"type":"tool_call","tool":"check_active_sanctions","args":{"entity_name":"Guajira"}}

data: {"type":"tool_result","tool":"check_active_sanctions","summary":"sancionado_activo: 4 contratos detectados"}

data: {"type":"thinking","iteration":2}

data: {"type":"tool_call","tool":"render_chart","args":{"chart_type":"bar","title":"Contratos irregulares",...}}

data: {"type":"tool_result","tool":"render_chart","summary":"chart chart_abc123"}

data: {"type":"chart","chart":{"id":"chart_abc123","title":"Contratos irregulares","chart_js_spec":{...}}}

data: {"type":"answer","text":"Encontré 2 personas inhabilitadas que firmaron 4 contratos..."}

data: {"type":"done","conversation_id":"abc-123","usage":{"input_tokens":1800,"output_tokens":420},"latency_ms":38000}
```

> **El texto llega completo en `answer`**, no carácter a carácter. No existe `text_delta`.

#### Latencia esperada

El agente hace 1-3 llamadas al LLM. Cada una tarda ~10-20 seg. El total es **30-60 segundos**. Con SSE la pantalla no queda en blanco — los eventos `thinking` y `tool_call` aparecen en tiempo real, lo que crea el efecto visual de razonamiento progresivo.

### 6.3 GET /ai/datasets

```
GET /ai/datasets
```

```json
[
  { "id": "jbjy-vk9h", "name": "SECOP – Contratos", "fields": [{"name":"id_contrato","type":"string"}, ...] },
  { "id": "dmgg-8hin", "name": "SECOP – Documentos", "fields": [...] }
]
```

Útil para sugerencias de preguntas o mostrar qué dataset se está consultando.

### 6.4 GET /ai/conversations

```
GET /ai/conversations
```

```json
[
  { "conversation_id": "abc-123", "title": "Analiza la Gobernación de La Guajira", "created_at": "2026-05-09T14:30:00", "updated_at": "2026-05-09T14:31:00" }
]
```

### 6.5 GET /ai/conversations/{id}

```
GET /ai/conversations/abc-123
```

```json
{
  "conversation_id": "abc-123",
  "title": "Analiza la Gobernación de La Guajira",
  "messages": [
    { "role": "user", "content": "Analiza los contratos de la Gobernación de La Guajira" },
    { "role": "assistant", "content": "Encontré 2 personas...", "tool_calls": [...], "charts": [...] }
  ],
  "created_at": "2026-05-09T14:30:00",
  "updated_at": "2026-05-09T14:31:00"
}
```

---

## 7. Servicios Angular

### 7.1 VeridiaService

```typescript
// src/app/services/veridia.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Dashboard, AlertaResumen, ListaHallazgos,
  HallazgoSancionado, HallazgoMultado, HallazgoPuerta,
  Perfil, GrafoResponse,
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
  getSancionados(limit = 50, offset = 0): Observable<ListaHallazgos<HallazgoSancionado>> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<ListaHallazgos<HallazgoSancionado>>(`${this.base}/alertas/sancionados`, { params });
  }

  getMultadosResumen(): Observable<AlertaResumen> {
    return this.http.get<AlertaResumen>(`${this.base}/alertas/multados/resumen`);
  }
  getMultados(limit = 50, offset = 0): Observable<ListaHallazgos<HallazgoMultado>> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<ListaHallazgos<HallazgoMultado>>(`${this.base}/alertas/multados`, { params });
  }

  getPuertaGiratoriaResumen(): Observable<AlertaResumen> {
    return this.http.get<AlertaResumen>(`${this.base}/alertas/puerta-giratoria/resumen`);
  }
  getPuertaGiratoria(limit = 50, offset = 0, confianza?: 'alta'|'media'): Observable<ListaHallazgos<HallazgoPuerta>> {
    let params = new HttpParams().set('limit', limit).set('offset', offset);
    if (confianza) params = params.set('confianza', confianza);
    return this.http.get<ListaHallazgos<HallazgoPuerta>>(`${this.base}/alertas/puerta-giratoria`, { params });
  }

  getPerfil(documento: string): Observable<Perfil> {
    return this.http.get<Perfil>(`${this.base}/perfil/${documento.replace(/\D/g, '')}`);
  }

  getGrafo(nit: string, limit = 40): Observable<GrafoResponse> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<GrafoResponse>(`${this.base}/grafo/entidad/${nit}`, { params });
  }
}
```

### 7.2 AiService (chat bloqueante + historial)

```typescript
// src/app/services/ai.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { ChatRequest, ChatResponse, ConversationSummary, ConversationDetail, DatasetInfo } from '../models/veridia.models';

@Injectable({ providedIn: 'root' })
export class AiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/ai`;

  chat(body: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.base}/chat`, body);
  }

  getDatasets(): Observable<DatasetInfo[]> {
    return this.http.get<DatasetInfo[]>(`${this.base}/datasets`);
  }

  getConversations(): Observable<ConversationSummary[]> {
    return this.http.get<ConversationSummary[]>(`${this.base}/conversations`);
  }

  getConversation(id: string): Observable<ConversationDetail> {
    return this.http.get<ConversationDetail>(`${this.base}/conversations/${id}`);
  }
}
```

### 7.3 AiStreamService (SSE)

```typescript
// src/app/services/ai-stream.service.ts
import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';
import { SseEvent } from '../models/veridia.models';

@Injectable({ providedIn: 'root' })
export class AiStreamService {
  private readonly auth = inject(AuthService);

  // Usa fetch nativo — no necesita @microsoft/fetch-event-source
  async *stream(message: string, conversationId: string | null = null): AsyncGenerator<SseEvent> {
    const response = await fetch(`${environment.apiUrl}/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.auth.getToken()}`,
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop()!;

      for (const part of parts) {
        const line = part.trim();
        if (line.startsWith('data: ')) {
          try { yield JSON.parse(line.slice(6)) as SseEvent; } catch { /* ignorar */ }
        }
      }
    }
  }
}
```

---

## 8. Componentes a implementar

### Estructura de carpetas

```
src/app/features/
├── veridia/
│   ├── veridia.component.ts           ← contenedor con tabs
│   ├── dashboard/
│   │   └── veridia-dashboard.component.ts   ← KPI cards
│   ├── alertas/
│   │   ├── sancionados.component.ts
│   │   ├── multados.component.ts
│   │   └── puerta-giratoria.component.ts
│   ├── perfil/
│   │   └── perfil.component.ts
│   └── grafo/
│       └── grafo-entidad.component.ts  ← Cytoscape.js (ver sección 9)
│
└── ai-chat/
    ├── ai-chat.component.ts            ← contenedor principal
    ├── components/
    │   ├── message-bubble/
    │   │   └── message-bubble.component.ts
    │   ├── tool-trace/
    │   │   └── tool-trace.component.ts
    │   ├── chart-card/
    │   │   └── chart-card.component.ts
    │   └── conversations-sidebar/
    │       └── conversations-sidebar.component.ts
    └── services/   ← ver sección 7
```

### ChartCard — renderiza spec Chart.js del agente

El backend devuelve `chart_js_spec` con el formato exacto que espera `ng2-charts`.

```typescript
@Component({
  selector: 'app-chart-card',
  standalone: true,
  imports: [NgChartsModule],
  template: `
    <div class="bg-white rounded-lg shadow p-4">
      <h3 class="text-sm font-semibold mb-2">{{ spec.title }}</h3>
      <div class="h-64">
        <canvas baseChart
          [data]="spec.chart_js_spec.data"
          [options]="spec.chart_js_spec.options"
          [type]="spec.chart_js_spec.type">
        </canvas>
      </div>
    </div>
  `,
})
export class ChartCardComponent {
  @Input() spec!: ChartItem;
}
```

### ToolTrace — razonamiento visible (clave para la demo)

```typescript
@Component({
  selector: 'app-tool-trace',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="border-l-4 pl-3 py-2 text-xs font-mono transition-colors"
         [class]="step.status === 'running'
           ? 'border-blue-400 bg-blue-50 animate-pulse'
           : 'border-emerald-500 bg-emerald-50'">
      <div class="flex items-center gap-2">
        <span *ngIf="step.status === 'running'" class="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
        <span *ngIf="step.status === 'done'"    class="text-emerald-600">✓</span>
        <span class="font-semibold">{{ TOOL_LABELS[step.tool] ?? step.tool }}</span>
        <span class="text-gray-500" *ngIf="step.summary">— {{ step.summary }}</span>
      </div>
      <pre *ngIf="step.soql_url && expanded"
           class="mt-1 text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap">{{ step.soql_url }}</pre>
      <button *ngIf="step.soql_url" (click)="expanded = !expanded"
              class="text-blue-500 text-xs mt-0.5">
        {{ expanded ? 'Ocultar query' : 'Ver query SoQL' }}
      </button>
    </div>
  `,
})
export class ToolTraceComponent {
  @Input() step!: { tool: string; status: 'running'|'done'; summary: string; soql_url?: string };
  expanded = false;

  readonly TOOL_LABELS: Record<string, string> = {
    get_alert_summary:       '📊 Obteniendo resumen global',
    check_active_sanctions:  '🔴 Verificando inhabilitaciones SIRI',
    check_fines:             '🟠 Verificando multas SECOP I',
    check_revolving_door:    '🟡 Verificando puerta giratoria',
    get_person_profile:      '👤 Construyendo perfil del contratista',
    query_secop:             '🔍 Consultando SECOP II',
    render_chart:            '📈 Generando gráfico',
    lookup_record:           '📄 Buscando contrato',
    cross_datasets:          '🔗 Cruzando datasets',
    text_search:             '🔎 Búsqueda de texto',
  };
}
```

### AiChat — componente principal con SSE

```typescript
@Component({ /* ... */ })
export class AiChatComponent {
  private readonly streamSvc = inject(AiStreamService);
  private readonly aiSvc     = inject(AiService);
  private readonly cdr       = inject(ChangeDetectorRef);

  conversationId: string | null = localStorage.getItem('conversation_id');
  conversations: ConversationSummary[] = [];
  messages: { role: string; content: string; toolSteps?: any[]; charts?: ChartItem[] }[] = [];

  isStreaming = false;
  thinkingLabel = '';
  currentToolSteps: { tool: string; status: 'running'|'done'; summary: string; soql_url?: string }[] = [];
  currentCharts: ChartItem[] = [];
  currentAnswer = '';

  async sendMessage(text: string) {
    if (this.isStreaming || !text.trim()) return;

    this.messages.push({ role: 'user', content: text });
    this.isStreaming = true;
    this.currentToolSteps = [];
    this.currentCharts = [];
    this.currentAnswer = '';

    try {
      for await (const event of this.streamSvc.stream(text, this.conversationId)) {
        switch (event.type) {
          case 'init':
            this.conversationId = event.conversation_id!;
            localStorage.setItem('conversation_id', this.conversationId);
            break;
          case 'thinking':
            this.thinkingLabel = `Pensando (paso ${event.iteration})...`;
            break;
          case 'tool_call':
            this.currentToolSteps.push({ tool: event.tool!, status: 'running', summary: '', soql_url: undefined });
            break;
          case 'tool_result': {
            const s = this.currentToolSteps.findLast(s => s.tool === event.tool);
            if (s) { s.status = 'done'; s.summary = event.summary!; }
            break;
          }
          case 'chart':
            this.currentCharts.push(event.chart!);
            break;
          case 'answer':
            this.currentAnswer = event.text!;
            break;
          case 'done':
            this.messages.push({
              role: 'assistant', content: this.currentAnswer,
              toolSteps: [...this.currentToolSteps], charts: [...this.currentCharts],
            });
            this.isStreaming = false;
            this.loadConversations();
            break;
          case 'error':
            this.messages.push({ role: 'assistant', content: `Error: ${event.detail}` });
            this.isStreaming = false;
            break;
        }
        this.cdr.markForCheck();
      }
    } catch {
      this.messages.push({ role: 'assistant', content: 'Error de conexión con el agente.' });
      this.isStreaming = false;
    }
  }

  loadConversations() {
    this.aiSvc.getConversations().subscribe(c => { this.conversations = c; });
  }

  loadConversation(id: string) {
    this.aiSvc.getConversation(id).subscribe(conv => {
      this.conversationId = id;
      this.messages = conv.messages;
    });
  }

  newConversation() {
    this.conversationId = null;
    this.messages = [];
    localStorage.removeItem('conversation_id');
  }
}
```

---

## 9. Cytoscape.js — Grafo de entidad

### Instalación

```bash
npm install cytoscape cytoscape-fcose
npm install --save-dev @types/cytoscape
```

### Componente completo

```typescript
// src/app/features/veridia/grafo/grafo-entidad.component.ts
import { Component, ElementRef, Input, OnChanges, OnDestroy, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VeridiaService } from '../../../services/veridia.service';
import { GrafoResponse } from '../../../models/veridia.models';
import cytoscape from 'cytoscape';
// @ts-ignore
import fcose from 'cytoscape-fcose';

cytoscape.use(fcose);

@Component({
  selector: 'app-grafo-entidad',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative w-full h-full">
      <div #cy class="w-full h-full rounded-lg bg-gray-900"></div>

      <div *ngIf="meta" class="absolute top-3 left-3 bg-white/90 rounded-lg p-3 text-xs shadow space-y-1">
        <p class="font-semibold">{{ meta.entidad }}</p>
        <p class="text-gray-500">{{ meta.total_contratistas }} proveedores</p>
        <p class="text-red-600 font-medium" *ngIf="meta.alertas_rojo">🔴 {{ meta.alertas_rojo }} inhabilitados</p>
        <p class="text-orange-500 font-medium" *ngIf="meta.alertas_naranja">🟠 {{ meta.alertas_naranja }} multados</p>
      </div>

      <div *ngIf="loading" class="absolute inset-0 flex items-center justify-center bg-gray-900/60 rounded-lg">
        <span class="text-white animate-pulse text-sm">Cargando grafo...</span>
      </div>
    </div>

    <div id="cy-tooltip"
         class="fixed z-50 hidden bg-white shadow-lg rounded p-2 text-xs max-w-xs pointer-events-none border border-gray-200">
    </div>
  `,
})
export class GrafoEntidadComponent implements OnChanges, OnDestroy {
  @Input() nit!: string;
  @Input() limit = 40;
  @ViewChild('cy', { static: true }) container!: ElementRef<HTMLDivElement>;

  private readonly svc = inject(VeridiaService);
  private cy?: cytoscape.Core;

  loading = false;
  meta?: GrafoResponse['meta'];

  ngOnChanges() { if (this.nit) this.load(); }
  ngOnDestroy()  { this.cy?.destroy(); }

  private load() {
    this.loading = true;
    this.svc.getGrafo(this.nit, this.limit).subscribe({
      next: g => { this.meta = g.meta; this.render(g); this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  private render(grafo: GrafoResponse) {
    this.cy?.destroy();
    this.cy = cytoscape({
      container: this.container.nativeElement,
      elements: [
        // Nodos: API → Cytoscape (sin cambios en data)
        ...grafo.nodes.map(n => ({ data: { id: n.id, label: n.label, group: n.group, value: n.value, title: n.title } })),
        // Aristas: from/to (vis-network) → source/target (Cytoscape)
        ...grafo.edges.map((e, i) => ({ data: { id: `edge_${i}`, source: e.from, target: e.to, value: e.value, title: e.title } })),
      ],
      style: CYTOSCAPE_STYLE,
      layout: { name: 'fcose', animate: true, animationDuration: 600, nodeRepulsion: 8000, idealEdgeLength: 120 } as any,
    });

    const tooltip = document.getElementById('cy-tooltip')!;
    this.cy.on('mouseover', 'node', e => { tooltip.innerHTML = e.target.data('title'); tooltip.style.display = 'block'; });
    this.cy.on('mousemove', e => {
      const ev = e.originalEvent as MouseEvent;
      tooltip.style.left = ev.clientX + 12 + 'px';
      tooltip.style.top  = ev.clientY + 12 + 'px';
    });
    this.cy.on('mouseout', 'node', () => { tooltip.style.display = 'none'; });
    this.cy.on('tap', 'node[group != "entidad"]', e => {
      const doc = e.target.id().replace('c_', '');
      // this.router.navigate(['/veridia/perfil', doc]);
    });
  }
}

const CYTOSCAPE_STYLE: cytoscape.Stylesheet[] = [
  { selector: 'node', style: { label: 'data(label)', 'font-size': 10, 'text-valign': 'bottom', 'text-margin-y': 4, color: '#fff', 'text-outline-width': 2, 'text-outline-color': '#00000088', width: 'mapData(value,1,100,30,80)', height: 'mapData(value,1,100,30,80)' } },
  { selector: 'node[group = "entidad"]',     style: { 'background-color': '#2980b9', shape: 'diamond', width: 80, height: 80 } },
  { selector: 'node[group = "contratista"]', style: { 'background-color': '#27ae60' } },
  { selector: 'node[group = "sancionado"]',  style: { 'background-color': '#c0392b' } },
  { selector: 'node[group = "multado"]',     style: { 'background-color': '#e67e22' } },
  { selector: 'node[group = "alto_riesgo"]', style: { 'background-color': '#7b241c', 'border-width': 3, 'border-color': '#f1c40f' } },
  { selector: 'edge', style: { width: 'mapData(value,1,20,1,6)', 'line-color': '#4a5568', 'target-arrow-color': '#4a5568', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', opacity: 0.6 } },
  { selector: 'node:selected', style: { 'border-width': 3, 'border-color': '#f1c40f' } },
];
```

### Uso

```html
<div class="h-[600px] w-full">
  <app-grafo-entidad [nit]="'800099780'" [limit]="50" />
</div>
```

### Leyenda de colores

| Color | `group` | Significado |
|-------|---------|-------------|
| Azul diamante | `entidad` | La entidad pública consultada |
| Verde | `contratista` | Sin alertas |
| Rojo | `sancionado` | Inhabilitado SIRI |
| Naranja | `multado` | Multado SECOP I |
| Granate + borde amarillo | `alto_riesgo` | Inhabilitado y multado |

---

## 10. Layout y comportamiento

```
┌──────────────────────────────────────────────────────────────────┐
│ Dashboard · header (logout, usuario)                             │
├──────────────────────────────────────────────────────────────────┤
│ Tabs: [ Records ] [ Analytics ] [ Veridia ] [ AI Chat ]          │
├──────────────────────────────────────────────────────────────────┤
│ TAB VERIDIA:                                                     │
│  KPI Cards: 🔴 14 inhabilitados  🟠 8 multados  🟡 312 puerta  │
│  Sub-tabs: [ Sancionados ] [ Multados ] [ Puerta giratoria ]     │
│  Tabla paginada de hallazgos + botón "Ver perfil" + "Verificar"  │
│                                                                  │
│ TAB AI CHAT:                                                     │
│ ┌────────────┐  ┌────────────────────────────────────────────┐  │
│ │ Conversa-  │  │ Mensajes                                   │  │
│ │ ciones     │  │  ┌─ user ──────────────────────────┐       │  │
│ │ ── chat 1  │  │  │ Analiza la Gobernación Guajira  │       │  │
│ │ ── chat 2  │  │  └────────────────────────────────┘       │  │
│ │ + Nueva    │  │  ┌─ assistant ────────────────────┐       │  │
│ │            │  │  │ ✓ check_active_sanctions (4)   │       │  │
│ │            │  │  │ ✓ render_chart                  │       │  │
│ │            │  │  │ [chart-card]                    │       │  │
│ │            │  │  │ Encontré 2 personas...          │       │  │
│ │            │  │  └────────────────────────────────┘       │  │
│ │            │  │                                            │  │
│ └────────────┘  │  [ Pregunta al agente... ] [ Enviar ]      │  │
│                 └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Comportamiento del chat:**
- Al enviar: burbuja del usuario aparece inmediatamente
- `thinking` → mostrar label "Pensando (paso N)..."
- `tool_call` → insertar `<tool-trace>` en estado `running` con animación pulsante
- `tool_result` → cambiar `<tool-trace>` a estado `done` con checkmark
- `chart` → insertar `<chart-card>` debajo de los tool-traces
- `answer` → mostrar texto final en la burbuja del asistente
- `done` → deshabilitar spinner, habilitar input, recargar sidebar

**Comportamiento del sidebar:**
- Click en conversación → `loadConversation(id)` reconstruye los mensajes
- Botón "Nueva" → `newConversation()` limpia estado y `localStorage`
- Cargar historial al init: `getConversations()`

---

## 11. Patrones de UI

### Badge de nivel de alerta

```typescript
@Pipe({ name: 'nivelBadge', standalone: true })
export class NivelBadgePipe implements PipeTransform {
  transform(nivel: string) {
    return {
      rojo:     { label: 'INHABILITADO',     cls: 'bg-red-100 text-red-800 border-red-300' },
      naranja:  { label: 'MULTADO',          cls: 'bg-orange-100 text-orange-800 border-orange-300' },
      amarillo: { label: 'PUERTA GIRATORIA', cls: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
      verde:    { label: 'SIN ALERTAS',      cls: 'bg-green-100 text-green-800 border-green-300' },
    }[nivel] ?? { label: nivel, cls: 'bg-gray-100 text-gray-800' };
  }
}
```

```html
<span class="px-2 py-0.5 rounded border text-xs font-semibold"
      [ngClass]="(hallazgo.nivel_alerta | nivelBadge).cls">
  {{ (hallazgo.nivel_alerta | nivelBadge).label }}
</span>
```

### Botón verificar en SECOP (sancionados)

```html
<a [href]="hallazgo.url_secop" target="_blank" rel="noopener noreferrer"
   class="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline">
  ↗ Verificar en SECOP
</a>
```

### Botón ver expediente (multados)

```html
<a [href]="hallazgo.url_evidencia" target="_blank" rel="noopener noreferrer"
   class="inline-flex items-center gap-1 text-xs text-orange-600 hover:underline">
  ↗ Ver expediente de multa
</a>
```

### Formateo de montos COP

```typescript
// En template directamente:
{{ hallazgo.valor_contrato | currency:'COP':'symbol':'1.0-0':'es-CO' }}

// O como método utilitario:
formatCOP = (n: number) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n);
```

---

## 12. Estados de UI a manejar

| Estado | Comportamiento |
|--------|----------------|
| Cargando datos | Skeleton loader en la tabla / KPI cards |
| Tool del agente ejecutándose | `<tool-trace>` pulsante en azul |
| Tool completada | `<tool-trace>` con ✓ en verde |
| Respuesta en proceso | Spinner en el área de respuesta |
| Dataset no disponible | Banner amarillo en el dashboard con qué dataset falta |
| Sin hallazgos | Mensaje "No se encontraron irregularidades para este filtro" |
| Error de red | Toast rojo + botón "Reintentar" |
| Token expirado | Redirect a `/login` (el interceptor ya lo hace) |
| Perfil no encontrado | 404 → "No hay registros para este documento" |

---

## 13. Notas técnicas

### EventSource vs fetch

`EventSource` **no soporta POST** ni headers personalizados — no usarlo para SSE. El `AiStreamService` de la sección 7.3 usa `fetch` nativo con `ReadableStream`. No se necesita ninguna librería extra.

### Markdown en respuestas del agente

El agente puede responder con Markdown (negritas, listas, bloques de código):

```typescript
// app.config.ts
import { provideMarkdown } from 'ngx-markdown';
// ...
provideMarkdown()

// En el template:
<markdown [data]="message.content" />
```

### Sanitización HTML

El `title` de los nodos del grafo contiene HTML generado por el backend (`<b>`, `<span style="...">`). Para `[innerHTML]`:

```typescript
import { DomSanitizer } from '@angular/platform-browser';
const safe = this.sanitizer.bypassSecurityTrustHtml(node.title);
```

Para el resto de respuestas del agente (texto Markdown), usa `<markdown>` en lugar de `[innerHTML]` crudo.

### Cobertura de datos del dataset contratos

Los contratos disponibles cubren **únicamente el año 2025**. SIRI, multas y patrimonio son históricos completos. El agente lo sabe y lo aclara si el usuario pregunta por otros años.

### Cytoscape.js en SSR / Angular Universal

```typescript
if (isPlatformBrowser(this.platformId)) {
  const { default: cy }    = await import('cytoscape');
  const { default: fcose } = await import('cytoscape-fcose');
  cy.use(fcose);
}
```

---

## 14. Criterios de aceptación

- [ ] Usuario puede iniciar sesión y el token se aplica automáticamente
- [ ] Dashboard Veridia muestra los 3 KPIs correctamente
- [ ] Tabla de sancionados carga con paginación y muestra `url_secop` clickeable
- [ ] Tabla de multados muestra `url_evidencia` clickeable
- [ ] Tabla de puerta giratoria filtra por `confianza=alta` por defecto
- [ ] Perfil de persona/empresa muestra `nivel_alerta` con color correcto
- [ ] Grafo de entidad carga con Cytoscape.js, nodos coloreados por grupo
- [ ] Click en nodo del grafo navega al perfil del contratista
- [ ] Chat SSE muestra `<tool-trace>` en tiempo real durante el razonamiento
- [ ] `<chart-card>` renderiza el spec Chart.js devuelto por el agente
- [ ] Sidebar de conversaciones lista y permite retomar conversaciones previas
- [ ] Botón "Nueva conversación" limpia el estado
- [ ] Si falla el backend, se muestra error sin romper la app
- [ ] Mobile-friendly (sidebar colapsable en < 768px)

---

## 15. Lo que NO debes hacer

- ❌ No usar `EventSource` nativo para SSE con POST — no funciona
- ❌ No cambiar Chart.js por Plotly — el backend genera specs Chart.js
- ❌ No implementar lógica de tool-use en el frontend — vive en el backend
- ❌ No llamar a Socrata directamente — todo va por `/veridia/*` y `/ai/*`
- ❌ No commitear tokens ni `.env` con credenciales reales
- ❌ No usar `[innerHTML]` con texto del agente sin sanitizar
- ❌ No confiar en `FRONTEND.md` — está desactualizado, este documento lo reemplaza
