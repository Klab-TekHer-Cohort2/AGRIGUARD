/**
 * Screen: Community Outbreak Early-Warning Map & Sentinel Dashboard
 *
 * Visualises pest and disease propagation across Rwandan districts
 * and agro-ecological zones (Gatsibo, Musanze, Bugesera, Nyagatare).
 * Provides transparent 0â€“100 risk scores, 5 km Haversine alert zones,
 * and agronomist containment protocols.
 */
import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  FlatList,
} from 'react-native';
import { useRouter } from 'expo-router';
import {
  MapPin,
  AlertTriangle,
  Shield,
  Activity,
  Layers,
  Filter,
  CheckCircle,
  Clock,
  ArrowLeft,
  ChevronRight,
  TrendingUp,
  Info,
  Radio,
} from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { Card } from '../../src/components/common/Card';
import { useDemoStore } from '../../src/demo/demoStore';

interface DistrictOutbreak {
  id: string;
  district: string;
  province: string;
  sector: string;
  primaryCrop: string;
  problem: string;
  riskScore: number; // 0 - 100
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  reportCount: number;
  alertRadiusKm: number;
  lastReported: string;
  status: 'VERIFIED' | 'SUSPECTED' | 'RESOLVED';
  recommendation: string;
  affectedVillages: string[];
}

const DISTRICT_OUTBREAKS: DistrictOutbreak[] = [
  {
    id: 'out-01',
    district: 'Gatsibo',
    province: 'Eastern Province',
    sector: 'Kabarore',
    primaryCrop: 'Maize',
    problem: 'Fall Armyworm (Inkongwa)',
    riskScore: 84,
    severity: 'HIGH',
    reportCount: 14,
    alertRadiusKm: 5.0,
    lastReported: '2 hours ago',
    status: 'VERIFIED',
    recommendation: 'Immediate whorl scouting; organic neem/biological control dispatched to local cooperatives.',
    affectedVillages: ['Kabarore Center', 'Kabeza', 'Rugarama', 'Nyabisindu'],
  },
  {
    id: 'out-02',
    district: 'Musanze',
    province: 'Northern Province',
    sector: 'Kinigi',
    primaryCrop: 'Irish Potato',
    problem: 'Late Blight (Imvura/Miyangire)',
    riskScore: 92,
    severity: 'CRITICAL',
    reportCount: 19,
    alertRadiusKm: 6.5,
    lastReported: '45 mins ago',
    status: 'VERIFIED',
    recommendation: 'High humidity outbreak detected. Apply preventive copper-based fungicide; isolate affected plots.',
    affectedVillages: ['Bisoke Foothills', 'Nyange', 'Kagano', 'Susa'],
  },
  {
    id: 'out-03',
    district: 'Bugesera',
    province: 'Eastern Province',
    sector: 'Nyamata',
    primaryCrop: 'Cassava',
    problem: 'Cassava Mosaic Disease (CMD)',
    riskScore: 58,
    severity: 'MEDIUM',
    reportCount: 7,
    alertRadiusKm: 4.0,
    lastReported: '1 day ago',
    status: 'SUSPECTED',
    recommendation: 'Uproot and destroy infected cuttings. Plant certified CMD-tolerant varieties from RAB.',
    affectedVillages: ['Nyamata West', 'Kayumba', 'Kanzenze'],
  },
  {
    id: 'out-04',
    district: 'Nyagatare',
    province: 'Eastern Province',
    sector: 'Nyagatare',
    primaryCrop: 'Beans',
    problem: 'Bean Anthracnose',
    riskScore: 34,
    severity: 'LOW',
    reportCount: 3,
    alertRadiusKm: 3.0,
    lastReported: '3 days ago',
    status: 'RESOLVED',
    recommendation: 'Seed rotation completed. Sporadic lesions successfully contained.',
    affectedVillages: ['Rukomo', 'Ryabega'],
  },
];

export default function OutbreakMapScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const isDemoMode = useDemoStore((s) => s.isDemoMode);

  const [selectedCrop, setSelectedCrop] = useState<string>('ALL');
  const [selectedCluster, setSelectedCluster] = useState<DistrictOutbreak>(DISTRICT_OUTBREAKS[0]);

  // Filtered outbreaks
  const filteredOutbreaks = useMemo(() => {
    if (selectedCrop === 'ALL') return DISTRICT_OUTBREAKS;
    return DISTRICT_OUTBREAKS.filter((d) => d.primaryCrop.toUpperCase() === selectedCrop);
  }, [selectedCrop]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={[styles.content, { paddingTop: insets.top + 12, paddingBottom: insets.bottom + 40 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn} accessibilityRole="button">
          <ArrowLeft size={20} color={Colors.primaryForest} />
        </TouchableOpacity>
        <View style={styles.headerTitleWrap}>
          <Text style={styles.headerTitle}>Outbreak Early Warning</Text>
          <Text style={styles.headerSubtitle}>Community Sentinel Surveillance Map</Text>
        </View>
        <View style={styles.badgeWrap}>
          <Text style={styles.demoBadgeText}>SENTINEL</Text>
        </View>
      </View>

      {/* Explainer Banner */}
      <View style={styles.infoBanner}>
        <Info size={16} color={Colors.primaryForest} />
        <Text style={styles.infoBannerText}>
          When a farmer submits a crop photograph, AgriGuard geo-clusters reports within a 5 km radius, calculating an outbreak risk score to warn neighboring smallholders before pests spread.
        </Text>
      </View>

      {/* Interactive Rwanda Agro-Ecological Map Graphic */}
      <View style={styles.mapContainer}>
        <View style={styles.mapHeader}>
          <View style={styles.mapHeaderLeft}>
            <Radio size={14} color={Colors.secondaryEmerald} />
            <Text style={styles.mapHeaderText}>RWANDA AGRO-CLUSTERS</Text>
          </View>
          <Text style={styles.liveBadge}>LIVE SENTINEL</Text>
        </View>

        {/* Visual Map Representation */}
        <View style={styles.mapCanvas}>
          {/* Map Region Markers */}
          {DISTRICT_OUTBREAKS.map((ob) => {
            const isSelected = selectedCluster.id === ob.id;
            const severityColor =
              ob.severity === 'CRITICAL' ? Colors.severityCritical :
              ob.severity === 'HIGH' ? Colors.severityHigh :
              ob.severity === 'MEDIUM' ? Colors.severityMedium : Colors.secondaryEmerald;

            return (
              <TouchableOpacity
                key={ob.id}
                style={[
                  styles.mapPinWrap,
                  ob.district === 'Musanze' && { top: 32, left: '22%' },
                  ob.district === 'Gatsibo' && { top: 60, right: '20%' },
                  ob.district === 'Bugesera' && { bottom: 44, left: '46%' },
                  ob.district === 'Nyagatare' && { top: 24, right: '14%' },
                ]}
                onPress={() => setSelectedCluster(ob)}
                activeOpacity={0.8}
              >
                {/* 5 km Radius Pulse circle */}
                <View style={[styles.pulseRing, { borderColor: severityColor, transform: [{ scale: isSelected ? 1.4 : 1 }] }]} />
                <View style={[styles.mapPinCircle, { backgroundColor: severityColor, borderWidth: isSelected ? 3 : 1.5 }]}>
                  <Text style={styles.pinText}>{ob.reportCount}</Text>
                </View>
                <Text style={[styles.pinLabel, isSelected && styles.pinLabelSelected]}>{ob.district}</Text>
              </TouchableOpacity>
            );
          })}

          {/* Compass Rose */}
          <View style={styles.compass}>
            <Text style={styles.compassText}>N</Text>
            <Text style={styles.compassSub}>RWANDA</Text>
          </View>
        </View>

        {/* Crop Filter Tabs */}
        <View style={styles.filterRow}>
          {['ALL', 'MAIZE', 'POTATO', 'CASSAVA', 'BEANS'].map((crop) => (
            <TouchableOpacity
              key={crop}
              style={[styles.filterChip, selectedCrop === crop && styles.filterChipActive]}
              onPress={() => setSelectedCrop(crop)}
            >
              <Text style={[styles.filterChipText, selectedCrop === crop && styles.filterChipTextActive]}>{crop}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Selected Outbreak Cluster Detail */}
      <View style={styles.clusterDetailCard}>
        <View style={styles.clusterHeader}>
          <View>
            <View style={styles.clusterTitleRow}>
              <Text style={styles.clusterDistrict}>{selectedCluster.district}</Text>
              <Text style={styles.clusterSector}>({selectedCluster.sector} Sector)</Text>
            </View>
            <Text style={styles.clusterProvince}>{selectedCluster.province}</Text>
          </View>
          <SeverityBadge severity={selectedCluster.severity} size="md" />
        </View>

        {/* Risk Score Gauge Metric */}
        <View style={styles.scoreRow}>
          <View style={styles.scoreBox}>
            <Text style={styles.scoreNumber}>{selectedCluster.riskScore}</Text>
            <Text style={styles.scoreLabel}>Outbreak Risk Score (0-100)</Text>
          </View>
          <View style={styles.scoreDivider} />
          <View style={styles.metricBox}>
            <Text style={styles.metricVal}>{selectedCluster.reportCount} reports</Text>
            <Text style={styles.metricSub}>within {selectedCluster.alertRadiusKm} km radius</Text>
          </View>
        </View>

        {/* Outbreak Specifics */}
        <View style={styles.outbreakField}>
          <Text style={styles.fieldLabel}>AFFECTED CROP & PROBLEM</Text>
          <Text style={styles.fieldVal}>{selectedCluster.primaryCrop} â€” {selectedCluster.problem}</Text>
        </View>

        <View style={styles.outbreakField}>
          <Text style={styles.fieldLabel}>MONITORED VILLAGES</Text>
          <Text style={styles.fieldVal}>{selectedCluster.affectedVillages.join(' â€¢ ')}</Text>
        </View>

        <View style={[styles.outbreakField, styles.recommendationBox]}>
          <View style={styles.recTitleRow}>
            <Shield size={14} color={Colors.primaryForest} />
            <Text style={styles.recTitle}>AGRONOMIST INTERVENTION ADVICE</Text>
          </View>
          <Text style={styles.recText}>{selectedCluster.recommendation}</Text>
        </View>
      </View>

      {/* All Monitored Clusters List */}
      <View style={styles.listSection}>
        <Text style={styles.listSectionTitle}>All Monitored Outbreak Zones ({filteredOutbreaks.length})</Text>
        {filteredOutbreaks.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={[styles.itemCard, selectedCluster.id === item.id && styles.itemCardActive]}
            onPress={() => setSelectedCluster(item)}
            activeOpacity={0.8}
          >
            <View style={styles.itemRow}>
              <View style={styles.itemLeft}>
                <Text style={styles.itemTitle}>{item.district} â€” {item.problem}</Text>
                <Text style={styles.itemSub}>{item.reportCount} reports â€¢ Last reported {item.lastReported}</Text>
              </View>
              <SeverityBadge severity={item.severity} size="sm" />
            </View>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.backgroundWarm,
  },
  content: {
    paddingHorizontal: Spacing.md,
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginBottom: Spacing.sm,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: Radius.full,
    backgroundColor: Colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.borderLight,
    marginRight: Spacing.sm,
  },
  headerTitleWrap: {
    flex: 1,
  },
  headerTitle: {
    fontSize: FontSize.h4,
    fontFamily: FontFamily.bold,
    color: Colors.charcoal,
  },
  headerSubtitle: {
    fontSize: FontSize.caption,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalMuted,
  },
  badgeWrap: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: Colors.severityHighBg,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.severityHigh,
  },
  demoBadgeText: {
    fontSize: 10,
    fontFamily: FontFamily.bold,
    color: '#7C2D12',
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSage,
    padding: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: Spacing.md,
    width: '100%',
    maxWidth: 540,
    gap: 8,
  },
  infoBannerText: {
    flex: 1,
    fontSize: FontSize.caption,
    fontFamily: FontFamily.regular,
    color: Colors.charcoal,
    lineHeight: 18,
  },
  mapContainer: {
    width: '100%',
    maxWidth: 540,
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    marginBottom: Spacing.md,
  },
  mapHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  mapHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  mapHeaderText: {
    fontSize: 11,
    fontFamily: FontFamily.bold,
    color: Colors.charcoal,
    letterSpacing: 0.5,
  },
  liveBadge: {
    fontSize: 9,
    fontFamily: FontFamily.bold,
    color: Colors.secondaryEmerald,
    backgroundColor: Colors.successBg,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: Radius.sm,
  },
  mapCanvas: {
    height: 230,
    backgroundColor: '#EFF7ED',
    borderRadius: Radius.md,
    position: 'relative',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: Colors.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  mapPinWrap: {
    position: 'absolute',
    alignItems: 'center',
    zIndex: 10,
  },
  pulseRing: {
    position: 'absolute',
    width: 44,
    height: 44,
    borderRadius: Radius.full,
    borderWidth: 1.5,
    opacity: 0.4,
    top: -6,
  },
  mapPinCircle: {
    width: 30,
    height: 30,
    borderRadius: Radius.full,
    borderColor: Colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  pinText: {
    color: Colors.white,
    fontFamily: FontFamily.bold,
    fontSize: 12,
  },
  pinLabel: {
    fontSize: 10,
    fontFamily: FontFamily.semiBold,
    color: Colors.charcoal,
    marginTop: 2,
    backgroundColor: 'rgba(255,255,255,0.85)',
    paddingHorizontal: 4,
    borderRadius: 3,
  },
  pinLabelSelected: {
    fontFamily: FontFamily.bold,
    color: Colors.primaryForest,
  },
  compass: {
    position: 'absolute',
    top: 10,
    right: 12,
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.7)',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 4,
  },
  compassText: {
    fontSize: 10,
    fontFamily: FontFamily.bold,
    color: Colors.charcoalMuted,
  },
  compassSub: {
    fontSize: 8,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalLight,
  },
  filterRow: {
    flexDirection: 'row',
    marginTop: 10,
    gap: 6,
    flexWrap: 'wrap',
  },
  filterChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: Radius.full,
    backgroundColor: Colors.backgroundWarm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  filterChipActive: {
    backgroundColor: Colors.primaryForest,
    borderColor: Colors.primaryForest,
  },
  filterChipText: {
    fontSize: 10,
    fontFamily: FontFamily.semiBold,
    color: Colors.charcoalMuted,
  },
  filterChipTextActive: {
    color: Colors.white,
  },
  clusterDetailCard: {
    width: '100%',
    maxWidth: 540,
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    marginBottom: Spacing.md,
  },
  clusterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  clusterTitleRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
  },
  clusterDistrict: {
    fontSize: FontSize.h4,
    fontFamily: FontFamily.bold,
    color: Colors.charcoal,
  },
  clusterSector: {
    fontSize: FontSize.bodySm,
    fontFamily: FontFamily.medium,
    color: Colors.charcoalMuted,
  },
  clusterProvince: {
    fontSize: FontSize.caption,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalLight,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundWarm,
    borderRadius: Radius.md,
    padding: Spacing.sm,
    marginBottom: 12,
  },
  scoreBox: {
    flex: 1,
  },
  scoreNumber: {
    fontSize: 26,
    fontFamily: FontFamily.bold,
    color: Colors.primaryForest,
  },
  scoreLabel: {
    fontSize: 10,
    fontFamily: FontFamily.medium,
    color: Colors.charcoalMuted,
  },
  scoreDivider: {
    width: 1,
    height: 36,
    backgroundColor: Colors.border,
    marginHorizontal: 12,
  },
  metricBox: {
    flex: 1,
  },
  metricVal: {
    fontSize: 14,
    fontFamily: FontFamily.bold,
    color: Colors.charcoal,
  },
  metricSub: {
    fontSize: 10,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalLight,
  },
  outbreakField: {
    marginBottom: 8,
  },
  fieldLabel: {
    fontSize: 10,
    fontFamily: FontFamily.bold,
    color: Colors.charcoalMuted,
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  fieldVal: {
    fontSize: 13,
    fontFamily: FontFamily.medium,
    color: Colors.charcoal,
  },
  recommendationBox: {
    backgroundColor: Colors.backgroundSage,
    padding: 10,
    borderRadius: Radius.md,
    marginTop: 4,
  },
  recTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  recTitle: {
    fontSize: 10,
    fontFamily: FontFamily.bold,
    color: Colors.primaryForest,
    letterSpacing: 0.5,
  },
  recText: {
    fontSize: 12,
    fontFamily: FontFamily.regular,
    color: Colors.charcoal,
    lineHeight: 17,
  },
  listSection: {
    width: '100%',
    maxWidth: 540,
    marginBottom: Spacing.md,
  },
  listSectionTitle: {
    fontSize: FontSize.bodySm,
    fontFamily: FontFamily.bold,
    color: Colors.charcoal,
    marginBottom: 8,
  },
  itemCard: {
    backgroundColor: Colors.white,
    padding: 12,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    marginBottom: 8,
  },
  itemCardActive: {
    borderColor: Colors.secondaryEmerald,
    backgroundColor: '#F3F9F1',
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemLeft: {
    flex: 1,
    marginRight: 8,
  },
  itemTitle: {
    fontSize: 13,
    fontFamily: FontFamily.bold,
    color: Colors.charcoal,
    marginBottom: 2,
  },
  itemSub: {
    fontSize: 11,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalMuted,
  },
});
