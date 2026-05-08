import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { NgChartsModule } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import 'chart.js/auto';
import { AnalyticsService } from '../../core/services/analytics.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, NgChartsModule],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit {
  activeTab: 'records' | 'analytics' = 'records';
  barChartData: ChartConfiguration<'bar'>['data'] = { labels: [], datasets: [] };
  barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false
  };

  lineChartData: ChartConfiguration<'line'>['data'] = { labels: [], datasets: [] };
  lineChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false
  };

  doughnutChartData: ChartConfiguration<'doughnut'>['data'] = {
    labels: [],
    datasets: []
  };
  doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false
  };

  latencyChartData: ChartConfiguration<'line'>['data'] = { labels: [], datasets: [] };
  latencyChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false
  };

  snapshot = {
    activeUsers: 0,
    jobsProcessed: 0,
    alerts: 0
  };

  records: Array<Record<string, string | number | null>> = [];
  recordColumns: string[] = [];
  recordsLoading = false;
  recordsError = '';

  constructor(
    private readonly analyticsService: AnalyticsService,
    private readonly authService: AuthService,
    private readonly router: Router
  ) {}

  ngOnInit(): void {
    this.analyticsService.getWeeklyUsage().subscribe((series) => {
      this.barChartData = {
        labels: series.labels,
        datasets: [
          {
            data: series.values,
            label: 'Eventos por dia',
            backgroundColor: 'rgba(34, 197, 94, 0.6)'
          }
        ]
      };
    });

    this.analyticsService.getThroughput().subscribe((series) => {
      this.lineChartData = {
        labels: series.labels,
        datasets: [
          {
            data: series.values,
            label: 'Throughput',
            borderColor: '#7c3aed',
            backgroundColor: 'rgba(124, 58, 237, 0.25)',
            fill: true
          }
        ]
      };
    });

    this.doughnutChartData = {
      labels: ['OK', 'WARN', 'FAIL'],
      datasets: [
        {
          data: [68, 22, 10],
          backgroundColor: ['#22c55e', '#a855f7', '#ef4444']
        }
      ]
    };

    this.latencyChartData = {
      labels: ['00h', '03h', '06h', '09h', '12h', '15h', '18h', '21h'],
      datasets: [
        {
          data: [210, 240, 320, 260, 280, 350, 300, 220],
          label: 'Latency ms',
          borderColor: '#4ade80',
          backgroundColor: 'rgba(34, 197, 94, 0.2)',
          fill: true
        }
      ]
    };

    this.analyticsService.getSnapshot().subscribe((snapshot) => {
      this.snapshot = snapshot;
    });

    this.loadRecords();
  }

  loadRecords() {
    this.recordsLoading = true;
    this.recordsError = '';

    this.analyticsService.getRecords().subscribe({
      next: (records) => {
        this.records = records;
        this.recordColumns = records.length > 0 ? Object.keys(records[0]) : [];
        this.recordsLoading = false;
      },
      error: () => {
        this.recordsLoading = false;
        this.recordsError = 'No se pudo cargar SECOP II.';
      }
    });
  }

  formatColumn(column: string): string {
    return column.replace(/_/g, ' ');
  }

  setTab(tab: 'records' | 'analytics') {
    this.activeTab = tab;
  }

  logout() {
    this.authService.logout();
    this.router.navigateByUrl('/login');
  }
}
