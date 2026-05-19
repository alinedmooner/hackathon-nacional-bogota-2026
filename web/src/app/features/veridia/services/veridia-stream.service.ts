import { Injectable, inject } from '@angular/core';

import { AuthService } from '../../../core/services/auth.service';
import { RUNTIME_CONFIG } from '../../../core/config/runtime-config';
import { SseEvent } from '../models/veridia.types';

/**
 * Cliente del endpoint POST /ai/chat/stream del backend.
 *
 * Usa fetch + ReadableStream porque EventSource nativo no soporta
 * POST ni headers personalizados (Authorization Bearer).
 *
 * El backend envía eventos SSE con `data: {json}\n\n`. Cada chunk
 * puede traer múltiples eventos o uno fragmentado, así que se
 * acumula en un buffer y se separa por `\n\n`.
 */
@Injectable({ providedIn: 'root' })
export class VeridiaStreamService {
  private readonly auth = inject(AuthService);
  private readonly config = inject(RUNTIME_CONFIG);

  /**
   * Async generator que produce eventos SSE conforme van llegando.
   *
   * Uso:
   *   for await (const ev of svc.streamChat(text, convId)) { ... }
   */
  async *streamChat(
    message: string,
    conversationId: string | null = null,
    signal?: AbortSignal,
  ): AsyncGenerator<SseEvent> {
    const url = `${this.config.backendUrl}/ai/chat/stream`;
    const token = this.auth.getToken();

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
      signal,
    });

    if (!response.ok) {
      yield {
        type: 'error',
        detail: `HTTP ${response.status} · ${response.statusText}`,
      };
      return;
    }
    if (!response.body) {
      yield { type: 'error', detail: 'response sin body' };
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Eventos SSE separados por línea doble \n\n
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          for (const line of part.split('\n')) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data:')) continue;
            const payload = trimmed.slice(5).trim();
            if (!payload) continue;
            try {
              yield JSON.parse(payload) as SseEvent;
            } catch {
              // ignorar JSON mal formado
            }
          }
        }
      }
    } finally {
      try {
        reader.releaseLock();
      } catch {
        /* noop */
      }
    }
  }
}
