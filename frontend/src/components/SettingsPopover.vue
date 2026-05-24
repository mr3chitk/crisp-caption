<script setup lang="ts">
import type { UiSettings } from '@/types';

defineProps<{
  settings: UiSettings;
}>();

defineEmits<{
  updateSettings: [settings: Partial<UiSettings>];
}>();

function checkedValue(event: Event): boolean {
  return (event.target as HTMLInputElement).checked;
}

function numberValue(event: Event): number {
  return Number((event.target as HTMLInputElement).value);
}

</script>

<template>
  <section class="settings-popover">
    <div class="settings-title">Settings</div>
    <div class="settings-list">
      <label class="check-row">
        <input
          :checked="settings.showPartials"
          type="checkbox"
          @change="$emit('updateSettings', { showPartials: checkedValue($event) })"
        />
        <span>Show partials</span>
      </label>
      <label class="check-row">
        <input
          :checked="settings.autoScroll"
          type="checkbox"
          @change="$emit('updateSettings', { autoScroll: checkedValue($event) })"
        />
        <span>Auto scroll</span>
      </label>
      <label class="field-row">
        <span>Display</span>
        <select
          :value="settings.displayMode"
          @change="
            $emit('updateSettings', {
              displayMode: ($event.target as HTMLSelectElement).value as UiSettings['displayMode'],
            })
          "
        >
          <option value="both">Source + translation</option>
          <option value="translation">Translation only</option>
        </select>
      </label>
      <label class="field-row">
        <span>Text size</span>
        <div class="range-control">
          <input
            :value="settings.transcriptFontPx"
            type="range"
            min="14"
            max="28"
            step="1"
            @input="$emit('updateSettings', { transcriptFontPx: numberValue($event) })"
          />
          <output>{{ settings.transcriptFontPx }}px</output>
        </div>
      </label>
    </div>
  </section>
</template>
