/**
 * Welcome / Onboarding screen
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Shield, Leaf, Users, FlaskConical, Smartphone, Phone, MapPin } from 'lucide-react-native';
import { Button } from '../../src/components/common/Button';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { Colors, FontFamily, FontSize, Spacing, Radius, Shadow, MaxContentWidth } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDemoStore } from '../../src/demo/demoStore';
import { useAuthStore } from '../../src/store/authStore';
import { DEMO_PROFILE } from '../../src/demo/data';

const features = [
  { icon: Leaf,   title: 'AI Pest Detection',   desc: 'Photograph your crop and get an instant diagnosis.' },
  { icon: Shield, title: 'Outbreak Alerts',      desc: 'Know when pests are spreading near your community.' },
  { icon: Users,  title: 'Agronomist Support',   desc: 'Connect directly with certified extension officers.' },
];

export default function WelcomeScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const enableDemo = useDemoStore((s) => s.enableDemo);
  const setAuth = useAuthStore((s) => s.setAuth);
  const setLanguage = useAuthStore((s) => s.setLanguage);

  const handleEnterDemo = async () => {
    enableDemo();
    await setAuth({
      access_token: 'DEMO_TOKEN',
      token_type: 'bearer',
      role: 'FARMER',
      user_id: DEMO_PROFILE.id,
      phone_number: DEMO_PROFILE.phone_number,
      full_name: DEMO_PROFILE.full_name,
    });
    await setLanguage('en');
    router.replace('/(farmer)/home');
  };

  const handleLaunchChannel = async (route: '/(farmer)/ussd' | '/(farmer)/ivr' | '/(farmer)/outbreak-map') => {
    enableDemo();
    await setAuth({
      access_token: 'DEMO_TOKEN',
      token_type: 'bearer',
      role: 'FARMER',
      user_id: DEMO_PROFILE.id,
      phone_number: DEMO_PROFILE.phone_number,
      full_name: DEMO_PROFILE.full_name,
    });
    await setLanguage('en');
    router.push(route);
  };

  return (
    <View style={styles.root}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.centreCol}>
          {/* Hero */}
          <LinearGradient
            colors={[Colors.deepForest, Colors.primaryForest]}
            style={[styles.hero, { paddingTop: insets.top + 20 }]}
          >
            <View style={styles.langRow}>
              <LanguageToggle />
            </View>

            {/* Logo mark */}
            <View style={styles.logoWrap}>
              <View style={styles.logoCircle}>
                <Leaf size={36} color={Colors.limeAccent} />
              </View>
              <Text style={styles.appName}>AgriGuard</Text>
              <Text style={styles.tagline}>Protecting Rwanda's Harvests</Text>
            </View>

            <View style={styles.heroArc} />
          </LinearGradient>

          {/* Features */}
          <View style={styles.featuresSection}>
            {features.map(({ icon: Icon, title, desc }, i) => (
              <View key={i} style={styles.featureRow}>
                <View style={styles.featureIcon}>
                  <Icon size={22} color={Colors.secondaryEmerald} />
                </View>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>{title}</Text>
                  <Text style={styles.featureDesc}>{desc}</Text>
                </View>
              </View>
            ))}
          </View>

          {/* CTAs */}
          <View style={[styles.ctaSection, { paddingBottom: insets.bottom + Spacing.xxxl }]}>
            {/* Demo CTA — most prominent */}
            <TouchableOpacity
              onPress={handleEnterDemo}
              style={styles.demoCTA}
              activeOpacity={0.85}
              accessibilityLabel="Explore interactive demo with sample data"
              accessibilityRole="button"
            >
              <LinearGradient
                colors={[Colors.secondaryEmerald, Colors.primaryForest]}
                style={styles.demoCTAGrad}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.demoCTAIcon}>
                  <FlaskConical size={22} color={Colors.limeAccent} />
                </View>
                <View style={styles.demoCTAText}>
                  <Text style={styles.demoCTATitle}>Explore Interactive Demo</Text>
                  <Text style={styles.demoCTASub}>Try all features — no account needed</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>

            {/* Quick channel jump */}
            <View style={styles.channelsRow}>
              {[
                { label: 'USSD (*922#)', icon: <Smartphone size={14} color={Colors.primaryForest} />, route: '/(farmer)/ussd' as const },
                { label: 'IVR Voice',    icon: <Phone size={14} color={Colors.secondaryEmerald} />,  route: '/(farmer)/ivr' as const },
                { label: 'Outbreak Map', icon: <MapPin size={14} color={Colors.warning} />,           route: '/(farmer)/outbreak-map' as const },
              ].map(({ label, icon, route }) => (
                <TouchableOpacity
                  key={label}
                  style={styles.channelBtn}
                  onPress={() => handleLaunchChannel(route)}
                  activeOpacity={0.75}
                >
                  {icon}
                  <Text style={styles.channelBtnText}>{label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Divider */}
            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or sign in with your account</Text>
              <View style={styles.dividerLine} />
            </View>

            <Button
              label={t.auth.register}
              onPress={() => router.push('/(auth)/register')}
              variant="outline"
              size="lg"
              fullWidth
            />
            <Button
              label={t.auth.login}
              onPress={() => router.push('/(auth)/login')}
              variant="ghost"
              size="md"
              fullWidth
            />

            <View style={styles.demoNotice}>
              <FlaskConical size={12} color={Colors.charcoalLight} />
              <Text style={styles.demoNoticeText}>
                Demo mode uses sample data only. No real farm records are created or changed.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.backgroundWarm,
    // Centre content on wide screens
    ...(Platform.OS === 'web' ? { alignItems: 'center' } : {}),
  },
  scroll: { flex: 1, width: '100%' },
  scrollContent: {
    flexGrow: 1,
    ...(Platform.OS === 'web' ? { alignItems: 'center' } : {}),
  },
  centreCol: {
    width: '100%',
    maxWidth: MaxContentWidth,
    alignSelf: 'center',
    overflow: 'hidden',
  },
  hero: {
    paddingHorizontal: Spacing.xl,
    paddingBottom: Spacing.giant,
  },
  langRow: { flexDirection: 'row', justifyContent: 'flex-end', marginBottom: Spacing.xl },
  logoWrap: { alignItems: 'center', paddingBottom: Spacing.xxl },
  logoCircle: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: 'rgba(197,232,108,0.15)',
    borderWidth: 2,
    borderColor: Colors.limeAccent + '55',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.base,
  },
  appName: {
    fontFamily: FontFamily.bold,
    fontSize: 32,
    color: Colors.white,
    letterSpacing: -0.5,
    marginBottom: 4,
  },
  tagline: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: 'rgba(255,255,255,0.75)',
  },
  heroArc: {
    position: 'absolute',
    bottom: -1,
    left: 0,
    right: 0,
    height: 36,
    backgroundColor: Colors.backgroundWarm,
    borderTopLeftRadius: 36,
    borderTopRightRadius: 36,
  },
  featuresSection: {
    paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.lg,
    gap: Spacing.lg,
  },
  featureRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.base },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: Colors.mintBg,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  featureText: { flex: 1, paddingTop: 4 },
  featureTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    marginBottom: 3,
  },
  featureDesc: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: Colors.charcoalMuted,
    lineHeight: 20,
  },
  ctaSection: {
    paddingHorizontal: Spacing.xl,
    gap: Spacing.sm,
  },
  demoCTA: {
    borderRadius: Radius.xl,
    overflow: 'hidden',
    marginBottom: Spacing.sm,
    ...Shadow.md,
  },
  demoCTAGrad: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.lg,
    gap: Spacing.base,
  },
  demoCTAIcon: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  demoCTAText: { flex: 1 },
  demoCTATitle: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
    color: Colors.white,
    marginBottom: 2,
  },
  demoCTASub: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: 'rgba(255,255,255,0.8)',
  },
  channelsRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.sm },
  channelBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    backgroundColor: Colors.backgroundCard,
    paddingVertical: 10,
    paddingHorizontal: 6,
    borderRadius: Radius.lg,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    ...Shadow.xs,
  },
  channelBtnText: {
    fontFamily: FontFamily.semiBold,
    fontSize: 11,
    color: Colors.charcoal,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginVertical: Spacing.sm,
  },
  dividerLine: { flex: 1, height: 1, backgroundColor: Colors.borderLight },
  dividerText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalLight,
  },
  demoNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    padding: Spacing.sm,
    backgroundColor: Colors.backgroundSage,
    borderRadius: Radius.md,
    marginTop: Spacing.xs,
  },
  demoNoticeText: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalLight,
    lineHeight: 18,
  },
});
