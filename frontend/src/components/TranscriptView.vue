<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';

import type { DisplayMode, TranscriptRow as Row } from '@/types';

import TranscriptRow from './TranscriptRow.vue';

const props = defineProps<{
  rows: Row[];
  displayMode: DisplayMode;
  autoScroll: boolean;
  textSize: number;
}>();

const transcriptRef = ref<HTMLElement | null>(null);

watch(
  () => props.rows,
  async () => {
    if (!props.autoScroll) return;
    await nextTick();
    if (transcriptRef.value) transcriptRef.value.scrollTop = transcriptRef.value.scrollHeight;
  },
  { deep: true },
);
</script>

<template>
  <section
    ref="transcriptRef"
    class="transcript"
    :style="{ '--transcript-font-size': `${textSize}px` }"
  >
    <div v-if="!rows.length" class="empty">Waiting for transcript events.</div>
    <TranscriptRow
      v-for="row in rows"
      v-else
      :key="row.key"
      :row="row"
      :display-mode="displayMode"
    />
  </section>
</template>
