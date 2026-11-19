import { Redirect } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';

/** Root index — redirect based on auth state */
export default function Index() {
  const { token, isHydrated } = useAuthStore();

  if (!isHydrated) return null;

  if (token) {
    return <Redirect href="/(farmer)/home" />;
  }

  return <Redirect href="/(auth)/welcome" />;
}
