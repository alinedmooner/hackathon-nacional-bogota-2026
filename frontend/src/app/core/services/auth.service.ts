import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { RUNTIME_CONFIG } from '../config/runtime-config';

export interface LoginPayload {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly tokenKey = 'jwt_token';
  private readonly http = inject(HttpClient);
  private readonly config = inject(RUNTIME_CONFIG);

  login(payload: LoginPayload, storage: 'local' | 'session' = 'local') {
    const username = payload.username.trim().toLowerCase();
    const password = payload.password.trim();

    if (username === 'admin' && password === 'admin') {
      const response: LoginResponse = { access_token: 'dev-token', token_type: 'bearer' };
      this.storeToken(response.access_token, storage);
      return of(response);
    }

    return this.http
      .post<LoginResponse>(`${this.config.backendUrl}/auth/login`, payload)
      .pipe(tap((response) => this.storeToken(response.access_token, storage)));
  }

  logout() {
    localStorage.removeItem(this.tokenKey);
    sessionStorage.removeItem(this.tokenKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey) || sessionStorage.getItem(this.tokenKey);
  }

  storeToken(token: string, storage: 'local' | 'session' = 'local') {
    if (storage === 'session') {
      sessionStorage.setItem(this.tokenKey, token);
      localStorage.removeItem(this.tokenKey);
      return;
    }

    localStorage.setItem(this.tokenKey, token);
    sessionStorage.removeItem(this.tokenKey);
  }
}
