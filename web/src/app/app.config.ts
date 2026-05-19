import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { RUNTIME_CONFIG, getRuntimeConfig } from './core/config/runtime-config';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    {
      provide: RUNTIME_CONFIG,
      useFactory: getRuntimeConfig
    }
  ]
};
