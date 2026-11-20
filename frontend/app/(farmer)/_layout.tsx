import React from 'react';
import { Tabs } from 'expo-router';
import { Home, FileText, MessageCircle, Bell, User, BookOpen } from 'lucide-react-native';
import { Colors, FontFamily, FontSize } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useAuthStore } from '../../src/store/authStore';
import { useDemoStore } from '../../src/demo/demoStore';
import { Redirect } from 'expo-router';

export default function FarmerLayout() {
  const { t } = useTranslation();
  const { token } = useAuthStore();
  const isDemoMode = useDemoStore((s) => s.isDemoMode);

  // Allow navigation if user is authenticated OR in demo mode
  if (!token && !isDemoMode) return <Redirect href="/(auth)/welcome" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: Colors.secondaryEmerald,
        tabBarInactiveTintColor: Colors.charcoalLight,
        tabBarStyle: {
          backgroundColor: Colors.backgroundCard,
          borderTopColor: Colors.borderLight,
          borderTopWidth: 1,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarLabelStyle: {
          fontFamily: FontFamily.medium,
          fontSize: FontSize.labelSm,
        },
      }}
    >
      <Tabs.Screen name="home" options={{ title: t.nav.home, tabBarIcon: ({ color, size }) => <Home size={size} color={color} /> }} />
      <Tabs.Screen name="reports" options={{ title: t.nav.reports, tabBarIcon: ({ color, size }) => <FileText size={size} color={color} /> }} />
      <Tabs.Screen name="ask" options={{ title: t.nav.ask, tabBarIcon: ({ color, size }) => <MessageCircle size={size} color={color} /> }} />
      <Tabs.Screen name="alerts" options={{ title: t.nav.alerts, tabBarIcon: ({ color, size }) => <Bell size={size} color={color} /> }} />
      <Tabs.Screen name="advice" options={{ title: 'Advice', tabBarIcon: ({ color, size }) => <BookOpen size={size} color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: t.nav.profile, tabBarIcon: ({ color, size }) => <User size={size} color={color} /> }} />
      {/* Hidden screens */}
      <Tabs.Screen name="report-new" options={{ href: null }} />
      <Tabs.Screen name="report-detail" options={{ href: null }} />
      <Tabs.Screen name="ussd" options={{ href: null }} />
      <Tabs.Screen name="ivr" options={{ href: null }} />
      <Tabs.Screen name="outbreak-map" options={{ href: null }} />
    </Tabs>
  );
}
