import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface AnalysisResult {
  _id: string;
  timestamp: string;
  type: string;
  image_features: {
    mean_r: number;
    mean_g: number;
    mean_b: number;
    brightness: number;
    entropy: number;
  };
  ml_predictions: {
    confidence: number;
    predicted_class: number;
  };
  status: string;
  processing_time_ms: number;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'AI Analyzer';
  apiStatus = 'checking';
  results: AnalysisResult[] = [];
  loading = false;
  error = '';

  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.checkApiStatus();
    this.loadResults();
    setInterval(() => this.loadResults(), 10000);
  }

  checkApiStatus() {
    this.http.get<any>(`${this.apiUrl}/`).subscribe({
      next: (data) => {
        this.apiStatus = 'connected';
      },
      error: () => {
        this.apiStatus = 'disconnected';
      }
    });
  }

  loadResults() {
    this.loading = true;
    this.error = '';
    
    this.http.get<AnalysisResult[]>(`${this.apiUrl}/results`).subscribe({
      next: (data) => {
        this.results = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar los resultados: ' + err.message;
        this.loading = false;
      }
    });
  }

  refresh() {
    this.loadResults();
  }
}