/**
 * Home Dashboard
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  RefreshControl, Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import {
  Plus, FileText, Bell, MessageCircle, ChevronRight,
  AlertTriangle, Leaf, Clock, BookOpen, Smartphone, Phone, MapPin,
} from 'lucide-react-native';
import { Card } from '../../src/components/common/Card';
import { StatusChip } from '../../src/components/common/StatusChip';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { Colors, FontFamily, FontSize, Spacing, Radius, Shadow, MaxContentWidth } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useAuthStore } from '../../src/store/authStore';
import {
  reportsApi, outbreakApi, farmersApi,
  CropReportResponse, AlertResponse, FarmerProfileResponse,
} from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDemoStore } from '../../src/demo/demoStore';
import { DEMO_PROFILE, DEMO_REPORTS, DEMO_ALERTS, DEMO_STATS } from '../../src/demo/data';

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function HomeScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const insets = useSafeAreaInsets();
  const isDemoMode = useDemoStore((s) => s.isDemoMode);

  const [profile, setProfile]           = useState<FarmerProfileResponse | null>(null);
  const [latestReport, setLatestReport] = useState<CropReportResponse | null>(null);
  const [alerts, setAlerts]             = useState<AlertResponse[]>([]);
  const [refreshing, setRefreshing]     = useState(false);
  const [loading, setLoading]           = useState(true);

  const loadData = useCallback(async () => {
    if (isDemoMode) {
      setProfile(DEMO_PROFILE);
      setLatestReport(DEMO_REPORTS[0]);
      setAlerts(DEMO_ALERTS.filter((a) => a.status === 'ACTIVE').slice(0, 2));
      setLoading(false);
      return;
    }
    try {
      const [prof, reports] = await Promise.allSettled([
        farmersApi.getProfile(),
        reportsApi.myReports({ limit: 1 }),
      ]);
      let district: string | undefined;
      if (prof.status === 'fulfilled')    { setProfile(prof.value);                    district = prof.value.locations?.[0]?.district; }
      if (reports.status === 'fulfilled') { setLatestReport(reports.value[0] ?? null); }
      if (district) {
        try { const a = await outbreakApi.listAlerts({ district, limit: 3 }); setAlerts(a.filter((x) => x.status === 'ACTIVE')); }
        catch { /* non-critical */ }
      }
    } catch { /* silent */ } finally { setLoading(false); }
  }, [isDemoMode]);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };
  const firstName = (profile?.full_name ?? user?.full_name ?? '').split(' ')[0];
  const district  = profile?.locations?.[0]?.district;

  return (
    <View style={styles.root}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 80 }]}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.limeAccent} />}
      >
        <View style={styles.centreCol}>
          {/* ── Header ───────────────────────────────────────────────── */}
          <LinearGradient
            colors={[Colors.deepForest, Colors.primaryForest]}
            style={[styles.header, { paddingTop: insets.top + 16 }]}
          >
            <View style={styles.headerRow}>
              <View style={styles.headerLeft}>
                <View style={styles.logoMark}>
                  <Leaf size={16} color={Colors.limeAccent} />
                </View>
                <View>
                  <Text style={styles.greeting}>{getGreeting()}, {firstName} 👋</Text>
                  {district && <Text style={styles.districtText}>📍 {district}</Text>}
                </View>
              </View>
              <LanguageToggle />
            </View>

            {isDemoMode && (
              <View style={styles.statsRow}>
                <StatPill label="Reports" value={String(DEMO_STATS.totalReports)} />
                <StatPill label="Farmers"  value={String(DEMO_STATS.totalFarmers)} />
                <StatPill label="Alerts"   value={String(DEMO_STATS.activeAlerts)} />
              </View>
            )}
          </LinearGradient>

          {/* ── Big CTA ──────────────────────────────────────────────── */}
          <View style={styles.ctaWrap}>
            <TouchableOpacity
              onPress={() => router.push('/(farmer)/report-new')}
              style={styles.bigCTA}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel={t.home.reportCTA}
            >
              <LinearGradient
                colors={[Colors.secondaryEmerald, '#12803A']}
                style={styles.bigCTAGrad}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              >
                <View style={styles.bigCTAIcon}>
                  <Plus size={28} color={Colors.white} />
                </View>
                <View style={styles.bigCTABody}>
                  <Text style={styles.bigCTATitle}>{t.home.reportCTA}</Text>
                  <Text style={styles.bigCTASub}>{t.home.reportSubtitle}</Text>
                </View>
                <ChevronRight size={20} color="rgba(255,255,255,0.65)" />
              </LinearGradient>
            </TouchableOpacity>
          </View>

          {/* ── Body ─────────────────────────────────────────────────── */}
          <View style={styles.body}>
            {/* Alert strip */}
            {alerts.length > 0 && (
              <TouchableOpacity
                onPress={() => router.push('/(farmer)/alerts')}
                activeOpacity={0.85}
                accessibilityRole="button"
                style={styles.alertStrip}
              >
                <View style={[styles.alertStripBar, { backgroundColor: alerts[0].severity === 'CRITICAL' ? Colors.severityCritical : Colors.warning }]} />
                <AlertTriangle size={18} color={Colors.warning} />
                <View style={styles.alertStripText}>
                  <Text style={styles.alertStripTitle}>
                    {t.home.communityAlert}{isDemoMode ? ' (sample)' : ''}
                  </Text>
                  <Text style={styles.alertStripDesc} numberOfLines={1}>
                    {alerts[0].title_en ?? alerts[0].pest_name}
                  </Text>
                </View>
                <SeverityBadge severity={alerts[0].severity} size="sm" />
                <ChevronRight size={15} color={Colors.charcoalLight} />
              </TouchableOpacity>
            )}

            {/* Quick actions */}
            <View style={styles.quickActions}>
              <QuickAction icon={<FileText    size={22} color={Colors.primaryForest} />} label={t.home.myReports}    onPress={() => router.push('/(farmer)/reports')} />
              <QuickAction icon={<MessageCircle size={22} color={Colors.primaryForest} />} label={t.home.askAgriGuard} onPress={() => router.push('/(farmer)/ask')} />
              <QuickAction icon={<Bell         size={22} color={Colors.primaryForest} />} label={t.nav.alerts}       onPress={() => router.push('/(farmer)/alerts')} />
              <QuickAction icon={<BookOpen     size={22} color={Colors.primaryForest} />} label="Advice"             onPress={() => router.push('/(farmer)/advice')} />
            </View>

            {/* Latest report */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                {t.home.lastReport}{isDemoMode ? ' (sample)' : ''}
              </Text>
              <TouchableOpacity onPress={() => router.push('/(farmer)/reports')} accessibilityRole="button">
                <Text style={styles.viewAll}>{t.home.viewAll}</Text>
              </TouchableOpacity>
            </View>

            {latestReport ? (
              <TouchableOpacity
                onPress={() => router.push(`/(farmer)/report-detail?code=${latestReport.report_code}`)}
                activeOpacity={0.82}
                accessibilityRole="button"
              >
                <Card style={styles.reportCard}>
                  <View style={styles.reportCardRow}>
                    <View style={styles.reportCardLeaf}><Leaf size={20} color={Colors.secondaryEmerald} /></View>
                    <View style={styles.reportCardInfo}>
                      <Text style={styles.reportCode}>{latestReport.report_code}</Text>
                      <Text style={styles.reportCrop}>{latestReport.crop_name_en}</Text>
                      {latestReport.ai_result && (
                        <Text style={styles.reportPest} numberOfLines={1}>
                          {latestReport.ai_result.predicted_pest_en}
                        </Text>
                      )}
                    </View>
                    <View style={styles.reportCardRight}>
                      <StatusChip status={latestReport.status} />
                      <View style={styles.dateRow}>
                        <Clock size={11} color={Colors.charcoalLight} />
                        <Text style={styles.dateText}>
                          {new Date(latestReport.created_at).toLocaleDateString()}
                        </Text>
                      </View>
                    </View>
                  </View>
                </Card>
              </TouchableOpacity>
            ) : !loading ? (
              <View style={styles.emptyCard}>
                <View style={styles.emptyIcon}><Leaf size={28} color={Colors.sageSoft} /></View>
                <Text style={styles.emptyText}>{t.home.noReports}</Text>
                <TouchableOpacity
                  onPress={() => router.push('/(farmer)/report-new')}
                  style={styles.emptyBtn}
                  accessibilityRole="button"
                >
                  <Text style={styles.emptyBtnText}>Submit your first report →</Text>
                </TouchableOpacity>
              </View>
            ) : null}

            {/* Inclusion channels */}
            <View style={styles.channelsSection}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>Other Channels</Text>
                <View style={styles.rwBadge}><Text style={styles.rwBadgeText}>RWANDA READY</Text></View>
              </View>
              <View style={styles.channelCards}>
                {[
                  { icon: <Smartphone size={18} color="#0369A1" />, bg: '#E0F2FE', title: 'USSD (*922#)', sub: 'Basic keypad',   route: '/(farmer)/ussd'          as const },
                  { icon: <Phone      size={18} color={Colors.secondaryEmerald} />, bg: Colors.mintBg, title: 'IVR Voice',    sub: 'Toll-free',     route: '/(farmer)/ivr'           as const },
                  { icon: <MapPin     size={18} color={Colors.warning} />, bg: '#FEF3C7', title: 'Outbreak Map', sub: '5 km zones',    route: '/(farmer)/outbreak-map'  as const },
                ].map(({ icon, bg, title, sub, route }) => (
                  <TouchableOpacity
                    key={title}
                    style={styles.channelCard}
                    onPress={() => router.push(route)}
                    activeOpacity={0.78}
                  >
                    <View style={[styles.channelCardIcon, { backgroundColor: bg }]}>{icon}</View>
                    <Text style={styles.channelCardTitle}>{title}</Text>
                    <Text style={styles.channelCardSub}>{sub}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <View style={statStyles.pill}>
      <Text style={statStyles.value}>{value}</Text>
      <Text style={statStyles.label}>{label}</Text>
    </View>
  );
}
const statStyles = StyleSheet.create({
  pill:  { alignItems: 'center', flex: 1 },
  value: { fontFamily: FontFamily.bold, fontSize: FontSize.h3, color: Colors.limeAccent },
  label: { fontFamily: FontFamily.regular, fontSize: 10, color: 'rgba(255,255,255,0.65)', marginTop: 1 },
});

function QuickAction({ icon, label, onPress }: { icon: React.ReactNode; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={styles.quickAction}
      accessibilityRole="button"
      accessibilityLabel={label}
      activeOpacity={0.75}
    >
      <View style={styles.quickActionIcon}>{icon}</View>
      <Text style={styles.quickActionLabel} numberOfLines={2}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.backgroundWarm,
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
  },
  header: {
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.xxl,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, flex: 1 },
  logoMark: {
    width: 32, height: 32, borderRadius: 10,
    backgroundColor: 'rgba(197,232,108,0.2)',
    alignItems: 'center', justifyContent: 'center',
  },
  greeting: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
    color: Colors.white,
  },
  districtText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 1,
  },
  statsRow: {
    flexDirection: 'row',
    marginTop: Spacing.lg,
    paddingTop: Spacing.base,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.12)',
  },
  ctaWrap: {
    marginTop: -Spacing.xl,
    paddingHorizontal: Spacing.base,
    marginBottom: Spacing.sm,
  },
  bigCTA: { borderRadius: Radius.xl, overflow: 'hidden', ...Shadow.md },
  bigCTAGrad: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.lg,
    gap: Spacing.base,
  },
  bigCTAIcon: {
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center', justifyContent: 'center',
  },
  bigCTABody: { flex: 1 },
  bigCTATitle: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
    color: Colors.white,
  },
  bigCTASub: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  body: { paddingHorizontal: Spacing.base },
  alertStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    marginBottom: Spacing.base,
    gap: Spacing.sm,
    overflow: 'hidden',
    ...Shadow.xs,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  alertStripBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    borderTopLeftRadius: Radius.lg,
    borderBottomLeftRadius: Radius.lg,
  },
  alertStripText: { flex: 1, paddingLeft: 2 },
  alertStripTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.bodySm,
    color: Colors.charcoal,
  },
  alertStripDesc: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    marginTop: 1,
  },
  quickActions: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginBottom: Spacing.xl,
  },
  quickAction: {
    flex: 1,
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.lg,
    padding: Spacing.sm,
    paddingVertical: Spacing.md,
    alignItems: 'center',
    gap: 6,
    ...Shadow.xs,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  quickActionIcon: {
    width: 44, height: 44,
    borderRadius: 13,
    backgroundColor: Colors.mintBg,
    alignItems: 'center', justifyContent: 'center',
  },
  quickActionLabel: {
    fontFamily: FontFamily.medium,
    fontSize: 11,
    color: Colors.charcoal,
    textAlign: 'center',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  sectionTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
  },
  viewAll: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.secondaryEmerald,
  },
  reportCard: { marginBottom: Spacing.base, padding: Spacing.base },
  reportCardRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm },
  reportCardLeaf: {
    width: 42, height: 42, borderRadius: 12,
    backgroundColor: Colors.mintBg,
    alignItems: 'center', justifyContent: 'center',
  },
  reportCardInfo: { flex: 1 },
  reportCode: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.bodySm,
    color: Colors.primaryForest,
  },
  reportCrop: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    marginTop: 1,
  },
  reportPest: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    marginTop: 2,
  },
  reportCardRight: { alignItems: 'flex-end', gap: 4 },
  dateRow: { flexDirection: 'row', alignItems: 'center', gap: 3, marginTop: 2 },
  dateText: { fontFamily: FontFamily.regular, fontSize: 10, color: Colors.charcoalLight },
  emptyCard: {
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.lg,
    padding: Spacing.xl,
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    borderStyle: 'dashed',
  },
  emptyIcon: {
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: Colors.mintBg,
    alignItems: 'center', justifyContent: 'center',
  },
  emptyText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    textAlign: 'center',
  },
  emptyBtn: { paddingVertical: 6 },
  emptyBtnText: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.bodySm,
    color: Colors.secondaryEmerald,
  },
  channelsSection: { marginTop: Spacing.xl, marginBottom: Spacing.xl },
  channelCards: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
  channelCard: {
    flex: 1,
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.lg,
    padding: Spacing.sm,
    paddingVertical: 14,
    alignItems: 'center',
    gap: 6,
    ...Shadow.xs,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  channelCardIcon: {
    width: 40, height: 40, borderRadius: 20,
    alignItems: 'center', justifyContent: 'center',
    marginBottom: 2,
  },
  channelCardTitle: {
    fontFamily: FontFamily.bold,
    fontSize: 11,
    color: Colors.charcoal,
    textAlign: 'center',
  },
  channelCardSub: {
    fontFamily: FontFamily.regular,
    fontSize: 10,
    color: Colors.charcoalMuted,
    textAlign: 'center',
  },
  rwBadge: {
    backgroundColor: Colors.mintBg,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: Radius.full,
  },
  rwBadgeText: {
    fontFamily: FontFamily.bold,
    fontSize: 9,
    color: Colors.primaryForest,
    letterSpacing: 0.5,
  },
});
