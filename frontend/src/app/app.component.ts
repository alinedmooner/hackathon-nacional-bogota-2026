import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';

import { AuthService } from './core/services/auth.service';
import { VeridiaChatComponent } from './features/veridia/components/veridia-chat/veridia-chat.component';
import { OnboardingOverlayComponent } from './features/veridia/onboarding/onboarding-overlay.component';
import { OnboardingService } from './features/veridia/onboarding/onboarding.service';

interface NavLink {
  label: string;
  path: string;
  icon: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    VeridiaChatComponent,
    OnboardingOverlayComponent,
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  title = 'VeridIA';

  // Si la ruta es una de estas, el contenido se renderiza full-width sin
  // el envoltorio max-w-6xl del shell (ej. el mapa Veridia).
  readonly fullWidthRoutes = ['/graph', '/login'];
  isFullWidth = false;
  isAuthRoute = false;

  chatOpen = false;

  readonly navLinks: NavLink[] = [
    { label: 'Mapa',      path: '/graph',     icon: '⌬' },
    { label: 'Dashboard', path: '/dashboard', icon: '▦' },
  ];

  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);
  readonly onboarding = inject(OnboardingService);

  constructor() {
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe((e) => {
        const url = e.urlAfterRedirects.split('?')[0];
        this.isFullWidth = this.fullWidthRoutes.some((r) => url.startsWith(r));
        this.isAuthRoute = url.startsWith('/login');
      });
  }

  ngOnInit(): void {
    // Muestra dialog inicial si nunca ha visto el tour
    this.onboarding.bootstrap();
  }

  startTour(): void {
    this.onboarding.openWelcome();
  }

  get isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  logout(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
