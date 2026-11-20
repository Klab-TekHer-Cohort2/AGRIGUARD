import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { View, ActivityIndicator } from 'react-native';
import {
  useFonts,
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
  Inter_700Bold,
} from '@expo-google-fonts/inter';
import * as SplashScreen from 'expo-splash-screen';
import { useAuthStore } from '../src/store/authStore';
import { Colors } from '../src/theme';
import { DemoBanner } from '../src/components/common/DemoBanner';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const { hydrate, isHydrated } = useAuthStore();

  const [fontsLoaded] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
  });

  useEffect(() => {
    hydrate();
  }, []);

  useEffect(() => {
    if (isHydrated && fontsLoaded) {
      SplashScreen.hideAsync();
    }
  }, [isHydrated, fontsLoaded]);

  if (!isHydrated || !fontsLoaded) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: Colors.primaryForest }}>
        <ActivityIndicator color={Colors.limeAccent} size="large" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" backgroundColor={Colors.backgroundWarm} />
      <DemoBanner />
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(farmer)" />
      </Stack>
    </SafeAreaProvider>
  );
}
