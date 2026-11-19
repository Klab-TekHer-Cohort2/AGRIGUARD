import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { Colors, FontFamily, FontSize } from '../../theme';
import { useTranslation } from '../../hooks/useTranslation';

interface ConfidenceRingProps {
  score: number; // 0–1
  size?: number;
}

export function ConfidenceRing({ score, size = 72 }: ConfidenceRingProps) {
  const { t } = useTranslation();
  const percentage = Math.round(score * 100);
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const filled = circumference * score;
  const strokeDashoffset = circumference - filled;

  const ringColor =
    score >= 0.75 ? Colors.secondaryEmerald :
    score >= 0.5 ? Colors.severityMedium :
    Colors.severityHigh;

  const confidenceLabel =
    score >= 0.75 ? t.aiResult.confidenceHigh :
    score >= 0.5 ? t.aiResult.confidenceMedium :
    t.aiResult.confidenceLow;

  return (
    <View style={styles.wrapper} accessibilityLabel={`Confidence: ${percentage}%`}>
      <Svg width={size} height={size} style={styles.svg}>
        {/* Track */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={Colors.borderLight}
          strokeWidth={6}
          fill="none"
        />
        {/* Fill */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={ringColor}
          strokeWidth={6}
          fill="none"
          strokeDasharray={`${filled} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          rotation={-90}
          originX={size / 2}
          originY={size / 2}
        />
      </Svg>
      <View style={[styles.labelContainer, { width: size, height: size }]}>
        <Text style={[styles.pct, { color: ringColor }]}>{percentage}%</Text>
      </View>
      <Text style={styles.caption} numberOfLines={2}>{confidenceLabel}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
    gap: 4,
  },
  svg: {
  },
  labelContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pct: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
  },
  caption: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    textAlign: 'center',
    maxWidth: 90,
  },
});
