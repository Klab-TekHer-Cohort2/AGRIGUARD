import { en } from './en';
import { rw } from './rw';

export type Language = 'en' | 'rw';
export type Translations = typeof en;

export const translations: Record<Language, typeof en> = {
  en,
  rw: rw as unknown as typeof en,
};

export { en, rw };
