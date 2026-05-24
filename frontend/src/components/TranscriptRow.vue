<script setup lang="ts">
import type { DisplayMode, TranscriptRow } from '@/types';

defineProps<{
  row: TranscriptRow;
  displayMode: DisplayMode;
}>();

function timeRange(row: TranscriptRow): string {
  if (row.t0 == null || row.t1 == null) return '';
  return `${Number(row.t0).toFixed(1)}-${Number(row.t1).toFixed(1)}s`;
}
</script>

<template>
  <article class="row" :class="{ final: row.kind === 'final', error: row.error }">
    <div class="meta">
      <span class="badge" :class="row.kind === 'final' ? 'final' : 'partial'">
        {{ row.kind || 'event' }}
      </span>
      <span>{{ row.utterance_id != null ? `utt ${row.utterance_id}` : `seq ${row.seq}` }}</span>
      <span v-if="timeRange(row)">{{ timeRange(row) }}</span>
    </div>
    <div v-if="displayMode !== 'translation'" class="source">{{ row.text || '' }}</div>
    <div class="target" :class="{ pending: !row.translation && !row.error }">
      {{
        row.error ||
        row.translation ||
        (row.kind === 'final' ? 'Translation pending' : 'Partial ASR')
      }}
    </div>
  </article>
</template>
