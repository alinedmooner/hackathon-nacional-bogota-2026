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
import cytoscape, { Core, ElementDefinition, NodeSingular } from 'cytoscape';
import fcose from 'cytoscape-fcose';

import { GrafoNode, GrafoResponse } from '../../models/veridia.types';

cytoscape.use(fcose);

@Component({
  selector: 'app-veridia-graph-canvas',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative h-full w-full overflow-hidden rounded border border-line bg-card">
      <div #host class="absolute inset-0"></div>

      <!-- Meta info flotante (esquina superior derecha) -->
      <div *ngIf="grafo?.meta as m"
           class="absolute right-3 top-3 z-10 max-w-xs rounded border border-line bg-cream-2/95 p-3 shadow-sm backdrop-blur">
        <p class="text-[11px] uppercase tracking-widest text-muted font-semibold">Entidad analizada</p>
        <p class="mt-1 font-editorial text-base font-semibold text-ink leading-tight">{{ m.entidad }}</p>
        <p class="text-xs font-mono text-muted tabular">NIT {{ m.nit }}</p>
        <div class="mt-2 flex flex-wrap gap-1.5">
          <span class="rounded bg-cream px-2 py-0.5 text-xs text-ink-2 border border-line">
            {{ m.total_contratistas }} proveedores
          </span>
          <span *ngIf="m.alertas_rojo"
                class="rounded bg-err/10 px-2 py-0.5 text-xs text-err border border-err/30">
            🚩 {{ m.alertas_rojo }} sancionados
          </span>
          <span *ngIf="m.alertas_naranja"
                class="rounded bg-gold/15 px-2 py-0.5 text-xs text-gold-deep border border-gold/40">
            ⚠ {{ m.alertas_naranja }} multados
          </span>
        </div>
      </div>

      <!-- Empty state -->
      <div *ngIf="!hasData"
           class="pointer-events-none absolute inset-0 flex items-center justify-center text-center">
        <div class="space-y-3 px-6">
          <div class="font-editorial text-5xl text-line-strong">⌬</div>
          <p class="text-xs uppercase tracking-widest text-muted font-semibold">VeridIA · Mapa</p>
          <p class="text-sm text-ink-2 max-w-xs mx-auto leading-relaxed">
            Selecciona un hallazgo en la lista para visualizar la red de la entidad y sus contratistas.
          </p>
        </div>
      </div>
    </div>
  `,
  styles: [`:host { display: block; height: 100%; width: 100%; }`],
})
export class VeridiaGraphCanvasComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('host', { static: true }) host!: ElementRef<HTMLDivElement>;

  @Input() grafo: GrafoResponse | null = null;

  @Output() nodeClick = new EventEmitter<GrafoNode>();

  hasData = false;

  private cy: Core | null = null;

  constructor(private zone: NgZone) {}

  ngAfterViewInit(): void {
    this.initGraph();
    if (this.grafo) this.applyData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['grafo'] && this.cy) {
      this.applyData();
    }
  }

  ngOnDestroy(): void {
    this.cy?.destroy();
    this.cy = null;
  }

  // ────────────────────────────────────────────────────────────
  // API pública
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
    this.clearHighlight();
  }
  screenshot(): string | null {
    if (!this.cy) return null;
    return this.cy.png({ output: 'base64uri', bg: '#ffffff', full: true, scale: 2 });
  }
  focusNode(nodeId: string): void {
    if (!this.cy) return;
    const node = this.cy.getElementById(nodeId);
    if (!node || !node.length) return;
    this.cy.animate({ center: { eles: node }, zoom: 1.4, duration: 600 });
    this.highlightNeighborhood(node as NodeSingular);
  }

  clearHighlight(): void {
    if (!this.cy) return;
    this.cy.batch(() => {
      this.cy!.elements().removeClass('vd-highlighted vd-faded vd-focused');
    });
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
        const node = evt.target as NodeSingular;
        this.highlightNeighborhood(node);
        const data = node.data() as GrafoNode;
        this.zone.run(() => this.nodeClick.emit(data));
      });

      this.cy.on('tap', (evt) => {
        if (evt.target === this.cy) this.clearHighlight();
      });
    });
  }

  private highlightNeighborhood(node: NodeSingular): void {
    if (!this.cy) return;
    const neighborhood = node.closedNeighborhood();
    this.cy.batch(() => {
      this.cy!.elements().removeClass('vd-highlighted vd-faded vd-focused');
      this.cy!.elements().not(neighborhood).addClass('vd-faded');
      neighborhood.addClass('vd-highlighted');
      node.addClass('vd-focused');
    });
  }

  private applyData(): void {
    if (!this.cy || !this.grafo) {
      this.hasData = false;
      return;
    }

    // Adaptador: vis-network (from/to) → Cytoscape (source/target)
    const elements: ElementDefinition[] = [
      ...this.grafo.nodes.map((n) => ({
        group: 'nodes' as const,
        data: { id: n.id, label: n.label, group: n.group, value: n.value, title: n.title },
        classes: `group-${n.group}`,
      })),
      ...this.grafo.edges.map((e, i) => ({
        group: 'edges' as const,
        data: {
          id: `edge_${i}`,
          source: e.from,
          target: e.to,
          value: e.value,
          title: e.title,
        },
      })),
    ];

    this.hasData = elements.some((e) => e.group === 'nodes');

    this.zone.runOutsideAngular(() => {
      if (!this.cy) return;
      this.cy.elements().remove();
      this.cy.add(elements);
      // Asegura que el container reporte su tamaño actual antes del layout
      this.cy.resize();

      this.cy.layout({
        name: 'fcose',
        animate: true,
        animationDuration: 700,
        nodeRepulsion: 16000,
        idealEdgeLength: 160,
        edgeElasticity: 0.45,
        gravity: 0.15,
        gravityRange: 1.5,
        padding: 60,
        randomize: true,
        nodeSeparation: 100,
      } as any).run();

      setTimeout(() => {
        this.cy?.resize();
        this.cy?.fit(undefined, 80);
        // auto-focus a la entidad central
        const entidad = this.cy?.nodes('.group-entidad').first();
        if (entidad && entidad.nonempty()) {
          this.highlightNeighborhood(entidad as NodeSingular);
        }
      }, 800);
    });
  }

  private buildStylesheet(): any[] {
    return [
      // ── nodos base · light mode institucional ──────────
      {
        selector: 'node',
        style: {
          'background-color': '#7a9ec2',
          'border-width': 1.5,
          'border-color': '#1a3a5c',
          'background-opacity': 1,
          label: 'data(label)',
          color: '#14202c',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-margin-y': -30,
          'font-family': 'Public Sans, -apple-system, sans-serif',
          'font-size': 11,
          'font-weight': 500,
          'text-wrap': 'wrap',
          'text-max-width': '160px',
          'text-background-color': '#ffffff',
          'text-background-opacity': 0.95,
          'text-background-padding': '5px',
          'text-background-shape': 'roundrectangle',
          'text-border-color': '#e7e3d8',
          'text-border-width': 1,
          'text-border-opacity': 1,
          width: 'mapData(value, 1, 100, 30, 75)',
          height: 'mapData(value, 1, 100, 30, 75)',
          'transition-property': 'background-color, border-color, opacity',
          'transition-duration': 200 as any,
        },
      },
      // ── grupos (paleta institucional) ──────────────────
      {
        selector: 'node.group-entidad',
        style: {
          'background-color': '#1a3a5c',          // navy
          'border-color': '#0f2438',               // navy-deep
          'border-width': 2,
          shape: 'diamond',
          width: 70,
          height: 70,
          'font-weight': 700,
          'text-margin-y': -38,
        },
      },
      {
        selector: 'node.group-contratista',
        style: {
          'background-color': '#7a9ec2',          // navy-ui (azul UI claro)
          'border-color': '#2c5582',
        },
      },
      {
        selector: 'node.group-sancionado',
        style: {
          'background-color': '#a14545',          // err
          'border-color': '#7a3030',
        },
      },
      {
        selector: 'node.group-multado',
        style: {
          'background-color': '#c9a961',          // gold
          'border-color': '#b08e3f',               // gold-deep
        },
      },
      {
        selector: 'node.group-alto_riesgo',
        style: {
          'background-color': '#a14545',          // err
          'border-color': '#c9a961',               // gold como anillo de alerta
          'border-width': 3,
          'overlay-color': '#a14545',
          'overlay-opacity': 0.15,
          'overlay-padding': 6,
        },
      },
      // ── aristas ────────────────────────────────────────
      {
        selector: 'edge',
        style: {
          width: 'mapData(value, 1, 20, 1, 5)',
          'line-color': 'rgba(107, 119, 133, 0.45)',  // muted con alpha
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': 'rgba(107, 119, 133, 0.55)',
          'arrow-scale': 0.9,
          opacity: 0.85,
        },
      },
      // ── highlight neighborhood ─────────────────────────
      {
        selector: '.vd-faded',
        style: { opacity: 0.18, 'text-opacity': 0.3, 'z-index': 1 },
      },
      {
        selector: 'node.vd-highlighted',
        style: { opacity: 1, 'text-opacity': 1, 'z-index': 50 },
      },
      {
        selector: 'edge.vd-highlighted',
        style: {
          opacity: 1,
          width: 'mapData(value, 1, 20, 2, 6)',
          'line-color': '#c9a961',                  // gold (marca acento)
          'target-arrow-color': '#b08e3f',           // gold-deep
          'z-index': 60,
        },
      },
      {
        selector: 'node.vd-focused',
        style: {
          'border-color': '#c9a961',                 // gold ring
          'border-width': 4,
          'overlay-color': '#c9a961',
          'overlay-opacity': 0.18,
          'overlay-padding': 9,
          'z-index': 100,
        },
      },
    ];
  }
}
