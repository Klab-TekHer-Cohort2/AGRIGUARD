import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, FontFamily, FontSize, Radius, Spacing } from '../../theme';
import { useTranslation } from '../../hooks/useTranslation';

interface StatusChipProps {
  status: string;
}

const statusConfig: Record<string, { bg: string; text: string; label?: string }> = {
  PENDING: { bg: '#FEF3C7', text: '#92400E' },
  AI_ANALYZED: { bg: '#ECFDF5', text: '#065F46' },
  AGRONOMIST_REVIEWING: { bg: '#EFF6FF', text: '#1D4ED8' },
  VERIFIED: { bg: '#DCFCE7', text: '#166534' },
  ESCALATED: { bg: '#FEF2F2', text: '#991B1B' },
  RESOLVED: { bg: Colors.backgroundSage, text: Colors.primaryForest },
  CLOSED: { bg: Colors.grey100, text: Colors.grey600 },
};

export function StatusChip({ status }: StatusChipProps) {
  const { t } = useTranslation();
  const cfg = statusConfig[status] ?? { bg: Colors.grey100, text: Colors.grey600 };
  const label = t.myReports.status[status as keyof typeof t.myReports.status] ?? status;

  return (
    <View
      style={[styles.chip, { backgroundColor: cfg.bg }]}
      accessibilityRole="text"
      accessibilityLabel={`Status: ${label}`}
    >
      <Text style={[styles.text, { color: cfg.text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: Radius.full,
    alignSelf: 'flex-start',
  },
  text: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.labelSm,
    letterSpacing: 0.3,
  },
});
