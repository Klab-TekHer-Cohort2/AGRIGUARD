/**
 * Screen 10 — Community Alerts
 * Live: GET /outbreak/alerts, GET /outbreak/risk-score
 * Demo: DEMO_ALERTS, DEMO_RISK from demo/data.ts
 */
import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Bell, AlertTriangle, TrendingUp, MapPin, ChevronRight, Radio } from 'lucide-react-native';
import { ScreenHeader } from '../../src/components/common/ScreenHeader';
import { Card } from '../../src/components/common/Card';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { EmptyState } from '../../src/components/common/EmptyState';
import { SkeletonCard } from '../../src/components/common/SkeletonLoader';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { outbreakApi, farmersApi, AlertResponse, RiskScoreResponse } from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDemoStore } from '../../src/demo/demoStore';
import { DEMO_ALERTS, DEMO_RISK } from '../../src/demo/data';

export default function AlertsScreen() {
  const router = useRouter();
  const { t, language } = useTranslation();
  const insets = useSafeAreaInsets();
  const isDemoMode = useDemoStore((s) => s.isDemoMode);

  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [riskScore, setRiskScore] = useState<RiskScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadData = useCallback(async () => {
    if (isDemoMode) {
      setAlerts(DEMO_ALERTS);
      setRiskScore(DEMO_RISK);
      setLoading(false);
      return;
    }
    try {
      let dist: string | null = null;
      try { const prof = await farmersApi.getProfile(); dist = prof.locations?.[0]?.district ?? null; } catch { /* ok */ }
      const params = dist ? { district: dist } : {};
      const alertData = await outbreakApi.listAlerts({ ...params, limit: 50 });
      setAlerts(alertData);
      if (dist) { try { setRiskScore(await outbreakApi.riskScore(dist)); } catch { /* ok */ } }
      setError(null);
    } catch (err) { setError(err as Error); } finally { setLoading(false); }
  }, [isDemoMode]);

  useEffect(() => { loadData(); }, [loadData]);
  const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <ScreenHeader title={t.alerts.title} />
        <View style={styles.list}>{[1, 2, 3].map((i) => <SkeletonCard key={i} />)}</View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScreenHeader title={`${t.alerts.title}${isDemoMode ? ' (Sample)' : ''}`} showLanguage />
      <FlatList
        data={alerts}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 80 }]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.secondaryEmerald} />}
        ListHeaderComponent={
          <>
            {/* Outbreak Map Sentinel Button */}
            <TouchableOpacity
              style={styles.mapBannerBtn}
              onPress={() => router.push('/(farmer)/outbreak-map')}
              activeOpacity={0.85}
            >
              <View style={styles.mapBannerIcon}>
                <Radio size={18} color={Colors.white} />
              </View>
              <View style={styles.mapBannerTextWrap}>
                <Text style={styles.mapBannerTitle}>Rwanda Outbreak Surveillance Map</Text>
                <Text style={styles.mapBannerSub}>Explore 5 km community risk clusters & active alerts</Text>
              </View>
              <ChevronRight size={18} color={Colors.primaryForest} />
            </TouchableOpacity>

            {riskScore && (
              <Card style={[styles.riskCard, riskScore.above_threshold ? styles.riskCardAlert : null]}>
                <View style={styles.riskHeader}>
                  <TrendingUp size={18} color={riskScore.above_threshold ? Colors.severityCritical : Colors.secondaryEmerald} />
                  <Text style={styles.riskTitle}>Outbreak Risk — {riskScore.district}{isDemoMode ? ' (Sample)' : ''}</Text>
                </View>
                <View style={styles.riskBarWrap}>
                  <View style={styles.riskBar}>
                    <View style={[styles.riskBarFill, { width: `${Math.round(riskScore.risk_score * 100)}%` as any, backgroundColor: riskScore.above_threshold ? Colors.severityCritical : Colors.secondaryEmerald }]} />
                  </View>
                  <Text style={[styles.riskScore, riskScore.above_threshold && { color: Colors.severityCritical }]}>{Math.round(riskScore.risk_score * 100)}%</Text>
                </View>
                <Text style={styles.riskReports}>{riskScore.contributing_report_count} reports in last 30 days</Text>
              </Card>
            )}
            <Text style={styles.subtitle}>{t.alerts.subtitle}{isDemoMode ? ' — illustrative data' : ''}</Text>
          </>
        }
        ListEmptyComponent={<EmptyState title={t.alerts.empty} subtitle={t.alerts.emptySubtitle} icon={<Bell size={36} color={Colors.sageSoft} />} />}
        renderItem={({ item }) => (
          <Card style={styles.alertCard}>
            <View style={styles.alertTopRow}>
              <View style={styles.alertIcon}><AlertTriangle size={18} color={Colors.warning} /></View>
              <View style={styles.alertInfo}>
                <Text style={styles.alertTitle} numberOfLines={2}>{language === 'rw' ? item.title_rw : item.title_en}</Text>
                {item.pest_name && <Text style={styles.alertPest}>{item.pest_name}</Text>}
              </View>
              <SeverityBadge severity={item.severity} size="sm" />
            </View>
            <View style={styles.alertMeta}>
              <View style={styles.metaRow}><MapPin size={12} color={Colors.charcoalLight} /><Text style={styles.metaText}>{item.target_district}{item.target_sector ? ` · ${item.target_sector}` : ''}</Text></View>
              <Text style={styles.metaText}>{item.affected_report_count} {t.alerts.affectedFarms}</Text>
            </View>
            <View style={styles.alertFooter}>
              <View style={[styles.statusBadge, item.status === 'ACTIVE' ? styles.statusActive : styles.statusResolved]}>
                <Text style={[styles.statusText, item.status === 'ACTIVE' ? styles.statusTextActive : styles.statusTextResolved]}>{item.status}</Text>
              </View>
              <Text style={styles.dateText}>{new Date(item.created_at).toLocaleDateString()}</Text>
            </View>
          </Card>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  list: { paddingHorizontal: Spacing.base, paddingTop: Spacing.sm },
  subtitle: { fontFamily: FontFamily.medium, fontSize: FontSize.bodySm, color: Colors.charcoalMuted, marginBottom: Spacing.sm, marginTop: Spacing.sm },
  riskCard: { marginBottom: Spacing.base, padding: Spacing.base },
  riskCardAlert: { borderWidth: 1, borderColor: Colors.severityCritical + '40', backgroundColor: Colors.severityCriticalBg },
  riskHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.sm },
  riskTitle: { fontFamily: FontFamily.semiBold, fontSize: FontSize.body, color: Colors.charcoal, flex: 1 },
  riskBarWrap: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: 4 },
  riskBar: { flex: 1, height: 8, backgroundColor: Colors.borderLight, borderRadius: Radius.full, overflow: 'hidden' },
  riskBarFill: { height: '100%', borderRadius: Radius.full, minWidth: 4 },
  riskScore: { fontFamily: FontFamily.bold, fontSize: FontSize.body, color: Colors.secondaryEmerald, minWidth: 36, textAlign: 'right' },
  riskReports: { fontFamily: FontFamily.regular, fontSize: FontSize.labelSm, color: Colors.charcoalMuted },
  alertCard: { marginBottom: Spacing.sm, padding: Spacing.base },
  alertTopRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm },
  alertIcon: { width: 38, height: 38, borderRadius: 12, backgroundColor: Colors.warningBg, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  alertInfo: { flex: 1 },
  alertTitle: { fontFamily: FontFamily.semiBold, fontSize: FontSize.body, color: Colors.charcoal },
  alertPest: { fontFamily: FontFamily.regular, fontSize: FontSize.bodySm, color: Colors.charcoalMuted, marginTop: 2 },
  alertMeta: { marginTop: Spacing.sm, gap: 4 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaText: { fontFamily: FontFamily.regular, fontSize: FontSize.labelSm, color: Colors.charcoalMuted },
  alertFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: Spacing.sm, paddingTop: Spacing.sm, borderTopWidth: 1, borderTopColor: Colors.borderLight },
  statusBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 3, borderRadius: Radius.full },
  statusActive: { backgroundColor: Colors.severityCriticalBg },
  statusResolved: { backgroundColor: Colors.successBg },
  statusText: { fontFamily: FontFamily.semiBold, fontSize: 10, letterSpacing: 0.5 },
  statusTextActive: { color: Colors.severityCritical },
  statusTextResolved: { color: Colors.secondaryEmerald },
  dateText: { fontFamily: FontFamily.regular, fontSize: FontSize.labelSm, color: Colors.charcoalLight },
  mapBannerBtn: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.mintBg,
    borderWidth: 1, borderColor: Colors.border,
    borderRadius: Radius.lg, padding: Spacing.base,
    marginBottom: Spacing.base, gap: Spacing.sm,
    ...Shadow.xs,
  },
  mapBannerIcon: {
    width: 38, height: 38, borderRadius: 19,
    backgroundColor: Colors.secondaryEmerald,
    alignItems: 'center', justifyContent: 'center',
  },
  mapBannerTextWrap: { flex: 1 },
  mapBannerTitle: { fontSize: FontSize.bodySm, fontFamily: FontFamily.bold, color: Colors.primaryForest },
  mapBannerSub: { fontSize: 11, fontFamily: FontFamily.regular, color: Colors.charcoalMuted, marginTop: 2 },
});
