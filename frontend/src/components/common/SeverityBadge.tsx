import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, FontFamily, FontSize, Radius, Spacing, severityColorMap } from '../../theme';

interface SeverityBadgeProps {
  severity: string;
  size?: 'sm' | 'md';
}

/** Severity badge — semantic colour only, never decorative */
export function SeverityBadge({ severity, size = 'md' }: SeverityBadgeProps) {
  const upper = severity?.toUpperCase() ?? 'LOW';
  const normalised =
    upper === 'MODERATE' ? 'MEDIUM' :
    upper === 'LOW' ? 'LOW' :
    upper === 'HIGH' ? 'HIGH' :
    upper === 'CRITICAL' ? 'CRITICAL' :
    severity; // allow "Low", "High", etc.

  const colours = severityColorMap[normalised] ?? severityColorMap[severity] ?? {
    text: Colors.charcoal,
    bg: Colors.backgroundSage,
    badge: Colors.sageSoft,
  };

  const isSmall = size === 'sm';

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: colours.bg },
        isSmall && styles.badgeSm,
      ]}
      accessibilityRole="text"
      accessibilityLabel={`Severity: ${severity}`}
    >
      <View style={[styles.dot, { backgroundColor: colours.badge }]} />
      <Text
        style={[
          styles.text,
          { color: colours.text },
          isSmall && styles.textSm,
        ]}
      >
        {normalised}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: Radius.full,
    gap: Spacing.xs,
    alignSelf: 'flex-start',
  },
  badgeSm: {
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  text: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.label,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  textSm: {
    fontSize: FontSize.labelSm,
  },
});
