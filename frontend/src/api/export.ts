import type { DisplayMode, TranscriptRow } from '@/types';

export function finalRows(rows: TranscriptRow[]): TranscriptRow[] {
  return rows.filter((row) => row.kind === 'final');
}

function rowText(row: TranscriptRow, displayMode: DisplayMode): string {
  if (displayMode === 'translation') {
    return row.error || row.translation || '';
  }
  return [row.text, row.error || row.translation].filter(Boolean).join('\n');
}

function vttTime(seconds: number | undefined): string {
  const value = Math.max(0, Number(seconds) || 0);
  const h = Math.floor(value / 3600);
  const m = Math.floor((value % 3600) / 60);
  const s = Math.floor(value % 60);
  const ms = Math.floor((value - Math.floor(value)) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(
    2,
    '0',
  )}.${String(ms).padStart(3, '0')}`;
}

export function vttText(rows: TranscriptRow[], displayMode: DisplayMode): string {
  const cues = finalRows(rows).map((row, index) => {
    const start = row.t0 != null ? Number(row.t0) : index * 3;
    const end = row.t1 != null ? Number(row.t1) : start + 3;
    const text = rowText(row, displayMode);
    return `${index + 1}\n${vttTime(start)} --> ${vttTime(Math.max(end, start + 0.5))}\n${text}`;
  });
  return `WEBVTT\n\n${cues.join('\n\n')}\n`;
}

export function downloadText(name: string, text: string, type: string): void {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
