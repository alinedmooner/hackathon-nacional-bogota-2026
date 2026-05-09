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
         class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity"></div>

    <!-- Slide-over panel -->
    <aside class="fixed right-0 top-0 z-50 flex h-full w-full max-w-[28rem] flex-col bg-slate-950/95 border-l border-slate-800 shadow-2xl shadow-fuchsia-500/10 backdrop-blur transition-transform duration-300"
           [class.translate-x-0]="open"
           [class.translate-x-full]="!open"
           [attr.aria-hidden]="!open">

      <!-- Header -->
      <header class="flex items-center justify-between gap-3 border-b border-slate-800/60 px-5 py-4">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-fuchsia-500 to-violet-600 text-base font-bold text-white">
            V
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-100">
              Verid<span class="text-fuchsia-400">IA</span>
            </p>
            <p class="text-[10px] uppercase tracking-[0.2em] text-slate-500">
              Asistente conversacional
            </p>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <button (click)="newConversation()"
                  title="Nueva conversación"
                  class="rounded-lg border border-slate-700 px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-slate-400 transition hover:border-fuchsia-500/40 hover:text-fuchsia-200">
            Nueva
          </button>
          <button (click)="requestClose()"
                  title="Cerrar"
                  class="ml-1 rounded-md px-2 py-1 text-slate-400 transition hover:bg-slate-800 hover:text-slate-200">
            ✕
          </button>
        </div>
      </header>

      <!-- Mensajes -->
      <div #scrollArea class="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-4">

        <!-- Estado inicial: sugerencias -->
        <div *ngIf="!messages.length"
             class="space-y-3 px-1">
          <div class="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
            <p class="text-xs font-semibold text-slate-200">
              👋 Pregunta sobre la contratación pública en lenguaje natural.
            </p>
            <p class="mt-1 text-[11px] leading-relaxed text-slate-500">
              VeridIA cruza SECOP con sanciones de Procuraduría, Contraloría y SIC, y
              te muestra el razonamiento paso a paso.
            </p>
          </div>
          <p class="text-[10px] uppercase tracking-widest text-slate-500 px-1">Prueba con</p>
          <button *ngFor="let q of suggestions"
                  (click)="sendSuggestion(q)"
                  class="block w-full rounded-xl border border-slate-800 bg-slate-900/30 px-4 py-3 text-left text-xs text-slate-300 transition hover:border-fuchsia-500/40 hover:text-fuchsia-200">
            <span class="text-fuchsia-400 mr-1">›</span>{{ q }}
          </button>
        </div>

        <!-- Burbujas -->
        <div *ngFor="let m of messages; trackBy: trackByIdx; let i = index"
             [class.justify-end]="m.role === 'user'"
             class="flex">
          <div [ngClass]="m.role === 'user'
                 ? 'bg-fuchsia-500/15 border-fuchsia-500/30 text-slate-100'
                 : 'bg-slate-900/60 border-slate-800 text-slate-200'"
               class="max-w-[88%] rounded-2xl border px-4 py-3">
            <p class="mb-1.5 text-[10px] uppercase tracking-widest"
               [ngClass]="m.role === 'user' ? 'text-fuchsia-300' : 'text-slate-500'">
              {{ m.role === 'user' ? 'Tú' : 'VeridIA' }}
            </p>

            <!-- Tool calls (badges) -->
            <div *ngIf="m.tool_calls.length" class="mb-2 space-y-1">
              <div *ngFor="let tc of m.tool_calls"
                   class="flex items-center gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/5 px-2 py-1 text-[10px] font-mono text-emerald-300">
                <span>🔍</span>
                <span class="font-semibold">{{ tc.tool }}</span>
                <span class="text-slate-500">·</span>
                <span class="truncate text-slate-400">{{ tc.summary || '...' }}</span>
              </div>
            </div>

            <!-- Indicador thinking -->
            <div *ngIf="m.thinking"
                 class="mb-2 inline-flex items-center gap-2 rounded-md bg-slate-800/60 px-2 py-1 text-[10px] text-slate-400">
              <span class="flex space-x-0.5">
                <span class="h-1 w-1 animate-bounce rounded-full bg-fuchsia-400"></span>
                <span class="h-1 w-1 animate-bounce rounded-full bg-fuchsia-400" style="animation-delay: 0.15s"></span>
                <span class="h-1 w-1 animate-bounce rounded-full bg-fuchsia-400" style="animation-delay: 0.3s"></span>
              </span>
              <span>{{ m.thinking }}</span>
            </div>

            <!-- Texto de respuesta -->
            <p *ngIf="m.text" class="whitespace-pre-wrap text-sm leading-relaxed">{{ m.text }}</p>

            <!-- Charts inline -->
            <div *ngFor="let ch of m.charts"
                 class="mt-3 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <p *ngIf="ch.title" class="mb-2 text-[10px] uppercase tracking-widest text-slate-400">{{ ch.title }}</p>
              <div class="h-48">
                <canvas baseChart
                        [type]="ch.chart_js_spec.type"
                        [data]="ch.chart_js_spec.data"
                        [options]="ch.chart_js_spec.options"></canvas>
              </div>
            </div>

            <!-- Footer (latencia) -->
            <p *ngIf="m.latency_ms" class="mt-2 text-[9px] text-slate-600">
              {{ (m.latency_ms / 1000).toFixed(1) }}s
            </p>
          </div>
        </div>

        <!-- Error -->
        <div *ngIf="errorMsg"
             class="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {{ errorMsg }}
        </div>
      </div>

      <!-- Input -->
      <form (ngSubmit)="send()"
            class="border-t border-slate-800/60 bg-slate-950/80 px-4 py-3">
        <div class="flex gap-2">
          <input type="text"
                 [(ngModel)]="inputText"
                 name="inputText"
                 [disabled]="isStreaming"
                 placeholder="Pregunta sobre contratación pública…"
                 class="flex-1 rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-fuchsia-500 focus:outline-none disabled:opacity-50" />
          <button type="submit"
                  [disabled]="isStreaming || !inputText.trim()"
                  class="rounded-xl bg-fuchsia-500/80 px-4 py-2.5 text-xs font-semibold uppercase tracking-widest text-white transition hover:bg-fuchsia-500 disabled:cursor-not-allowed disabled:opacity-40">
            <span *ngIf="!isStreaming">Enviar</span>
            <span *ngIf="isStreaming">…</span>
          </button>
        </div>
        <p class="mt-1.5 text-[9px] text-slate-600 text-center">
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
