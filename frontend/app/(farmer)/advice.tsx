/**
 * Agricultural Advice screen
 * Displays farming guidance organised by crop and pest.
 * Always shows sample data — this is a local knowledge base feature.
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, FlatList } from 'react-native';
import { BookOpen, ChevronDown, ChevronUp, CheckCircle } from 'lucide-react-native';
import { ScreenHeader } from '../../src/components/common/ScreenHeader';
import { Card } from '../../src/components/common/Card';
import { SeverityBadge } from '../../src/components/common/SeverityBadge';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { DEMO_ADVICE } from '../../src/demo/data';

export default function AdviceScreen() {
  const { language } = useTranslation();
  const insets = useSafeAreaInsets();
  const [expanded, setExpanded] = useState<number | null>(0);
  const [cropFilter, setCropFilter] = useState<string>('All');

  const crops = ['All', ...Array.from(new Set(DEMO_ADVICE.map((a) => a.crop)))];
  const filtered = cropFilter === 'All' ? DEMO_ADVICE : DEMO_ADVICE.filter((a) => a.crop === cropFilter);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScreenHeader title="Agricultural Advice" showLanguage />

      {/* Info banner */}
      <View style={styles.infoBanner}>
        <BookOpen size={14} color={Colors.info} />
        <Text style={styles.infoText}>Sample farming guidance. Verify recommendations with your local extension officer.</Text>
      </View>

      {/* Crop filter */}
      <FlatList
        data={crops}
        horizontal
        showsHorizontalScrollIndicator={false}
        keyExtractor={(s) => s}
        contentContainerStyle={styles.filterRow}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => setCropFilter(item)}
            style={[styles.filterChip, cropFilter === item && styles.filterChipActive]}
            accessibilityRole="button"
            accessibilityState={{ selected: cropFilter === item }}
          >
            <Text style={[styles.filterChipText, cropFilter === item && styles.filterChipTextActive]}>{item}</Text>
          </TouchableOpacity>
        )}
      />

      <ScrollView contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 80 }]} showsVerticalScrollIndicator={false}>
        {filtered.map((article, i) => {
          const isOpen = expanded === i;
          return (
            <Card key={article.id} style={styles.articleCard}>
              <TouchableOpacity
                onPress={() => setExpanded(isOpen ? null : i)}
                style={styles.articleHeader}
                accessibilityRole="button"
                accessibilityState={{ expanded: isOpen }}
                accessibilityLabel={article.title}
              >
                <View style={styles.articleHeaderLeft}>
                  <View style={styles.cropBadge}>
                    <Text style={styles.cropBadgeText}>{language === 'rw' ? article.crop_rw : article.crop}</Text>
                  </View>
                  <SeverityBadge severity={article.severity_risk} size="sm" />
                </View>
                <Text style={styles.articleTitle}>{language === 'rw' ? article.title_rw : article.title}</Text>
                <View style={styles.articleToggle}>
                  {isOpen ? <ChevronUp size={18} color={Colors.charcoalMuted} /> : <ChevronDown size={18} color={Colors.charcoalMuted} />}
                </View>
              </TouchableOpacity>

              {isOpen && (
                <View style={styles.articleBody}>
                  <Text style={styles.summary}>{article.summary}</Text>
                  <Text style={styles.stepsLabel}>Recommended Steps:</Text>
                  {article.steps.map((step, j) => (
                    <View key={j} style={styles.step}>
                      <CheckCircle size={14} color={Colors.secondaryEmerald} style={{ marginTop: 2 }} />
                      <Text style={styles.stepText}>{step}</Text>
                    </View>
                  ))}
                </View>
              )}
            </Card>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  infoBanner: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, backgroundColor: Colors.infoBg, paddingHorizontal: Spacing.base, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: Colors.info + '20' },
  infoText: { flex: 1, fontFamily: FontFamily.regular, fontSize: FontSize.labelSm, color: Colors.info },
  filterRow: { gap: Spacing.sm, paddingHorizontal: Spacing.base, paddingVertical: Spacing.sm },
  filterChip: { paddingHorizontal: Spacing.sm, paddingVertical: 6, borderRadius: Radius.full, borderWidth: 1, borderColor: Colors.border, backgroundColor: Colors.backgroundCard },
  filterChipActive: { backgroundColor: Colors.secondaryEmerald, borderColor: Colors.secondaryEmerald },
  filterChipText: { fontFamily: FontFamily.medium, fontSize: FontSize.labelSm, color: Colors.charcoal },
  filterChipTextActive: { color: Colors.white },
  list: { paddingHorizontal: Spacing.base, paddingTop: Spacing.sm, gap: Spacing.sm },
  articleCard: { padding: 0, overflow: 'hidden' },
  articleHeader: { padding: Spacing.base, gap: 6 },
  articleHeaderLeft: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'center', marginBottom: 4 },
  cropBadge: { backgroundColor: Colors.backgroundSage, borderRadius: Radius.full, paddingHorizontal: Spacing.sm, paddingVertical: 3 },
  cropBadgeText: { fontFamily: FontFamily.semiBold, fontSize: FontSize.labelSm, color: Colors.primaryForest },
  articleTitle: { fontFamily: FontFamily.semiBold, fontSize: FontSize.body, color: Colors.charcoal, lineHeight: 22 },
  articleToggle: { position: 'absolute', right: Spacing.base, top: Spacing.base },
  articleBody: { padding: Spacing.base, paddingTop: 0, borderTopWidth: 1, borderTopColor: Colors.borderLight, gap: Spacing.sm },
  summary: { fontFamily: FontFamily.regular, fontSize: FontSize.body, color: Colors.charcoalMuted, lineHeight: 22 },
  stepsLabel: { fontFamily: FontFamily.semiBold, fontSize: FontSize.bodySm, color: Colors.charcoal, marginTop: 4 },
  step: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'flex-start' },
  stepText: { flex: 1, fontFamily: FontFamily.regular, fontSize: FontSize.body, color: Colors.charcoal, lineHeight: 22 },
});
