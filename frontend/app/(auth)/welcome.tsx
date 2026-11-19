/**
 * Screen 1 — Welcome / Onboarding
 * First screen a new farmer sees.
 * Language toggle is prominent — equal interface, not an afterthought.
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  Image,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Shield, Leaf, Users } from 'lucide-react-native';
import { Button } from '../../src/components/common/Button';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { width, height } = Dimensions.get('window');

const features = [
  { icon: Leaf, titleKey: 'report.step1Title', descKey: 'home.reportSubtitle' },
  { icon: Shield, titleKey: 'aiResult.title', descKey: 'aiResult.noResult' },
  { icon: Users, titleKey: 'alerts.title', descKey: 'alerts.subtitle' },
];

export default function WelcomeScreen() {
  const router = useRouter();
  const { t, tr } = useTranslation();
  const insets = useSafeAreaInsets();

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={{ flexGrow: 1 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero section */}
      <LinearGradient
        colors={[Colors.primaryForest, '#0F4A28', Colors.primaryForest + 'CC']}
        style={[styles.hero, { paddingTop: insets.top + 16 }]}
      >
        {/* Language toggle — top right */}
        <View style={styles.langRow}>
          <LanguageToggle />
        </View>

        {/* Logo / branding */}
        <View style={styles.logoWrap}>
          <View style={styles.logoCircle}>
            <Leaf size={40} color={Colors.limeAccent} />
          </View>
          <Text style={styles.appName}>{t.appName}</Text>
          <Text style={styles.tagline}>{t.tagline}</Text>
        </View>

        {/* Decorative arc */}
        <View style={styles.arc} />
      </LinearGradient>

      {/* Features */}
      <View style={styles.featuresSection}>
        {features.map(({ icon: Icon, titleKey, descKey }, i) => (
          <View key={i} style={styles.featureRow}>
            <View style={styles.featureIcon}>
              <Icon size={22} color={Colors.secondaryEmerald} />
            </View>
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>{tr(titleKey)}</Text>
              <Text style={styles.featureDesc}>{tr(descKey)}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* CTA Buttons */}
      <View style={[styles.cta, { paddingBottom: insets.bottom + Spacing.lg }]}>
        <Button
          label={t.auth.register}
          onPress={() => router.push('/(auth)/register')}
          variant="primary"
          size="lg"
          fullWidth
          style={styles.btnPrimary}
        />
        <Button
          label={t.auth.login}
          onPress={() => router.push('/(auth)/login')}
          variant="outline"
          size="lg"
          fullWidth
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: Colors.backgroundWarm,
  },
  hero: {
    minHeight: height * 0.45,
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.xxxl,
    position: 'relative',
  },
  langRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: Spacing.xxxl,
  },
  logoWrap: {
    alignItems: 'center',
    marginTop: Spacing.lg,
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(197, 232, 108, 0.2)',
    borderWidth: 2,
    borderColor: Colors.limeAccent + '60',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.base,
  },
  appName: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h1,
    color: Colors.white,
    letterSpacing: -0.5,
    marginBottom: Spacing.xs,
  },
  tagline: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
  },
  arc: {
    position: 'absolute',
    bottom: -1,
    left: 0,
    right: 0,
    height: 32,
    backgroundColor: Colors.backgroundWarm,
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
  },
  featuresSection: {
    paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.lg,
    gap: Spacing.base,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.base,
  },
  featureIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  featureText: {
    flex: 1,
    paddingTop: 2,
  },
  featureTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    marginBottom: 2,
  },
  featureDesc: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: Colors.charcoalMuted,
    lineHeight: 20,
  },
  cta: {
    paddingHorizontal: Spacing.xl,
    gap: Spacing.md,
  },
  btnPrimary: {
    // Forest green is too dark for primary — use Emerald
  },
});
