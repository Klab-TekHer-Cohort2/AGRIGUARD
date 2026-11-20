/**
 * DemoBanner — persistent indicator that demo mode is active.
 *
 * Displayed at the top of every screen when isDemoMode === true.
 * Never hidden, never dismissible mid-session, never deceiving.
 * The user can exit demo mode from the profile screen.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { FlaskConical } from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Spacing } from '../../theme';
import { useDemoStore } from '../../demo/demoStore';

export function DemoBanner() {
  const isDemoMode = useDemoStore((s) => s.isDemoMode);
  if (!isDemoMode) return null;

  return (
    <View style={styles.banner} accessibilityRole="status" accessibilityLabel="Demo mode active — showing sample data">
      <FlaskConical size={14} color={Colors.warning} />
      <Text style={styles.text} numberOfLines={2}>
        DEMO MODE — Showing sample data. No real farmer reports or AI predictions are being processed.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.warningBg,
    borderBottomWidth: 1,
    borderBottomColor: Colors.warning + '40',
    paddingHorizontal: Spacing.base,
    paddingVertical: 6,
    gap: Spacing.sm,
  },
  text: {
    flex: 1,
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.warning,
  },
});
