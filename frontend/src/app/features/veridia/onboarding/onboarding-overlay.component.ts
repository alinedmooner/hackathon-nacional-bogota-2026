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
         class="fixed inset-0 z-[80] flex items-center justify-center bg-ink/30 backdrop-blur-sm">
      <div class="relative w-full max-w-md rounded border-t-4 border-navy bg-card shadow-xl">
        <div class="px-7 pt-6 pb-5">
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded bg-navy font-editorial text-2xl font-semibold text-cream shadow-[inset_0_-3px_0_var(--gold)]">
              V
            </div>
            <div>
              <p class="eyebrow">Bienvenido a</p>
              <h2 class="font-editorial text-2xl font-semibold leading-none text-ink">
                Verid<span class="text-navy">IA</span>
              </h2>
            </div>
          </div>

          <p class="mt-5 text-base leading-relaxed text-ink-2">
            Inteligencia anticorrupción para contratación pública.
            Conectamos SECOP con sanciones de Procuraduría, Contraloría y SIC,
            y te mostramos el razonamiento del agente paso a paso.
          </p>

          <div class="mt-5 rounded border border-line bg-cream-2 p-4">
            <p class="eyebrow">Tour guiado</p>
            <p class="mt-1 text-sm leading-relaxed text-ink-2">
              Te mostramos cómo investigar la
              <b class="text-navy">Alcaldía de Soacha</b>
              en seis pasos. Tu compañero narra · tú avanzas con el botón
              <b>Siguiente</b>.
            </p>
          </div>
        </div>

        <div class="flex gap-2 border-t border-line bg-cream-2 px-7 py-4">
          <button (click)="svc.dismissWelcome()"
                  class="btn-ghost flex-1">
            Saltar tour
          </button>
          <button (click)="svc.start()"
                  class="btn-primary flex-1">
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
           [class.bg-ink]="step.position === 'center'"
           [class.bg-opacity-30]="step.position === 'center'"
           [class.backdrop-blur-sm]="step.position === 'center'">
      </div>

      <!-- Caption posicionado según step.position -->
      <div class="fixed z-[75] w-[24rem]"
           [ngClass]="{
             'inset-0 flex items-center justify-center w-full': step.position === 'center',
             'top-24 right-6':              step.position === 'top-right',
             'top-28 left-6':               step.position === 'left',
             'top-1/2 -translate-y-1/2 right-6':       step.position === 'right',
             'bottom-24 right-6':           step.position === 'bottom-right',
             'bottom-24 left-6':            step.position === 'bottom-left'
           }">
        <div class="rounded border-t-4 border-gold bg-card shadow-xl"
             [class.max-w-lg]="step.position === 'center'">
          <div class="px-5 pt-4 pb-5">
            <!-- Header con # paso -->
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <span class="flex h-7 w-7 items-center justify-center rounded-full bg-navy font-editorial text-sm font-semibold text-cream">
                  {{ idx + 1 }}
                </span>
                <span class="eyebrow">
                  Paso {{ idx + 1 }} de {{ svc.steps.length }}
                </span>
              </div>
              <button (click)="svc.skip()"
                      title="Saltar tour (Esc)"
                      class="rounded px-2 py-0.5 text-xs uppercase tracking-wider text-muted transition hover:text-ink">
                Saltar
              </button>
            </div>

            <!-- Caption -->
            <p class="mt-3 text-base leading-relaxed text-ink-2"
               [class.text-lg]="step.position === 'center'">
              {{ step.caption }}
            </p>

            <!-- Indicadores de paso -->
            <div class="mt-4 flex gap-1.5">
              <span *ngFor="let s of svc.steps; let i = index"
                    class="h-1 flex-1 rounded-full transition"
                    [ngClass]="i <= idx ? 'bg-navy' : 'bg-line'">
              </span>
            </div>
          </div>

          <!-- Botón siguiente -->
          <div class="flex justify-end border-t border-line bg-cream-2 px-5 py-3">
            <button (click)="svc.next()"
                    class="btn-primary">
              {{ step.cta }} →
            </button>
          </div>
        </div>
      </div>
    </ng-container>
  `,
})
export class OnboardingOverlayComponent implements OnInit, OnDestroy {
  readonly svc = inject(OnboardingService);

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
