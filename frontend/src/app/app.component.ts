import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';

import { AuthService } from './core/services/auth.service';

interface NavLink {
  label: string;
  path: string;
  icon: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  title = 'VeridIA';

  // Si la ruta es una de estas, el contenido se renderiza full-width sin
  // el envoltorio max-w-6xl del shell (ej. el mapa Veridia).
  readonly fullWidthRoutes = ['/graph', '/login'];
  isFullWidth = false;
  isAuthRoute = false;

  readonly navLinks: NavLink[] = [
    { label: 'Mapa',      path: '/graph',     icon: '⌬' },
    { label: 'Dashboard', path: '/dashboard', icon: '▦' },
  ];

  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  constructor() {
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe((e) => {
        const url = e.urlAfterRedirects.split('?')[0];
        this.isFullWidth = this.fullWidthRoutes.some((r) => url.startsWith(r));
        this.isAuthRoute = url.startsWith('/login');
      });
  }

  get isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  logout(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
