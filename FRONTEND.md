# Especificación del Frontend · Agente IA SECOP

> **Audiencia:** quien implemente el frontend del módulo IA.
> **Versión:** v1 · **Fecha:** 2026-05-08
> **No es responsabilidad de este desarrollador (módulo IA backend).**
> Este documento es el **contrato** que el frontend debe cumplir para
> integrarse con el agente.

---

## 0. Contexto

El proyecto ya tiene un frontend Angular 17 funcionando en
`hackathon5.0/frontend/` con:

- **Angular 17.2** (standalone components)
- **Tailwind CSS 3.4**
- **Chart.js 4.4** vía **ng2-charts 5.0**
- **JWT auth** con interceptor (`auth.interceptor.ts`)
- **Layout** ya armado: login + dashboard con tabs "records" / "analytics"
- **Runtime config** vía `window.__env.BACKEND_URL` (default: `/api`)

**No cambies el stack.** Reutilízalo. Chart.js (no Plotly) por consistencia.

---

## 1. Objetivo

Agregar al dashboard una **sección de chat** que permita al usuario
hacer preguntas en lenguaje natural sobre los datasets SECOP, y
mostrar:

1. Las **respuestas en texto** del agente.
2. Los **gráficos** que el agente decida generar (usando Chart.js).
3. Las **queries SoQL** que el agente ejecutó (transparencia).
4. Los **resultados tabulares** cuando aplique.

---

## 2. Endpoints que vas a consumir

> Todos requieren `Authorization: Bearer <token>` que el interceptor ya
> añade automáticamente.

### 2.1 `POST /ai/chat` — respuesta no-streaming (modo simple)

**Request:**
```json
{
  "message": "¿Cuál es el contrato más caro firmado en 2026?",
  "conversation_id": null
}
```

**Response (200):**
```json
{
  "conversation_id": "uuid-v4",
  "answer": "El contrato más caro de 2026 es...",
  "tool_calls": [
    {
      "tool": "query_secop",
      "input": {"select": "...", "where": "..."},
      "soql_url": "https://www.datos.gov.co/resource/jbjy-vk9h.json?$select=...",
      "result_summary": "1 fila devuelta"
    }
  ],
  "charts": [
    {
      "id": "chart_1",
      "chart_js_spec": {
        "type": "bar",
        "data": { "labels": [...], "datasets": [...] },
        "options": { "responsive": true, ... }
      }
    }
  ],
  "tables": [
    {
      "id": "table_1",
      "columns": ["id_contrato", "valor_del_contrato", "entidad"],
      "rows": [["...", "...", "..."], ...]
    }
  ],
  "usage": { "input_tokens": 1234, "output_tokens": 567 },
  "latency_ms": 4200
}
```

### 2.2 `POST /ai/chat/stream` — Server-Sent Events (modo recomendado)

**Request:** mismo body que `/ai/chat`.
**Response:** `text/event-stream` con eventos:

```
event: text_delta
data: {"text": "El contrato"}

event: text_delta
data: {"text": " más caro"}

event: tool_call
data: {"tool": "query_secop", "input": {...}, "soql_url": "..."}

event: tool_result
data: {"tool": "query_secop", "rows": 1, "summary": "..."}

event: chart
data: {"id": "chart_1", "chart_js_spec": {...}}

event: table
data: {"id": "table_1", "columns": [...], "rows": [...]}

event: done
data: {"conversation_id": "...", "usage": {...}, "latency_ms": 4200}
```

### 2.3 `GET /ai/datasets` — schema de datasets disponibles

```json
[
  {
    "id": "jbjy-vk9h",
    "name": "SECOP – Contratos",
    "fields": [
      {"name": "id_contrato", "type": "string"},
      {"name": "valor_del_contrato", "type": "number"},
      ...
    ]
  },
  {
    "id": "dmgg-8hin",
    "name": "SECOP – Documentos",
    "fields": [...]
  }
]
```

(Útil para mostrar al usuario qué dataset están consultando o para
sugerencias de preguntas.)

### 2.4 `GET /ai/conversations` — historial del usuario

```json
[
  {
    "conversation_id": "uuid-1",
    "title": "Contrato más caro 2026",
    "first_message": "...",
    "last_message_at": "2026-05-08T14:30:00Z",
    "message_count": 4
  }
]
```

### 2.5 `GET /ai/conversations/{id}` — mensajes de una conversación

```json
{
  "conversation_id": "uuid-1",
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "charts": [...], "tool_calls": [...], "timestamp": "..."}
  ]
}
```

---

## 3. Componentes a implementar

```
src/app/features/ai-chat/
├── ai-chat.component.ts           ← contenedor principal
├── ai-chat.component.html
├── ai-chat.component.css          (o tailwind classes)
├── components/
│   ├── chat-input/
│   │   └── chat-input.component.ts        ← textarea + botón enviar
│   ├── message-bubble/
│   │   └── message-bubble.component.ts    ← bubble user / assistant
│   ├── tool-trace/
│   │   └── tool-trace.component.ts        ← muestra "ejecutando query…" + SoQL
│   ├── chart-card/
│   │   └── chart-card.component.ts        ← envuelve ng2-charts BaseChartDirective
│   ├── table-card/
│   │   └── table-card.component.ts        ← tabla con scroll
│   └── conversations-sidebar/
│       └── conversations-sidebar.component.ts  ← lista de conversaciones
└── services/
    └── ai-agent.service.ts        ← cliente HTTP + SSE
```

### 3.1 `AiAgentService` (servicio core)

```typescript
@Injectable({ providedIn: 'root' })
export class AiAgentService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(RUNTIME_CONFIG);

  sendMessage(message: string, conversationId: string | null): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(
      `${this.config.backendUrl}/ai/chat`,
      { message, conversation_id: conversationId }
    );
  }

  sendMessageStream(message: string, conversationId: string | null): Observable<StreamEvent> {
    return new Observable(observer => {
      const url = `${this.config.backendUrl}/ai/chat/stream`;
      const eventSource = new EventSource(url, { withCredentials: true });
      // … emitir eventos por cada `event:` recibido
    });
  }

  getDatasets(): Observable<DatasetInfo[]> { ... }
  getConversations(): Observable<ConversationSummary[]> { ... }
  getConversation(id: string): Observable<ConversationDetail> { ... }
}
```

> ⚠️ **`EventSource` no soporta `POST` ni headers personalizados.** Hay
> 2 opciones:
>
> 1. **`fetch` API con streaming** (recomendado) — permite POST + headers
>    `Authorization`. Lee con `ReadableStream` y parsea el formato SSE
>    manualmente. Hay librerías helpers: `@microsoft/fetch-event-source`.
> 2. **GET con token en query param** — usar `EventSource` directo pero
>    pasando el JWT como `?token=...`. Menos seguro (queda en logs del
>    servidor).
>
> Recomendación: usar **`@microsoft/fetch-event-source`**:
> ```bash
> npm install @microsoft/fetch-event-source
> ```

### 3.2 `<chart-card>` — renderiza Chart.js spec

El backend devuelve un `chart_js_spec` con la forma exacta que espera
`ng2-charts` (`type`, `data`, `options`). Solo hay que pasarlo:

```html
<canvas baseChart
        [data]="spec.data"
        [options]="spec.options"
        [type]="spec.type">
</canvas>
```

```typescript
@Component({
  selector: 'app-chart-card',
  standalone: true,
  imports: [NgChartsModule],
  template: `
    <div class="bg-white rounded-lg shadow p-4">
      <h3 class="text-sm font-semibold mb-2">{{ spec.title }}</h3>
      <div class="h-64">
        <canvas baseChart [data]="spec.data" [options]="spec.options" [type]="spec.type"></canvas>
      </div>
    </div>
  `
})
export class ChartCardComponent {
  @Input() spec!: ChartJsSpec;
}
```

### 3.3 `<tool-trace>` — transparencia (gana puntos con jurado)

Muestra la SoQL ejecutada, colapsable:

```html
<div class="border-l-4 border-emerald-500 bg-emerald-50 pl-3 py-2 text-xs font-mono">
  <button (click)="expanded = !expanded" class="flex items-center gap-1">
    <span>🔍</span>
    <span class="font-semibold">{{ tool.tool }}</span>
    <span class="text-gray-500">({{ tool.result_summary }})</span>
  </button>
  <pre *ngIf="expanded" class="mt-2 overflow-x-auto">{{ tool.soql_url }}</pre>
</div>
```

---

## 4. Layout sugerido

```
┌──────────────────────────────────────────────────────────────────┐
│ Dashboard · header existente (logout, etc.)                      │
├──────────────────────────────────────────────────────────────────┤
│ Tabs: [ Records ] [ Analytics ] [ AI Chat ]   ← agregar tab      │
├──────────────────────────────────────────────────────────────────┤
│ ┌────────────┐  ┌────────────────────────────────────────────┐  │
│ │ Conversa-  │  │ Mensajes ↓                                 │  │
│ │ ciones     │  │  ┌─ user ─────────────────────┐             │  │
│ │ ── chat 1  │  │  │ ¿Contrato más caro 2026?   │             │  │
│ │ ── chat 2  │  │  └─────────────────────────────┘             │  │
│ │ ── chat 3  │  │  ┌─ assistant ───────────────┐               │  │
│ │            │  │  │ 🔍 query_secop (1 fila)   │               │  │
│ │ + Nueva    │  │  │                            │               │  │
│ │            │  │  │ El contrato más caro es… │               │  │
│ │            │  │  │ ┌────────────────────────┐│               │  │
│ │            │  │  │ │ <chart-card> bar       ││               │  │
│ │            │  │  │ └────────────────────────┘│               │  │
│ │            │  │  └────────────────────────────┘               │  │
│ │            │  │                                              │  │
│ └────────────┘  │  ─────────── input ──────────                │  │
│                 │  [ Pregúntale al agente…       ] [ Enviar ]  │  │
│                 └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Comportamiento

- Al enviar mensaje:
  - Mostrar inmediatamente la burbuja del usuario.
  - Aparecer "indicador de escribiendo" (3 puntos).
  - Recibir `text_delta` → ir concatenando texto en la burbuja del asistente.
  - Recibir `tool_call` → mostrar `<tool-trace>` con animación pulsante.
  - Recibir `tool_result` → cambiar el `<tool-trace>` a estado "completado".
  - Recibir `chart` → insertar `<chart-card>` debajo del texto.
  - Recibir `done` → quitar indicador, habilitar el input.
- Al hacer click en una conversación del sidebar: cargar mensajes.
- Botón "Nueva conversación" → resetea el estado y `conversation_id = null`.

---

## 5. Cambios mínimos necesarios en el código existente

### 5.1 `package.json`

```bash
npm install @microsoft/fetch-event-source
```

### 5.2 `app.routes.ts` o tab dentro de `dashboard`

**Opción A:** nueva ruta protegida.
```typescript
{ path: 'chat', component: AiChatComponent, canActivate: [authGuard] }
```

**Opción B (recomendada):** tab dentro del dashboard existente. Solo
agregar al template:
```html
<button (click)="setTab('chat')">AI Chat</button>
<app-ai-chat *ngIf="activeTab === 'chat'"></app-ai-chat>
```

### 5.3 `proxy.conf.json`

No requiere cambio si el backend AI vive en la misma API (`:8000`). El
proxy `/api → :8000` ya cubre los nuevos endpoints `/ai/*`.

---

## 6. Estados de UI a manejar

| Estado | UI |
|---|---|
| Loading inicial | Skeleton de mensaje + tool-trace pulsante |
| Tool ejecutándose | Trace en estado `running` con spinner |
| Tool falló | Trace en rojo con mensaje de error |
| Sin internet | Toast "Sin conexión" + reintentar |
| Token expirado | Redirect a `/login` (ya lo hace el interceptor) |
| Mensaje muy largo | Botón "Ver más" colapsable |
| Gráfico no se puede renderizar | Fallback a tabla de datos |

---

## 7. Detalles técnicos importantes

### 7.1 Streaming con `fetch-event-source`

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource(`${this.config.backendUrl}/ai/chat/stream`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${this.authService.getToken()}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ message, conversation_id }),
  onmessage(ev) {
    if (ev.event === 'text_delta') { ... }
    if (ev.event === 'tool_call') { ... }
    if (ev.event === 'chart') { ... }
    if (ev.event === 'done') { ... }
  },
  onerror(err) { ... },
});
```

### 7.2 Markdown en respuestas del agente

El agente puede responder con Markdown (negritas, listas, código).
Recomendado: `marked` o `ngx-markdown`:
```bash
npm install ngx-markdown marked
```

### 7.3 Sanitización de HTML

**Nunca** usar `[innerHTML]` con respuestas del agente sin sanitizar.
Usar `DomSanitizer` de Angular.

### 7.4 Persistencia local

- Guardar `conversation_id` en `localStorage` para mantener la conversación
  entre recargas.
- Guardar el último mensaje no enviado en `sessionStorage` (UX nice-to-have).

---

## 8. Criterios de aceptación

- [ ] Usuario puede escribir una pregunta y recibir respuesta del agente.
- [ ] La respuesta llega en streaming (texto aparece progresivamente).
- [ ] Cuando el agente ejecuta un tool, aparece el badge `<tool-trace>`.
- [ ] Cuando el agente devuelve un chart, se renderiza con Chart.js.
- [ ] Click en una conversación del sidebar carga sus mensajes.
- [ ] Botón "Nueva conversación" resetea el estado.
- [ ] El interceptor JWT se aplica automáticamente (sin código extra).
- [ ] Si falla el backend, se muestra toast de error sin romper la app.
- [ ] Mobile-friendly (sidebar colapsable en pantallas <768px).

---

## 9. Lo que NO debes hacer

- ❌ No cambiar a Plotly (mantener Chart.js — el backend manda specs Chart.js).
- ❌ No implementar lógica de tool-use en el frontend (eso vive en el backend).
- ❌ No llamar a la API de Socrata directamente (todo va por el backend).
- ❌ No commitear el `dev-token` ni credenciales reales.
- ❌ No usar `EventSource` nativo con POST (no funciona).

---

## 10. Recursos

- [ng2-charts docs](https://valor-software.com/ng2-charts/)
- [Chart.js samples](https://www.chartjs.org/samples/latest/)
- [@microsoft/fetch-event-source](https://github.com/Azure/fetch-event-source)
- [Tailwind UI patterns](https://tailwindui.com/components/application-ui)
- Mock del API mientras backend no esté listo: usar `MirageJS` o
  `json-server` con responses simuladas.

---

## 11. Punto de contacto

Cualquier cambio en los **endpoints** o el **formato de eventos SSE**
debe coordinarse con el desarrollador del módulo IA backend
(este desarrollador). Si necesitas un campo extra en el response,
abre un issue en GitLab con tag `ia-frontend`.
