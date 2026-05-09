import { CommonModule } from '@angular/common';
import { Component, HostListener, OnDestroy, OnInit, inject } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { OnboardingService, OnboardingStep } from './onboarding.service';

@Component({
  selector: 'app-onboarding-overlay',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- ════════════════════════════════════════════════════════ -->
    <!-- Welcome dialog · primera vez o cuando se pide repetir    -->
    <!-- ════════════════════════════════════════════════════════ -->
    <div *ngIf="(svc.showWelcome$ | async)"
         class="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div class="relative w-full max-w-md rounded-2xl border border-fuchsia-500/30 bg-slate-950/95 p-7 shadow-2xl shadow-fuchsia-500/20">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-fuchsia-500 to-violet-600 text-xl font-bold text-white shadow-lg">
            V
          </div>
          <div>
            <p class="text-[10px] uppercase tracking-[0.3em] text-fuchsia-300">Bienvenido a</p>
            <h2 class="text-2xl font-semibold leading-none">
              Verid<span class="text-fuchsia-400">IA</span>
            </h2>
          </div>
        </div>

        <p class="mt-5 text-sm leading-relaxed text-slate-300">
          Inteligencia anticorrupción para contratación pública en Colombia.
          Conectamos SECOP con sanciones de Procuraduría, Contraloría y SIC,
          y mostramos el razonamiento del agente paso a paso.
        </p>

        <div class="mt-6 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p class="text-[10px] uppercase tracking-widest text-slate-500">Tour guiado</p>
          <p class="mt-1 text-xs leading-relaxed text-slate-300">
            Te mostramos cómo investigar la <b class="text-fuchsia-200">Alcaldía de Soacha</b> en seis pasos.
            Tu compañero narra · tú avanzas con el botón <b>Siguiente</b>.
          </p>
        </div>

        <div class="mt-6 flex gap-2">
          <button (click)="svc.dismissWelcome()"
                  class="flex-1 rounded-xl border border-slate-700 px-4 py-2.5 text-xs font-semibold uppercase tracking-widest text-slate-400 transition hover:border-slate-600 hover:text-slate-200">
            Saltar tour
          </button>
          <button (click)="svc.start()"
                  class="flex-1 rounded-xl bg-gradient-to-r from-fuchsia-500 to-violet-600 px-4 py-2.5 text-xs font-semibold uppercase tracking-widest text-white shadow-lg shadow-fuchsia-500/30 transition hover:shadow-fuchsia-500/50">
            ▶ Comenzar tour
          </button>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════ -->
    <!-- Overlay del tour activo                                   -->
    <!-- ════════════════════════════════════════════════════════ -->
    <ng-container *ngIf="step">
      <!-- Backdrop oscurece toda la UI cuando estamos en step center -->
      <div class="pointer-events-none fixed inset-0 z-[70]"
           [class.bg-black]="step.position === 'center'"
           [class.bg-opacity-60]="step.position === 'center'"
           [class.backdrop-blur-sm]="step.position === 'center'">
      </div>

      <!-- Caption posicionado según step.position -->
      <div class="fixed z-[75] w-[22rem]"
           [ngClass]="{
             'inset-0 flex items-center justify-center w-full': step.position === 'center',
             'top-20 right-6':              step.position === 'top-right',
             'top-24 left-6':               step.position === 'left',
             'top-1/2 -translate-y-1/2 right-6':       step.position === 'right',
             'bottom-24 right-6':           step.position === 'bottom-right',
             'bottom-24 left-6':            step.position === 'bottom-left'
           }">
        <div class="rounded-2xl border border-fuchsia-500/40 bg-slate-950/95 p-5 shadow-2xl shadow-fuchsia-500/30 backdrop-blur"
             [class.max-w-lg]="step.position === 'center'">
          <!-- Header con # paso -->
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-fuchsia-500 to-violet-600 text-xs font-bold text-white">
                {{ idx + 1 }}
              </span>
              <span class="text-[10px] uppercase tracking-[0.25em] text-fuchsia-300">
                Paso {{ idx + 1 }} de {{ svc.steps.length }}
              </span>
            </div>
            <button (click)="svc.skip()"
                    title="Saltar tour (Esc)"
                    class="rounded-md px-2 py-0.5 text-[10px] uppercase tracking-widest text-slate-500 transition hover:text-slate-300">
              Saltar
            </button>
          </div>

          <!-- Caption -->
          <p class="mt-3 text-sm leading-relaxed text-slate-200"
             [class.text-base]="step.position === 'center'">
            {{ step.caption }}
          </p>

          <!-- Indicadores de paso -->
          <div class="mt-4 flex gap-1.5">
            <span *ngFor="let s of svc.steps; let i = index"
                  class="h-1 flex-1 rounded-full transition"
                  [ngClass]="i <= idx ? 'bg-fuchsia-500' : 'bg-slate-700'">
            </span>
          </div>

          <!-- Botón siguiente -->
          <div class="mt-4 flex justify-end">
            <button (click)="svc.next()"
                    class="rounded-xl bg-fuchsia-500/90 px-5 py-2 text-xs font-semibold uppercase tracking-widest text-white transition hover:bg-fuchsia-500">
              {{ step.cta }}
              <span class="ml-1 text-fuchsia-200">→</span>
            </button>
          </div>
        </div>
      </div>
    </ng-container>
  `,
})
export class OnboardingOverlayComponent implements OnInit, OnDestroy {
  readonly svc = inject(OnboardingService);

  // Estado local reactivo (necesitamos getters porque idx=0 es válido pero falsy)
  idx = -1;
  step: OnboardingStep | null = null;

  private readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.svc.stepIndex$
      .pipe(takeUntil(this.destroy$))
      .subscribe((i) => {
        this.idx = i;
        this.step = i >= 0 ? this.svc.steps[i] : null;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Atajos de teclado
  @HostListener('window:keydown.arrowright')
  @HostListener('window:keydown.space')
  onNext(): void {
    if (this.svc.isActive) this.svc.next();
  }

  @HostListener('window:keydown.escape')
  onEscape(): void {
    if (this.svc.isActive) this.svc.skip();
  }
}
