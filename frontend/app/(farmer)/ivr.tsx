/**
 * Screen: IVR Voice Assistant Simulator
 *
 * Demonstrates toll-free interactive voice response (IVR) for farmers
 * with low literacy or visual impairments. Provides spoken audio guidance,
 * touch-tone DTMF navigation (1-5), and a conversational voice assistant.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import {
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  Mic,
  ArrowLeft,
  Bot,
  User,
  Radio,
  Clock,
  Sparkles,
  Info,
  HelpCircle,
} from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDemoStore } from '../../src/demo/demoStore';

interface DialogueLine {
  id: string;
  sender: 'system' | 'caller';
  text: string;
  timestamp: string;
}

export default function IvrScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const isDemoMode = useDemoStore((s) => s.isDemoMode);

  // Call simulation state
  const [callActive, setCallActive] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [speakerOn, setSpeakerOn] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [language, setLanguage] = useState<'rw' | 'en'>('rw');
  const [activeStep, setActiveStep] = useState<string>('intro');
  const [dialogue, setDialogue] = useState<DialogueLine[]>([]);
  const [showKeypad, setShowKeypad] = useState(true);

  const scrollRef = useRef<ScrollView>(null);

  // Call duration timer
  useEffect(() => {
    if (!callActive) return;
    const interval = setInterval(() => {
      setCallDuration((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [callActive]);

  // Format call duration MM:SS
  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  // Browser speech synthesis handler
  const speakText = (text: string, lang: 'rw' | 'en') => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window && speakerOn) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      // Fallback voice selection
      utterance.lang = lang === 'rw' ? 'sw-TZ' : 'en-US'; // sw-TZ / en-US sounds natural
      utterance.rate = 0.95;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setIsSpeaking(true);
      setTimeout(() => setIsSpeaking(false), 2500);
    }
  };

  // Add line to dialogue
  const appendDialogue = (sender: 'system' | 'caller', text: string) => {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setDialogue((prev) => [...prev, { id: `${Date.now()}-${Math.random()}`, sender, text, timestamp: timeStr }]);
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 150);
  };

  // Start Call
  const handleStartCall = () => {
    setIsCalling(true);
    setDialogue([]);
    setCallDuration(0);

    setTimeout(() => {
      setIsCalling(false);
      setCallActive(true);
      setActiveStep('intro');

      const welcomeMsg = language === 'rw'
        ? "Murakaza neza kuri AgriGuard Rwanda, umurongo utishyurwa w'ubuhinzi. Kanda 1 gutanga raporo y'icyonnyi, Kanda 2 kumva amakuru y'indwara mu gace kawe, Kanda 3 kumva inama z'ubuhinzi, Kanda 4 kureba uko raporo yawe imeze, cyangwa Kanda 5 kuvugana n'umufasha wa AI."
        : "Welcome to AgriGuard Rwanda toll-free agricultural voice line. Press 1 to report a crop pest, Press 2 to listen to community outbreak alerts, Press 3 for crop guidance, Press 4 to check report status, or Press 5 to talk to AgriGuard AI assistant.";

      appendDialogue('system', welcomeMsg);
      speakText(welcomeMsg, language);
    }, 1200);
  };

  // Hang Up Call
  const handleEndCall = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setCallActive(false);
    setIsCalling(false);
    setIsSpeaking(false);
    appendDialogue('system', language === 'rw' ? 'Ihamagara ryasojwe. Murakoze.' : 'Call ended. Thank you for calling AgriGuard.');
  };

  // Keypad DTMF option selected
  const handleDtmfInput = (digit: string) => {
    if (!callActive) return;

    if (digit === '1') {
      appendDialogue('caller', language === 'rw' ? "Kanda 1: Tanga raporo y'icyonnyi" : "Pressed 1: Report a crop problem");
      const resp = language === 'rw'
        ? "Guhitamo igihingwa: Kanda 1 ku bigori, Kanda 2 ku bishyimbo, Kanda 3 ku birayi, cyangwa vuga ibimenyetso ubona nyuma y'ijwi ry'akamenyetso."
        : "Crop selection: Press 1 for Maize, Press 2 for Beans, Press 3 for Irish Potato, or speak symptoms after the tone.";
      appendDialogue('system', resp);
      speakText(resp, language);
      return;
    }

    if (digit === '2') {
      appendDialogue('caller', language === 'rw' ? "Kanda 2: Amakuru y'indwara" : "Pressed 2: Community alerts");
      const resp = language === 'rw'
        ? "Icyitonderwa muri Gatsibo, Umurenge wa Kabarore: Inkongwa y'ibigori (Fall Armyworm) yabonetse mu mirima 14. Uburemere ni KININI. Abahinzi basabwe gusuzuma ibigori bito."
        : "Warning in Gatsibo District, Kabarore sector: Fall Armyworm outbreak identified across 14 farms. Severity is HIGH. All farmers are advised to inspect whorls of young maize plants.";
      appendDialogue('system', resp);
      speakText(resp, language);
      return;
    }

    if (digit === '3') {
      appendDialogue('caller', language === 'rw' ? "Kanda 3: Inama z'ubuhinzi" : "Pressed 3: Farming guidance");
      const resp = language === 'rw'
        ? "Inama yo kurinda ibigori: Teza kare ku gihe cy'imvura. Fata ifumbire y'imborera iboze neza, kandi ukurikirane amababi abiri buri cyumweru."
        : "Maize protection tip: Plant early at onset of rains. Use well-decomposed organic compost and scout young fields twice a week for pest egg masses.";
      appendDialogue('system', resp);
      speakText(resp, language);
      return;
    }

    if (digit === '4') {
      appendDialogue('caller', language === 'rw' ? "Kanda 4: Reba raporo" : "Pressed 4: Check report status");
      const resp = language === 'rw'
        ? "Raporo yawe yaherutse AG-2026-001 i Kabarore yemejwe n'umuhanga Jean Pierre Mugabo. Ikibazo cyari Inkongwa, imiti yemewe yatanzwe muri koperative."
        : "Your recent report AG-2026-001 in Kabarore was reviewed and verified by agronomist Jean Pierre Mugabo. Identified as Fall Armyworm. Organic neem spray recommended.";
      appendDialogue('system', resp);
      speakText(resp, language);
      return;
    }

    if (digit === '5') {
      appendDialogue('caller', language === 'rw' ? "Kanda 5: Umufasha wa AI" : "Pressed 5: Ask AgriGuard AI");
      const resp = language === 'rw'
        ? "Ubu uri kuvugana n'umufasha wa AgriGuard. Urugero: Nonese nabigenza nte niba ibigori byanjye bifite utwobo mu bibabi? AI igusubiza ako kanya."
        : "You are now connected to the AgriGuard AI Voice Assistant. You may ask any question, such as: What is the recommended treatment for Maize Fall Armyworm?";
      appendDialogue('system', resp);
      speakText(resp, language);
      return;
    }

    // Default
    const defaultResp = language === 'rw'
      ? `Wakanze ${digit}. Hitamo hagati ya 1 na 5 kugira ngo ukomeze.`
      : `You pressed ${digit}. Please select an option between 1 and 5.`;
    appendDialogue('system', defaultResp);
    speakText(defaultResp, language);
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={[styles.content, { paddingTop: insets.top + 12, paddingBottom: insets.bottom + 40 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn} accessibilityRole="button">
          <ArrowLeft size={20} color={Colors.primaryForest} />
        </TouchableOpacity>
        <View style={styles.headerTitleWrap}>
          <Text style={styles.headerTitle}>IVR Voice Assistant</Text>
          <Text style={styles.headerSubtitle}>Toll-Free Call Line: 0800-AGRI-GUARD</Text>
        </View>
        <View style={styles.badgeWrap}>
          <Text style={styles.demoBadgeText}>VOICE DEMO</Text>
        </View>
      </View>

      {/* Explainer Banner */}
      <View style={styles.infoBanner}>
        <Info size={16} color={Colors.primaryForest} />
        <Text style={styles.infoBannerText}>
          The IVR channel empowers smallholder farmers with limited reading literacy to call and receive spoken guidance in Kinyarwanda with simple keypad choices.
        </Text>
      </View>

      {/* Virtual Call Console */}
      <View style={styles.callCard}>
        {/* Call Status Bar */}
        <LinearGradient
          colors={[Colors.primaryForest, '#134D2C']}
          style={styles.callHeader}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.callStatusRow}>
            <View style={styles.onlinePill}>
              <View style={[styles.statusDot, { backgroundColor: callActive ? '#4ADE80' : isCalling ? '#FACC15' : '#94A3B8' }]} />
              <Text style={styles.statusText}>
                {callActive ? 'CONNECTED' : isCalling ? 'DIALING...' : 'STANDBY'}
              </Text>
            </View>
            {callActive && (
              <View style={styles.timerPill}>
                <Clock size={12} color={Colors.limeAccent} />
                <Text style={styles.timerText}>{formatDuration(callDuration)}</Text>
              </View>
            )}
          </View>

          <View style={styles.callerInfo}>
            <Text style={styles.callerNumber}>0800 2474 (AgriGuard Free Voice)</Text>
            <Text style={styles.callerSub}>RAB Crop Surveillance Network</Text>
          </View>

          {/* Speaking Wave Animation Indicator */}
          {isSpeaking && (
            <View style={styles.speakingWave}>
              <Volume2 size={16} color={Colors.limeAccent} />
              <Text style={styles.speakingText}>
                {language === 'rw' ? 'Ijwi riravuga...' : 'Audio playing...'}
              </Text>
            </View>
          )}
        </LinearGradient>

        {/* Live Conversation Transcript */}
        <View style={styles.transcriptWrap}>
          <View style={styles.transcriptHeader}>
            <Text style={styles.transcriptTitle}>Call Audio & Transcript</Text>
            <View style={styles.langToggle}>
              <TouchableOpacity
                onPress={() => setLanguage('rw')}
                style={[styles.langBtn, language === 'rw' && styles.langBtnActive]}
              >
                <Text style={[styles.langBtnText, language === 'rw' && styles.langBtnTextActive]}>RW</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setLanguage('en')}
                style={[styles.langBtn, language === 'en' && styles.langBtnActive]}
              >
                <Text style={[styles.langBtnText, language === 'en' && styles.langBtnTextActive]}>EN</Text>
              </TouchableOpacity>
            </View>
          </View>

          <ScrollView
            ref={scrollRef}
            style={styles.transcriptScroll}
            contentContainerStyle={styles.transcriptList}
            nestedScrollEnabled
          >
            {dialogue.length === 0 ? (
              <View style={styles.emptyCall}>
                <Phone size={32} color={Colors.charcoalLight} />
                <Text style={styles.emptyCallText}>
                  Press the green CALL button below to simulate an incoming toll-free IVR phone call.
                </Text>
              </View>
            ) : (
              dialogue.map((line) => (
                <View
                  key={line.id}
                  style={[
                    styles.dialogueBubble,
                    line.sender === 'system' ? styles.bubbleSystem : styles.bubbleCaller,
                  ]}
                >
                  <View style={styles.bubbleHeader}>
                    {line.sender === 'system' ? (
                      <Bot size={14} color={Colors.secondaryEmerald} />
                    ) : (
                      <User size={14} color={Colors.charcoalMuted} />
                    )}
                    <Text style={styles.senderLabel}>
                      {line.sender === 'system' ? 'AgriGuard Voice System' : 'Farmer Keypad'}
                    </Text>
                    <Text style={styles.timestampLabel}>{line.timestamp}</Text>
                  </View>
                  <Text style={styles.bubbleText}>{line.text}</Text>
                </View>
              ))
            )}
          </ScrollView>
        </View>

        {/* Keypad Menu Choices (1 to 5) */}
        {callActive && (
          <View style={styles.dtmfMenu}>
            <Text style={styles.dtmfTitle}>Voice Menu Touchtone (DTMF) Keys:</Text>
            <View style={styles.dtmfGrid}>
              {[
                { key: '1', label: language === 'rw' ? '1. Tanga Raporo' : '1. Report Problem' },
                { key: '2', label: language === 'rw' ? "2. Amakuru y'Indwara" : '2. Outbreak Alerts' },
                { key: '3', label: language === 'rw' ? "3. Inama z'Ubuhinzi" : '3. Farming Advice' },
                { key: '4', label: language === 'rw' ? '4. Reba Raporo' : '4. Check Status' },
                { key: '5', label: language === 'rw' ? '5. Umufasha wa AI' : '5. Ask AI Assistant' },
              ].map((opt) => (
                <TouchableOpacity
                  key={opt.key}
                  style={styles.dtmfBtn}
                  onPress={() => handleDtmfInput(opt.key)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.dtmfKey}>{opt.key}</Text>
                  <Text style={styles.dtmfLabel}>{opt.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Call Action Bar (Call / Hangup / Speaker) */}
        <View style={styles.callActionBar}>
          <TouchableOpacity
            style={[styles.circleBtn, speakerOn ? styles.speakerActive : styles.speakerInactive]}
            onPress={() => setSpeakerOn(!speakerOn)}
            accessibilityRole="button"
          >
            {speakerOn ? <Volume2 size={20} color={Colors.primaryForest} /> : <VolumeX size={20} color={Colors.charcoalLight} />}
          </TouchableOpacity>

          {!callActive ? (
            <TouchableOpacity
              style={[styles.primaryCallBtn, styles.greenCallBtn]}
              onPress={handleStartCall}
              disabled={isCalling}
              accessibilityRole="button"
            >
              {isCalling ? (
                <ActivityIndicator color={Colors.white} size="small" />
              ) : (
                <>
                  <Phone size={22} color={Colors.white} />
                  <Text style={styles.callBtnText}>CALL 0800</Text>
                </>
              )}
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.primaryCallBtn, styles.redCallBtn]}
              onPress={handleEndCall}
              accessibilityRole="button"
            >
              <PhoneOff size={22} color={Colors.white} />
              <Text style={styles.callBtnText}>HANG UP</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={styles.circleBtn}
            onPress={() => setShowKeypad(!showKeypad)}
            accessibilityRole="button"
          >
            <Mic size={20} color={Colors.primaryForest} />
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.backgroundWarm,
  },
  content: {
    paddingHorizontal: Spacing.md,
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginBottom: Spacing.sm,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: Radius.full,
    backgroundColor: Colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.borderLight,
    marginRight: Spacing.sm,
  },
  headerTitleWrap: {
    flex: 1,
  },
  headerTitle: {
    fontSize: FontSize.h4,
    fontFamily: FontFamily.bold,
    color: Colors.charcoal,
  },
  headerSubtitle: {
    fontSize: FontSize.caption,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalMuted,
  },
  badgeWrap: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: Colors.severityLowBg,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.secondaryEmerald,
  },
  demoBadgeText: {
    fontSize: 10,
    fontFamily: FontFamily.bold,
    color: Colors.primaryForest,
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSage,
    padding: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: Spacing.md,
    width: '100%',
    maxWidth: 520,
    gap: 8,
  },
  infoBannerText: {
    flex: 1,
    fontSize: FontSize.caption,
    fontFamily: FontFamily.regular,
    color: Colors.charcoal,
    lineHeight: 18,
  },
  callCard: {
    width: '100%',
    maxWidth: 520,
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.xl,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: Colors.borderLight,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  callHeader: {
    padding: 16,
  },
  callStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  onlinePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.25)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: Radius.full,
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: Radius.full,
  },
  statusText: {
    color: Colors.white,
    fontSize: 10,
    fontFamily: FontFamily.bold,
    letterSpacing: 1,
  },
  timerPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.25)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: Radius.full,
    gap: 4,
  },
  timerText: {
    color: Colors.limeAccent,
    fontFamily: FontFamily.bold,
    fontSize: 12,
  },
  callerInfo: {
    marginVertical: 12,
    alignItems: 'center',
  },
  callerNumber: {
    color: Colors.white,
    fontSize: 18,
    fontFamily: FontFamily.bold,
    letterSpacing: 0.5,
  },
  callerSub: {
    color: Colors.sageSoft,
    fontSize: 12,
    fontFamily: FontFamily.regular,
    marginTop: 2,
  },
  speakingWave: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.15)',
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: Radius.full,
    alignSelf: 'center',
    gap: 6,
  },
  speakingText: {
    color: Colors.limeAccent,
    fontSize: 11,
    fontFamily: FontFamily.medium,
  },
  transcriptWrap: {
    padding: Spacing.md,
    backgroundColor: Colors.backgroundWarm,
  },
  transcriptHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  transcriptTitle: {
    fontSize: 12,
    fontFamily: FontFamily.bold,
    color: Colors.charcoalMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  langToggle: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  langBtn: {
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  langBtnActive: {
    backgroundColor: Colors.primaryForest,
  },
  langBtnText: {
    fontSize: 10,
    fontFamily: FontFamily.bold,
    color: Colors.charcoalMuted,
  },
  langBtnTextActive: {
    color: Colors.white,
  },
  transcriptScroll: {
    height: 190,
  },
  transcriptList: {
    gap: 8,
    paddingBottom: 8,
  },
  emptyCall: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 160,
    paddingHorizontal: 20,
  },
  emptyCallText: {
    fontSize: 12,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalMuted,
    textAlign: 'center',
    marginTop: 10,
    lineHeight: 18,
  },
  dialogueBubble: {
    padding: 10,
    borderRadius: Radius.md,
    maxWidth: '92%',
  },
  bubbleSystem: {
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    alignSelf: 'flex-start',
  },
  bubbleCaller: {
    backgroundColor: '#E0F2FE',
    borderWidth: 1,
    borderColor: '#BAE6FD',
    alignSelf: 'flex-end',
  },
  bubbleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  senderLabel: {
    fontSize: 10,
    fontFamily: FontFamily.semiBold,
    color: Colors.charcoalMuted,
    flex: 1,
  },
  timestampLabel: {
    fontSize: 9,
    fontFamily: FontFamily.regular,
    color: Colors.charcoalLight,
  },
  bubbleText: {
    fontSize: 12,
    fontFamily: FontFamily.regular,
    color: Colors.charcoal,
    lineHeight: 17,
  },
  dtmfMenu: {
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.sm,
  },
  dtmfTitle: {
    fontSize: 11,
    fontFamily: FontFamily.semiBold,
    color: Colors.charcoalMuted,
    marginBottom: 6,
  },
  dtmfGrid: {
    gap: 6,
  },
  dtmfBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 10,
  },
  dtmfKey: {
    width: 22,
    height: 22,
    borderRadius: Radius.full,
    backgroundColor: Colors.primaryForest,
    color: Colors.white,
    textAlign: 'center',
    lineHeight: 22,
    fontFamily: FontFamily.bold,
    fontSize: 12,
  },
  dtmfLabel: {
    fontSize: 12,
    fontFamily: FontFamily.medium,
    color: Colors.charcoal,
  },
  callActionBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    backgroundColor: Colors.white,
  },
  circleBtn: {
    width: 44,
    height: 44,
    borderRadius: Radius.full,
    backgroundColor: Colors.backgroundWarm,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  speakerActive: {
    backgroundColor: Colors.backgroundSage,
    borderColor: Colors.secondaryEmerald,
  },
  speakerInactive: {
    backgroundColor: Colors.backgroundWarm,
  },
  primaryCallBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    height: 48,
    borderRadius: Radius.full,
    gap: 8,
  },
  greenCallBtn: {
    backgroundColor: Colors.secondaryEmerald,
  },
  redCallBtn: {
    backgroundColor: '#DC2626',
  },
  callBtnText: {
    color: Colors.white,
    fontFamily: FontFamily.bold,
    fontSize: 13,
    letterSpacing: 0.5,
  },
});
