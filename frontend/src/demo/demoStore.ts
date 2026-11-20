/**
 * AgriGuard Demo Mode Store
 *
 * Controls whether the app shows real API data or the clearly-labelled
 * demo/sample data defined in data.ts.
 *
 * Rules:
 * - Demo mode is a frontend-only feature.
 * - It never modifies the backend, database, or AI service.
 * - It never silently replaces real API responses.
 * - The demo banner is always visible when active.
 * - Disabling demo mode restores the original API-driven behaviour.
 */

import { create } from 'zustand';

interface DemoState {
  isDemoMode: boolean;
  enableDemo: () => void;
  disableDemo: () => void;
}

export const useDemoStore = create<DemoState>((set) => ({
  isDemoMode: false,
  enableDemo: () => set({ isDemoMode: true }),
  disableDemo: () => set({ isDemoMode: false }),
}));
