/**
 * AgriGuard Auth Store (Zustand)
 * Persists JWT + user info via web-safe storage adapter.
 * On native: expo-secure-store (encrypted).
 * On web: localStorage (acceptable for demo).
 * Token getter registered into the API client on hydration.
 */

import { create } from 'zustand';
import * as Storage from '../utils/storage';
import { setTokenGetter, TokenResponse } from '../api/client';

const TOKEN_KEY = 'agriguard_token';
const USER_KEY = 'agriguard_user';
const LANG_KEY = 'agriguard_lang';

interface AuthUser {
  user_id: number;
  phone_number: string;
  full_name: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  language: 'en' | 'rw';
  isHydrated: boolean;

  // Actions
  setAuth: (resp: TokenResponse) => Promise<void>;
  logout: () => Promise<void>;
  setLanguage: (lang: 'en' | 'rw') => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Register the token getter with the API client
  setTokenGetter(() => get().token);

  return {
    token: null,
    user: null,
    language: 'rw', // Default to Kinyarwanda for Rwandan farmers
    isHydrated: false,

    setAuth: async (resp: TokenResponse) => {
      const user: AuthUser = {
        user_id: resp.user_id,
        phone_number: resp.phone_number,
        full_name: resp.full_name,
        role: resp.role,
      };
      await Storage.setItem(TOKEN_KEY, resp.access_token);
      await Storage.setItem(USER_KEY, JSON.stringify(user));
      set({ token: resp.access_token, user });
    },

    logout: async () => {
      await Storage.deleteItem(TOKEN_KEY);
      await Storage.deleteItem(USER_KEY);
      set({ token: null, user: null });
    },

    setLanguage: async (lang: 'en' | 'rw') => {
      await Storage.setItem(LANG_KEY, lang);
      set({ language: lang });
    },

    hydrate: async () => {
      try {
        const token = await Storage.getItem(TOKEN_KEY);
        const userJson = await Storage.getItem(USER_KEY);
        const langStr = await Storage.getItem(LANG_KEY);
        const user = userJson ? (JSON.parse(userJson) as AuthUser) : null;
        const language = (langStr === 'en' || langStr === 'rw') ? langStr : 'rw';
        set({ token, user, language, isHydrated: true });
      } catch {
        set({ isHydrated: true });
      }
    },
  };
});
