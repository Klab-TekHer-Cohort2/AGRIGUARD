/**
 * AgriGuard Spacing & Layout Tokens
 * 8px base grid. Min touch target 48px (WCAG 2.5.5).
 * Desktop: content max-width 480px, centred on cream background.
 */

export const Spacing = {
  xs:   4,
  sm:   8,
  md:   12,
  base: 16,
  lg:   20,
  xl:   24,
  xxl:  32,
  xxxl: 40,
  huge: 48,
  giant: 64,
} as const;

export const Radius = {
  sm:   6,
  md:   10,
  lg:   16,   // Cards — warm, not extreme
  xl:   22,
  xxl:  30,
  full: 9999,
} as const;

export const Shadow = {
  xs: {
    shadowColor: '#0F3D24',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  sm: {
    shadowColor: '#0F3D24',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 2,
  },
  md: {
    shadowColor: '#0F3D24',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.09,
    shadowRadius: 12,
    elevation: 4,
  },
  lg: {
    shadowColor: '#0F3D24',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 20,
    elevation: 8,
  },
} as const;

/** Minimum touch target — WCAG 2.5.5 */
export const TouchTarget = 48;

/** Max content width for farmer screens on desktop */
export const MaxContentWidth = 480;
