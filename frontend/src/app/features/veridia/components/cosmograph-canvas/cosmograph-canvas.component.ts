import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  NgZone,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import cytoscape, { Core, ElementDefinition } from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import dagre from 'cytoscape-dagre';

import { CytoscapeElement, LayoutKind, NodeData } from '../../models/veridia.types';

cytoscape.use(coseBilkent);
cytoscape.use(dagre);

@Component({
  selector: 'app-cosmograph-canvas',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative h-full w-full overflow-hidden rounded-2xl bg-[#0a0a0f]">
      <div #host class="absolute inset-0"></div>

      <!-- Empty state -->
      <div *ngIf="!hasData"
           class="pointer-events-none absolute inset-0 flex items-center justify-center text-center">
        <div class="space-y-3 px-6">
          <div class="text-6xl opacity-20">⌬</div>
          <p class="text-sm uppercase tracking-[0.4em] text-slate-500">Veridia</p>
          <p class="text-xs text-slate-600">Selecciona un caso para visualizar el grafo</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; width: 100%; }
  `],
})
export class CosmographCanvasComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('host', { static: true }) host!: ElementRef<HTMLDivElement>;

  @Input() elements: CytoscapeElement[] = [];
  @Input() layout: LayoutKind = 'cose-bilkent';

  @Output() nodeClick = new EventEmitter<NodeData>();

  hasData = false;

  private cy: Core | null = null;

  constructor(private zone: NgZone) {}

  ngAfterViewInit(): void {
    this.initGraph();
    if (this.elements.length) this.applyData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['elements'] || changes['layout']) && this.cy) {
      this.applyData();
    }
  }

  ngOnDestroy(): void {
    this.cy?.destroy();
    this.cy = null;
  }

  // ────────────────────────────────────────────────────────────
  // API pública (consumida por la página)
  // ────────────────────────────────────────────────────────────
  fitView(): void {
    this.cy?.animate({ fit: { eles: this.cy.elements(), padding: 60 }, duration: 600 });
  }

  zoomIn(): void {
    if (!this.cy) return;
    const z = this.cy.zoom();
    this.cy.animate({ zoom: z * 1.25, duration: 250 });
  }

  zoomOut(): void {
    if (!this.cy) return;
    const z = this.cy.zoom();
    this.cy.animate({ zoom: z * 0.8, duration: 250 });
  }

  reset(): void {
    if (!this.cy) return;
    this.cy.animate({ fit: { eles: this.cy.elements(), padding: 80 }, duration: 800 });
  }

  screenshot(): string | null {
    if (!this.cy) return null;
    return this.cy.png({ output: 'base64uri', bg: '#0a0a0f', full: true, scale: 2 });
  }

  focusNode(nodeId: string): void {
    if (!this.cy) return;
    const node = this.cy.getElementById(nodeId);
    if (!node || !node.length) return;
    this.cy.animate({ center: { eles: node }, zoom: 1.5, duration: 600 });
    this.cy.elements().unselect();
    node.select();
  }

  // ────────────────────────────────────────────────────────────
  // Internals
  // ────────────────────────────────────────────────────────────
  private initGraph(): void {
    this.zone.runOutsideAngular(() => {
      this.cy = cytoscape({
        container: this.host.nativeElement,
        wheelSensitivity: 0.25,
        minZoom: 0.2,
        maxZoom: 3,
        style: this.buildStylesheet(),
        elements: [],
        layout: { name: 'preset' } as any,
      });

      this.cy.on('tap', 'node', (evt) => {
        const node = evt.target;
        this.highlightNeighborhood(node);
        const data = node.data() as NodeData;
        this.zone.run(() => this.nodeClick.emit(data));
      });

      // Click en el fondo (no sobre un nodo) → limpiar highlight
      this.cy.on('tap', (evt) => {
        if (evt.target === this.cy) {
          this.clearHighlight();
        }
      });
    });
  }

  /** Resalta un nodo y sus vecinos directos, opacando todo lo demás. */
  private highlightNeighborhood(node: cytoscape.NodeSingular): void {
    if (!this.cy) return;
    const neighborhood = node.closedNeighborhood();    // nodo + edges + vecinos
    this.cy.batch(() => {
      this.cy!.elements().removeClass('vd-highlighted vd-faded');
      this.cy!.elements().not(neighborhood).addClass('vd-faded');
      neighborhood.addClass('vd-highlighted');
      node.addClass('vd-focused');
    });
  }

  /** Limpia cualquier highlight activo. */
  clearHighlight(): void {
    if (!this.cy) return;
    this.cy.batch(() => {
      this.cy!.elements().removeClass('vd-highlighted vd-faded vd-focused');
    });
  }

  private applyData(): void {
    if (!this.cy) return;

    const elements: ElementDefinition[] = this.elements.map((e) => {
      const isEdge = 'source' in e.data;
      return {
        group: isEdge ? 'edges' : 'nodes',
        data: e.data as any,
        classes: e.classes ?? '',
      } as ElementDefinition;
    });

    this.hasData = elements.some((e) => e.group === 'nodes');

    this.zone.runOutsideAngular(() => {
      if (!this.cy) return;
      this.cy.elements().remove();
      this.cy.add(elements);
      this.runLayout();
    });
  }

  private runLayout(): void {
    if (!this.cy) return;
    const opts = this.layoutOptions(this.layout);
    this.cy.layout(opts).run();
    setTimeout(() => {
      this.cy?.fit(undefined, 60);
      this.autoFocusFlagged();
    }, 50);
  }

  /**
   * Tras cargar un grafo, resalta automáticamente el primer nodo "flagged"
   * (bandera roja) para llamar la atención del usuario al caso clave.
   */
  private autoFocusFlagged(): void {
    if (!this.cy) return;
    const flagged = this.cy.nodes('.flagged').first();
    if (flagged.nonempty()) {
      this.highlightNeighborhood(flagged);
    }
  }

  private layoutOptions(kind: LayoutKind): any {
    if (kind === 'dagre') {
      return {
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 60,
        rankSep: 110,
        animate: true,
        animationDuration: 500,
      };
    }
    if (kind === 'concentric') {
      return {
        name: 'concentric',
        concentric: (node: any) => (node.data('flagged') ? 2 : 1),
        levelWidth: () => 1,
        minNodeSpacing: 60,
        animate: true,
        animationDuration: 500,
      };
    }
    if (kind === 'circle') {
      return {
        name: 'circle',
        radius: 220,
        animate: true,
        animationDuration: 500,
      };
    }
    // cose-bilkent (force-directed con clusters) por defecto
    return {
      name: 'cose-bilkent',
      animate: 'end',
      animationDuration: 600,
      nodeRepulsion: 6000,
      idealEdgeLength: 110,
      gravity: 0.25,
      gravityRange: 1.2,
      gravityCompound: 1.0,
      numIter: 2500,
      tile: true,
      randomize: true,
    };
  }

  private buildStylesheet(): any[] {
    return [
      // ── nodos base ─────────────────────────────────────
      {
        selector: 'node',
        style: {
          'background-color': '#64748b',
          'border-width': 2,
          'border-color': '#1e293b',
          label: 'data(label)',
          color: '#e2e8f0',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-margin-y': -28,
          'font-size': 11,
          'font-weight': 600,
          'text-wrap': 'wrap',
          'text-max-width': '160px',
          'text-background-color': '#0f172a',
          'text-background-opacity': 0.85,
          'text-background-padding': '4px',
          'text-background-shape': 'roundrectangle',
          'text-border-color': '#1e293b',
          'text-border-width': 1,
          'text-border-opacity': 0.6,
          width: 36,
          height: 36,
          'transition-property': 'background-color, border-color, width, height',
          'transition-duration': 200 as any,
        },
      },
      // ── tipos ──────────────────────────────────────────
      { selector: 'node.type-persona',  style: { 'background-color': '#3b82f6', 'border-color': '#1d4ed8' } },
      { selector: 'node.type-empresa',  style: { 'background-color': '#f59e0b', 'border-color': '#b45309', width: 44, height: 44 } },
      { selector: 'node.type-entidad',  style: { 'background-color': '#a855f7', 'border-color': '#7e22ce', width: 50, height: 50, 'shape': 'round-rectangle' } },
      { selector: 'node.type-contrato', style: { 'background-color': '#10b981', 'border-color': '#047857', width: 26, height: 26, 'shape': 'round-rectangle' } },
      { selector: 'node.type-sancion',  style: { 'background-color': '#ef4444', 'border-color': '#991b1b', 'shape': 'diamond', width: 32, height: 32 } },
      // ── flagged (bandera roja) ─────────────────────────
      {
        selector: 'node.flagged',
        style: {
          'border-color': '#ef4444',
          'border-width': 4,
          'overlay-color': '#ef4444',
          'overlay-opacity': 0.15,
          'overlay-padding': 6,
        },
      },
      // ── selección / hover ──────────────────────────────
      {
        selector: 'node:selected',
        style: {
          'border-color': '#22d3ee',
          'border-width': 5,
          'overlay-color': '#22d3ee',
          'overlay-opacity': 0.2,
        },
      },
      // ── neighborhood highlight ─────────────────────────
      // Elementos opacados (fuera del vecindario)
      {
        selector: '.vd-faded',
        style: {
          opacity: 0.12,
          'text-opacity': 0.25,
          'z-index': 1,
        },
      },
      // Vecindario destacado (nodo + aristas + vecinos)
      {
        selector: 'node.vd-highlighted',
        style: {
          opacity: 1,
          'text-opacity': 1,
          'z-index': 50,
        },
      },
      {
        selector: 'edge.vd-highlighted',
        style: {
          opacity: 1,
          width: 2.5,
          'line-color': '#22d3ee',
          'target-arrow-color': '#22d3ee',
          'z-index': 60,
          'text-background-opacity': 1,
        },
      },
      // Nodo focal (el clickeado) — más prominente
      {
        selector: 'node.vd-focused',
        style: {
          'border-color': '#22d3ee',
          'border-width': 5,
          'overlay-color': '#22d3ee',
          'overlay-opacity': 0.25,
          'overlay-padding': 10,
          'z-index': 100,
        },
      },
      // ── aristas ─────────────────────────────────────────
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#475569',
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#475569',
          'arrow-scale': 0.8,
          opacity: 0.7,
          label: 'data(label)',
          'font-size': 9,
          color: '#94a3b8',
          'text-rotation': 'autorotate' as any,
          'text-background-color': '#0a0a0f',
          'text-background-opacity': 0.8,
          'text-background-padding': '2px',
        },
      },
      { selector: 'edge[relacion="contrato"]', style: { 'line-color': '#10b981', 'target-arrow-color': '#10b981' } },
      { selector: 'edge[relacion="sancion"]',  style: { 'line-color': '#ef4444', 'target-arrow-color': '#ef4444', width: 2.5 } },
      { selector: 'edge[relacion="cargo"]',    style: { 'line-color': '#fbbf24', 'target-arrow-color': '#fbbf24', 'line-style': 'dashed' } },
      { selector: 'edge[relacion="control"]',  style: { 'line-color': '#6366f1', 'target-arrow-color': '#6366f1' } },
      {
        selector: 'edge.flagged',
        style: {
          'line-color': '#ef4444',
          'target-arrow-color': '#ef4444',
          width: 3,
          opacity: 0.95,
        },
      },
    ];
  }
}
