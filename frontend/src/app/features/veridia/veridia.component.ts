import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { CosmographCanvasComponent } from './components/cosmograph-canvas/cosmograph-canvas.component';
import {
  AlertSummary,
  AlertType,
  InvestigationGraph,
  NodeData,
  NodeType,
} from './models/veridia.types';
import { VeridiaMockService } from './services/veridia-mock.service';

interface LegendEntry {
  type: NodeType;
  label: string;
  colorClass: string;
}

@Component({
  selector: 'app-veridia',
  standalone: true,
  imports: [CommonModule, FormsModule, CosmographCanvasComponent],
  templateUrl: './veridia.component.html',
})
export class VeridiaComponent implements OnInit {
  @ViewChild(CosmographCanvasComponent) canvas?: CosmographCanvasComponent;

  alerts: AlertSummary[] = [];
  selectedAlert: AlertType = 'sancionado_activo';

  investigation: InvestigationGraph | null = null;
  loading = false;

  selectedNode: NodeData | null = null;

  searchQuery = '';
  showLabels = true;

  legend: LegendEntry[] = [
    { type: 'persona', label: 'Persona', colorClass: 'bg-cyan-400' },
    { type: 'empresa', label: 'Empresa', colorClass: 'bg-amber-400' },
    { type: 'entidad', label: 'Entidad pública', colorClass: 'bg-violet-400' },
    { type: 'contrato', label: 'Contrato', colorClass: 'bg-emerald-400' },
    { type: 'sancion', label: 'Sanción', colorClass: 'bg-rose-400' },
  ];

  constructor(private readonly mock: VeridiaMockService) {}

  ngOnInit(): void {
    this.mock.getAlertSummaries().subscribe((a) => {
      this.alerts = a;
    });
    this.loadInvestigation(this.selectedAlert);
  }

  selectAlert(type: AlertType): void {
    if (this.selectedAlert === type && this.investigation) return;
    this.selectedAlert = type;
    this.loadInvestigation(type);
  }

  loadInvestigation(type: AlertType): void {
    this.loading = true;
    this.selectedNode = null;
    this.mock.getInvestigation(type).subscribe({
      next: (inv) => {
        this.investigation = inv;
        this.loading = false;
        // Permitir que el canvas reciba elements y luego ajustar
        setTimeout(() => this.canvas?.fitView(), 350);
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  onNodeClick(node: NodeData): void {
    this.selectedNode = node;
  }

  closeDetail(): void {
    this.selectedNode = null;
    this.canvas?.clearHighlight();
  }

  zoomIn(): void {
    this.canvas?.zoomIn();
  }
  zoomOut(): void {
    this.canvas?.zoomOut();
  }
  fitView(): void {
    this.canvas?.fitView();
  }
  reset(): void {
    this.canvas?.reset();
  }

  screenshot(): void {
    const data = this.canvas?.screenshot();
    if (!data) return;
    const a = document.createElement('a');
    a.href = data;
    a.download = `veridia-${this.selectedAlert}-${Date.now()}.png`;
    a.click();
  }

  searchAndFocus(): void {
    if (!this.searchQuery.trim() || !this.investigation) return;
    const q = this.searchQuery.trim().toLowerCase();
    const match = this.investigation.elements.find((el) => {
      const d = el.data as NodeData;
      return d.label && (
        d.label.toLowerCase().includes(q) ||
        (d.identificacion && d.identificacion.toLowerCase().includes(q))
      );
    });
    if (match) {
      const node = match.data as NodeData;
      this.canvas?.focusNode(node.id);
      this.selectedNode = node;
    }
  }

  iconFor(type: NodeType): string {
    return {
      persona:  '👤',
      empresa:  '🏢',
      entidad:  '🏛',
      contrato: '📄',
      sancion:  '⚠',
    }[type];
  }

  formatNumber(n: number | string | undefined): string {
    if (n === undefined || n === null) return '—';
    if (typeof n === 'number') {
      return n.toLocaleString('es-CO');
    }
    return n;
  }

  metricEntries(metrics?: Record<string, string | number>): { k: string; v: string }[] {
    if (!metrics) return [];
    return Object.entries(metrics).map(([k, v]) => ({ k, v: this.formatNumber(v) }));
  }

  alertColor(type: AlertType): string {
    return {
      sancionado_activo: 'border-rose-500/40 text-rose-300 bg-rose-500/10',
      puerta_giratoria: 'border-amber-500/40 text-amber-300 bg-amber-500/10',
      redes_ocultas:    'border-violet-500/40 text-violet-300 bg-violet-500/10',
    }[type];
  }

  confidenceBarColor(type: AlertType): string {
    return {
      sancionado_activo: 'bg-rose-400',
      puerta_giratoria: 'bg-amber-400',
      redes_ocultas:    'bg-violet-400',
    }[type];
  }
}
