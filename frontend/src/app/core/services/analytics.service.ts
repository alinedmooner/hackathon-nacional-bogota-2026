import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

export interface UsageSeries {
  labels: string[];
  values: number[];
}

export interface UsageSnapshot {
  activeUsers: number;
  jobsProcessed: number;
  alerts: number;
}

export type RecordEntry = Record<string, string | number | null>;

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly secopUrl = '/datos-gov/api/v3/views/dmgg-8hin/query.json';
  getWeeklyUsage(): Observable<UsageSeries> {
    return of({
      labels: ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'],
      values: [120, 180, 90, 240, 260, 140, 200]
    });
  }

  getThroughput(): Observable<UsageSeries> {
    return of({
      labels: ['00h', '04h', '08h', '12h', '16h', '20h'],
      values: [20, 35, 60, 90, 70, 40]
    });
  }

  getSnapshot(): Observable<UsageSnapshot> {
    return of({
      activeUsers: 128,
      jobsProcessed: 842,
      alerts: 5
    });
  }

  getRecords(limit = 50): Observable<RecordEntry[]> {
    const params = new HttpParams().set('limit', limit.toString());

    return this.http.get<any>(this.secopUrl, { params }).pipe(
      map((response) => this.mapSocrataResponse(response)),
      catchError(() => of([]))
    );
  }

  private mapSocrataResponse(response: any): RecordEntry[] {
    if (!response) {
      return [];
    }

    if (Array.isArray(response)) {
      return response as RecordEntry[];
    }

    const columns = Array.isArray(response.columns) ? response.columns : [];
    const data = Array.isArray(response.data) ? response.data : [];

    if (!columns.length || !data.length) {
      return [];
    }

    const keys: string[] = columns.map((column: any, index: number) =>
      column.fieldName || column.name || column.id || `col_${index}`
    );

    return data.map((row: any) => {
      if (row && typeof row === 'object' && !Array.isArray(row)) {
        return row as RecordEntry;
      }

      const record: RecordEntry = {};
      if (Array.isArray(row)) {
        keys.forEach((key: string, index: number) => {
          record[key] = row[index] ?? null;
        });
      }

      return record;
    });
  }
}
