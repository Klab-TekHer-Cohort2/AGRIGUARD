/**
 * Screen 2 — Register (Farmer account)
 * POST /auth/register
 * Fields: phone_number, password, full_name, preferred_language,
 *         district, sector (optional but helpful for location-aware alerts)
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
import { Phone, Lock, User, MapPin, Leaf } from 'lucide-react-native';
import { Button } from '../../src/components/common/Button';
import { Input } from '../../src/components/common/Input';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { ErrorBanner } from '../../src/components/common/ErrorBanner';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useAuthStore } from '../../src/store/authStore';
import { authApi } from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type Language = 'rw' | 'en';

export default function RegisterScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const setLanguage = useAuthStore((s) => s.setLanguage);
  const insets = useSafeAreaInsets();

  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [district, setDistrict] = useState('');
  const [sector, setSector] = useState('');
  const [preferredLang, setPreferredLang] = useState<Language>('rw');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!fullName.trim() || fullName.trim().length < 2) errs.fullName = t.auth.fieldRequired;
    if (!phone.trim()) errs.phone = t.auth.fieldRequired;
    if (!password || password.length < 6) errs.password = t.auth.passwordTooShort;
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleRegister() {
    if (!validate()) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await authApi.register({
        phone_number: phone.trim(),
        password,
        full_name: fullName.trim(),
        role: 'FARMER',
        preferred_language: preferredLang,
        district: district.trim() || undefined,
        sector: sector.trim() || undefined,
      });
      await setAuth(resp);
      await setLanguage(preferredLang);
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
        {/* Top bar */}
        <View style={[styles.topBar, { paddingTop: insets.top + 8 }]}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backHit}>
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

        <Text style={styles.title}>{t.auth.register}</Text>
        <Text style={styles.subtitle}>{t.auth.welcomeSubtitle}</Text>

        {error && <ErrorBanner error={error} />}

        <View style={styles.form}>
          <Input
            label={t.auth.fullName}
            placeholder={t.auth.fullNameHint}
            value={fullName}
            onChangeText={setFullName}
            autoCapitalize="words"
            autoComplete="name"
            error={fieldErrors.fullName}
            leftIcon={<User size={18} color={Colors.charcoalLight} />}
          />
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
            autoComplete="new-password"
            error={fieldErrors.password}
            leftIcon={<Lock size={18} color={Colors.charcoalLight} />}
          />

          {/* Language preference */}
          <View style={styles.langSection}>
            <Text style={styles.langLabel}>{t.auth.preferredLanguage}</Text>
            <View style={styles.langRow}>
              {(['rw', 'en'] as Language[]).map((lang) => (
                <TouchableOpacity
                  key={lang}
                  onPress={() => setPreferredLang(lang)}
                  style={[
                    styles.langOption,
                    preferredLang === lang && styles.langOptionActive,
                  ]}
                  accessibilityRole="button"
                  accessibilityState={{ selected: preferredLang === lang }}
                  accessibilityLabel={lang === 'rw' ? 'Kinyarwanda' : 'English'}
                >
                  <Text
                    style={[
                      styles.langOptionText,
                      preferredLang === lang && styles.langOptionTextActive,
                    ]}
                  >
                    {lang === 'rw' ? '🇷🇼 Ikinyarwanda' : '🇬🇧 English'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Optional location fields */}
          <Text style={styles.optionalLabel}>
            {t.auth.district} ({t.common.optional})
          </Text>
          <Input
            placeholder={t.auth.districtHint}
            value={district}
            onChangeText={setDistrict}
            leftIcon={<MapPin size={18} color={Colors.charcoalLight} />}
            containerStyle={{ marginBottom: Spacing.sm }}
          />
          <Input
            placeholder={t.auth.sectorHint}
            value={sector}
            onChangeText={setSector}
            leftIcon={<MapPin size={18} color={Colors.charcoalLight} />}
          />
        </View>

        <Button
          label={t.auth.register}
          onPress={handleRegister}
          loading={loading}
          fullWidth
          size="lg"
          style={styles.btn}
        />

        <TouchableOpacity
          onPress={() => router.push('/(auth)/login')}
          style={styles.switchLink}
          accessibilityRole="button"
        >
          <Text style={styles.switchText}>{t.auth.alreadyHaveAccount}</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.backgroundWarm },
  scroll: { flex: 1 },
  content: { paddingHorizontal: Spacing.xl },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  backHit: { padding: Spacing.sm },
  backText: { fontSize: 22, color: Colors.charcoal, fontFamily: FontFamily.regular },
  logoWrap: { alignItems: 'center', marginBottom: Spacing.lg },
  logoCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
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
    marginBottom: Spacing.lg,
  },
  form: { marginBottom: Spacing.sm },
  langSection: { marginBottom: Spacing.base },
  langLabel: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.charcoal,
    marginBottom: Spacing.sm,
  },
  langRow: { flexDirection: 'row', gap: Spacing.sm },
  langOption: {
    flex: 1,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1.5,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  langOptionActive: {
    borderColor: Colors.secondaryEmerald,
    backgroundColor: Colors.successBg,
  },
  langOptionText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.charcoalMuted,
  },
  langOptionTextActive: { color: Colors.primaryForest },
  optionalLabel: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.charcoal,
    marginBottom: Spacing.sm,
  },
  btn: { marginBottom: Spacing.base },
  switchLink: { paddingVertical: Spacing.base, alignItems: 'center' },
  switchText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.body,
    color: Colors.secondaryEmerald,
  },
});
