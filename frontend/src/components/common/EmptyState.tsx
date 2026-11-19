import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Leaf } from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Spacing } from '../../theme';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  subtitle?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({ title, subtitle, actionLabel, onAction, icon }: EmptyStateProps) {
  return (
    <View style={styles.container} accessibilityRole="text">
      <View style={styles.iconWrap}>
        {icon ?? <Leaf size={40} color={Colors.sageSoft} />}
      </View>
      <Text style={styles.title}>{title}</Text>
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      {actionLabel && onAction && (
        <Button
          label={actionLabel}
          onPress={onAction}
          variant="outline"
          style={styles.btn}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.xxxl,
    paddingVertical: Spacing.xxxl,
  },
  iconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  title: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
  subtitle: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: Spacing.lg,
  },
  btn: {
    marginTop: Spacing.sm,
  },
});
