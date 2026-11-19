/**
 * Screen 10 — Community Alerts
 * GET /outbreak/alerts
 * GET /outbreak/risk-score?district=X
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { Bell, AlertTriangle, TrendingUp, MapPin, ChevronRight } from 'lucide-react-native';
import { ScreenHeader } from '../../src/components/common/ScreenHeader';
import { Card } from '../../src/components/common/Card';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { EmptyState } from '../../src/components/common/EmptyState';
import { SkeletonCard } from '../../src/components/common/SkeletonLoader';
import { ErrorBanner } from '../../src/components/common/ErrorBanner';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import {
  outbreakApi,
  farmersApi,
  AlertResponse,
  RiskScoreResponse,
} from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function AlertsScreen() {
  const { t, language } = useTranslation();
  const insets = useSafeAreaInsets();

  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [riskScore, setRiskScore] = useState<RiskScoreResponse | null>(null);
  const [district, setDistrict] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadData = useCallback(async () => {
    try {
      // Get farmer's district first
      let dist: string | null = null;
      try {
        const prof = await farmersApi.getProfile();
        dist = prof.locations?.[0]?.district ?? null;
        setDistrict(dist);
      } catch {
        // non-critical
      }

      const params = dist ? { district: dist } : {};
      const alertData = await outbreakApi.listAlerts({ ...params, limit: 50 });
      setAlerts(alertData);

      if (dist) {
        try {
          const risk = await outbreakApi.riskScore(dist);
          setRiskScore(risk);
        } catch {
          // non-critical
        }
      }

      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <ScreenHeader title={t.alerts.title} />
        <View style={styles.list}>
          {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScreenHeader title={t.alerts.title} showLanguage />
      <FlatList
        data={alerts}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 80 }]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={Colors.secondaryEmerald}
          />
        }
        ListHeaderComponent={
          <>
            {error && (
              <View style={{ marginBottom: Spacing.sm }}>
                <ErrorBanner error={error} onRetry={loadData} />
              </View>
            )}

            {/* Risk score card for farmer's district */}
            {riskScore && (
              <Card
                style={[
                  styles.riskCard,
                  riskScore.above_threshold ? styles.riskCardAlert : null,
                ]}
              >
                <View style={styles.riskHeader}>
                  <TrendingUp
                    size={18}
                    color={riskScore.above_threshold ? Colors.severityCritical : Colors.secondaryEmerald}
                  />
                  <Text style={styles.riskTitle}>
                    {t.alerts.riskScore} — {riskScore.district}
                  </Text>
                </View>
                <View style={styles.riskBarWrap}>
                  <View style={styles.riskBar}>
                    <View
                      style={[
                        styles.riskBarFill,
                        {
                          width: `${Math.round(riskScore.risk_score * 100)}%`,
                          backgroundColor: riskScore.above_threshold
                            ? Colors.severityCritical
                            : Colors.secondaryEmerald,
                        },
                      ]}
                    />
                  </View>
                  <Text
                    style={[
                      styles.riskScore,
                      riskScore.above_threshold && { color: Colors.severityCritical },
                    ]}
                  >
                    {Math.round(riskScore.risk_score * 100)}%
                  </Text>
                </View>
                <Text style={styles.riskReports}>
                  {riskScore.contributing_report_count} reports in last 30 days
                </Text>
              </Card>
            )}

            <Text style={styles.subtitle}>{t.alerts.subtitle}</Text>
          </>
        }
        ListEmptyComponent={
          <EmptyState
            title={t.alerts.empty}
            subtitle={t.alerts.emptySubtitle}
            icon={<Bell size={36} color={Colors.sageSoft} />}
          />
        }
        renderItem={({ item }) => <AlertCard alert={item} language={language} t={t} />}
      />
    </View>
  );
}

function AlertCard({
  alert,
  language,
  t,
}: {
  alert: AlertResponse;
  language: string;
  t: ReturnType<typeof useTranslation>['t'];
}) {
  return (
    <Card style={styles.alertCard}>
      <View style={styles.alertTopRow}>
        <View style={styles.alertIcon}>
          <AlertTriangle size={18} color={Colors.warning} />
        </View>
        <View style={styles.alertInfo}>
          <Text style={styles.alertTitle} numberOfLines={2}>
            {language === 'rw' ? alert.title_rw : alert.title_en}
          </Text>
          {alert.pest_name && (
            <Text style={styles.alertPest}>{alert.pest_name}</Text>
          )}
        </View>
        <SeverityBadge severity={alert.severity} size="sm" />
      </View>

      <View style={styles.alertMeta}>
        <View style={styles.metaRow}>
          <MapPin size={12} color={Colors.charcoalLight} />
          <Text style={styles.metaText}>{alert.target_district}</Text>
          {alert.target_sector && (
            <Text style={styles.metaText}>· {alert.target_sector}</Text>
          )}
        </View>
        <Text style={styles.metaText}>
          {alert.affected_report_count} {t.alerts.affectedFarms}
        </Text>
      </View>

      <View style={styles.alertFooter}>
        <View
          style={[
            styles.statusBadge,
            alert.status === 'ACTIVE' ? styles.statusActive : styles.statusResolved,
          ]}
        >
          <Text
            style={[
              styles.statusText,
              alert.status === 'ACTIVE' ? styles.statusTextActive : styles.statusTextResolved,
            ]}
          >
            {alert.status}
          </Text>
        </View>
        <Text style={styles.dateText}>
          {new Date(alert.created_at).toLocaleDateString()}
        </Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  list: { paddingHorizontal: Spacing.base, paddingTop: Spacing.sm },
  subtitle: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.charcoalMuted,
    marginBottom: Spacing.sm,
    marginTop: Spacing.sm,
  },
  riskCard: {
    marginBottom: Spacing.base,
    padding: Spacing.base,
  },
  riskCardAlert: {
    borderWidth: 1,
    borderColor: Colors.severityCritical + '40',
    backgroundColor: Colors.severityCriticalBg,
  },
  riskHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  riskTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    flex: 1,
  },
  riskBarWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: 4,
  },
  riskBar: {
    flex: 1,
    height: 8,
    backgroundColor: Colors.borderLight,
    borderRadius: Radius.full,
    overflow: 'hidden',
  },
  riskBarFill: {
    height: '100%',
    borderRadius: Radius.full,
    minWidth: 4,
  },
  riskScore: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.body,
    color: Colors.secondaryEmerald,
    minWidth: 36,
    textAlign: 'right',
  },
  riskReports: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
  },
  alertCard: { marginBottom: Spacing.sm, padding: Spacing.base },
  alertTopRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm },
  alertIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.warningBg,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  alertInfo: { flex: 1 },
  alertTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
  },
  alertPest: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: Colors.charcoalMuted,
    marginTop: 2,
  },
  alertMeta: {
    marginTop: Spacing.sm,
    gap: 4,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
  },
  alertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: Spacing.sm,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  statusBadge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: Radius.full,
  },
  statusActive: { backgroundColor: Colors.severityCriticalBg },
  statusResolved: { backgroundColor: Colors.successBg },
  statusText: {
    fontFamily: FontFamily.semiBold,
    fontSize: 10,
    letterSpacing: 0.5,
  },
  statusTextActive: { color: Colors.severityCritical },
  statusTextResolved: { color: Colors.secondaryEmerald },
  dateText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalLight,
  },
});
