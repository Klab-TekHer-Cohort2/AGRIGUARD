/**
 * Screen: USSD Simulator (Basic / Feature Phone Access)
 *
 * Demonstrates how smallholder farmers without smartphones or internet
 * access AgriGuard using the Africa's Talking CON/END USSD protocol (*922#).
 *
 * Provides a tactile feature-phone interface with interactive keypad,
 * live session timeouts, bilingual support (Kinyarwanda & English),
 * and end-to-end report creation.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import {
  Phone,
  RotateCcw,
  Delete,
  ArrowLeft,
  CheckCircle,
  Radio,
  Clock,
  Shield,
  Smartphone,
  Info,
} from 'lucide-react-native';
import { Colors, FontFamily, FontSize, Spacing, Radius } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDemoStore } from '../../src/demo/demoStore';

const USSD_CODE = '*922#';
const SESSION_TIMEOUT_SEC = 90;

interface MenuNode {
  title: string;
  isEnd?: boolean;
  content: string[];
}

export default function UssdScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const isDemoMode = useDemoStore((s) => s.isDemoMode);

  // Phone simulation state
  const [dialCode, setDialCode] = useState(USSD_CODE);
  const [sessionActive, setSessionActive] = useState(false);
  const [inputBuffer, setInputBuffer] = useState('');
  const [language, setLanguage] = useState<'rw' | 'en'>('rw');
  const [step, setStep] = useState<string>('lang');
  const [historyTrail, setHistoryTrail] = useState<string[]>([]);
  const [timeLeft, setTimeLeft] = useState(SESSION_TIMEOUT_SEC);
  const [generatedRef, setGeneratedRef] = useState<string>('');

  // Report state collected via USSD
  const [reportData, setReportData] = useState({
    crop: '',
    problem: '',
    severity: '',
  });

  // Session countdown timer
  useEffect(() => {
    if (!sessionActive) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          setSessionActive(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [sessionActive]);

  // Start USSD Session
  const handleDial = () => {
    if (dialCode.trim() !== USSD_CODE && dialCode.trim() !== '*XXX#') {
      alert(`Invalid service code. Use ${USSD_CODE}`);
      return;
    }
    setSessionActive(true);
    setStep('lang');
    setInputBuffer('');
    setHistoryTrail([]);
    setTimeLeft(SESSION_TIMEOUT_SEC);
  };

  // Reset Session
  const handleReset = () => {
    setSessionActive(false);
    setStep('lang');
    setInputBuffer('');
    setHistoryTrail([]);
    setTimeLeft(SESSION_TIMEOUT_SEC);
  };

  // Keypad press handler
  const handleKeyPress = (key: string) => {
    if (!sessionActive) {
      if (dialCode.length < 10) setDialCode((prev) => prev + key);
      return;
    }
    setInputBuffer((prev) => prev + key);
  };

  const handleDelete = () => {
    if (!sessionActive) {
      setDialCode((prev) => prev.slice(0, -1));
      return;
    }
    setInputBuffer((prev) => prev.slice(0, -1));
  };

  // Send action (Advance menu)
  const handleSend = () => {
    const input = inputBuffer.trim();
    setInputBuffer('');

    if (step === 'lang') {
      if (input === '1') {
        setLanguage('rw');
        setStep('main');
        setHistoryTrail((prev) => [...prev, 'Ururimi: Ikinyarwanda']);
      } else if (input === '2') {
        setLanguage('en');
        setStep('main');
        setHistoryTrail((prev) => [...prev, 'Language: English']);
      }
      return;
    }

    if (step === 'main') {
      switch (input) {
        case '1':
          setStep('rep_crop');
          break;
        case '2':
          setStep('alerts');
          break;
        case '3':
          setStep('advice');
          break;
        case '4':
          setStep('status');
          break;
        case '5':
          setStep('support');
          break;
        case '0':
          setStep('exit');
          break;
        default:
          break;
      }
      return;
    }

    // Report Flow: Select Crop
    if (step === 'rep_crop') {
      const cropsRw = ['Ibigori (Maize)', 'Ibishyimbo (Beans)', 'Imyumbati (Cassava)', 'Ibirayi (Potato)', 'Inyanya (Tomato)'];
      const idx = parseInt(input, 10) - 1;
      if (idx >= 0 && idx < cropsRw.length) {
        setReportData((prev) => ({ ...prev, crop: cropsRw[idx] }));
        setStep('rep_symptom');
      }
      return;
    }

    // Report Flow: Select Symptom
    if (step === 'rep_symptom') {
      const symptomsRw = ['Umuhondo ku bibabi', 'Utwobo mu bibabi (Inkongwa)', 'Ibibabi buma (Kuraba)', 'Ibyonnyi biboneka'];
      const idx = parseInt(input, 10) - 1;
      if (idx >= 0 && idx < symptomsRw.length) {
        setReportData((prev) => ({ ...prev, problem: symptomsRw[idx] }));
        setStep('rep_severity');
      }
      return;
    }

    // Report Flow: Select Severity
    if (step === 'rep_severity') {
      const severities = ['Gike (Low)', 'Hagati (Medium)', 'Kinini (High/Critical)'];
      const idx = parseInt(input, 10) - 1;
      if (idx >= 0 && idx < severities.length) {
        const ref = `AG-${Math.floor(1000 + Math.random() * 9000)}`;
        setGeneratedRef(ref);
        setReportData((prev) => ({ ...prev, severity: severities[idx] }));
        setStep('rep_confirm');
      }
      return;
    }

    // Report Flow: Confirm
    if (step === 'rep_confirm') {
      if (input === '1') {
        setStep('rep_done');
      } else {
        setStep('main');
      }
      return;
    }

    // Status Check
    if (step === 'status') {
      setStep('status_result');
      return;
    }

    // Back to main on any input from terminal views
    if (['alerts', 'advice', 'rep_done', 'status_result', 'support', 'exit'].includes(step)) {
      setStep('main');
    }
  };

  // Render current screen LCD content
  const renderLcdContent = () => {
    if (!sessionActive) {
      return (
        <View style={styles.idleLcd}>
          <Text style={styles.lcdHeader}>MTN RWANDA / AIRTEL</Text>
          <Text style={styles.lcdTime}>22:45</Text>
          <View style={styles.dialDisplay}>
            <Text style={styles.dialText}>{dialCode || 'Enter *922#'}</Text>
          </View>
          <Text style={styles.lcdSubtext}>Press DIAL or SEND to connect</Text>
        </View>
      );
    }

    // Step 1: Language selection
    if (step === 'lang') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>AgriGuard Rwanda (*922#)</Text>
          <Text style={styles.lcdBody}>Hitamo ururimi / Choose language:</Text>
          <Text style={styles.lcdOption}>1. Ikinyarwanda</Text>
          <Text style={styles.lcdOption}>2. English</Text>
        </View>
      );
    }

    // Step 2: Main Menu
    if (step === 'main') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'AgriGuard Ubuhinzi' : 'AgriGuard Menu'}</Text>
          {language === 'rw' ? (
            <>
              <Text style={styles.lcdOption}>1. Tanga raporo y'ikibazo</Text>
              <Text style={styles.lcdOption}>2. Amakuru y'indwara (Alerts)</Text>
              <Text style={styles.lcdOption}>3. Inama z'ubuhinzi</Text>
              <Text style={styles.lcdOption}>4. Reba uko raporo imeze</Text>
              <Text style={styles.lcdOption}>5. Ubufasha bw'umuhanga</Text>
              <Text style={styles.lcdOption}>0. Sohoka</Text>
            </>
          ) : (
            <>
              <Text style={styles.lcdOption}>1. Report a crop problem</Text>
              <Text style={styles.lcdOption}>2. Community pest alerts</Text>
              <Text style={styles.lcdOption}>3. Farming advice & tips</Text>
              <Text style={styles.lcdOption}>4. Check report status</Text>
              <Text style={styles.lcdOption}>5. Request agronomist help</Text>
              <Text style={styles.lcdOption}>0. Exit</Text>
            </>
          )}
        </View>
      );
    }

    // Step: Report Crop
    if (step === 'rep_crop') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Hitamo igihingwa:' : 'Select your crop:'}</Text>
          <Text style={styles.lcdOption}>1. Ibigori (Maize)</Text>
          <Text style={styles.lcdOption}>2. Ibishyimbo (Beans)</Text>
          <Text style={styles.lcdOption}>3. Imyumbati (Cassava)</Text>
          <Text style={styles.lcdOption}>4. Ibirayi (Potato)</Text>
          <Text style={styles.lcdOption}>5. Inyanya (Tomato)</Text>
        </View>
      );
    }

    // Step: Report Symptom
    if (step === 'rep_symptom') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Ibimenyetso ubona:' : 'Select symptoms:'}</Text>
          <Text style={styles.lcdOption}>1. Umuhondo ku bibabi</Text>
          <Text style={styles.lcdOption}>2. Utwobo mu bibabi (Inkongwa)</Text>
          <Text style={styles.lcdOption}>3. Ibimera biraraba</Text>
          <Text style={styles.lcdOption}>4. Ibyonnyi biragaragara</Text>
        </View>
      );
    }

    // Step: Report Severity
    if (step === 'rep_severity') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Uburemere bw\'ikibazo:' : 'Select severity:'}</Text>
          <Text style={styles.lcdOption}>1. Gike (Low)</Text>
          <Text style={styles.lcdOption}>2. Hagati (Medium)</Text>
          <Text style={styles.lcdOption}>3. Kinini cyane (Critical)</Text>
        </View>
      );
    }

    // Step: Confirm
    if (step === 'rep_confirm') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Emeza kohereza:' : 'Confirm submission:'}</Text>
          <Text style={styles.lcdBody}>Igihingwa: {reportData.crop}</Text>
          <Text style={styles.lcdBody}>Ikibazo: {reportData.problem}</Text>
          <Text style={styles.lcdOption}>1. Yego, Ohereza (Submit)</Text>
          <Text style={styles.lcdOption}>2. Hagarika (Cancel)</Text>
        </View>
      );
    }

    // Step: Report Done
    if (step === 'rep_done') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitleSuccess}>
            {language === 'rw' ? 'Raporo Yakiriwe!' : 'Report Submitted!'}
          </Text>
          <Text style={styles.lcdBody}>
            {language === 'rw'
              ? `Nimero: ${generatedRef}\nImpuguke mu buhinzi iri buyisuzume. AI irimo kubyitegereza.`
              : `Ref: ${generatedRef}\nAI analysis in progress. An agronomist will review.`}
          </Text>
          <Text style={styles.lcdOption}>0. Subira ku ntangiriro</Text>
        </View>
      );
    }

    // Step: Alerts
    if (step === 'alerts') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Amatangazo y\'Ibyorezo:' : 'Outbreak Alerts:'}</Text>
          <Text style={styles.lcdBody}>
            {language === 'rw'
              ? 'âš  GATSIBO (Kabarore):\nInkongwa y\'ibigori (Fall Armyworm) yagaragaye. Uburemere: KININI.\nInama: Suzuma ibigori buri gitondo.'
              : 'âš  GATSIBO (Kabarore):\nFall Armyworm outbreak confirmed on Maize. Severity: HIGH.\nAction: Inspect whorls immediately.'}
          </Text>
          <Text style={styles.lcdOption}>0. Subira inyuma (Back)</Text>
        </View>
      );
    }

    // Step: Advice
    if (step === 'advice') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Inama z\'Ubuhinzi:' : 'Farming Advice:'}</Text>
          <Text style={styles.lcdBody}>
            {language === 'rw'
              ? 'Ibigori: Teza kare ku gihe cy\'imvura. Fata ifumbire y\'imborera, urinde ibyonnyi ukoresheje imitego y\'isazi.'
              : 'Maize: Plant early at the onset of rain. Apply compost and use pheromone traps for Fall Armyworm.'}
          </Text>
          <Text style={styles.lcdOption}>0. Subira inyuma (Back)</Text>
        </View>
      );
    }

    // Step: Status
    if (step === 'status') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Reba Raporo Yawe:' : 'Check Report Status:'}</Text>
          <Text style={styles.lcdBody}>
            {language === 'rw' ? 'Andika nimero ya raporo (urugero: 2026):' : 'Enter report code (e.g., 2026):'}
          </Text>
        </View>
      );
    }

    // Step: Status Result
    if (step === 'status_result') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Uko Raporo Imeze:' : 'Report Status:'}</Text>
          <Text style={styles.lcdBody}>
            {language === 'rw'
              ? 'Raporo AG-2026-001:\nImiterere: BYEMEWE (Verified)\nIkibazo: Fall Armyworm\nInama: Umuhanga Jean Pierre Mugabo yatanze ubufasha.'
              : 'Report AG-2026-001:\nStatus: VERIFIED\nPest: Fall Armyworm\nNote: Extension officer dispatched guidance.'}
          </Text>
          <Text style={styles.lcdOption}>0. Subira inyuma (Back)</Text>
        </View>
      );
    }

    // Step: Support
    if (step === 'support') {
      return (
        <View style={styles.activeLcd}>
          <Text style={styles.lcdTitle}>{language === 'rw' ? 'Ubufasha bw\'Umuhanga:' : 'Agronomist Request:'}</Text>
          <Text style={styles.lcdBody}>
            {language === 'rw'
              ? 'Gusaba gusurwa n\'umuhanga byoherejwe kuri RAB/AgriGuard extension officer w\'umurenge wa Kabarore.'
              : 'Your field visit request has been logged for the Kabarore sector extension officer.'}
          </Text>
          <Text style={styles.lcdOption}>0. Subira inyuma (Back)</Text>
        </View>
      );
    }

    // Exit
    return (
      <View style={styles.activeLcd}>
        <Text style={styles.lcdTitle}>{language === 'rw' ? 'AgriGuard Murakoze!' : 'AgriGuard Goodbye!'}</Text>
        <Text style={styles.lcdBody}>
          {language === 'rw' ? 'Urakoze gukoresha serivisi y\'ubuhinzi. Kanda RESET ngo utangire nanone.' : 'Thank you for using AgriGuard. Press RESET to restart.'}
        </Text>
      </View>
    );
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={[styles.content, { paddingTop: insets.top + 12, paddingBottom: insets.bottom + 40 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Top Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn} accessibilityRole="button">
          <ArrowLeft size={20} color={Colors.primaryForest} />
        </TouchableOpacity>
        <View style={styles.headerTitleWrap}>
          <Text style={styles.headerTitle}>USSD Simulator</Text>
          <Text style={styles.headerSubtitle}>Basic Phone (*922#) â€” Africa's Talking</Text>
        </View>
        <View style={styles.badgeWrap}>
          <Text style={styles.demoBadgeText}>DEMO</Text>
        </View>
      </View>

      {/* Simulator Explainer Banner */}
      <View style={styles.infoBanner}>
        <Info size={16} color={Colors.primaryForest} />
        <Text style={styles.infoBannerText}>
          In Rwanda, 68%+ of smallholder farmers use basic feature phones without 4G or internet. AgriGuard works over USSD so any farmer can report crop pests in Kinyarwanda.
        </Text>
      </View>

      {/* Retro Phone Frame */}
      <View style={styles.phoneOuter}>
        {/* Speaker slot */}
        <View style={styles.phoneSpeaker} />

        {/* LCD Screen Display */}
        <View style={styles.lcdScreen}>
          {sessionActive && (
            <View style={styles.lcdTopBar}>
              <View style={styles.lcdIndicator}>
                <Radio size={12} color="#005511" />
                <Text style={styles.lcdIndicatorText}>CON</Text>
              </View>
              <View style={styles.lcdIndicator}>
                <Clock size={12} color="#005511" />
                <Text style={styles.lcdIndicatorText}>{timeLeft}s</Text>
              </View>
            </View>
          )}

          {/* Main LCD screen content */}
          <View style={styles.lcdMainContent}>
            {renderLcdContent()}
          </View>

          {/* Input buffer display */}
          {sessionActive && (
            <View style={styles.lcdInputRow}>
              <Text style={styles.lcdInputLabel}>Response:</Text>
              <Text style={styles.lcdInputText}>{inputBuffer}_</Text>
            </View>
          )}
        </View>

        {/* Action / Control Buttons */}
        <View style={styles.controlRow}>
          <TouchableOpacity
            style={[styles.dialActionBtn, styles.greenBtn]}
            onPress={sessionActive ? handleSend : handleDial}
            accessibilityRole="button"
          >
            <Phone size={16} color={Colors.white} />
            <Text style={styles.actionBtnText}>{sessionActive ? 'SEND' : 'DIAL'}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.dialActionBtn, styles.grayBtn]}
            onPress={handleDelete}
            accessibilityRole="button"
          >
            <Delete size={16} color={Colors.charcoal} />
            <Text style={[styles.actionBtnText, { color: Colors.charcoal }]}>CLEAR</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.dialActionBtn, styles.redBtn]}
            onPress={handleReset}
            accessibilityRole="button"
          >
            <RotateCcw size={16} color={Colors.white} />
            <Text style={styles.actionBtnText}>RESET</Text>
          </TouchableOpacity>
        </View>

        {/* Numeric Keypad Grid */}
        <View style={styles.keypadGrid}>
          {[
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['*', '0', '#'],
          ].map((row, rIdx) => (
            <View key={rIdx} style={styles.keypadRow}>
              {row.map((key) => (
                <TouchableOpacity
                  key={key}
                  style={styles.keypadKey}
                  onPress={() => handleKeyPress(key)}
                  activeOpacity={0.7}
                  accessibilityRole="button"
                >
                  <Text style={styles.keyText}>{key}</Text>
                </TouchableOpacity>
              ))}
            </View>
          ))}
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
    backgroundColor: Colors.severityMediumBg,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.severityMedium,
  },
  demoBadgeText: {
    fontSize: 10,
    fontFamily: FontFamily.bold,
    color: '#92400E',
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
    maxWidth: 420,
    gap: 8,
  },
  infoBannerText: {
    flex: 1,
    fontSize: FontSize.caption,
    fontFamily: FontFamily.regular,
    color: Colors.charcoal,
    lineHeight: 18,
  },
  phoneOuter: {
    width: '100%',
    maxWidth: 380,
    backgroundColor: '#263329',
    borderRadius: 36,
    padding: 20,
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#18241B',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 8,
  },
  phoneSpeaker: {
    width: 60,
    height: 6,
    backgroundColor: '#17251B',
    borderRadius: Radius.full,
    marginBottom: 16,
  },
  lcdScreen: {
    width: '100%',
    backgroundColor: '#95AF88',
    borderRadius: Radius.lg,
    padding: 12,
    borderWidth: 3,
    borderColor: '#68825D',
    minHeight: 220,
    justifyContent: 'space-between',
  },
  lcdTopBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#78936D',
    paddingBottom: 4,
    marginBottom: 8,
  },
  lcdIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  lcdIndicatorText: {
    fontSize: 11,
    fontFamily: FontFamily.bold,
    color: '#123315',
  },
  lcdMainContent: {
    flex: 1,
    justifyContent: 'center',
  },
  idleLcd: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  lcdHeader: {
    fontSize: 11,
    fontFamily: FontFamily.semiBold,
    color: '#284725',
    letterSpacing: 1,
  },
  lcdTime: {
    fontSize: 26,
    fontFamily: FontFamily.bold,
    color: '#123315',
    marginVertical: 4,
  },
  dialDisplay: {
    backgroundColor: '#A8C29C',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: '#78936D',
    marginVertical: 6,
  },
  dialText: {
    fontSize: 18,
    fontFamily: FontFamily.bold,
    color: '#0F2B12',
    letterSpacing: 2,
  },
  lcdSubtext: {
    fontSize: 11,
    fontFamily: FontFamily.regular,
    color: '#284725',
    marginTop: 4,
  },
  activeLcd: {
    paddingVertical: 4,
  },
  lcdTitle: {
    fontSize: 13,
    fontFamily: FontFamily.bold,
    color: '#0F2B12',
    borderBottomWidth: 1,
    borderBottomColor: '#78936D',
    paddingBottom: 4,
    marginBottom: 6,
  },
  lcdTitleSuccess: {
    fontSize: 14,
    fontFamily: FontFamily.bold,
    color: '#093B12',
    marginBottom: 6,
  },
  lcdBody: {
    fontSize: 12,
    fontFamily: FontFamily.medium,
    color: '#173618',
    marginBottom: 6,
    lineHeight: 16,
  },
  lcdOption: {
    fontSize: 12,
    fontFamily: FontFamily.semiBold,
    color: '#0F2B12',
    lineHeight: 18,
  },
  lcdInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#78936D',
    paddingTop: 6,
    marginTop: 6,
  },
  lcdInputLabel: {
    fontSize: 12,
    fontFamily: FontFamily.semiBold,
    color: '#123315',
    marginRight: 6,
  },
  lcdInputText: {
    fontSize: 14,
    fontFamily: FontFamily.bold,
    color: '#09260C',
  },
  controlRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginVertical: 14,
    gap: 8,
  },
  dialActionBtn: {
    flex: 1,
    flexDirection: 'row',
    height: 38,
    borderRadius: Radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  greenBtn: {
    backgroundColor: Colors.secondaryEmerald,
  },
  grayBtn: {
    backgroundColor: '#BAC8B8',
  },
  redBtn: {
    backgroundColor: '#C53030',
  },
  actionBtnText: {
    color: Colors.white,
    fontFamily: FontFamily.bold,
    fontSize: 11,
  },
  keypadGrid: {
    width: '100%',
    gap: 8,
  },
  keypadRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  keypadKey: {
    flex: 1,
    height: 44,
    backgroundColor: '#354739',
    borderRadius: Radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomWidth: 3,
    borderBottomColor: '#1F2C22',
  },
  keyText: {
    color: Colors.white,
    fontFamily: FontFamily.bold,
    fontSize: 18,
  },
});
