import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'dist/**',
      'build/**',
      'coverage/**',
      '.venv/**',
      'venv/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.strict,
);
