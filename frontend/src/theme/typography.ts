/**
 * AgriGuard Typography System
 * Font: Inter (humanist sans-serif — renders Kinyarwanda cleanly)
 * Scale: display → heading → body → label
 * 12px minimum for anything a farmer reads.
 * Kinyarwanda text budget: +30% horizontal space.
 */

export const FontFamily = {
  regular: 'Inter_400Regular',
  medium: 'Inter_500Medium',
  semiBold: 'Inter_600SemiBold',
  bold: 'Inter_700Bold',
} as const;

export const FontSize = {
  /** Display: hero screens, splash (32–40px) */
  display: 36,
  displaySm: 32,

  /** Heading: section titles, card titles (20–28px) */
  h1: 28,
  h2: 24,
  h3: 20,

  /** Body: main reading text (14–16px) */
  bodyLg: 16,
  body: 15,
  bodySm: 14,

  /** Label: captions, badges, metadata (12px min) */
  label: 13,
  labelSm: 12,
} as const;

export const LineHeight = {
  display: 44,
  h1: 36,
  h2: 32,
  h3: 28,
  bodyLg: 26,
  body: 24,
  bodySm: 22,
  label: 20,
  labelSm: 18,
} as const;

export const LetterSpacing = {
  tight: -0.5,
  normal: 0,
  wide: 0.3,
  wider: 0.5,
} as const;
