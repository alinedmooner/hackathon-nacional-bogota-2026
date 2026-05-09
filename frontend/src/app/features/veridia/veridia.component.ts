import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  AlertSummary,
  AlertType,
  Dashboard,
  GrafoNode,
  GrafoResponse,
  Hallazgo,
} from './models/veridia.types';
import { VeridiaService } from './services/veridia.service';
import { VeridiaGraphCanvasComponent } from './components/veridia-graph-canvas/veridia-graph-canvas.component';

@Component({
  selector: 'app-veridia',
  standalone: true,
  imports: [CommonModule, FormsModule, VeridiaGraphCanvasComponent],
  templateUrl: './veridia.component.html',
})
export class VeridiaComponent implements OnInit {
  @ViewChild(VeridiaGraphCanvasComponent) canvas?: VeridiaGraphCanvasComponent;

  // Dashboard global
  dashboard: Dashboard | null = null;
  dashboardLoading = false;

  // Tipo de alerta seleccionada
  selectedAlert: AlertType = 'sancionados';

  // Lista de hallazgos del tipo seleccionado
  hallazgos: Hallazgo[] = [];
  hallazgosLoading = false;
  hallazgosError = '';

  // Grafo de entidad (cargado al hacer click en un hallazgo)
  grafo: GrafoResponse | null = null;
  grafoLoading = false;
  selectedHallazgo: Hallazgo | null = null;

  // Detalles del nodo del grafo seleccionado
  selectedNode: GrafoNode | null = null;

  // Cards de alertas para el sidebar
  alerts: AlertSummary[] = [
    {
      type: 'sancionados',
      label: 'Sancionados activos',
      description: 'Inhabilitados por la Procuraduría con contratos vigentes',
      count: 0,
      color: '#fb7185',
    },
    {
      type: 'multados',
      label: 'Multados activos',
      description: 'Multados en SECOP I que siguen contratando',
      count: 0,
      color: '#fbbf24',
    },
    {
      type: 'puerta_giratoria',
      label: 'Puerta giratoria',
      description: 'Ex-funcionarios contratistas de su antigua entidad',
      count: 0,
      color: '#a78bfa',
    },
  ];

  legend = [
    { group: 'entidad',     label: 'Entidad pública', colorClass: 'bg-violet-400' },
    { group: 'contratista', label: 'Contratista',     colorClass: 'bg-emerald-400' },
    { group: 'sancionado',  label: 'Sancionado',      colorClass: 'bg-rose-400' },
    { group: 'multado',     label: 'Multado',         colorClass: 'bg-amber-400' },
    { group: 'alto_riesgo', label: 'Alto riesgo',     colorClass: 'bg-rose-500 ring-2 ring-amber-400' },
  ];

  constructor(private readonly api: VeridiaService) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.loadHallazgos(this.selectedAlert);
  }

  // ── Dashboard ─────────────────────────────────────────────
  loadDashboard(): void {
    this.dashboardLoading = true;
    this.api.getDashboard().subscribe({
      next: (d) => {
        this.dashboard = d;
        // Sincroniza counts con dashboard
        this.alerts[0].count = d.sancionados_activos.total_personas ?? d.sancionados_activos.total_contratos;
        this.alerts[1].count = d.multados_activos.total_contratistas ?? d.multados_activos.total_contratos;
        this.alerts[2].count = d.puerta_giratoria.total_personas ?? d.puerta_giratoria.total_contratos;
        this.dashboardLoading = false;
      },
      error: () => {
        this.dashboardLoading = false;
      },
    });
  }

  // ── Lista de hallazgos ────────────────────────────────────
  selectAlert(type: AlertType): void {
    if (this.selectedAlert === type) return;
    this.selectedAlert = type;
    this.loadHallazgos(type);
  }

  loadHallazgos(type: AlertType): void {
    this.hallazgosLoading = true;
    this.hallazgosError = '';
    this.hallazgos = [];
    this.api.getHallazgos(type, 50, 0).subscribe({
      next: (r) => {
        this.hallazgos = r.hallazgos;
        this.hallazgosLoading = false;
        // UX: auto-selecciona el primer hallazgo para mostrar el grafo de inmediato
        if (this.hallazgos.length) {
          this.selectHallazgo(this.hallazgos[0]);
        }
      },
      error: () => {
        this.hallazgosError = 'No fue posible cargar los hallazgos';
        this.hallazgosLoading = false;
      },
    });
  }

  // ── Click en un hallazgo → carga grafo de su entidad ──────
  selectHallazgo(h: Hallazgo): void {
    this.selectedHallazgo = h;
    this.selectedNode = null;
    this.grafoLoading = true;
    this.api.getGrafo(h.nit_entidad, 40).subscribe({
      next: (g) => {
        this.grafo = g;
        this.grafoLoading = false;
      },
      error: () => {
        this.grafoLoading = false;
      },
    });
  }

  // ── Click en nodo del grafo ───────────────────────────────
  onNodeClick(node: GrafoNode): void {
    this.selectedNode = node;
  }

  closeNodeDetail(): void {
    this.selectedNode = null;
    this.canvas?.clearHighlight();
  }

  // ── Toolbar grafo ─────────────────────────────────────────
  zoomIn(): void {  this.canvas?.zoomIn();  }
  zoomOut(): void { this.canvas?.zoomOut(); }
  fitView(): void { this.canvas?.fitView(); }
  reset(): void {   this.canvas?.reset();   }
  screenshot(): void {
    const data = this.canvas?.screenshot();
    if (!data) return;
    const a = document.createElement('a');
    a.href = data;
    a.download = `veridia-${this.selectedHallazgo?.nit_entidad ?? 'graph'}-${Date.now()}.png`;
    a.click();
  }

  // ── Helpers de UI ─────────────────────────────────────────
  formatCOP(value: number | undefined): string {
    if (value === undefined || value === null) return '—';
    if (value >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}B COP`;
    if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}MM COP`;
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M COP`;
    return `$${value.toLocaleString('es-CO')} COP`;
  }

  formatDate(s: string | undefined): string {
    if (!s) return '—';
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return s;
    return d.toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' });
  }

  hallazgoNombre(h: Hallazgo): string {
    return h.nombre_sancionado ?? h.nombre_contratista ?? h.nombre_declarante ?? `Doc ${h.documento}`;
  }

  groupColor(group: string): string {
    return {
      entidad:     'bg-violet-400/15 text-violet-300 border-violet-400/40',
      contratista: 'bg-emerald-400/15 text-emerald-300 border-emerald-400/40',
      sancionado:  'bg-rose-400/15 text-rose-300 border-rose-400/40',
      multado:     'bg-amber-400/15 text-amber-300 border-amber-400/40',
      alto_riesgo: 'bg-rose-500/15 text-rose-200 border-rose-500/60',
    }[group] ?? 'bg-slate-800/40 text-slate-300 border-slate-700';
  }

  alertColor(type: AlertType): string {
    return {
      sancionados:      'border-rose-500/40 text-rose-300 bg-rose-500/10',
      multados:         'border-amber-500/40 text-amber-300 bg-amber-500/10',
      puerta_giratoria: 'border-violet-500/40 text-violet-300 bg-violet-500/10',
    }[type];
  }

  trackByDoc(_i: number, h: Hallazgo): string {
    return `${h.documento}-${h.id_contrato}`;
  }
}
