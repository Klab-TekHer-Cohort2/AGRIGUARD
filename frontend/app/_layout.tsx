import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { View, ActivityIndicator } from 'react-native';
import { useAuthStore } from '../src/store/authStore';
import { Colors } from '../src/theme';

export default function RootLayout() {
  const { hydrate, isHydrated } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, []);

  if (!isHydrated) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: Colors.primaryForest }}>
        <ActivityIndicator color={Colors.limeAccent} size="large" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" backgroundColor={Colors.backgroundWarm} />
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(farmer)" />
      </Stack>
    </SafeAreaProvider>
  );
}
