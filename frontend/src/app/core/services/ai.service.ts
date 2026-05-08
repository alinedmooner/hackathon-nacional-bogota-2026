import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { RUNTIME_CONFIG } from '../config/runtime-config';

export interface ToolCallLog {
  tool: string;
  input: Record<string, unknown>;
  result_summary: string;
  soql_url?: string | null;
}

export interface ChartItem {
  id: string;
  title: string;
  chart_js_spec: {
    type: 'bar' | 'line' | 'doughnut' | 'pie';
    data: { labels: string[]; datasets: any[] };
    options: any;
  };
}

export interface AiChatResponse {
  conversation_id: string;
  answer: string;
  tool_calls: ToolCallLog[];
  charts: ChartItem[];
  usage: { input_tokens: number; output_tokens: number };
  latency_ms: number;
}

export interface ConversationSummary {
  conversation_id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
}

@Injectable({ providedIn: 'root' })
export class AiService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(RUNTIME_CONFIG);

  private url(path: string): string {
    return `${this.config.backendUrl}/ai/${path}`;
  }

  sendMessage(message: string, conversationId: string | null): Observable<AiChatResponse> {
    return this.http.post<AiChatResponse>(this.url('chat'), {
      message,
      conversation_id: conversationId,
    });
  }

  listConversations(): Observable<ConversationSummary[]> {
    return this.http
      .get<ConversationSummary[]>(this.url('conversations'))
      .pipe(catchError(() => of([])));
  }

  getConversation(id: string): Observable<{ conversation_id: string; title: string; messages: any[] }> {
    return this.http.get<{ conversation_id: string; title: string; messages: any[] }>(
      this.url(`conversations/${id}`)
    );
  }
}
