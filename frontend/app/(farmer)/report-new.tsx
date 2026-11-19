/**
 * Screen 5 — Report a Problem (5-step flow)
 * Step 1: Pick crop (GET /crops/)
 * Step 2: Describe symptoms
 * Step 3: Take/upload photo (POST /reports/{id}/images)
 * Step 4: Confirm location
 * Step 5: Submit (POST /reports/) → AI result reveal
 *
 * Screen 6 — AI Result Card (shown after submission)
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Image,
  ActivityIndicator,
  Alert,
  FlatList,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import * as Location from 'expo-location';
import {
  Camera,
  Image as ImageIcon,
  MapPin,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
  X,
  Leaf,
  Zap,
} from 'lucide-react-native';
import { Button } from '../../src/components/common/Button';
import { Card } from '../../src/components/common/Card';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { ConfidenceRing } from '../../src/components/common/ConfidenceRing';
import { Input } from '../../src/components/common/Input';
import { SkeletonCard } from '../../src/components/common/SkeletonLoader';
import { Colors, FontFamily, FontSize, Spacing, Radius, Shadow } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { cropsApi, reportsApi, CropResponse, CropReportResponse } from '../../src/api/client';
import { BACKEND_BASE_URL } from '../../src/api/config';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Common symptoms a farmer might observe
const COMMON_SYMPTOMS = [
  'yellowing_leaves', 'brown_spots', 'wilting', 'holes_in_leaves',
  'white_powder', 'black_mold', 'stem_rot', 'root_rot',
  'stunted_growth', 'leaf_curl', 'discoloration', 'pest_visible',
];

type Step = 1 | 2 | 3 | 4 | 5 | 'result';
type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export default function ReportNewScreen() {
  const router = useRouter();
  const { t, language } = useTranslation();
  const insets = useSafeAreaInsets();

  // Step state
  const [step, setStep] = useState<Step>(1);

  // Form state
  const [crops, setCrops] = useState<CropResponse[]>([]);
  const [selectedCrop, setSelectedCrop] = useState<CropResponse | null>(null);
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState<Severity>('LOW');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [district, setDistrict] = useState('');
  const [sector, setSector] = useState('');
  const [lat, setLat] = useState<number | undefined>();
  const [lng, setLng] = useState<number | undefined>();

  // Submission state
  const [loading, setLoading] = useState(false);
  const [cropsLoading, setCropsLoading] = useState(true);
  const [result, setResult] = useState<CropReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cropsApi.list().then((cs) => {
      setCrops(cs);
      setCropsLoading(false);
    }).catch(() => setCropsLoading(false));
  }, []);

  const pickImage = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return;
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
      allowsEditing: true,
    });
    if (!res.canceled) {
      const compressed = await ImageManipulator.manipulateAsync(
        res.assets[0].uri,
        [{ resize: { width: 1024 } }],
        { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG },
      );
      setPhotoUri(compressed.uri);
    }
  };

  const takePhoto = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) return;
    const res = await ImagePicker.launchCameraAsync({
      quality: 0.8,
      allowsEditing: true,
    });
    if (!res.canceled) {
      const compressed = await ImageManipulator.manipulateAsync(
        res.assets[0].uri,
        [{ resize: { width: 1024 } }],
        { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG },
      );
      setPhotoUri(compressed.uri);
    }
  };

  const getLocation = async () => {
    const perm = await Location.requestForegroundPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('', t.report.locationPermissionDenied);
      return;
    }
    const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    setLat(loc.coords.latitude);
    setLng(loc.coords.longitude);
  };

  const toggleSymptom = (s: string) => {
    setSymptoms((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
    );
  };

  const handleSubmit = async () => {
    if (!selectedCrop) return;
    setLoading(true);
    setStep(5);
    setError(null);

    try {
      // Create report
      const report = await reportsApi.create({
        crop_id: selectedCrop.id,
        channel: 'APP',
        description: description || undefined,
        symptoms,
        severity,
        district: district || undefined,
        sector: sector || undefined,
        latitude: lat,
        longitude: lng,
      });

      // Upload photo if provided
      if (photoUri) {
        try {
          const form = new FormData();
          form.append('file', {
            uri: photoUri,
            name: 'crop_photo.jpg',
            type: 'image/jpeg',
          } as unknown as Blob);
          await reportsApi.uploadImage(report.id, form);
        } catch {
          // non-fatal — report submitted, photo failed
        }
      }

      // Reload full report (with AI result)
      let full = report;
      try {
        full = await reportsApi.getByCode(report.report_code);
      } catch {
        // use initial response
      }

      setResult(full);
      setStep('result');
    } catch (err) {
      setError(t.report.submitError);
      setStep(4);
    } finally {
      setLoading(false);
    }
  };

  if (step === 'result' && result) {
    return <AIResultScreen result={result} onDone={() => router.replace('/(farmer)/reports')} />;
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Progress header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => (step === 1 ? router.back() : setStep((s) => (Number(s) - 1) as Step))}
          style={styles.backBtn}
          accessibilityLabel={t.common.back}
        >
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <View style={styles.progressWrap}>
          {([1, 2, 3, 4] as const).map((s) => (
            <View
              key={s}
              style={[
                styles.progressDot,
                (step as number) >= s && styles.progressDotActive,
              ]}
            />
          ))}
        </View>
        <View style={{ width: 40 }} />
      </View>

      {/* Step 1 — Pick Crop */}
      {step === 1 && (
        <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.stepTitle}>{t.report.step1Title}</Text>
          <Text style={styles.stepSubtitle}>{t.report.step1Subtitle}</Text>
          {cropsLoading ? (
            <View style={styles.cropGrid}>
              {[1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)}
            </View>
          ) : (
            <View style={styles.cropGrid}>
              {crops.map((crop) => (
                <TouchableOpacity
                  key={crop.id}
                  onPress={() => { setSelectedCrop(crop); setStep(2); }}
                  style={[
                    styles.cropCard,
                    selectedCrop?.id === crop.id && styles.cropCardActive,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={`${crop.name_en}, ${crop.name_rw}`}
                  accessibilityState={{ selected: selectedCrop?.id === crop.id }}
                >
                  <View style={styles.cropIcon}>
                    <Leaf size={24} color={Colors.secondaryEmerald} />
                  </View>
                  <Text style={styles.cropNameEn} numberOfLines={1}>
                    {language === 'rw' ? crop.name_rw : crop.name_en}
                  </Text>
                  <Text style={styles.cropNameRw} numberOfLines={1}>
                    {language === 'rw' ? crop.name_en : crop.name_rw}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
          <View style={{ height: 80 }} />
        </ScrollView>
      )}

      {/* Step 2 — Symptoms */}
      {step === 2 && (
        <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.stepTitle}>{t.report.step2Title}</Text>
          <Text style={styles.stepSubtitle}>{t.report.step2Subtitle}</Text>
          <Text style={styles.sectionLabel}>{t.report.symptoms}</Text>
          <View style={styles.symptomsWrap}>
            {COMMON_SYMPTOMS.map((s) => {
              const selected = symptoms.includes(s);
              return (
                <TouchableOpacity
                  key={s}
                  onPress={() => toggleSymptom(s)}
                  style={[styles.symptomChip, selected && styles.symptomChipActive]}
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: selected }}
                  accessibilityLabel={s.replace(/_/g, ' ')}
                >
                  {selected && <CheckCircle size={14} color={Colors.white} />}
                  <Text style={[styles.symptomText, selected && styles.symptomTextActive]}>
                    {s.replace(/_/g, ' ')}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text style={styles.sectionLabel}>{t.report.description}</Text>
          <TextInput
            style={styles.textArea}
            placeholder={t.report.descriptionHint}
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={4}
            placeholderTextColor={Colors.charcoalLight}
            accessibilityLabel={t.report.description}
          />

          <Text style={styles.sectionLabel}>{t.report.severity}</Text>
          <View style={styles.severityRow}>
            {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as Severity[]).map((s) => (
              <TouchableOpacity
                key={s}
                onPress={() => setSeverity(s)}
                style={[styles.severityBtn, severity === s && styles.severityBtnActive]}
                accessibilityRole="button"
                accessibilityState={{ selected: severity === s }}
              >
                <Text style={[styles.severityBtnText, severity === s && styles.severityBtnTextActive]}>
                  {s}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Button
            label={t.common.next}
            onPress={() => setStep(3)}
            fullWidth
            size="lg"
            style={styles.nextBtn}
          />
          <View style={{ height: 80 }} />
        </ScrollView>
      )}

      {/* Step 3 — Photo */}
      {step === 3 && (
        <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.stepTitle}>{t.report.step3Title}</Text>
          <Text style={styles.stepSubtitle}>{t.report.step3Subtitle}</Text>

          {photoUri ? (
            <View style={styles.photoPreviewWrap}>
              <Image source={{ uri: photoUri }} style={styles.photoPreview} resizeMode="cover" />
              <TouchableOpacity
                onPress={() => setPhotoUri(null)}
                style={styles.removePhoto}
                accessibilityLabel="Remove photo"
              >
                <X size={16} color={Colors.white} />
              </TouchableOpacity>
            </View>
          ) : (
            <Card variant="flat" style={styles.photoPlaceholder}>
              <ImageIcon size={40} color={Colors.border} />
              <Text style={styles.photoPlaceholderText}>{t.report.photoOptional}</Text>
            </Card>
          )}

          <View style={styles.photoActions}>
            <Button
              label={t.report.takePhoto}
              onPress={takePhoto}
              variant="outline"
              icon={<Camera size={18} color={Colors.secondaryEmerald} />}
              style={styles.photoBtn}
            />
            <Button
              label={t.report.uploadPhoto}
              onPress={pickImage}
              variant="outline"
              icon={<ImageIcon size={18} color={Colors.secondaryEmerald} />}
              style={styles.photoBtn}
            />
          </View>

          <Button
            label={t.common.next}
            onPress={() => setStep(4)}
            fullWidth
            size="lg"
            style={styles.nextBtn}
          />
          <View style={{ height: 80 }} />
        </ScrollView>
      )}

      {/* Step 4 — Location */}
      {step === 4 && (
        <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.stepTitle}>{t.report.step4Title}</Text>
          <Text style={styles.stepSubtitle}>{t.report.step4Subtitle}</Text>

          {error && (
            <View style={styles.errorBanner}>
              <AlertTriangle size={16} color={Colors.error} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          <Input
            label={t.report.locationDistrict}
            placeholder={t.auth.districtHint}
            value={district}
            onChangeText={setDistrict}
            leftIcon={<MapPin size={18} color={Colors.charcoalLight} />}
          />
          <Input
            label={t.report.locationSector}
            placeholder={t.auth.sectorHint}
            value={sector}
            onChangeText={setSector}
            leftIcon={<MapPin size={18} color={Colors.charcoalLight} />}
          />

          <Button
            label={t.report.useCurrentLocation}
            onPress={getLocation}
            variant="outline"
            icon={<MapPin size={18} color={Colors.secondaryEmerald} />}
            fullWidth
            style={styles.locationBtn}
          />
          {lat && lng && (
            <Text style={styles.gpsText}>
              📍 {lat.toFixed(4)}, {lng.toFixed(4)}
            </Text>
          )}

          {/* Summary */}
          <Card variant="sage" style={styles.summary}>
            <Text style={styles.summaryTitle}>
              {language === 'rw' ? selectedCrop?.name_rw : selectedCrop?.name_en}
            </Text>
            {symptoms.length > 0 && (
              <Text style={styles.summaryDetail}>
                {symptoms.length} symptom{symptoms.length > 1 ? 's' : ''}
              </Text>
            )}
            {photoUri && (
              <Text style={styles.summaryDetail}>📷 Photo attached</Text>
            )}
          </Card>

          <Button
            label={t.report.submitTitle}
            onPress={handleSubmit}
            loading={loading}
            fullWidth
            size="lg"
            style={styles.nextBtn}
            icon={<Zap size={18} color={Colors.white} />}
          />
          <View style={{ height: 80 }} />
        </ScrollView>
      )}

      {/* Step 5 — Analyzing */}
      {step === 5 && (
        <View style={styles.analyzingScreen}>
          <ActivityIndicator size="large" color={Colors.secondaryEmerald} />
          <Text style={styles.analyzingTitle}>{t.report.analyzing}</Text>
          <Text style={styles.analyzingSubtitle}>{t.report.analyzeSubtitle}</Text>
        </View>
      )}
    </View>
  );
}

/** AI Result reveal screen */
function AIResultScreen({
  result,
  onDone,
}: {
  result: CropReportResponse;
  onDone: () => void;
}) {
  const { t, language } = useTranslation();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const ai = result.ai_result;

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Success header */}
      <View style={[styles.resultHeader, { paddingTop: insets.top + 16 }]}>
        <CheckCircle size={40} color={Colors.secondaryEmerald} />
        <Text style={styles.resultSuccessText}>{t.report.submitSuccess}</Text>
        <Text style={styles.resultCode}>{result.report_code}</Text>
      </View>

      {/* AI Result Card */}
      {ai ? (
        <View style={styles.resultBody}>
          {/* Mock notice — never show mock as confirmed */}
          {ai.is_mock && (
            <View style={styles.mockBanner}>
              <AlertTriangle size={16} color={Colors.warning} />
              <View style={{ flex: 1 }}>
                <Text style={styles.mockBadge}>{t.aiResult.mockBadge}</Text>
                <Text style={styles.mockNotice}>{t.aiResult.mockNotice}</Text>
              </View>
            </View>
          )}

          <Card style={styles.aiCard}>
            {/* Pest name */}
            <Text style={styles.aiLabel}>{t.aiResult.detectedPest}</Text>
            <Text style={styles.pestName}>
              {language === 'rw' ? (ai.predicted_pest_rw ?? ai.predicted_pest_en) : ai.predicted_pest_en}
            </Text>
            {language === 'en' && ai.predicted_pest_rw && (
              <Text style={styles.pestNameRw}>{ai.predicted_pest_rw}</Text>
            )}

            {/* Confidence ring + severity badge */}
            <View style={styles.aiMetrics}>
              <ConfidenceRing score={ai.confidence_score} />
              <View style={styles.aiMetricsRight}>
                <Text style={styles.aiLabel}>{t.aiResult.severity}</Text>
                <SeverityBadge severity={ai.detected_severity} />
              </View>
            </View>

            {/* Escalation banner */}
            {ai.detected_severity === 'HIGH' || ai.detected_severity === 'CRITICAL' ? (
              <View style={styles.escalationBanner}>
                <AlertTriangle size={16} color={Colors.severityCritical} />
                <Text style={styles.escalationText}>{t.aiResult.escalationBanner}</Text>
              </View>
            ) : null}

            {/* Recommendations */}
            {ai.recommendations && ai.recommendations.length > 0 && (
              <>
                <Text style={[styles.aiLabel, { marginTop: Spacing.base }]}>
                  {t.aiResult.recommendations}
                </Text>
                {ai.recommendations.map((rec, i) => (
                  <View key={i} style={styles.recRow}>
                    <Text style={styles.recBullet}>•</Text>
                    <Text style={styles.recText}>{rec}</Text>
                  </View>
                ))}
              </>
            )}
          </Card>

          {/* Contact agronomist CTA */}
          <Button
            label={t.aiResult.contactAgronomist}
            onPress={() => {}}
            variant="outline"
            fullWidth
            style={{ marginTop: Spacing.sm }}
          />
        </View>
      ) : (
        <Card style={[styles.resultBody, styles.noResultCard]}>
          <Text style={styles.noResultText}>{t.aiResult.noResult}</Text>
        </Card>
      )}

      <Button
        label={t.common.done}
        onPress={onDone}
        fullWidth
        size="lg"
        style={{ marginHorizontal: Spacing.base, marginTop: Spacing.base }}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  backBtn: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
  backText: { fontSize: 22, color: Colors.charcoal },
  progressWrap: { flexDirection: 'row', gap: 6 },
  progressDot: {
    width: 24,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.border,
  },
  progressDotActive: { backgroundColor: Colors.secondaryEmerald },
  scroll: { flex: 1, paddingHorizontal: Spacing.base },
  stepTitle: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h2,
    color: Colors.charcoal,
    marginTop: Spacing.xl,
    marginBottom: Spacing.xs,
  },
  stepSubtitle: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    marginBottom: Spacing.xl,
  },
  cropGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  cropCard: {
    width: '47%',
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    alignItems: 'center',
    gap: Spacing.sm,
    borderWidth: 1.5,
    borderColor: Colors.border,
    ...Shadow.xs,
  },
  cropCardActive: {
    borderColor: Colors.secondaryEmerald,
    backgroundColor: Colors.successBg,
  },
  cropIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cropNameEn: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    textAlign: 'center',
  },
  cropNameRw: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    textAlign: 'center',
  },
  sectionLabel: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    marginBottom: Spacing.sm,
    marginTop: Spacing.sm,
  },
  symptomsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
    marginBottom: Spacing.base,
  },
  symptomChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 7,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.backgroundCard,
  },
  symptomChipActive: {
    backgroundColor: Colors.secondaryEmerald,
    borderColor: Colors.secondaryEmerald,
  },
  symptomText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.charcoal,
    textTransform: 'capitalize',
  },
  symptomTextActive: { color: Colors.white },
  textArea: {
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.md,
    borderWidth: 1.5,
    borderColor: Colors.border,
    padding: Spacing.base,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: Spacing.base,
  },
  severityRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginBottom: Spacing.base,
    flexWrap: 'wrap',
  },
  severityBtn: {
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  severityBtnActive: {
    backgroundColor: Colors.primaryForest,
    borderColor: Colors.primaryForest,
  },
  severityBtnText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.charcoal,
  },
  severityBtnTextActive: { color: Colors.white },
  nextBtn: { marginTop: Spacing.xl },
  photoPlaceholder: {
    height: 180,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.base,
  },
  photoPlaceholderText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: Colors.charcoalLight,
    textAlign: 'center',
    maxWidth: 200,
  },
  photoPreviewWrap: {
    borderRadius: Radius.lg,
    overflow: 'hidden',
    marginBottom: Spacing.base,
    position: 'relative',
  },
  photoPreview: { width: '100%', height: 200 },
  removePhoto: {
    position: 'absolute',
    top: Spacing.sm,
    right: Spacing.sm,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(0,0,0,0.6)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoActions: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.base },
  photoBtn: { flex: 1 },
  locationBtn: { marginBottom: Spacing.sm },
  gpsText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    marginBottom: Spacing.base,
    textAlign: 'center',
  },
  summary: { padding: Spacing.base, marginBottom: Spacing.base },
  summaryTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.h3,
    color: Colors.primaryForest,
    marginBottom: 4,
  },
  summaryDetail: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.bodySm,
    color: Colors.charcoalMuted,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.errorBg,
    borderRadius: Radius.md,
    padding: Spacing.base,
    marginBottom: Spacing.base,
  },
  errorText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.error,
    flex: 1,
  },
  analyzingScreen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.base,
    paddingHorizontal: Spacing.xxxl,
  },
  analyzingTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
    textAlign: 'center',
  },
  analyzingSubtitle: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    textAlign: 'center',
  },
  // Result screen
  resultHeader: {
    alignItems: 'center',
    padding: Spacing.xl,
    backgroundColor: Colors.backgroundCard,
    gap: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  resultSuccessText: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.h3,
    color: Colors.primaryForest,
  },
  resultCode: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
  },
  resultBody: { padding: Spacing.base },
  mockBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
    backgroundColor: Colors.warningBg,
    borderRadius: Radius.md,
    padding: Spacing.base,
    marginBottom: Spacing.sm,
    borderLeftWidth: 3,
    borderLeftColor: Colors.warning,
  },
  mockBadge: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.bodySm,
    color: Colors.warning,
  },
  mockNotice: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    marginTop: 2,
  },
  aiCard: { padding: Spacing.base },
  aiLabel: {
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
    marginBottom: Spacing.base,
  },
  aiMetrics: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xl,
    marginVertical: Spacing.base,
  },
  aiMetricsRight: { flex: 1, gap: 6 },
  escalationBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.severityCriticalBg,
    borderRadius: Radius.md,
    padding: Spacing.sm,
    marginTop: Spacing.sm,
    borderLeftWidth: 3,
    borderLeftColor: Colors.severityCritical,
  },
  escalationText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.severityCritical,
    flex: 1,
  },
  recRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  recBullet: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.secondaryEmerald,
    marginTop: 2,
  },
  recText: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    lineHeight: 22,
  },
  noResultCard: { alignItems: 'center', padding: Spacing.xl },
  noResultText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    textAlign: 'center',
  },
});
