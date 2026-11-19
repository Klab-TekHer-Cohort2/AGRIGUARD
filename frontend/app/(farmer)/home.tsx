/**
 * Screen 4 — Home Dashboard
 * Endpoints used:
 *   GET /reports/my-reports?limit=1  → latest report status
 *   GET /outbreak/alerts?district=X  → community alerts for farmer's district
 *   GET /farmers/profile             → farmer name + language
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import {
  Plus,
  FileText,
  Bell,
  MessageCircle,
  ChevronRight,
  AlertTriangle,
  Leaf,
  Clock,
} from 'lucide-react-native';
import { Button } from '../../src/components/common/Button';
import { Card } from '../../src/components/common/Card';
import { StatusChip } from '../../src/components/common/StatusChip';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { Colors, FontFamily, FontSize, Spacing, Radius, Shadow } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useAuthStore } from '../../src/store/authStore';
import {
  reportsApi,
  outbreakApi,
  farmersApi,
  CropReportResponse,
  AlertResponse,
  FarmerProfileResponse,
} from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function HomeScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const insets = useSafeAreaInsets();

  const [profile, setProfile] = useState<FarmerProfileResponse | null>(null);
  const [latestReport, setLatestReport] = useState<CropReportResponse | null>(null);
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [prof, reports] = await Promise.allSettled([
        farmersApi.getProfile(),
        reportsApi.myReports({ limit: 1 }),
      ]);

      let district: string | undefined;
      if (prof.status === 'fulfilled') {
        setProfile(prof.value);
        district = prof.value.locations?.[0]?.district;
      }
      if (reports.status === 'fulfilled') {
        setLatestReport(reports.value[0] ?? null);
      }

      if (district) {
        try {
          const alertResp = await outbreakApi.listAlerts({ district, limit: 3 });
          setAlerts(alertResp.filter((a) => a.status === 'ACTIVE'));
        } catch {
          // non-critical
        }
      }
    } catch {
      // silent — individual sections handle empty states
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const firstName = (profile?.full_name ?? user?.full_name ?? '').split(' ')[0];
  const district = profile?.locations?.[0]?.district;

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.secondaryEmerald} />}
    >
      {/* Header gradient */}
      <LinearGradient
        colors={[Colors.primaryForest, '#145830']}
        style={[styles.header, { paddingTop: insets.top + 12 }]}
      >
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.greeting}>{t.home.greeting}, {firstName} 👋</Text>
            {district && (
              <Text style={styles.district}>📍 {district}</Text>
            )}
          </View>
          <LanguageToggle />
        </View>
      </LinearGradient>

      {/* Main CTA — Report a Problem */}
      <View style={styles.ctaWrap}>
        <TouchableOpacity
          onPress={() => router.push('/(farmer)/report-new')}
          style={styles.bigCTA}
          accessibilityLabel={t.home.reportCTA}
          accessibilityRole="button"
          activeOpacity={0.85}
        >
          <LinearGradient
            colors={[Colors.secondaryEmerald, '#14803A']}
            style={styles.bigCTAGrad}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <View style={styles.bigCTAIcon}>
              <Plus size={32} color={Colors.white} />
            </View>
            <View style={styles.bigCTAText}>
              <Text style={styles.bigCTATitle}>{t.home.reportCTA}</Text>
              <Text style={styles.bigCTASubtitle}>{t.home.reportSubtitle}</Text>
            </View>
            <ChevronRight size={22} color="rgba(255,255,255,0.7)" />
          </LinearGradient>
        </TouchableOpacity>
      </View>

      <View style={styles.body}>
        {/* Community alert banner */}
        {alerts.length > 0 && (
          <TouchableOpacity
            onPress={() => router.push('/(farmer)/alerts')}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel={t.home.communityAlert}
          >
            <View style={styles.alertBanner}>
              <AlertTriangle size={18} color={Colors.warning} />
              <View style={styles.alertBannerText}>
                <Text style={styles.alertBannerTitle}>{t.home.communityAlert}</Text>
                <Text style={styles.alertBannerDesc} numberOfLines={1}>
                  {alerts[0].title_en ?? alerts[0].pest_name}
                </Text>
              </View>
              <SeverityBadge severity={alerts[0].severity} size="sm" />
              <ChevronRight size={16} color={Colors.charcoalMuted} />
            </View>
          </TouchableOpacity>
        )}

        {/* Quick actions */}
        <View style={styles.quickActions}>
          <QuickAction
            icon={<FileText size={22} color={Colors.primaryForest} />}
            label={t.home.myReports}
            onPress={() => router.push('/(farmer)/reports')}
          />
          <QuickAction
            icon={<MessageCircle size={22} color={Colors.primaryForest} />}
            label={t.home.askAgriGuard}
            onPress={() => router.push('/(farmer)/ask')}
          />
          <QuickAction
            icon={<Bell size={22} color={Colors.primaryForest} />}
            label={t.nav.alerts}
            onPress={() => router.push('/(farmer)/alerts')}
          />
        </View>

        {/* Latest report card */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{t.home.lastReport}</Text>
          <TouchableOpacity onPress={() => router.push('/(farmer)/reports')} accessibilityRole="button">
            <Text style={styles.viewAll}>{t.home.viewAll}</Text>
          </TouchableOpacity>
        </View>

        {latestReport ? (
          <TouchableOpacity
            onPress={() => router.push(`/(farmer)/report-detail?code=${latestReport.report_code}`)}
            activeOpacity={0.85}
            accessibilityRole="button"
          >
            <Card style={styles.reportCard}>
              <View style={styles.reportCardRow}>
                <View style={styles.reportCardLeaf}>
                  <Leaf size={20} color={Colors.secondaryEmerald} />
                </View>
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
          <Card variant="flat" style={styles.emptyCard}>
            <Text style={styles.emptyText}>{t.home.noReports}</Text>
          </Card>
        ) : null}
      </View>
    </ScrollView>
  );
}

function QuickAction({
  icon,
  label,
  onPress,
}: {
  icon: React.ReactNode;
  label: string;
  onPress: () => void;
}) {
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
  scroll: { flex: 1, backgroundColor: Colors.backgroundWarm },
  header: {
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.xxxl,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  greeting: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h2,
    color: Colors.white,
  },
  district: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: 'rgba(255,255,255,0.75)',
    marginTop: 2,
  },
  ctaWrap: {
    marginTop: -Spacing.xl,
    paddingHorizontal: Spacing.base,
    marginBottom: Spacing.base,
  },
  bigCTA: {
    borderRadius: Radius.xl,
    overflow: 'hidden',
    ...Shadow.md,
  },
  bigCTAGrad: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.lg,
    gap: Spacing.base,
  },
  bigCTAIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  bigCTAText: { flex: 1 },
  bigCTATitle: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
    color: Colors.white,
  },
  bigCTASubtitle: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  body: { paddingHorizontal: Spacing.base },
  alertBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.warningBg,
    borderRadius: Radius.md,
    padding: Spacing.base,
    marginBottom: Spacing.base,
    gap: Spacing.sm,
    borderLeftWidth: 3,
    borderLeftColor: Colors.warning,
  },
  alertBannerText: { flex: 1 },
  alertBannerTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.bodySm,
    color: Colors.warning,
  },
  alertBannerDesc: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
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
    padding: Spacing.base,
    alignItems: 'center',
    gap: Spacing.sm,
    ...Shadow.xs,
  },
  quickActionIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionLabel: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
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
  reportCard: { marginBottom: Spacing.sm },
  reportCardRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm },
  reportCardLeaf: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
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
  },
  reportPest: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
  },
  reportCardRight: { alignItems: 'flex-end', gap: 4 },
  dateRow: { flexDirection: 'row', alignItems: 'center', gap: 3, marginTop: 2 },
  dateText: {
    fontFamily: FontFamily.regular,
    fontSize: 10,
    color: Colors.charcoalLight,
  },
  emptyCard: {
    padding: Spacing.xl,
    alignItems: 'center',
  },
  emptyText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    textAlign: 'center',
  },
});
