/**
 * Screen 9 — Report Detail
 * GET /reports/{code}
 * Shows full report with AI result, images, agronomist notes, history timeline.
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Image,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { CheckCircle, Clock, MapPin, Leaf, AlertTriangle } from 'lucide-react-native';
import { ScreenHeader } from '../../src/components/common/ScreenHeader';
import { Card } from '../../src/components/common/Card';
import { StatusChip } from '../../src/components/common/StatusChip';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { ConfidenceRing } from '../../src/components/common/ConfidenceRing';
import { ErrorBanner } from '../../src/components/common/ErrorBanner';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { reportsApi, CropReportResponse } from '../../src/api/client';
import { BACKEND_BASE_URL } from '../../src/api/config';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function ReportDetailScreen() {
  const { code } = useLocalSearchParams<{ code: string }>();
  const { t, language } = useTranslation();
  const insets = useSafeAreaInsets();

  const [report, setReport] = useState<CropReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (code) {
      reportsApi
        .getByCode(code)
        .then(setReport)
        .catch((e) => setError(e))
        .finally(() => setLoading(false));
    }
  }, [code]);

  if (loading) {
    return (
      <View style={[styles.center, { paddingTop: insets.top }]}>
        <ActivityIndicator color={Colors.secondaryEmerald} size="large" />
      </View>
    );
  }

  if (error || !report) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <ScreenHeader title={t.reportDetail.title} showBack />
        <View style={styles.errorWrap}>
          <ErrorBanner error={error} />
        </View>
      </View>
    );
  }

  const ai = report.ai_result;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScreenHeader title={t.reportDetail.title} showBack />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
      >
        {/* Report code + status */}
        <View style={styles.topBanner}>
          <View>
            <Text style={styles.reportCode}>{report.report_code}</Text>
            <Text style={styles.cropName}>
              {language === 'rw'
                ? (report.crop_name_rw ?? report.crop_name_en)
                : (report.crop_name_en ?? '')}
            </Text>
          </View>
          <StatusChip status={report.status} />
        </View>

        <View style={styles.body}>
          {/* Location */}
          <Card variant="flat" style={styles.section}>
            <View style={styles.sectionRow}>
              <MapPin size={16} color={Colors.secondaryEmerald} />
              <Text style={styles.sectionLabel}>{t.reportDetail.location}</Text>
            </View>
            <Text style={styles.locationText}>
              {[report.village, report.cell, report.sector, report.district]
                .filter(Boolean)
                .join(', ')}
            </Text>
            <View style={styles.submittedRow}>
              <Clock size={12} color={Colors.charcoalLight} />
              <Text style={styles.submittedText}>
                {new Date(report.created_at).toLocaleString()}
              </Text>
            </View>
          </Card>

          {/* Symptoms */}
          {report.symptoms.length > 0 && (
            <View style={styles.symptomsSection}>
              <Text style={styles.sectionTitle}>{t.report.symptoms}</Text>
              <View style={styles.symptomsWrap}>
                {report.symptoms.map((s, i) => (
                  <View key={i} style={styles.symptomTag}>
                    <Text style={styles.symptomTagText}>{s.replace(/_/g, ' ')}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Description */}
          {report.description && (
            <Card variant="flat" style={styles.section}>
              <Text style={styles.sectionTitle}>{t.report.description}</Text>
              <Text style={styles.descText}>{report.description}</Text>
            </Card>
          )}

          {/* Images */}
          {report.images.length > 0 && (
            <View style={styles.imagesSection}>
              <Text style={styles.sectionTitle}>{t.reportDetail.images}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                {report.images.map((img) => (
                  <Image
                    key={img.id}
                    source={{ uri: `${BACKEND_BASE_URL}${img.image_url}` }}
                    style={styles.reportImage}
                    resizeMode="cover"
                  />
                ))}
              </ScrollView>
            </View>
          )}

          {/* AI Result */}
          {ai && (
            <View style={styles.aiSection}>
              <Text style={styles.sectionTitle}>{t.reportDetail.aiResult}</Text>

              {ai.is_mock && (
                <View style={styles.mockBanner}>
                  <AlertTriangle size={14} color={Colors.warning} />
                  <Text style={styles.mockText}>{t.aiResult.mockBadge}</Text>
                </View>
              )}

              <Card style={styles.aiCard}>
                <Text style={styles.aiMeta}>{t.aiResult.detectedPest}</Text>
                <Text style={styles.pestName}>
                  {language === 'rw'
                    ? (ai.predicted_pest_rw ?? ai.predicted_pest_en)
                    : ai.predicted_pest_en}
                </Text>
                {language === 'en' && ai.predicted_pest_rw && (
                  <Text style={styles.pestNameRw}>{ai.predicted_pest_rw}</Text>
                )}

                <View style={styles.aiMetrics}>
                  <ConfidenceRing score={ai.confidence_score} size={64} />
                  <View>
                    <Text style={styles.aiMeta}>{t.aiResult.severity}</Text>
                    <SeverityBadge severity={ai.detected_severity} />
                  </View>
                </View>

                {/* High/Critical escalation */}
                {(ai.detected_severity === 'HIGH' || ai.detected_severity === 'CRITICAL') && (
                  <View style={styles.escalation}>
                    <AlertTriangle size={14} color={Colors.severityCritical} />
                    <Text style={styles.escalationText}>{t.aiResult.escalationBanner}</Text>
                  </View>
                )}

                {/* Recommendations */}
                {ai.recommendations && ai.recommendations.length > 0 && (
                  <View style={styles.recsSection}>
                    <Text style={styles.aiMeta}>{t.aiResult.recommendations}</Text>
                    {ai.recommendations.map((rec, i) => (
                      <View key={i} style={styles.recRow}>
                        <CheckCircle size={14} color={Colors.secondaryEmerald} />
                        <Text style={styles.recText}>{rec}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </Card>
            </View>
          )}

          {/* Agronomist notes */}
          {report.agronomist_notes && (
            <Card variant="sage" style={styles.section}>
              <Text style={styles.sectionTitle}>{t.reportDetail.agronomistNotes}</Text>
              <Text style={styles.descText}>{report.agronomist_notes}</Text>
            </Card>
          )}

          {/* History timeline */}
          {report.history.length > 0 && (
            <View style={styles.historySection}>
              <Text style={styles.sectionTitle}>{t.reportDetail.history}</Text>
              {report.history.map((h, i) => (
                <View key={h.id} style={styles.historyItem}>
                  <View style={styles.historyDot}>
                    <View style={[
                      styles.historyDotInner,
                      i === 0 && { backgroundColor: Colors.secondaryEmerald },
                    ]} />
                    {i < report.history.length - 1 && <View style={styles.historyLine} />}
                  </View>
                  <View style={styles.historyContent}>
                    <Text style={styles.historyAction}>{h.action_type.replace(/_/g, ' ')}</Text>
                    {h.notes && <Text style={styles.historyNotes}>{h.notes}</Text>}
                    <Text style={styles.historyDate}>
                      {new Date(h.created_at).toLocaleString()}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: Colors.backgroundWarm },
  errorWrap: { padding: Spacing.base },
  topBanner: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: Spacing.base,
    backgroundColor: Colors.backgroundCard,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  reportCode: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.primaryForest,
    marginBottom: 2,
  },
  cropName: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
  },
  body: { padding: Spacing.base, gap: Spacing.base },
  section: { padding: Spacing.base },
  sectionRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: 6 },
  sectionLabel: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.bodySm,
    color: Colors.primaryForest,
  },
  sectionTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    marginBottom: Spacing.sm,
  },
  locationText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    marginBottom: 4,
  },
  submittedRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  submittedText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalLight,
  },
  symptomsSection: { gap: Spacing.sm },
  symptomsWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  symptomTag: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 5,
    borderRadius: Radius.full,
    backgroundColor: Colors.backgroundSage,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  symptomTagText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.charcoal,
    textTransform: 'capitalize',
  },
  descText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    lineHeight: 22,
  },
  imagesSection: { gap: Spacing.sm },
  reportImage: {
    width: 180,
    height: 140,
    borderRadius: Radius.lg,
    marginRight: Spacing.sm,
  },
  aiSection: { gap: Spacing.sm },
  mockBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.warningBg,
    padding: Spacing.sm,
    borderRadius: Radius.md,
  },
  mockText: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.labelSm,
    color: Colors.warning,
  },
  aiCard: { padding: Spacing.base },
  aiMeta: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  pestName: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h2,
    color: Colors.charcoal,
    marginBottom: 2,
  },
  pestNameRw: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    marginBottom: Spacing.sm,
  },
  aiMetrics: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xl,
    marginVertical: Spacing.sm,
  },
  escalation: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.severityCriticalBg,
    padding: Spacing.sm,
    borderRadius: Radius.sm,
    marginTop: Spacing.sm,
  },
  escalationText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.severityCritical,
    flex: 1,
  },
  recsSection: { marginTop: Spacing.base, gap: Spacing.sm },
  recRow: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'flex-start' },
  recText: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    lineHeight: 22,
  },
  historySection: { gap: Spacing.sm },
  historyItem: { flexDirection: 'row', gap: Spacing.sm },
  historyDot: { alignItems: 'center', width: 16 },
  historyDotInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: Colors.border,
    marginTop: 4,
  },
  historyLine: {
    flex: 1,
    width: 2,
    backgroundColor: Colors.borderLight,
    marginTop: 4,
  },
  historyContent: { flex: 1, paddingBottom: Spacing.base },
  historyAction: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.bodySm,
    color: Colors.charcoal,
    textTransform: 'capitalize',
  },
  historyNotes: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    marginTop: 2,
  },
  historyDate: {
    fontFamily: FontFamily.regular,
    fontSize: 11,
    color: Colors.charcoalLight,
    marginTop: 3,
  },
});
