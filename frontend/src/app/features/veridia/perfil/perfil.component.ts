import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Subject } from 'rxjs';
import { switchMap, takeUntil } from 'rxjs/operators';

import { Perfil } from '../models/veridia.types';
import { VeridiaService } from '../services/veridia.service';

interface NivelBadge {
  label: string;
  cls: string;
  color: string;
}

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="mx-auto w-full max-w-5xl px-6 py-8">

      <!-- Breadcrumb -->
      <nav class="mb-4 flex items-center gap-2 text-xs text-muted">
        <a routerLink="/graph" class="hover:text-navy">Mapa</a>
        <span>›</span>
        <span>Perfil</span>
      </nav>

      <!-- Loading -->
      <div *ngIf="loading" class="rounded border border-line bg-card p-12 text-center">
        <div class="mx-auto flex w-fit space-x-1">
          <span class="h-2 w-2 animate-bounce rounded-full bg-navy"></span>
          <span class="h-2 w-2 animate-bounce rounded-full bg-navy" style="animation-delay: 0.15s"></span>
          <span class="h-2 w-2 animate-bounce rounded-full bg-navy" style="animation-delay: 0.3s"></span>
        </div>
        <p class="mt-3 eyebrow">Cargando perfil…</p>
      </div>

      <!-- Error / no encontrado -->
      <div *ngIf="error" class="rounded border-l-4 border-err bg-card p-6">
        <p class="eyebrow">Sin registros</p>
        <h2 class="mt-1 font-editorial text-xl font-semibold text-ink">{{ error }}</h2>
        <a routerLink="/graph" class="mt-3 inline-block text-sm text-navy hover:underline">
          ← Volver al mapa
        </a>
      </div>

      <!-- Perfil cargado -->
      <ng-container *ngIf="perfil as p">

        <!-- Header con badge de nivel -->
        <div class="rounded border-t-4 bg-card p-6 shadow-sm"
             [style.border-top-color]="badge(p.nivel_alerta).color">
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0 flex-1">
              <p class="eyebrow">Documento</p>
              <h1 class="mt-1 font-editorial text-2xl font-semibold text-ink tabular">
                {{ p.documento }}
              </h1>
            </div>
            <span class="shrink-0 rounded border px-3 py-1 text-xs font-bold uppercase"
                  [ngClass]="badge(p.nivel_alerta).cls">
              {{ badge(p.nivel_alerta).label }}
            </span>
          </div>
        </div>

        <!-- KPI cards -->
        <div class="mt-6 grid gap-4 md:grid-cols-4">
          <div class="rounded border-l-4 border-navy bg-card p-4">
            <p class="eyebrow">Contratos SECOP</p>
            <p class="mt-1 font-editorial text-2xl font-semibold text-navy tabular">
              {{ p.secop?.total_contratos ?? 0 }}
            </p>
          </div>
          <div class="rounded border-l-4 border-navy bg-card p-4">
            <p class="eyebrow">Valor total</p>
            <p class="mt-1 font-editorial text-lg font-semibold text-navy tabular">
              {{ formatCOP(p.secop?.valor_total_cop ?? 0) }}
            </p>
          </div>
          <div class="rounded border-l-4 border-err bg-card p-4">
            <p class="eyebrow">Inhabilitaciones SIRI</p>
            <p class="mt-1 font-editorial text-2xl font-semibold text-err tabular">
              {{ p.siri.length }}
            </p>
          </div>
          <div class="rounded border-l-4 border-gold bg-card p-4">
            <p class="eyebrow">Multas</p>
            <p class="mt-1 font-editorial text-2xl font-semibold text-gold-deep tabular">
              {{ p.multas.length }}
            </p>
          </div>
        </div>

        <!-- Sanciones SIRI -->
        <section *ngIf="p.siri.length" class="mt-6 rounded border-l-4 border-err bg-card p-6">
          <p class="eyebrow">Procuraduría</p>
          <h2 class="mt-1 font-editorial text-lg font-semibold text-err">
            Inhabilitaciones SIRI
          </h2>
          <ul class="mt-4 space-y-3">
            <li *ngFor="let s of p.siri"
                class="rounded border border-line bg-cream-2 p-4 text-sm">
              <p class="font-semibold text-ink">{{ s.sanciones || 'Sanción registrada' }}</p>
              <p class="mt-1 text-xs text-muted tabular">
                <span *ngIf="s.fecha_inicio">{{ s.fecha_inicio }}</span>
                <span *ngIf="s.fecha_fin"> → {{ s.fecha_fin }}</span>
                <span *ngIf="s.duracion_anos"> · {{ s.duracion_anos }} año(s)</span>
              </p>
            </li>
          </ul>
        </section>

        <!-- Multas -->
        <section *ngIf="p.multas?.length" class="mt-6 rounded border-l-4 border-gold bg-card p-6">
          <p class="eyebrow">Multas</p>
          <h2 class="mt-1 font-editorial text-lg font-semibold text-gold-deep">
            Sanciones administrativas
          </h2>
          <ul class="mt-4 space-y-3">
            <li *ngFor="let m of p.multas"
                class="rounded border border-line bg-cream-2 p-4 text-sm">
              <p class="font-semibold text-ink">{{ m.entidad_que_multo || 'Entidad sancionadora' }}</p>
              <p class="mt-1 font-mono text-xs text-muted tabular">{{ m.fecha_multa }} · {{ formatCOP(m.valor_sancion) }}</p>
            </li>
          </ul>
        </section>

        <!-- Contratos SECOP -->
        <section *ngIf="p.secop?.contratos?.length" class="mt-6 rounded bg-card p-6">
          <p class="eyebrow">SECOP II</p>
          <h2 class="mt-1 font-editorial text-lg font-semibold text-ink">
            Contratos vigentes
          </h2>
          <div class="mt-4 overflow-x-auto">
            <table class="w-full text-xs text-ink">
              <thead class="border-b-2 border-line-strong text-[10px] uppercase tracking-widest text-muted">
                <tr>
                  <th class="px-3 py-2 text-left font-semibold">Contrato</th>
                  <th class="px-3 py-2 text-left font-semibold">Entidad</th>
                  <th class="px-3 py-2 text-left font-semibold">Firma</th>
                  <th class="px-3 py-2 text-right font-semibold">Valor</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-line">
                <tr *ngFor="let c of p.secop?.contratos" class="hover:bg-cream-2">
                  <td class="px-3 py-2 font-mono text-ink-2">{{ c.id_contrato }}</td>
                  <td class="px-3 py-2 text-ink-2">{{ c.nombre_entidad }}</td>
                  <td class="px-3 py-2 text-muted tabular">{{ c.fecha_de_firma }}</td>
                  <td class="px-3 py-2 text-right font-mono text-navy tabular">{{ formatCOP(c.valor) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Estado vacío total -->
        <section *ngIf="!p.siri?.length && !p.multas?.length && !p.secop?.contratos?.length"
                 class="mt-6 rounded border border-dashed border-line-strong bg-card p-8 text-center">
          <p class="eyebrow">Sin registros</p>
          <p class="mt-2 text-sm text-ink-2">
            No se encontraron contratos ni sanciones para este documento.
          </p>
        </section>

      </ng-container>
    </div>
  `,
})
export class PerfilComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(VeridiaService);
  private readonly destroy$ = new Subject<void>();

  perfil: Perfil | null = null;
  loading = false;
  error = '';

  ngOnInit(): void {
    this.route.paramMap
      .pipe(
        takeUntil(this.destroy$),
        switchMap((params) => {
          const doc = (params.get('doc') ?? '').replace(/\D/g, '');
          this.loading = true;
          this.perfil = null;
          this.error = '';
          return this.api.getPerfil(doc);
        }),
      )
      .subscribe({
        next: (p) => {
          this.perfil = p;
          this.loading = false;
        },
        error: () => {
          this.loading = false;
          this.error = 'No hay registros para este documento.';
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  badge(nivel: Perfil['nivel_alerta']): NivelBadge {
    return {
      rojo:     { label: 'Inhabilitado',     cls: 'border-err/30 bg-err/10 text-err',                   color: '#a14545' },
      naranja:  { label: 'Multado',          cls: 'border-gold/40 bg-gold/15 text-gold-deep',           color: '#b08e3f' },
      amarillo: { label: 'Puerta giratoria', cls: 'border-gold/40 bg-gold/10 text-gold-deep',           color: '#c9a961' },
      verde:    { label: 'Sin alertas',      cls: 'border-ok/30 bg-ok/10 text-ok',                      color: '#4d7a3e' },
    }[nivel] ?? { label: nivel, cls: 'border-line bg-cream-2 text-ink-2', color: '#c8c2b0' };
  }

  formatCOP(value: number | undefined): string {
    if (value === undefined || value === null) return '—';
    if (value >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}B COP`;
    if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}MM COP`;
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M COP`;
    return `$${value.toLocaleString('es-CO')} COP`;
  }
}
