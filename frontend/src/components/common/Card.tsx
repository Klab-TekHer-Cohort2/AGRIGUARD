import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { Colors, Radius, Shadow, Spacing } from '../../theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'default' | 'sage' | 'elevated' | 'flat';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({ children, style, variant = 'default', padding = 'md' }: CardProps) {
  const paddingMap = {
    none: 0,
    sm: Spacing.sm,
    md: Spacing.base,
    lg: Spacing.xl,
  };

  const variantStyles: Record<string, ViewStyle> = {
    default: {
      backgroundColor: Colors.backgroundCard,
      ...Shadow.sm,
    },
    sage: {
      backgroundColor: Colors.backgroundSage,
    },
    elevated: {
      backgroundColor: Colors.backgroundCard,
      ...Shadow.md,
    },
    flat: {
      backgroundColor: Colors.backgroundCard,
      borderWidth: 1,
      borderColor: Colors.borderLight,
    },
  };

  return (
    <View
      style={[
        styles.base,
        variantStyles[variant],
        { padding: paddingMap[padding] },
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: Radius.lg,
    overflow: 'hidden',
  },
});
