import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ViewStyle,
  TextInputProps,
} from 'react-native';
import { Eye, EyeOff } from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Radius, Spacing } from '../../theme';

interface InputProps extends TextInputProps {
  label?: string;
  hint?: string;
  error?: string;
  containerStyle?: ViewStyle;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  password?: boolean;
}

export function Input({
  label,
  hint,
  error,
  containerStyle,
  leftIcon,
  rightIcon,
  password = false,
  ...props
}: InputProps) {
  const [focused, setFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const borderColor = error
    ? Colors.error
    : focused
    ? Colors.secondaryEmerald
    : Colors.border;

  return (
    <View style={[styles.container, containerStyle]}>
      {label && (
        <Text style={styles.label} accessibilityRole="text">
          {label}
        </Text>
      )}

      <View
        style={[
          styles.inputRow,
          { borderColor },
          focused && styles.focusedInput,
          error ? styles.errorInput : null,
        ]}
      >
        {leftIcon && <View style={styles.leftIcon}>{leftIcon}</View>}

        <TextInput
          {...props}
          secureTextEntry={password && !showPassword}
          style={[styles.input, leftIcon ? styles.inputWithLeft : null]}
          placeholderTextColor={Colors.charcoalLight}
          onFocus={(e) => {
            setFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            props.onBlur?.(e);
          }}
          accessibilityLabel={label}
          accessibilityHint={hint}
        />

        {password ? (
          <TouchableOpacity
            onPress={() => setShowPassword(!showPassword)}
            style={styles.rightIcon}
            accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? (
              <EyeOff size={18} color={Colors.charcoalLight} />
            ) : (
              <Eye size={18} color={Colors.charcoalLight} />
            )}
          </TouchableOpacity>
        ) : rightIcon ? (
          <View style={styles.rightIcon}>{rightIcon}</View>
        ) : null}
      </View>

      {error ? (
        <Text style={styles.errorText} accessibilityRole="alert">
          {error}
        </Text>
      ) : hint ? (
        <Text style={styles.hintText}>{hint}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: Spacing.base,
  },
  label: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.charcoal,
    marginBottom: Spacing.xs,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundCard,
    borderWidth: 1.5,
    borderRadius: Radius.md,
    borderColor: Colors.border,
    minHeight: 48,
  },
  focusedInput: {
    borderColor: Colors.secondaryEmerald,
    backgroundColor: Colors.backgroundCard,
  },
  errorInput: {
    borderColor: Colors.error,
  },
  input: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    minHeight: 48,
  },
  inputWithLeft: {
    paddingLeft: Spacing.sm,
  },
  leftIcon: {
    paddingLeft: Spacing.base,
  },
  rightIcon: {
    paddingRight: Spacing.base,
  },
  hintText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalLight,
    marginTop: Spacing.xs,
  },
  errorText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.error,
    marginTop: Spacing.xs,
  },
});
