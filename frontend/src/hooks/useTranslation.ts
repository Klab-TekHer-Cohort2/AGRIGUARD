/**
 * useTranslation hook — returns the translation object for current language
 * plus a helper t() that resolves nested keys safely.
 */

import { useAuthStore } from '../store/authStore';
import { translations } from '../i18n';
import type { Language } from '../i18n';

type NestedKeyOf<T extends object> = {
  [K in keyof T]: T[K] extends object
    ? `${string & K}.${NestedKeyOf<T[K]> & string}`
    : string & K;
}[keyof T];

export function useTranslation() {
  const language = useAuthStore((s) => s.language) as Language;
  const setLanguage = useAuthStore((s) => s.setLanguage);
  const t = translations[language] ?? translations['rw'];

  /** Resolve a dot-separated key, e.g. t('auth.login') */
  function tr(key: string): string {
    const parts = key.split('.');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let val: any = t;
    for (const part of parts) {
      if (val === undefined || val === null) return key;
      val = val[part];
    }
    return typeof val === 'string' ? val : key;
  }

  return { t, tr, language, setLanguage };
}
