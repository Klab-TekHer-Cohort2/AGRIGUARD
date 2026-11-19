/**
 * AgriGuard Official Design System — Colour Tokens
 *
 * Palette selected from Coolors — green-based brand identity
 * combining agricultural trust with modern AI technology.
 */

export const Colors = {
  // ── Brand greens ──────────────────────────────────────────────────────────
  primaryForest: '#1A6B3C',   // Forest green — primary brand, sidebar, headings
  secondaryEmerald: '#16A34A', // Emerald — primary buttons, active nav items
  sageSoft: '#A7C4A0',         // Sage — subtle backgrounds, secondary cards
  limeAccent: '#C5E86C',       // Lime — highlights, selected states, visual accents

  // ── Surface & text ────────────────────────────────────────────────────────
  backgroundWarm: '#F9FAF5',   // Warm cream — main app background
  backgroundCard: '#FFFFFF',   // Pure white for card surfaces
  backgroundSage: '#EFF5EE',   // Very light sage for secondary cards
  charcoal: '#17251B',         // Dark charcoal — primary text
  charcoalMuted: '#4A5A50',    // Muted charcoal — secondary text
  charcoalLight: '#8A9B90',    // Light charcoal — placeholders, captions
  border: '#D4E0D1',           // Subtle green-tinted border
  borderLight: '#EAF0E8',      // Very light border for cards

  // ── Semantic severity (agricultural risk levels ONLY) ─────────────────────
  severityLow: '#6EE7B7',      // Soft green — LOW severity
  severityLowBg: '#ECFDF5',
  severityMedium: '#FCD34D',   // Amber — MEDIUM severity
  severityMediumBg: '#FFFBEB',
  severityHigh: '#F97316',     // Orange — HIGH severity
  severityHighBg: '#FFF7ED',
  severityCritical: '#EF4444', // Red — CRITICAL severity
  severityCriticalBg: '#FEF2F2',

  // ── Utility ───────────────────────────────────────────────────────────────
  success: '#16A34A',
  successBg: '#DCFCE7',
  error: '#DC2626',
  errorBg: '#FEF2F2',
  warning: '#D97706',
  warningBg: '#FFFBEB',
  info: '#2563EB',             // Blue — links and informational states only
  infoBg: '#EFF6FF',

  // ── Neutrals ─────────────────────────────────────────────────────────────
  white: '#FFFFFF',
  black: '#000000',
  grey50: '#F9FAF5',
  grey100: '#EFF5EE',
  grey200: '#D4E0D1',
  grey300: '#B4C8B0',
  grey400: '#8A9B90',
  grey500: '#617068',
  grey600: '#4A5A50',
  grey700: '#354040',
  grey800: '#232E28',
  grey900: '#17251B',

  // ── Overlay ───────────────────────────────────────────────────────────────
  overlay: 'rgba(23, 37, 27, 0.5)',
  overlayLight: 'rgba(23, 37, 27, 0.15)',
} as const;

export type ColorKey = keyof typeof Colors;

/** Map severity string from API → colour token */
export const severityColorMap: Record<string, { text: string; bg: string; badge: string }> = {
  LOW: {
    text: '#065F46',
    bg: Colors.severityLowBg,
    badge: Colors.severityLow,
  },
  MEDIUM: {
    text: '#92400E',
    bg: Colors.severityMediumBg,
    badge: Colors.severityMedium,
  },
  HIGH: {
    text: '#7C2D12',
    bg: Colors.severityHighBg,
    badge: Colors.severityHigh,
  },
  CRITICAL: {
    text: '#7F1D1D',
    bg: Colors.severityCriticalBg,
    badge: Colors.severityCritical,
  },
  // AI service uses "Moderate" spelling
  Moderate: {
    text: '#92400E',
    bg: Colors.severityMediumBg,
    badge: Colors.severityMedium,
  },
  High: {
    text: '#7C2D12',
    bg: Colors.severityHighBg,
    badge: Colors.severityHigh,
  },
  Critical: {
    text: '#7F1D1D',
    bg: Colors.severityCriticalBg,
    badge: Colors.severityCritical,
  },
  Low: {
    text: '#065F46',
    bg: Colors.severityLowBg,
    badge: Colors.severityLow,
  },
};
