/**
 * Screen 3 — Login
 * Authenticates via POST /auth/login → JWT
 * Accepts phone number or email (backend handles both).
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Phone, Lock, Leaf } from 'lucide-react-native';
import { Button } from '../../src/components/common/Button';
import { Input } from '../../src/components/common/Input';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { ErrorBanner } from '../../src/components/common/ErrorBanner';
import { Colors, FontFamily, FontSize, Spacing } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useAuthStore } from '../../src/store/authStore';
import { authApi, ApiError } from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function LoginScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const insets = useSafeAreaInsets();

  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function validate() {
    const errs: Record<string, string> = {};
    if (!phone.trim()) errs.phone = t.auth.fieldRequired;
    if (!password) errs.password = t.auth.fieldRequired;
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleLogin() {
    if (!validate()) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await authApi.login({
        phone_number: phone.trim(),
        password,
      });
      await setAuth(resp);
      router.replace('/(farmer)/home');
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + Spacing.xxxl }]}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={[styles.topBar, { paddingTop: insets.top + 8 }]}>
          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.backHit}
            accessibilityLabel="Go back"
          >
            <Text style={styles.backText}>←</Text>
          </TouchableOpacity>
          <LanguageToggle compact />
        </View>

        {/* Logo */}
        <View style={styles.logoWrap}>
          <View style={styles.logoCircle}>
            <Leaf size={28} color={Colors.secondaryEmerald} />
          </View>
          <Text style={styles.appName}>{t.appName}</Text>
        </View>

        {/* Title */}
        <Text style={styles.title}>{t.auth.login}</Text>
        <Text style={styles.subtitle}>
          {t.auth.alreadyHaveAccount.replace('? Log In', '').replace('? Injira', '')}
        </Text>

        {/* Error */}
        {error && (
          <ErrorBanner error={error} />
        )}

        {/* Form */}
        <View style={styles.form}>
          <Input
            label={t.auth.phoneNumber}
            placeholder={t.auth.phoneHint}
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
            autoComplete="tel"
            error={fieldErrors.phone}
            leftIcon={<Phone size={18} color={Colors.charcoalLight} />}
          />
          <Input
            label={t.auth.password}
            placeholder={t.auth.passwordHint}
            value={password}
            onChangeText={setPassword}
            password
            autoComplete="password"
            error={fieldErrors.password}
            leftIcon={<Lock size={18} color={Colors.charcoalLight} />}
          />
        </View>

        <Button
          label={t.auth.login}
          onPress={handleLogin}
          loading={loading}
          fullWidth
          size="lg"
          style={styles.btn}
        />

        <TouchableOpacity
          onPress={() => router.push('/(auth)/register')}
          style={styles.switchLink}
          accessibilityRole="button"
        >
          <Text style={styles.switchText}>{t.auth.dontHaveAccount}</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.backgroundWarm },
  scroll: { flex: 1 },
  content: {
    paddingHorizontal: Spacing.xl,
    paddingTop: 0,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  backHit: {
    padding: Spacing.sm,
  },
  backText: {
    fontSize: 22,
    color: Colors.charcoal,
    fontFamily: FontFamily.regular,
  },
  logoWrap: {
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  logoCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: Colors.mintBg,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
    borderWidth: 1.5,
    borderColor: Colors.border,
  },
  appName: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h2,
    color: Colors.primaryForest,
  },
  title: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h1,
    color: Colors.charcoal,
    marginBottom: Spacing.xs,
  },
  subtitle: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    marginBottom: Spacing.xl,
  },
  form: {
    marginBottom: Spacing.sm,
  },
  btn: {
    marginBottom: Spacing.base,
  },
  switchLink: {
    paddingVertical: Spacing.base,
    alignItems: 'center',
  },
  switchText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.body,
    color: Colors.secondaryEmerald,
  },
});
