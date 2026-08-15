import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'formatCurrency',
  standalone: true
})
export class FormatCurrencyPipe implements PipeTransform {
  transform(value: number | undefined | null): string {
    if (value === undefined || value === null) return '—';
    return '$' + value.toLocaleString('es-CO', { maximumFractionDigits: 0 });
  }
}

@Pipe({
  name: 'formatBytes',
  standalone: true
})
export class FormatBytesPipe implements PipeTransform {
  transform(bytes: number | null | undefined): string {
    if (bytes === null || bytes === undefined) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }
}

@Pipe({
  name: 'formatColumn',
  standalone: true
})
export class FormatColumnPipe implements PipeTransform {
  transform(column: string): string {
    return column ? column.replace(/_/g, ' ') : '';
  }
}

@Pipe({
  name: 'formatCOP',
  standalone: true
})
export class FormatCOPPipe implements PipeTransform {
  transform(value: number | undefined | null): string {
    if (value === undefined || value === null) return '—';
    if (value >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}B COP`;
    if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}MM COP`;
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M COP`;
    return `$${value.toLocaleString('es-CO')} COP`;
  }
}
