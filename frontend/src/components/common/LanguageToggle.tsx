import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Globe } from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Radius, Spacing } from '../../theme';
import { useTranslation } from '../../hooks/useTranslation';

interface LanguageToggleProps {
  compact?: boolean;
}

export function LanguageToggle({ compact = false }: LanguageToggleProps) {
  const { language, setLanguage } = useTranslation();

  const toggle = () => setLanguage(language === 'en' ? 'rw' : 'en');

  if (compact) {
    return (
      <TouchableOpacity
        onPress={toggle}
        style={styles.compact}
        accessibilityLabel={`Switch language to ${language === 'en' ? 'Kinyarwanda' : 'English'}`}
        accessibilityRole="button"
      >
        <Globe size={16} color={Colors.primaryForest} />
        <Text style={styles.compactText}>{language.toUpperCase()}</Text>
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.container}>
      <Globe size={16} color={Colors.charcoalMuted} />
      <TouchableOpacity
        onPress={() => setLanguage('en')}
        style={[styles.option, language === 'en' && styles.activeOption]}
        accessibilityRole="button"
        accessibilityLabel="English"
        accessibilityState={{ selected: language === 'en' }}
      >
        <Text style={[styles.optionText, language === 'en' && styles.activeText]}>EN</Text>
      </TouchableOpacity>
      <View style={styles.divider} />
      <TouchableOpacity
        onPress={() => setLanguage('rw')}
        style={[styles.option, language === 'rw' && styles.activeOption]}
        accessibilityRole="button"
        accessibilityLabel="Kinyarwanda"
        accessibilityState={{ selected: language === 'rw' }}
      >
        <Text style={[styles.optionText, language === 'rw' && styles.activeText]}>RW</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSage,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    gap: Spacing.xs,
  },
  option: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: Radius.full,
  },
  activeOption: {
    backgroundColor: Colors.secondaryEmerald,
  },
  optionText: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
  },
  activeText: {
    color: Colors.white,
  },
  divider: {
    width: 1,
    height: 12,
    backgroundColor: Colors.border,
  },
  compact: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: Radius.full,
    backgroundColor: Colors.backgroundSage,
  },
  compactText: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.labelSm,
    color: Colors.primaryForest,
  },
});
