import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'formatColumn',
  standalone: true
})
export class FormatColumnPipe implements PipeTransform {
  transform(column: string): string {
    if (!column) return '';
    return column.replace(/_/g, ' ');
  }
}

@Pipe({
  name: 'formatCurrency',
  standalone: true
})
export class FormatCurrencyPipe implements PipeTransform {
  transform(value: number): string {
    if (value == null) return '';
    return '$' + value.toLocaleString('es-CO', { maximumFractionDigits: 0 });
  }
}

@Pipe({
  name: 'formatBytes',
  standalone: true
})
export class FormatBytesPipe implements PipeTransform {
  transform(bytes: number | null): string {
    if (bytes === null) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }
}
