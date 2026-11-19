import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { AlertTriangle, RefreshCw, WifiOff } from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Radius, Spacing } from '../../theme';
import { useTranslation } from '../../hooks/useTranslation';
import { ApiError } from '../../api/client';

interface ErrorBannerProps {
  error: Error | ApiError | null;
  onRetry?: () => void;
}

/** Friendly error UI — never exposes raw API error messages to farmers */
export function ErrorBanner({ error, onRetry }: ErrorBannerProps) {
  const { t } = useTranslation();

  if (!error) return null;

  let message = t.common.error;
  let icon = <AlertTriangle size={20} color={Colors.error} />;

  if (error instanceof ApiError) {
    if (error.code === 'NETWORK' || error.code === '0') {
      message = t.common.networkError;
      icon = <WifiOff size={20} color={Colors.warning} />;
    } else if (error.status === 401) {
      message = t.common.unauthorized;
    } else if (error.status === 404) {
      message = t.common.notFound;
    } else if (error.status >= 500) {
      message = t.common.serverError;
    }
  } else if (error.message?.toLowerCase().includes('network')) {
    message = t.common.networkError;
    icon = <WifiOff size={20} color={Colors.warning} />;
  }

  return (
    <View style={styles.banner} accessibilityRole="alert">
      {icon}
      <Text style={styles.message}>{message}</Text>
      {onRetry && (
        <TouchableOpacity onPress={onRetry} style={styles.retry} accessibilityLabel={t.common.retry}>
          <RefreshCw size={16} color={Colors.primaryForest} />
          <Text style={styles.retryText}>{t.common.retry}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.errorBg,
    borderRadius: Radius.md,
    padding: Spacing.base,
    gap: Spacing.sm,
    flexWrap: 'wrap',
  },
  message: {
    flex: 1,
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.error,
  },
  retry: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 4,
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.md,
    backgroundColor: Colors.backgroundCard,
  },
  retryText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.primaryForest,
  },
});
