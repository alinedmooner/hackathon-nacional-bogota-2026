import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

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
import { OnboardingService } from './onboarding/onboarding.service';
import { SOACHA_FOCUS_NODE_ID, SOACHA_GRAFO } from './onboarding/onboarding-soacha.mock';

@Component({
  selector: 'app-veridia',
  standalone: true,
  imports: [CommonModule, FormsModule, VeridiaGraphCanvasComponent],
  templateUrl: './veridia.component.html',
})
export class VeridiaComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();
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

  // ── Filtros (cliente-side sobre la lista cargada) ──────────
  searchText = '';
  filterConfianza: 'todas' | 'alta' | 'media' = 'todas';
  filterMinValor = 0;
  filterEntidad = '';
  filtersOpen = false;

  // Cards de alertas para el sidebar
  alerts: AlertSummary[] = [
    {
      type: 'sancionados',
      label: 'Sancionados activos',
      description: 'Inhabilitados por la Procuraduría con contratos vigentes',
      count: 0,
      color: '#a14545', // err
    },
    {
      type: 'multados',
      label: 'Multados activos',
      description: 'Multados en SECOP I que siguen contratando',
      count: 0,
      color: '#b08e3f', // gold-deep
    },
    {
      type: 'puerta_giratoria',
      label: 'Puerta giratoria',
      description: 'Ex-funcionarios contratistas de su antigua entidad',
      count: 0,
      color: '#1a3a5c', // navy
    },
  ];

  legend = [
    { group: 'entidad',     label: 'Entidad pública', colorClass: 'bg-navy' },
    { group: 'contratista', label: 'Contratista',     colorClass: 'bg-ok' },
    { group: 'sancionado',  label: 'Sancionado',      colorClass: 'bg-err' },
    { group: 'multado',     label: 'Multado',         colorClass: 'bg-gold-deep' },
    { group: 'alto_riesgo', label: 'Alto riesgo',     colorClass: 'bg-err ring-2 ring-gold' },
  ];

  constructor(
    private readonly api: VeridiaService,
    private readonly onboarding: OnboardingService,
    private readonly router: Router,
  ) {}

  /** Lista de datasets reportados como no disponibles (false) por el backend */
  get datasetsCaidos(): string[] {
    const d = this.dashboard?.disponibilidad_datasets;
    if (!d) return [];
    return Object.entries(d)
      .filter(([, v]) => !v)
      .map(([k]) => k);
  }

  /** Navega al perfil del nodo del grafo (cédula/NIT sin prefijo) */
  openPerfil(node: GrafoNode): void {
    // Los IDs del backend vienen como `c_12345678` o `e_800099780`
    const documento = node.id.replace(/^[a-z]_/, '');
    this.router.navigate(['/perfil', documento]);
  }

  ngOnInit(): void {
    this.loadDashboard();
    this.loadHallazgos(this.selectedAlert);

    // Hook al onboarding: escucha eventos para mostrar grafo + click programático
    this.onboarding.events$
      .pipe(takeUntil(this.destroy$))
      .subscribe((evt) => {
        switch (evt.kind) {
          case 'load-graph':
            // Modo demo: usa el grafo pre-grabado de Soacha
            this.grafo = SOACHA_GRAFO;
            this.grafoLoading = false;
            this.selectedHallazgo = {
              documento: '79834221',
              nombre_sancionado: 'Persona A · sancionada',
              id_contrato: 'CO1.PCCNTR.demo',
              fecha_de_firma: '2024-09-15',
              valor_contrato: 1_840_000_000,
              nombre_entidad: 'Alcaldía de Soacha',
              nit_entidad: '800094391',
              confianza: 'alta',
              sanciones: 'Inhabilidad disciplinaria · Procuraduría',
              fecha_inicio_sancion: '2023-04',
              fecha_fin_sancion: '2028-04',
              url_evidencia: 'https://www.procuraduria.gov.co/',
            };
            this.selectedNode = null;
            break;
          case 'click-sancionado-node':
            // Auto-click programático en el sancionado destacado
            setTimeout(() => {
              this.canvas?.focusNode(SOACHA_FOCUS_NODE_ID);
              const node = SOACHA_GRAFO.nodes.find((n) => n.id === SOACHA_FOCUS_NODE_ID);
              if (node) this.selectedNode = node;
            }, 800);
            break;
          case 'reset':
            // Vuelve al estado normal: recarga datos reales
            this.selectedNode = null;
            this.loadHallazgos(this.selectedAlert);
            break;
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
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
      entidad:     'bg-navy/10 text-navy border-navy/30',
      contratista: 'bg-ok/10 text-ok border-ok/30',
      sancionado:  'bg-err/10 text-err border-err/30',
      multado:     'bg-gold/15 text-gold-deep border-gold/40',
      alto_riesgo: 'bg-err/15 text-err border-err/50',
    }[group] ?? 'bg-cream-2 text-ink-2 border-line';
  }

  alertColor(type: AlertType): string {
    return {
      sancionados:      'border-err/40 text-err bg-err/10',
      multados:         'border-gold/40 text-gold-deep bg-gold/15',
      puerta_giratoria: 'border-navy/40 text-navy bg-navy/10',
    }[type];
  }

  trackByDoc(_i: number, h: Hallazgo): string {
    return `${h.documento}-${h.id_contrato}`;
  }

  // ── Filtros ────────────────────────────────────────────────
  get filteredHallazgos(): Hallazgo[] {
    const q = this.searchText.trim().toLowerCase();
    const ent = this.filterEntidad.trim().toLowerCase();
    return this.hallazgos.filter((h) => {
      if (this.filterConfianza !== 'todas' && h.confianza !== this.filterConfianza) return false;
      if (this.filterMinValor > 0 && (h.valor_contrato ?? 0) < this.filterMinValor) return false;
      if (ent) {
        const hit =
          h.nombre_entidad?.toLowerCase().includes(ent) ||
          h.nit_entidad?.toLowerCase().includes(ent);
        if (!hit) return false;
      }
      if (q) {
        const blob = [
          h.documento,
          h.nombre_sancionado,
          h.nombre_contratista,
          h.nombre_declarante,
          h.id_contrato,
          h.nombre_entidad,
          h.nit_entidad,
          h.sanciones,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        if (!blob.includes(q)) return false;
      }
      return true;
    });
  }

  get activeFiltersCount(): number {
    let n = 0;
    if (this.searchText.trim()) n++;
    if (this.filterConfianza !== 'todas') n++;
    if (this.filterMinValor > 0) n++;
    if (this.filterEntidad.trim()) n++;
    return n;
  }

  clearFilters(): void {
    this.searchText = '';
    this.filterConfianza = 'todas';
    this.filterMinValor = 0;
    this.filterEntidad = '';
  }

  toggleFilters(): void {
    this.filtersOpen = !this.filtersOpen;
  }
}
