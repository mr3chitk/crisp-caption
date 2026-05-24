import js from '@eslint/js';
import prettier from '@vue/eslint-config-prettier';
import vueTs from '@vue/eslint-config-typescript';
import pluginVue from 'eslint-plugin-vue';

export default [
  {
    ignores: ['dist/**'],
  },
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  ...vueTs(),
  prettier,
];
