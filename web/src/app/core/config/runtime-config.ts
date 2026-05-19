import { InjectionToken } from '@angular/core';

declare global {
  interface Window {
    __env?: {
      BACKEND_URL?: string;
    };
  }
}

export interface RuntimeConfig {
  backendUrl: string;
}

export const RUNTIME_CONFIG = new InjectionToken<RuntimeConfig>('runtime-config');

export const getRuntimeConfig = (): RuntimeConfig => {
  const fallbackUrl = '/api';
  const backendUrl = window.__env?.BACKEND_URL || fallbackUrl;
  return { backendUrl };
};
