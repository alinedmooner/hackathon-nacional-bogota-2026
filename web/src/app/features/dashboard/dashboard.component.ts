import { ChangeDetectionStrategy, Component, OnInit, inject, Pipe, PipeTransform } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ChartConfiguration } from 'chart.js';
import 'chart.js/auto';
import {
  AnalyticsService,
  EntidadDinero,
  AnomaliaFinanciera,
  AnomaliaTipoDato,
  Paso2Extended,
  Paso1Stats,
} from '../../core/services/analytics.service';
import { AuthService } from '../../core/services/auth.service';
import {
  AiService,
  AiChatResponse,
  ChartItem,
  ToolCallLog,
  ConversationSummary,
} from '../../core/services/ai.service';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  tool_calls?: ToolCallLog[];
  charts?: ChartItem[];
  latency_ms?: number;
}

@Pipe({ name: 'formatCurrency', standalone: true })
export class FormatCurrencyPipe implements PipeTransform {
  transform(value: number): string {
    if (value == null) return '';
    return '$' + value.toLocaleString('es-CO', { maximumFractionDigits: 0 });
  }
}

@Pipe({ name: 'formatColumn', standalone: true })
export class FormatColumnPipe implements PipeTransform {
  transform(column: string): string {
    if (!column) return '';
    return column.replace(/_/g, ' ');
  }
}

@Pipe({ name: 'formatBytes', standalone: true })
export class FormatBytesPipe implements PipeTransform {
  transform(bytes: number | null): string {
    if (bytes === null) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, CommonModule, FormatCurrencyPipe, FormatColumnPipe, FormatBytesPipe],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly analyticsService = inject(AnalyticsService);
  private readonly authService = inject(AuthService);
  private readonly aiService = inject(AiService);
  private readonly router = inject(Router);

  activeTab: 'records' | 'analytics' | 'archivos' | 'chat' = 'records';

  // ── AI Chat state ─────────────────────────────────────────
  chatMessages: ChatMessage[] = [];
  chatInput = '';
  chatLoading = false;
  chatError = '';
  conversationId: string | null = null;
  conversations: ConversationSummary[] = [];
  exampleQuestions: string[] = [
    '¿Cuál es el contrato más caro firmado en 2025?',
    'Top 5 departamentos con más contratos, hazme un gráfico',
    '¿Cuántos contratos cerrados hay en Antioquia?',
    'Busca contratos sobre construcción de aulas',
  ];
  barChartData: ChartConfiguration<'bar'>['data'] = { labels: [], datasets: [] };
  barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
  };

  lineChartData: ChartConfiguration<'line'>['data'] = { labels: [], datasets: [] };
  lineChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
  };

  doughnutChartData: ChartConfiguration<'doughnut'>['data'] = {
    labels: [],
    datasets: [],
  };
  doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
  };

  latencyChartData: ChartConfiguration<'line'>['data'] = { labels: [], datasets: [] };
  latencyChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
  };

  entidadesChartData: ChartConfiguration<'bar'>['data'] = { labels: [], datasets: [] };
  entidadesChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
  };

  snapshot = {
    totalContratos: 0,
    contratosPyme: 0,
    pagosAdelantados: 0,
  };

  // Paso 2 extended
  paso2Extended: Paso2Extended | null = null;
  topEntidades: EntidadDinero[] = [];
  anomaliasFinancieras: AnomaliaFinanciera[] = [];
  anomaliasEstadisticas = { media: 0, umbral_anomalia: 0 };
  anomaliasTiposDatos: AnomaliaTipoDato[] = [];

  // Paso 1
  paso1Stats: Paso1Stats | null = null;

  records: Array<Record<string, string | number | null>> = [];
  recordColumns: string[] = [
    'nombre_entidad',
    'departamento',
    'ciudad',
    'estado_contrato',
    'tipo_de_contrato',
    'proveedor_adjudicado',
    'valor_del_contrato',
    'fecha_de_firma',
    'objeto_del_contrato',
  ];
  recordsLoading = false;
  recordsError = '';
  currentPage = 1;
  totalPages = 0;
  totalRecords = 0;
  pageSize = 20;

  ngOnInit(): void {
    this.analyticsService.getTopDepartamentos().subscribe((series) => {
      this.barChartData = {
        labels: series.labels,
        datasets: [
          {
            data: series.values,
            label: 'Contratos',
            backgroundColor: 'rgba(26, 58, 92, 0.75)', // navy
            borderColor: '#1a3a5c',
            borderWidth: 1,
          },
        ],
      };
    });

    this.analyticsService.getTiposContrato().subscribe((series) => {
      this.lineChartData = {
        labels: series.labels,
        datasets: [
          {
            data: series.values,
            label: 'Contratos por tipo',
            borderColor: '#c9a961', // gold
            backgroundColor: 'rgba(201, 169, 97, 0.18)',
            fill: true,
            tension: 0.3,
          },
        ],
      };
    });

    this.analyticsService.getBrechaGenero().subscribe((data) => {
      this.doughnutChartData = {
        labels: data.labels,
        datasets: [
          {
            data: data.values,
            backgroundColor: ['#1a3a5c', '#c9a961', '#a14545', '#4d7a3e', '#7a9ec2'],
            borderColor: '#ffffff',
            borderWidth: 2,
          },
        ],
      };
    });

    this.analyticsService.getModalidades().subscribe((series) => {
      this.latencyChartData = {
        labels: series.labels,
        datasets: [
          {
            data: series.values,
            label: 'Contratos',
            borderColor: '#1a3a5c', // navy
            backgroundColor: 'rgba(26, 58, 92, 0.15)',
            fill: true,
            tension: 0.3,
          },
        ],
      };
    });

    this.analyticsService.getSnapshot().subscribe((snapshot) => {
      this.snapshot = snapshot;
    });

    // Paso 2 extended
    this.analyticsService.getTopEntidadesDinero().subscribe((data) => {
      this.topEntidades = data;
      this.entidadesChartData = {
        labels: data.map((e) => e.entidad.substring(0, 30)),
        datasets: [
          {
            data: data.map((e) => e.valor_total),
            label: 'Valor total ($)',
            backgroundColor: ['#1a3a5c', '#c9a961', '#b08e3f', '#7a9ec2', '#4d7a3e'],
            borderColor: '#ffffff',
            borderWidth: 1,
          },
        ],
      };
    });

    this.analyticsService.getAnomalasFinancieras().subscribe((data) => {
      this.anomaliasFinancieras = data.anomalos;
      this.anomaliasEstadisticas = data.estadisticas;
    });

    this.analyticsService.getAnomalasTiposDatos().subscribe((data) => {
      this.anomaliasTiposDatos = data;
    });

    this.analyticsService.getPaso2Extended().subscribe((data) => {
      this.paso2Extended = data;
    });

    // Paso 1
    this.analyticsService.getPaso1Stats().subscribe((data) => {
      this.paso1Stats = data;
    });

    this.loadRecords();
  }

  loadRecords(): void {
    this.recordsLoading = true;
    this.recordsError = '';

    this.analyticsService.getContratos(this.currentPage, this.pageSize).subscribe({
      next: (response) => {
        this.records = response.items;
        this.totalPages = response.pages;
        this.totalRecords = response.total;
        this.recordsLoading = false;
      },
      error: () => {
        this.recordsLoading = false;
        this.recordsError = 'No se pudo cargar SECOP II.';
      },
    });
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadRecords();
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadRecords();
    }
  }

  setTab(tab: 'records' | 'analytics' | 'archivos' | 'chat'): void {
    this.activeTab = tab;
    if (tab === 'chat' && this.conversations.length === 0) {
      this.aiService.listConversations().subscribe((c) => (this.conversations = c));
    }
  }

  // ── AI Chat handlers ──────────────────────────────────────
  sendChatMessage(): void {
    const text = this.chatInput.trim();
    if (!text || this.chatLoading) return;

    this.chatMessages.push({ role: 'user', content: text });
    this.chatInput = '';
    this.chatLoading = true;
    this.chatError = '';

    this.aiService.sendMessage(text, this.conversationId).subscribe({
      next: (resp: AiChatResponse) => {
        this.conversationId = resp.conversation_id;
        this.chatMessages.push({
          role: 'assistant',
          content: resp.answer,
          tool_calls: resp.tool_calls,
          charts: resp.charts,
          latency_ms: resp.latency_ms,
        });
        this.chatLoading = false;
        this.aiService.listConversations().subscribe((c) => (this.conversations = c));
      },
      error: (err) => {
        this.chatLoading = false;
        this.chatError = err?.error?.detail ?? 'No se pudo conectar con el agente IA.';
      },
    });
  }

  newConversation(): void {
    this.conversationId = null;
    this.chatMessages = [];
    this.chatError = '';
    this.chatInput = '';
  }

  loadConversation(id: string): void {
    this.aiService.getConversation(id).subscribe({
      next: (conv) => {
        this.conversationId = conv.conversation_id;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        this.chatMessages = conv.messages.map((m: any) => ({
          role: m.role,
          content: m.content || '',
          tool_calls: m.tool_calls,
          charts: m.charts,
        }));
      },
      error: () => {
        this.chatError = 'No se pudo cargar la conversación.';
      },
    });
  }

  useExample(q: string): void {
    this.chatInput = q;
  }

  trackByIndex(index: number): number {
    return index;
  }

  logout(): void {
    this.authService.logout();
    this.router.navigateByUrl('/login');
  }
}
