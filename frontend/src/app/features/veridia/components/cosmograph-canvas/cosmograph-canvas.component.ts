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
          'border-width': 1.5,
          'border-color': 'rgba(15, 23, 42, 0.8)',
          'background-opacity': 0.92,
          label: 'data(label)',
          color: '#e2e8f0',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-margin-y': -26,
          'font-family': 'JetBrains Mono, ui-monospace, SFMono-Regular, monospace',
          'font-size': 10,
          'font-weight': 500,
          'text-wrap': 'wrap',
          'text-max-width': '150px',
          'text-background-color': 'rgba(8, 8, 13, 0.92)',
          'text-background-opacity': 1,
          'text-background-padding': '4px',
          'text-background-shape': 'roundrectangle',
          'text-border-color': 'rgba(148, 163, 184, 0.15)',
          'text-border-width': 1,
          'text-border-opacity': 1,
          width: 34,
          height: 34,
          'transition-property': 'background-color, border-color, width, height, opacity',
          'transition-duration': 200 as any,
        },
      },
      // ── tipos · paleta neón sobre dark slate (alineada con el shell) ──
      {
        selector: 'node.type-persona',
        style: {
          'background-color': '#22d3ee',         // cyan-400
          'border-color': '#0e7490',              // cyan-700
        },
      },
      {
        selector: 'node.type-empresa',
        style: {
          'background-color': '#fbbf24',         // amber-400 (menos agresivo que 500)
          'border-color': '#92400e',              // amber-800
          width: 40,
          height: 40,
        },
      },
      {
        selector: 'node.type-entidad',
        style: {
          'background-color': '#a78bfa',         // violet-400
          'border-color': '#6d28d9',              // violet-700
          width: 46,
          height: 46,
          shape: 'round-rectangle',
        },
      },
      {
        selector: 'node.type-contrato',
        style: {
          'background-color': '#34d399',         // emerald-400
          'border-color': '#047857',              // emerald-700
          width: 24,
          height: 24,
          shape: 'round-rectangle',
        },
      },
      {
        selector: 'node.type-sancion',
        style: {
          'background-color': '#fb7185',         // rose-400 (menos rojo agresivo)
          'border-color': '#9f1239',              // rose-800
          shape: 'diamond',
          width: 30,
          height: 30,
        },
      },
      // ── flagged (bandera roja) ─────────────────────────
      {
        selector: 'node.flagged',
        style: {
          'border-color': '#fb7185',              // rose-400 coherente
          'border-width': 3,
          'overlay-color': '#fb7185',
          'overlay-opacity': 0.18,
          'overlay-padding': 7,
        },
      },
      // ── neighborhood highlight ─────────────────────────
      // Elementos opacados (fuera del vecindario seleccionado)
      {
        selector: '.vd-faded',
        style: {
          opacity: 0.1,
          'text-opacity': 0.2,
          'z-index': 1,
        },
      },
      // Vecindario destacado: el nodo + sus aristas + sus vecinos
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
          width: 2.2,
          'line-color': '#d946ef',                  // fuchsia-500 (alineado con branding)
          'target-arrow-color': '#e879f9',          // fuchsia-400
          'z-index': 60,
          'text-background-opacity': 1,
          color: '#fbcfe8',                          // pink-200 para texto
        },
      },
      // Nodo focal (el clickeado): glow fuchsia coherente con la marca
      {
        selector: 'node.vd-focused',
        style: {
          'border-color': '#e879f9',                 // fuchsia-400
          'border-width': 4,
          'overlay-color': '#d946ef',                // fuchsia-500
          'overlay-opacity': 0.22,
          'overlay-padding': 9,
          'z-index': 100,
        },
      },
      // ── aristas ─────────────────────────────────────────
      {
        selector: 'edge',
        style: {
          width: 1.2,
          'line-color': 'rgba(100, 116, 139, 0.55)',  // slate-500 con alpha
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': 'rgba(100, 116, 139, 0.55)',
          'arrow-scale': 0.85,
          opacity: 0.85,
          label: 'data(label)',
          'font-family': 'JetBrains Mono, ui-monospace, SFMono-Regular, monospace',
          'font-size': 8,
          'font-weight': 500,
          color: '#94a3b8',
          'text-rotation': 'autorotate' as any,
          'text-background-color': 'rgba(8, 8, 13, 0.95)',
          'text-background-opacity': 1,
          'text-background-padding': '3px',
          'text-background-shape': 'roundrectangle',
          'text-border-color': 'rgba(148, 163, 184, 0.12)',
          'text-border-width': 1,
          'text-border-opacity': 1,
        },
      },
      {
        selector: 'edge[relacion="contrato"]',
        style: {
          'line-color': 'rgba(52, 211, 153, 0.7)',     // emerald-400 con alpha
          'target-arrow-color': 'rgba(52, 211, 153, 0.85)',
        },
      },
      {
        selector: 'edge[relacion="sancion"]',
        style: {
          'line-color': 'rgba(251, 113, 133, 0.85)',   // rose-400
          'target-arrow-color': '#fb7185',
          width: 2,
        },
      },
      {
        selector: 'edge[relacion="cargo"]',
        style: {
          'line-color': 'rgba(251, 191, 36, 0.7)',     // amber-400
          'target-arrow-color': '#fbbf24',
          'line-style': 'dashed',
        },
      },
      {
        selector: 'edge[relacion="control"]',
        style: {
          'line-color': 'rgba(167, 139, 250, 0.7)',    // violet-400
          'target-arrow-color': '#a78bfa',
        },
      },
      {
        selector: 'edge[relacion="comparte_rl"], edge[relacion="comparte_dir"], edge[relacion="familiar"]',
        style: {
          'line-color': 'rgba(244, 114, 182, 0.6)',    // pink-400
          'target-arrow-color': '#f472b6',
          'line-style': 'dotted',
        },
      },
      {
        selector: 'edge.flagged',
        style: {
          'line-color': '#fb7185',
          'target-arrow-color': '#fb7185',
          width: 2.5,
          opacity: 1,
        },
      },
    ];
  }
}
