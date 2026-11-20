/**
 * Web-safe storage adapter
 *
 * expo-secure-store is native-only and throws on web.
 * This module wraps it with a localStorage fallback so the same
 * code works on both native and web without modification.
 *
 * On native:  uses expo-secure-store (encrypted)
 * On web:     uses localStorage (unencrypted — acceptable for demo)
 *
 * The authStore imports from here instead of directly from expo-secure-store.
 */

import { Platform } from 'react-native';

let SecureStore: typeof import('expo-secure-store') | null = null;

if (Platform.OS !== 'web') {
  // Dynamic require so the web bundle never attempts to load native code
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  SecureStore = require('expo-secure-store');
}

export async function setItem(key: string, value: string): Promise<void> {
  if (SecureStore) {
    await SecureStore.setItemAsync(key, value);
  } else {
    try {
      localStorage.setItem(key, value);
    } catch {
      // localStorage unavailable — no-op
    }
  }
}

export async function getItem(key: string): Promise<string | null> {
  if (SecureStore) {
    return SecureStore.getItemAsync(key);
  } else {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }
}

export async function deleteItem(key: string): Promise<void> {
  if (SecureStore) {
    await SecureStore.deleteItemAsync(key);
  } else {
    try {
      localStorage.removeItem(key);
    } catch {
      // no-op
    }
  }
}
