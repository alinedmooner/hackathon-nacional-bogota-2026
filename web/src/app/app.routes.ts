import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { VeridiaComponent } from './features/veridia/veridia.component';
import { PerfilComponent } from './features/veridia/perfil/perfil.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  {
    path: 'graph',
    component: VeridiaComponent,
    canActivate: [authGuard],
  },
  {
    path: 'perfil/:doc',
    component: PerfilComponent,
    canActivate: [authGuard],
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard],
  },
  { path: '', redirectTo: 'graph', pathMatch: 'full' },
  { path: '**', redirectTo: 'graph' },
];
