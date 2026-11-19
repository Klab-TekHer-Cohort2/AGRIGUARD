import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
  View,
} from 'react-native';
import { Colors, FontFamily, FontSize, Radius, Spacing, TouchTarget } from '../../theme';

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  accessibilityLabel?: string;
}

const variantStyles: Record<Variant, { container: ViewStyle; text: TextStyle }> = {
  primary: {
    container: { backgroundColor: Colors.secondaryEmerald },
    text: { color: Colors.white },
  },
  secondary: {
    container: { backgroundColor: Colors.primaryForest },
    text: { color: Colors.white },
  },
  outline: {
    container: {
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      borderColor: Colors.secondaryEmerald,
    },
    text: { color: Colors.secondaryEmerald },
  },
  ghost: {
    container: { backgroundColor: 'transparent' },
    text: { color: Colors.secondaryEmerald },
  },
  danger: {
    container: { backgroundColor: Colors.error },
    text: { color: Colors.white },
  },
};

const sizeStyles: Record<Size, { container: ViewStyle; text: TextStyle; height: number }> = {
  sm: {
    container: { paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm },
    text: { fontSize: FontSize.bodySm },
    height: 36,
  },
  md: {
    container: { paddingHorizontal: Spacing.lg, paddingVertical: Spacing.md },
    text: { fontSize: FontSize.body },
    height: TouchTarget,
  },
  lg: {
    container: { paddingHorizontal: Spacing.xl, paddingVertical: Spacing.base },
    text: { fontSize: FontSize.bodyLg },
    height: 52,
  },
};

export function Button({
  label,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  iconRight,
  fullWidth = false,
  style,
  textStyle,
  accessibilityLabel,
}: ButtonProps) {
  const vs = variantStyles[variant];
  const ss = sizeStyles[size];
  const isDisabled = disabled || loading;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.75}
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      style={[
        styles.base,
        vs.container,
        ss.container,
        { minHeight: ss.height },
        fullWidth && styles.fullWidth,
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'outline' || variant === 'ghost' ? Colors.secondaryEmerald : Colors.white}
          size="small"
        />
      ) : (
        <View style={styles.inner}>
          {icon && <View style={styles.iconLeft}>{icon}</View>}
          <Text
            style={[styles.text, vs.text, ss.text, textStyle]}
            numberOfLines={1}
          >
            {label}
          </Text>
          {iconRight && <View style={styles.iconRight}>{iconRight}</View>}
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: Radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  fullWidth: {
    width: '100%',
  },
  disabled: {
    opacity: 0.5,
  },
  inner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.sm,
  },
  text: {
    fontFamily: FontFamily.semiBold,
    letterSpacing: 0.1,
  },
  iconLeft: {
    marginRight: 2,
  },
  iconRight: {
    marginLeft: 2,
  },
});
