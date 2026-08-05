import { Pipe, PipeTransform } from '@angular/core';

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
