import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'graph',
    loadComponent: () =>
      import('./features/veridia/veridia.component').then((m) => m.VeridiaComponent),
    canActivate: [authGuard],
  },
  {
    path: 'perfil/:doc',
    loadComponent: () =>
      import('./features/veridia/perfil/perfil.component').then((m) => m.PerfilComponent),
    canActivate: [authGuard],
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
    canActivate: [authGuard],
  },
  { path: '', redirectTo: 'graph', pathMatch: 'full' },
  { path: '**', redirectTo: 'graph' },
];
