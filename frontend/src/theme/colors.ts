/**
 * AgriGuard Design System — Colour Tokens
 * Warm, human, agricultural. Forest greens with cream warmth.
 * Semantic severity colours only for risk/status indicators.
 * WCAG AA contrast verified on all button/text combinations.
 */

export const Colors = {
  // ── Brand greens ───────────────────────────────────────────────────────
  deepForest:       '#0F3D24',   // Deepest green — logo, hero gradient top
  primaryForest:    '#1A6B3C',   // Forest green — headers, nav active
  secondaryEmerald: '#16A34A',   // Emerald — primary buttons, links
  sageSoft:         '#A7C4A0',   // Sage — borders, icons on light bg
  mintBg:           '#E6F4EA',   // Mint — card backgrounds, section fills
  limeAccent:       '#C5E86C',   // Lime — small highlights ONLY (badges, dots)

  // ── Surface & text ────────────────────────────────────────────────────
  backgroundWarm:   '#F9FAF5',   // Warm cream — page background
  backgroundCard:   '#FFFFFF',   // Pure white — card surfaces
  backgroundSage:   '#EFF5EE',   // Very light sage — secondary card bg
  charcoal:         '#17251B',   // Primary text — dark forest charcoal
  charcoalMuted:    '#4A5A50',   // Secondary text
  charcoalLight:    '#7A8F82',   // Placeholders, captions
  border:           '#C8DEC4',   // Sage-tinted border
  borderLight:      '#E4EEE2',   // Very light border

  // ── Severity (semantic — risk levels only, never decorative) ──────────
  severityLow:          '#6EE7B7',
  severityLowBg:        '#ECFDF5',
  severityLowText:      '#065F46',
  severityMedium:       '#FCD34D',
  severityMediumBg:     '#FFFBEB',
  severityMediumText:   '#92400E',
  severityHigh:         '#F97316',
  severityHighBg:       '#FFF7ED',
  severityHighText:     '#7C2D12',
  severityCritical:     '#EF4444',
  severityCriticalBg:   '#FEF2F2',
  severityCriticalText: '#7F1D1D',

  // ── Utility ───────────────────────────────────────────────────────────
  success:   '#16A34A',
  successBg: '#DCFCE7',
  error:     '#DC2626',
  errorBg:   '#FEF2F2',
  warning:   '#D97706',
  warningBg: '#FFFBEB',

  // ── Neutrals ──────────────────────────────────────────────────────────
  white:  '#FFFFFF',
  black:  '#000000',

  // ── Overlay ───────────────────────────────────────────────────────────
  overlay:      'rgba(15, 61, 36, 0.5)',
  overlayLight: 'rgba(15, 61, 36, 0.12)',

  // ── Backwards-compatibility aliases ──────────────────────────────────
  backgroundSage: '#EFF5EE',   // alias → backgroundSage
  sageSoft:       '#A7C4A0',   // alias → sageSoft
  successBg:      '#DCFCE7',   // alias → successBg
  info:           '#2563EB',   // kept for status chips
  infoBg:         '#EFF6FF',
} as const;

export type ColorKey = keyof typeof Colors;

/** Map severity string from API to colour tokens */
export const severityColorMap: Record<string, { text: string; bg: string; badge: string }> = {
  LOW: {
    text: Colors.severityLowText,
    bg:   Colors.severityLowBg,
    badge: Colors.severityLow,
  },
  MEDIUM: {
    text: Colors.severityMediumText,
    bg:   Colors.severityMediumBg,
    badge: Colors.severityMedium,
  },
  HIGH: {
    text: Colors.severityHighText,
    bg:   Colors.severityHighBg,
    badge: Colors.severityHigh,
  },
  CRITICAL: {
    text: Colors.severityCriticalText,
    bg:   Colors.severityCriticalBg,
    badge: Colors.severityCritical,
  },
  // AI service variants (title-case)
  Low:      { text: Colors.severityLowText,      bg: Colors.severityLowBg,      badge: Colors.severityLow      },
  Moderate: { text: Colors.severityMediumText,   bg: Colors.severityMediumBg,   badge: Colors.severityMedium   },
  High:     { text: Colors.severityHighText,     bg: Colors.severityHighBg,     badge: Colors.severityHigh     },
  Critical: { text: Colors.severityCriticalText, bg: Colors.severityCriticalBg, badge: Colors.severityCritical },
};
