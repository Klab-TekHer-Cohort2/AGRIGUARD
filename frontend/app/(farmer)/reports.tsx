/**
 * Screen 8 — My Reports list
 * Live: GET /reports/my-reports
 * Demo: DEMO_REPORTS from demo/data.ts
 */
import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { Leaf, Clock, ChevronRight, Filter } from 'lucide-react-native';
import { ScreenHeader } from '../../src/components/common/ScreenHeader';
import { Card } from '../../src/components/common/Card';
import { StatusChip } from '../../src/components/common/StatusChip';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { EmptyState } from '../../src/components/common/EmptyState';
import { SkeletonCard } from '../../src/components/common/SkeletonLoader';
import { ErrorBanner } from '../../src/components/common/ErrorBanner';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { reportsApi, CropReportResponse } from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDemoStore } from '../../src/demo/demoStore';
import { DEMO_REPORTS } from '../../src/demo/data';

const STATUSES = ['ALL', 'PENDING', 'AI_ANALYZED', 'VERIFIED', 'ESCALATED', 'RESOLVED'];

export default function ReportsScreen() {
  const router = useRouter();
  const { t, language } = useTranslation();
  const insets = useSafeAreaInsets();
  const isDemoMode = useDemoStore((s) => s.isDemoMode);

  const [allReports, setAllReports] = useState<CropReportResponse[]>([]);
  const [filtered, setFiltered] = useState<CropReportResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadReports = useCallback(async () => {
    if (isDemoMode) {
      setAllReports(DEMO_REPORTS);
      setFiltered(DEMO_REPORTS);
      setLoading(false);
      return;
    }
    try {
      const data = await reportsApi.myReports({ limit: 50 });
      setAllReports(data);
      setFiltered(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [isDemoMode]);

  useEffect(() => { loadReports(); }, [loadReports]);

  useEffect(() => {
    if (statusFilter === 'ALL') { setFiltered(allReports); return; }
    setFiltered(allReports.filter((r) => r.status === statusFilter));
  }, [statusFilter, allReports]);

  const onRefresh = async () => { setRefreshing(true); await loadReports(); setRefreshing(false); };

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <ScreenHeader title={t.myReports.title} />
        <View style={styles.list}>{[1, 2, 3].map((i) => <SkeletonCard key={i} />)}</View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScreenHeader title={`${t.myReports.title}${isDemoMode ? ' (Sample)' : ''}`} showLanguage />
      {error && <View style={styles.errorWrap}><ErrorBanner error={error} onRetry={loadReports} /></View>}

      {/* Status filter chips */}
      <View style={styles.filterWrap}>
        <FlatList
          data={STATUSES}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(s) => s}
          contentContainerStyle={{ gap: Spacing.sm, paddingHorizontal: Spacing.base }}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => setStatusFilter(item)}
              style={[styles.filterChip, statusFilter === item && styles.filterChipActive]}
              accessibilityRole="button"
              accessibilityState={{ selected: statusFilter === item }}
            >
              <Text style={[styles.filterChipText, statusFilter === item && styles.filterChipTextActive]}>
                {item === 'ALL' ? 'All' : (t.myReports.status as Record<string,string>)[item] ?? item}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 80 }]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.secondaryEmerald} />}
        ListEmptyComponent={
          <EmptyState
            title={t.myReports.empty}
            subtitle={t.myReports.emptySubtitle}
            actionLabel={t.home.reportCTA}
            onAction={() => router.push('/(farmer)/report-new')}
          />
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => router.push(`/(farmer)/report-detail?code=${item.report_code}`)}
            activeOpacity={0.8}
            accessibilityRole="button"
          >
            <Card style={styles.reportCard}>
              <View style={styles.cardRow}>
                <View style={styles.cropIcon}><Leaf size={20} color={Colors.secondaryEmerald} /></View>
                <View style={styles.cardInfo}>
                  <View style={styles.cardTopRow}>
                    <Text style={styles.reportCode}>{item.report_code}</Text>
                    <StatusChip status={item.status} />
                  </View>
                  <Text style={styles.cropName}>{language === 'rw' ? (item.crop_name_rw ?? item.crop_name_en) : (item.crop_name_en ?? '')}</Text>
                  {item.ai_result && <Text style={styles.pestName} numberOfLines={1}>{language === 'rw' ? (item.ai_result.predicted_pest_rw ?? item.ai_result.predicted_pest_en) : item.ai_result.predicted_pest_en}</Text>}
                  <View style={styles.cardMeta}>
                    <View style={styles.dateRow}><Clock size={11} color={Colors.charcoalLight} /><Text style={styles.dateText}>{new Date(item.created_at).toLocaleDateString()}</Text></View>
                    <Text style={styles.districtText}>📍 {item.district}</Text>
                  </View>
                  {item.ai_result && <SeverityBadge severity={item.ai_result.detected_severity} size="sm" />}
                </View>
                <ChevronRight size={16} color={Colors.charcoalLight} style={styles.chevron} />
              </View>
            </Card>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  list: { paddingHorizontal: Spacing.base, paddingTop: Spacing.sm },
  errorWrap: { paddingHorizontal: Spacing.base, paddingTop: Spacing.sm },
  filterWrap: { paddingVertical: Spacing.sm },
  filterChip: { paddingHorizontal: Spacing.sm, paddingVertical: 6, borderRadius: Radius.full, borderWidth: 1, borderColor: Colors.border, backgroundColor: Colors.backgroundCard },
  filterChipActive: { backgroundColor: Colors.secondaryEmerald, borderColor: Colors.secondaryEmerald },
  filterChipText: { fontFamily: FontFamily.medium, fontSize: FontSize.labelSm, color: Colors.charcoal },
  filterChipTextActive: { color: Colors.white },
  reportCard: { marginBottom: Spacing.sm },
  cardRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm },
  cropIcon: { width: 40, height: 40, borderRadius: 10, backgroundColor: Colors.backgroundSage, alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 },
  cardInfo: { flex: 1 },
  cardTopRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 },
  reportCode: { fontFamily: FontFamily.semiBold, fontSize: FontSize.bodySm, color: Colors.primaryForest },
  cropName: { fontFamily: FontFamily.semiBold, fontSize: FontSize.body, color: Colors.charcoal, marginBottom: 2 },
  pestName: { fontFamily: FontFamily.regular, fontSize: FontSize.labelSm, color: Colors.charcoalMuted, marginBottom: 4 },
  cardMeta: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: 6 },
  dateRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  dateText: { fontFamily: FontFamily.regular, fontSize: 11, color: Colors.charcoalLight },
  districtText: { fontFamily: FontFamily.regular, fontSize: 11, color: Colors.charcoalLight },
  chevron: { alignSelf: 'center', marginLeft: 4 },
});
