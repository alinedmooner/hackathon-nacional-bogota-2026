import { CommonModule } from '@angular/common';
import {
  AfterViewChecked,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
  inject,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgChartsModule } from 'ng2-charts';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ChartItem } from '../../models/veridia.types';
import { VeridiaStreamService } from '../../services/veridia-stream.service';
import { OnboardingService } from '../../onboarding/onboarding.service';
import { SOACHA_STREAM, TimedSseEvent } from '../../onboarding/onboarding-soacha.mock';

interface ToolCallLog {
  tool: string;
  args: Record<string, unknown>;
  summary: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  tool_calls: ToolCallLog[];
  charts: ChartItem[];
  thinking?: string;
  isStreaming?: boolean;
  latency_ms?: number;
}

@Component({
  selector: 'app-veridia-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, NgChartsModule],
  template: `
    <!-- Backdrop -->
    <div *ngIf="open"
         (click)="requestClose()"
         class="fixed inset-0 z-40 bg-ink/30 backdrop-blur-sm transition-opacity"></div>

    <!-- Slide-over panel -->
    <aside class="fixed right-0 top-0 z-50 flex h-full w-full max-w-[28rem] flex-col bg-cream border-l-4 border-navy shadow-2xl transition-transform duration-300"
           [class.translate-x-0]="open"
           [class.translate-x-full]="!open"
           [attr.aria-hidden]="!open">

      <!-- Header -->
      <header class="flex items-center justify-between gap-3 border-b border-line bg-card px-5 py-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded bg-navy font-editorial text-lg font-semibold text-cream shadow-[inset_0_-2px_0_var(--gold)]">
            V
          </div>
          <div>
            <p class="font-editorial text-base font-semibold text-ink leading-none">
              Verid<span class="text-navy">IA</span>
            </p>
            <p class="eyebrow">Asistente conversacional</p>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <button (click)="newConversation()"
                  title="Nueva conversación"
                  class="rounded border border-line-strong px-2 py-1 text-xs font-medium text-ink-2 transition hover:border-navy hover:text-navy">
            Nueva
          </button>
          <button (click)="requestClose()"
                  title="Cerrar"
                  class="ml-1 rounded px-2 py-1 text-muted transition hover:bg-cream-2 hover:text-ink">
            ✕
          </button>
        </div>
      </header>

      <!-- Mensajes -->
      <div #scrollArea class="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-4 bg-cream">

        <!-- Estado inicial: sugerencias -->
        <div *ngIf="!messages.length"
             class="space-y-3 px-1">
          <div class="rounded border border-line bg-card p-4">
            <p class="font-editorial text-base font-semibold text-ink">
              👋 Pregunta lo que quieras saber
            </p>
            <p class="mt-1 text-sm leading-relaxed text-ink-2">
              VeridIA cruza SECOP con Procuraduría, Contraloría y SIC, y te muestra
              cómo llegó al hallazgo. En español. Sin jerga.
            </p>
          </div>
          <p class="eyebrow px-1">Prueba con</p>
          <button *ngFor="let q of suggestions"
                  (click)="sendSuggestion(q)"
                  class="block w-full rounded border border-line bg-card px-4 py-3 text-left text-sm text-ink-2 transition hover:border-navy hover:bg-cream-3">
            <span class="text-gold-deep mr-1">›</span>{{ q }}
          </button>
        </div>

        <!-- Burbujas -->
        <div *ngFor="let m of messages; trackBy: trackByIdx; let i = index"
             [class.justify-end]="m.role === 'user'"
             class="flex">
          <div [ngClass]="m.role === 'user'
                 ? 'bg-navy text-cream border-navy'
                 : 'bg-card text-ink border-line'"
               class="max-w-[88%] rounded border px-4 py-3">
            <p class="mb-1.5 text-xs uppercase tracking-wider font-semibold"
               [ngClass]="m.role === 'user' ? 'text-cream/70' : 'text-muted'">
              {{ m.role === 'user' ? 'Tú' : 'VeridIA' }}
            </p>

            <!-- Tool calls (badges) -->
            <div *ngIf="m.tool_calls.length" class="mb-2 space-y-1">
              <div *ngFor="let tc of m.tool_calls"
                   class="flex items-center gap-2 rounded border border-ok/40 bg-ok/10 px-2 py-1 text-xs"
                   [class.animate-pulse]="!tc.summary">
                <span class="shrink-0">{{ tc.summary ? '✓' : '◐' }}</span>
                <span class="font-semibold text-ok">{{ TOOL_LABELS[tc.tool] ?? tc.tool }}</span>
                <span *ngIf="tc.summary" class="text-muted">·</span>
                <span *ngIf="tc.summary" class="truncate text-ink-2">{{ tc.summary }}</span>
              </div>
            </div>

            <!-- Indicador thinking -->
            <div *ngIf="m.thinking"
                 class="mb-2 inline-flex items-center gap-2 rounded bg-cream-2 px-2 py-1 text-xs text-ink-2">
              <span class="flex space-x-0.5">
                <span class="h-1 w-1 animate-bounce rounded-full bg-navy"></span>
                <span class="h-1 w-1 animate-bounce rounded-full bg-navy" style="animation-delay: 0.15s"></span>
                <span class="h-1 w-1 animate-bounce rounded-full bg-navy" style="animation-delay: 0.3s"></span>
              </span>
              <span>{{ m.thinking }}</span>
            </div>

            <!-- Texto de respuesta -->
            <p *ngIf="m.text" class="whitespace-pre-wrap text-sm leading-relaxed">{{ m.text }}</p>

            <!-- Charts inline -->
            <div *ngFor="let ch of m.charts"
                 class="mt-3 rounded border border-line bg-cream-2 p-3">
              <p *ngIf="ch.title" class="mb-2 eyebrow">{{ ch.title }}</p>
              <div class="h-48">
                <canvas baseChart
                        [type]="ch.chart_js_spec.type"
                        [data]="ch.chart_js_spec.data"
                        [options]="ch.chart_js_spec.options"></canvas>
              </div>
            </div>

            <!-- Footer (latencia) -->
            <p *ngIf="m.latency_ms" class="mt-2 text-xs"
               [ngClass]="m.role === 'user' ? 'text-cream/50' : 'text-muted'">
              {{ (m.latency_ms / 1000).toFixed(1) }}s
            </p>
          </div>
        </div>

        <!-- Error -->
        <div *ngIf="errorMsg"
             class="rounded border border-err/40 bg-err/10 px-3 py-2 text-sm text-err">
          {{ errorMsg }}
        </div>
      </div>

      <!-- Input -->
      <form (ngSubmit)="send()"
            class="border-t border-line bg-card px-4 py-4">
        <div class="flex gap-2">
          <input type="text"
                 [(ngModel)]="inputText"
                 name="inputText"
                 [disabled]="isStreaming"
                 placeholder="Pregunta lo que quieras saber…"
                 class="flex-1 rounded border border-line-strong bg-cream px-4 py-2.5 text-sm text-ink placeholder-muted focus:border-navy focus:outline-none disabled:opacity-50" />
          <button type="submit"
                  [disabled]="isStreaming || !inputText.trim()"
                  class="btn-primary disabled:cursor-not-allowed disabled:opacity-40">
            <span *ngIf="!isStreaming">Enviar</span>
            <span *ngIf="isStreaming">…</span>
          </button>
        </div>
        <p class="mt-2 text-xs text-muted text-center">
          VeridIA puede cometer errores · Verifica con la fuente oficial
        </p>
      </form>
    </aside>
  `,
})
export class VeridiaChatComponent implements AfterViewChecked, OnInit, OnDestroy {
  @Input() open = false;
  @Output() openChange = new EventEmitter<boolean>();

  @ViewChild('scrollArea') scrollArea?: ElementRef<HTMLDivElement>;

  inputText = '';
  isStreaming = false;
  errorMsg = '';
  messages: ChatMessage[] = [];
  conversationId: string | null = null;

  suggestions = [
    '¿Qué contratistas inhabilitados están firmando contratos ahora?',
    'Muéstrame los 5 ex-funcionarios que volvieron como contratistas',
    '¿Cuál es la entidad pública con más alertas activas?',
    'Resumen de hallazgos de los últimos 30 días',
  ];

  /** Etiqueta humana para cada herramienta del agente — visible en el panel de razonamiento */
  readonly TOOL_LABELS: Record<string, string> = {
    get_alert_summary:      '📊 Obteniendo resumen global',
    check_active_sanctions: '🔴 Verificando inhabilitaciones SIRI',
    check_fines:            '🟠 Verificando multas SECOP I',
    check_revolving_door:   '🟡 Verificando puerta giratoria',
    get_person_profile:     '👤 Construyendo perfil del contratista',
    query_secop:            '🔍 Consultando SECOP II',
    render_chart:           '📈 Generando gráfico',
    lookup_record:          '📄 Buscando contrato',
    cross_datasets:         '🔗 Cruzando datasets',
    text_search:            '🔎 Búsqueda de texto',
  };

  private readonly stream = inject(VeridiaStreamService);
  private readonly onboarding = inject(OnboardingService);
  private readonly cdr = inject(ChangeDetectorRef);
  private shouldScroll = false;
  private readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.onboarding.events$
      .pipe(takeUntil(this.destroy$))
      .subscribe((evt) => {
        switch (evt.kind) {
          case 'open-chat-with-question':
            this.openWithQuestion(evt.text);
            break;
          case 'simulate-stream':
            this.runSimulatedStream();
            break;
          case 'close-chat':
            this.openChange.emit(false);
            break;
          case 'reset':
            this.newConversation();
            break;
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll && this.scrollArea) {
      this.scrollArea.nativeElement.scrollTop = this.scrollArea.nativeElement.scrollHeight;
      this.shouldScroll = false;
    }
  }

  // ── Onboarding helpers ────────────────────────────────────
  private openWithQuestion(text: string): void {
    this.openChange.emit(true);
    this.newConversation();
    // muestra inmediatamente la burbuja del usuario; el stream simulado
    // viene en el siguiente paso del onboarding
    this.messages.push({ role: 'user', text, tool_calls: [], charts: [] });
    this.messages.push({
      role: 'assistant',
      text: '',
      tool_calls: [],
      charts: [],
      thinking: 'Esperando…',
      isStreaming: true,
    });
    this.shouldScroll = true;
    this.cdr.markForCheck();
  }

  private async runSimulatedStream(): Promise<void> {
    const assistant = this.messages[this.messages.length - 1];
    if (!assistant || assistant.role !== 'assistant') return;

    this.isStreaming = true;
    for (const tev of SOACHA_STREAM) {
      await new Promise((r) => setTimeout(r, tev.delay));
      this.applySseEvent(assistant, tev);
      this.shouldScroll = true;
      this.cdr.markForCheck();
    }
    this.isStreaming = false;
    this.cdr.markForCheck();
  }

  private applySseEvent(assistant: ChatMessage, tev: TimedSseEvent): void {
    const ev = tev.event;
    switch (ev.type) {
      case 'init':
        this.conversationId = ev.conversation_id ?? this.conversationId;
        break;
      case 'thinking':
        assistant.thinking = `Razonando · paso ${ev.iteration ?? '?'}`;
        break;
      case 'tool_call':
        assistant.tool_calls.push({ tool: ev.tool ?? 'tool', args: ev.args ?? {}, summary: '' });
        assistant.thinking = `Consultando ${ev.tool}…`;
        break;
      case 'tool_result':
        const last = assistant.tool_calls.slice().reverse().find((t) => t.tool === ev.tool && !t.summary);
        if (last) last.summary = ev.summary ?? 'ok';
        break;
      case 'chart':
        if (ev.chart) assistant.charts.push(ev.chart);
        break;
      case 'answer':
        assistant.text = ev.text ?? '';
        assistant.thinking = undefined;
        break;
      case 'done':
        assistant.isStreaming = false;
        assistant.thinking = undefined;
        assistant.latency_ms = ev.latency_ms;
        break;
    }
  }

  requestClose(): void {
    this.openChange.emit(false);
  }

  newConversation(): void {
    this.conversationId = null;
    this.messages = [];
    this.errorMsg = '';
    this.inputText = '';
  }

  sendSuggestion(q: string): void {
    this.inputText = q;
    this.send();
  }

  async send(): Promise<void> {
    const text = this.inputText.trim();
    if (!text || this.isStreaming) return;

    this.errorMsg = '';
    this.inputText = '';
    this.isStreaming = true;

    // Mensaje del usuario
    this.messages.push({
      role: 'user',
      text,
      tool_calls: [],
      charts: [],
    });

    // Mensaje del asistente vacío que se va llenando con eventos SSE
    const assistant: ChatMessage = {
      role: 'assistant',
      text: '',
      tool_calls: [],
      charts: [],
      thinking: 'Analizando…',
      isStreaming: true,
    };
    this.messages.push(assistant);
    this.shouldScroll = true;

    try {
      for await (const ev of this.stream.streamChat(text, this.conversationId)) {
        switch (ev.type) {
          case 'init':
            this.conversationId = ev.conversation_id ?? this.conversationId;
            break;

          case 'thinking':
            assistant.thinking = `Razonando · paso ${ev.iteration ?? '?'}`;
            break;

          case 'tool_call':
            assistant.tool_calls.push({
              tool: ev.tool ?? 'tool',
              args: ev.args ?? {},
              summary: '',
            });
            assistant.thinking = `Consultando ${ev.tool}…`;
            break;

          case 'tool_result':
            const matching = assistant.tool_calls
              .slice()
              .reverse()
              .find((t) => t.tool === ev.tool && !t.summary);
            if (matching) matching.summary = ev.summary ?? 'ok';
            break;

          case 'chart':
            if (ev.chart) assistant.charts.push(ev.chart);
            break;

          case 'answer':
            assistant.text = ev.text ?? '';
            assistant.thinking = undefined;
            break;

          case 'done':
            assistant.isStreaming = false;
            assistant.thinking = undefined;
            assistant.latency_ms = ev.latency_ms;
            this.isStreaming = false;
            break;

          case 'error':
            assistant.thinking = undefined;
            assistant.isStreaming = false;
            this.errorMsg = ev.detail ?? 'Error en el agente';
            this.isStreaming = false;
            break;
        }
        this.shouldScroll = true;
        this.cdr.markForCheck();
      }
    } catch (err) {
      this.errorMsg = 'Error de conexión con VeridIA';
      assistant.thinking = undefined;
      assistant.isStreaming = false;
    } finally {
      this.isStreaming = false;
      this.shouldScroll = true;
      this.cdr.markForCheck();
    }
  }

  trackByIdx(i: number): number {
    return i;
  }
}
