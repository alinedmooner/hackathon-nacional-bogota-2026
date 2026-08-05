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
