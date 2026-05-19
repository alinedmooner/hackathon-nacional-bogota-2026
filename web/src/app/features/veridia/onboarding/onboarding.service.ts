import { Injectable } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';

export type OnboardingStepId =
  | 'welcome'
  | 'ask-natural'
  | 'reasoning'
  | 'graph'
  | 'evidence'
  | 'closing';

export interface OnboardingStep {
  id: OnboardingStepId;
  /** Caption narrativo (lo que el compañero amplía). */
  caption: string;
  /** Posición visual del dialog en pantalla. */
  position: 'center' | 'top-right' | 'right' | 'left' | 'bottom-right' | 'bottom-left';
  /** Texto del botón principal */
  cta: string;
}

export type OnboardingEvent =
  | { kind: 'open-chat-with-question'; text: string }
  | { kind: 'simulate-stream' }
  | { kind: 'close-chat' }
  | { kind: 'load-graph'; nit: string }
  | { kind: 'click-sancionado-node' }
  | { kind: 'reset' };

const STORAGE_KEY = 'veridia_onboarding_seen';

@Injectable({ providedIn: 'root' })
export class OnboardingService {
  private readonly _stepIndex$ = new BehaviorSubject<number>(-1);
  readonly stepIndex$ = this._stepIndex$.asObservable();

  private readonly _showWelcome$ = new BehaviorSubject<boolean>(false);
  readonly showWelcome$ = this._showWelcome$.asObservable();

  /** Eventos que componentes (chat, grafo) escuchan para reaccionar. */
  readonly events$ = new Subject<OnboardingEvent>();

  readonly steps: OnboardingStep[] = [
    {
      id: 'welcome',
      caption:
        'VeridIA es una capa de inteligencia que conecta SECOP con sanciones de Procuraduría, Contraloría y SIC. ' +
        'Te mostramos cómo funciona en menos de un minuto.',
      position: 'center',
      cta: '▶ Comenzar',
    },
    {
      id: 'ask-natural',
      caption:
        'Cualquier ciudadano puede preguntar en español natural. ' +
        'No necesita saber SQL, ni qué es SIRI, ni navegar 8 portales del Estado.',
      position: 'left',
      cta: 'Siguiente',
    },
    {
      id: 'reasoning',
      caption:
        'El agente DECIDE qué consultar. Aquí ves el razonamiento explicable: ' +
        'descarga 47 cédulas únicas de SECOP, las cruza con SIRI y verifica las fechas. ' +
        'No es un script — es planificación autónoma.',
      position: 'left',
      cta: 'Siguiente',
    },
    {
      id: 'graph',
      caption:
        'El resultado es visual. Las banderas rojas saltan al instante: ' +
        'dos contratistas con inhabilidad vigente firmaron contratos con la Alcaldía.',
      position: 'top-right',
      cta: 'Siguiente',
    },
    {
      id: 'evidence',
      caption:
        'Cada hallazgo trae cédula, fecha de la sanción, fecha de la firma, monto y URL pública. ' +
        'Cualquiera puede verificarlo HOY en SECOP y en el portal SIRI de la Procuraduría.',
      position: 'left',
      cta: 'Siguiente',
    },
    {
      id: 'closing',
      caption:
        'Lo que acabas de ver tomó treinta segundos. Un auditor humano tardaría días. ' +
        'Eso es VeridIA.',
      position: 'center',
      cta: 'Cerrar tour',
    },
  ];

  // ────────────────────────────────────────────────────────────
  // API pública
  // ────────────────────────────────────────────────────────────

  /** Llama esto al cargar la app: muestra dialog si nunca ha visto el tour. */
  bootstrap(): void {
    if (!this.hasSeenOnboarding()) {
      this._showWelcome$.next(true);
    }
  }

  /** Lanza el tour desde el primer paso (welcome). */
  start(): void {
    this._showWelcome$.next(false);
    this._stepIndex$.next(0);
  }

  /** Muestra el dialog inicial otra vez (botón en header). */
  openWelcome(): void {
    this._showWelcome$.next(true);
  }

  /** Cancela el dialog inicial (saltar). */
  dismissWelcome(): void {
    this._showWelcome$.next(false);
    this.markSeen();
  }

  /** Avanza al siguiente paso. Si era el último, cierra y dispara reset. */
  next(): void {
    const i = this._stepIndex$.value;
    if (i < 0) return;

    const nextIdx = i + 1;
    if (nextIdx >= this.steps.length) {
      this.finish();
      return;
    }

    this._stepIndex$.next(nextIdx);
    this.runStepSideEffects(this.steps[nextIdx].id);
  }

  /** Cierra el tour en cualquier momento. */
  skip(): void {
    this.finish();
  }

  /** Estado actual */
  get currentStepIndex(): number {
    return this._stepIndex$.value;
  }
  get currentStep(): OnboardingStep | null {
    const i = this._stepIndex$.value;
    return i >= 0 ? this.steps[i] : null;
  }
  get isActive(): boolean {
    return this._stepIndex$.value >= 0;
  }

  // ────────────────────────────────────────────────────────────
  // Internos
  // ────────────────────────────────────────────────────────────
  private finish(): void {
    this._stepIndex$.next(-1);
    this._showWelcome$.next(false);
    this.markSeen();
    this.events$.next({ kind: 'reset' });
  }

  /** Side effects al entrar en cada paso (acciones automáticas en la UI). */
  private runStepSideEffects(stepId: OnboardingStepId): void {
    switch (stepId) {
      case 'ask-natural':
        // Abre chat con la pregunta ya tipeada (y la dispara para que se vea
        // el burbujeo del usuario inmediatamente)
        this.events$.next({
          kind: 'open-chat-with-question',
          text: 'Analiza la Alcaldía de Soacha',
        });
        break;
      case 'reasoning':
        // Dispara el stream simulado (events SSE pre-grabados)
        this.events$.next({ kind: 'simulate-stream' });
        break;
      case 'graph':
        // Cierra el chat y carga el grafo de Soacha
        this.events$.next({ kind: 'close-chat' });
        this.events$.next({ kind: 'load-graph', nit: '800094391' });
        break;
      case 'evidence':
        // Auto-click en uno de los nodos sancionados para abrir panel detalle
        this.events$.next({ kind: 'click-sancionado-node' });
        break;
      // welcome y closing no tienen side effects automáticos
    }
  }

  private hasSeenOnboarding(): boolean {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  }

  private markSeen(): void {
    try {
      localStorage.setItem(STORAGE_KEY, 'true');
    } catch {
      /* noop */
    }
  }
}
