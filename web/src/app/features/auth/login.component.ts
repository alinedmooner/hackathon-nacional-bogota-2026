import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { RUNTIME_CONFIG } from '../../core/config/runtime-config';

@Component({
  selector: 'app-login',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
})
export class LoginComponent {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly runtimeConfig = inject(RUNTIME_CONFIG);

  readonly backendUrl = this.runtimeConfig.backendUrl.replace(/\/$/, '');
  readonly docsUrl = `${this.backendUrl}/docs`;

  loading = signal(false);
  error = signal('');

  form = this.formBuilder.nonNullable.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]],
    remember: true,
  });

  submit(): void {
    if (this.form.invalid || this.loading()) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.error.set('');

    const { username, password, remember } = this.form.getRawValue();
    const storage = remember ? 'local' : 'session';

    this.authService.login({ username, password }, storage).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigateByUrl('/dashboard');
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.message ?? 'Credenciales invalidas.');
      },
    });
  }
}
