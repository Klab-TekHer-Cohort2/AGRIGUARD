import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, StatusBar } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowLeft } from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Spacing, Shadow } from '../../theme';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LanguageToggle } from './LanguageToggle';

interface ScreenHeaderProps {
  title: string;
  showBack?: boolean;
  rightElement?: React.ReactNode;
  showLanguage?: boolean;
  transparent?: boolean;
}

export function ScreenHeader({
  title,
  showBack = false,
  rightElement,
  showLanguage = false,
  transparent = false,
}: ScreenHeaderProps) {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  return (
    <View
      style={[
        styles.header,
        { paddingTop: insets.top + 8 },
        !transparent && styles.solidHeader,
      ]}
      accessibilityRole="header"
    >
      <View style={styles.row}>
        <View style={styles.left}>
          {showBack && (
            <TouchableOpacity
              onPress={() => router.back()}
              style={styles.backButton}
              accessibilityLabel="Go back"
              accessibilityRole="button"
            >
              <ArrowLeft size={22} color={transparent ? Colors.white : Colors.charcoal} />
            </TouchableOpacity>
          )}
        </View>

        <Text
          style={[styles.title, transparent && { color: Colors.white }]}
          numberOfLines={1}
        >
          {title}
        </Text>

        <View style={styles.right}>
          {showLanguage && <LanguageToggle compact />}
          {rightElement}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.base,
  },
  solidHeader: {
    backgroundColor: Colors.backgroundWarm,
    ...Shadow.xs,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 44,
  },
  left: {
    width: 44,
    alignItems: 'flex-start',
  },
  right: {
    width: 80,
    alignItems: 'flex-end',
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: Spacing.sm,
  },
  title: {
    flex: 1,
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
    textAlign: 'center',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
