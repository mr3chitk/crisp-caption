<script setup lang="ts">
import type { DotState } from '@/types';

defineProps<{
  state: DotState;
}>();
</script>

<template>
  <span class="dot" :class="state"></span>
</template>
