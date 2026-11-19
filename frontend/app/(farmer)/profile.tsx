/**
 * Screen 11 — Farmer Profile
 * GET /farmers/profile
 * PUT /farmers/profile
 * GET /auth/me
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  TextInput,
} from 'react-native';
import {
  User,
  Phone,
  Globe,
  MapPin,
  FileText,
  Edit2,
  LogOut,
  CheckCircle,
  X,
  Calendar,
} from 'lucide-react-native';
import { ScreenHeader } from '../../src/components/common/ScreenHeader';
import { Card } from '../../src/components/common/Card';
import { Button } from '../../src/components/common/Button';
import { Input } from '../../src/components/common/Input';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useAuthStore } from '../../src/store/authStore';
import { farmersApi, FarmerProfileResponse } from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';

export default function ProfileScreen() {
  const { t } = useTranslation();
  const { logout, user } = useAuthStore();
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const [profile, setProfile] = useState<FarmerProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const loadProfile = useCallback(async () => {
    try {
      const prof = await farmersApi.getProfile();
      setProfile(prof);
      setEditName(prof.full_name);
      setEditEmail(prof.email ?? '');
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadProfile(); }, [loadProfile]);

  const handleSave = async () => {
    if (!editName.trim()) return;
    setSaving(true);
    try {
      const updated = await farmersApi.updateProfile({
        full_name: editName.trim(),
        email: editEmail.trim() || undefined,
      });
      setProfile(updated);
      setEditing(false);
      setSuccessMsg(t.profile.updateSuccess);
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch {
      // silent — show generic message
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      t.auth.logout,
      t.profile.logoutConfirm,
      [
        { text: t.common.cancel, style: 'cancel' },
        {
          text: t.auth.logout,
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/(auth)/welcome');
          },
        },
      ],
    );
  };

  const prof = profile;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScreenHeader
        title={t.profile.title}
        showLanguage
        rightElement={
          !editing ? (
            <TouchableOpacity
              onPress={() => setEditing(true)}
              style={styles.editBtn}
              accessibilityLabel={t.profile.editProfile}
            >
              <Edit2 size={18} color={Colors.secondaryEmerald} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              onPress={() => { setEditing(false); setEditName(prof?.full_name ?? ''); }}
              style={styles.editBtn}
              accessibilityLabel={t.common.cancel}
            >
              <X size={18} color={Colors.charcoalMuted} />
            </TouchableOpacity>
          )
        }
      />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
      >
        {/* Avatar / name section */}
        <View style={styles.avatarSection}>
          <View style={styles.avatar}>
            <Text style={styles.avatarInitial}>
              {(prof?.full_name ?? user?.full_name ?? 'U').charAt(0).toUpperCase()}
            </Text>
          </View>
          <Text style={styles.nameText}>{prof?.full_name ?? user?.full_name}</Text>
          <Text style={styles.phoneText}>{prof?.phone_number ?? user?.phone_number}</Text>
          <View style={styles.langRow}>
            <LanguageToggle />
          </View>
        </View>

        {/* Success message */}
        {successMsg ? (
          <View style={styles.successBanner}>
            <CheckCircle size={16} color={Colors.secondaryEmerald} />
            <Text style={styles.successText}>{successMsg}</Text>
          </View>
        ) : null}

        <View style={styles.body}>
          {/* Edit form */}
          {editing ? (
            <Card style={styles.section}>
              <Text style={styles.sectionTitle}>{t.profile.editProfile}</Text>
              <Input
                label={t.profile.fullName}
                value={editName}
                onChangeText={setEditName}
                autoCapitalize="words"
              />
              <Input
                label={t.profile.email}
                value={editEmail}
                onChangeText={setEditEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
              <Button
                label={t.common.save}
                onPress={handleSave}
                loading={saving}
                fullWidth
              />
            </Card>
          ) : null}

          {/* Stats */}
          <View style={styles.statsRow}>
            <View style={styles.stat}>
              <FileText size={20} color={Colors.secondaryEmerald} />
              <Text style={styles.statValue}>{prof?.total_reports ?? 0}</Text>
              <Text style={styles.statLabel}>{t.profile.totalReports}</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.stat}>
              <Calendar size={20} color={Colors.secondaryEmerald} />
              <Text style={styles.statValue}>
                {prof?.created_at
                  ? new Date(prof.created_at).toLocaleDateString('en-RW', { month: 'short', year: 'numeric' })
                  : '—'}
              </Text>
              <Text style={styles.statLabel}>{t.profile.memberSince}</Text>
            </View>
          </View>

          {/* Profile info */}
          <Card style={styles.section}>
            <ProfileRow
              icon={<Phone size={16} color={Colors.charcoalMuted} />}
              label={t.profile.phoneNumber}
              value={prof?.phone_number ?? user?.phone_number ?? ''}
            />
            <ProfileRow
              icon={<User size={16} color={Colors.charcoalMuted} />}
              label={t.profile.fullName}
              value={prof?.full_name ?? user?.full_name ?? ''}
            />
            {prof?.email && (
              <ProfileRow
                icon={<Globe size={16} color={Colors.charcoalMuted} />}
                label={t.profile.email}
                value={prof.email}
              />
            )}
            {prof?.cooperative_name && (
              <ProfileRow
                icon={<User size={16} color={Colors.charcoalMuted} />}
                label={t.profile.cooperative}
                value={prof.cooperative_name}
              />
            )}
          </Card>

          {/* Farm locations */}
          {prof?.locations && prof.locations.length > 0 && (
            <Card style={styles.section}>
              <Text style={styles.sectionTitle}>{t.profile.farmLocations}</Text>
              {prof.locations.map((loc) => (
                <View key={loc.id} style={styles.locationRow}>
                  <MapPin size={14} color={Colors.secondaryEmerald} />
                  <Text style={styles.locationText}>
                    {[loc.village, loc.cell, loc.sector, loc.district].filter(Boolean).join(', ')}
                    {loc.is_primary ? ` (${t.profile.primaryLocation})` : ''}
                  </Text>
                </View>
              ))}
            </Card>
          )}

          {/* Logout */}
          <Button
            label={t.auth.logout}
            onPress={handleLogout}
            variant="danger"
            fullWidth
            icon={<LogOut size={18} color={Colors.white} />}
            style={styles.logoutBtn}
          />
        </View>
      </ScrollView>
    </View>
  );
}

function ProfileRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <View style={rowStyles.row}>
      <View style={rowStyles.iconWrap}>{icon}</View>
      <View style={rowStyles.content}>
        <Text style={rowStyles.label}>{label}</Text>
        <Text style={rowStyles.value}>{value}</Text>
      </View>
    </View>
  );
}

const rowStyles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  iconWrap: {
    width: 24,
    alignItems: 'center',
    marginTop: 2,
  },
  content: { flex: 1 },
  label: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    marginBottom: 1,
  },
  value: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.body,
    color: Colors.charcoal,
  },
});

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  avatarSection: {
    alignItems: 'center',
    padding: Spacing.xl,
    gap: Spacing.sm,
    backgroundColor: Colors.backgroundCard,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.primaryForest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: {
    fontFamily: FontFamily.bold,
    fontSize: 32,
    color: Colors.limeAccent,
  },
  nameText: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
  },
  phoneText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
  },
  langRow: { marginTop: Spacing.sm },
  body: { padding: Spacing.base, gap: Spacing.base },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.successBg,
    padding: Spacing.base,
    marginHorizontal: Spacing.base,
    marginTop: Spacing.sm,
    borderRadius: Radius.md,
  },
  successText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.bodySm,
    color: Colors.secondaryEmerald,
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    alignItems: 'center',
  },
  stat: { flex: 1, alignItems: 'center', gap: 3 },
  statDivider: { width: 1, height: 40, backgroundColor: Colors.borderLight },
  statValue: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
  },
  statLabel: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.labelSm,
    color: Colors.charcoalMuted,
    textAlign: 'center',
  },
  section: { padding: Spacing.base },
  sectionTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    marginBottom: Spacing.sm,
  },
  editBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  locationText: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    lineHeight: 22,
  },
  logoutBtn: { marginTop: Spacing.sm },
});
