/**
 * Screen 7 — Ask AgriGuard
 * POST /api/ai/ask  (direct to AI service on port 5000)
 * Free-text question → RAG-powered agricultural answer
 */
import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Send, MessageCircle, AlertTriangle } from 'lucide-react-native';
import { ScreenHeader } from '../../src/components/common/ScreenHeader';
import { Card } from '../../src/components/common/Card';
import { Colors, FontFamily, FontSize, Spacing, Radius, Shadow } from '../../src/theme';
import { useTranslation } from '../../src/hooks/useTranslation';
import { aiApi } from '../../src/api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  needsAgronomist?: boolean;
  disclaimer?: string;
  loading?: boolean;
  error?: boolean;
}

export default function AskScreen() {
  const { t, language } = useTranslation();
  const insets = useSafeAreaInsets();
  const flatListRef = useRef<FlatList>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    const q = input.trim();
    if (!q || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: q,
    };
    const loadingMsg: Message = {
      id: `loading-${Date.now()}`,
      role: 'assistant',
      text: '',
      loading: true,
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setInput('');
    setLoading(true);

    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);

    try {
      const resp = await aiApi.ask(q, language as 'en' | 'rw');
      const data = resp.data;
      const assistantMsg: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        text: data.answer,
        needsAgronomist: data.needsAgronomist,
        disclaimer: data.disclaimer,
      };
      setMessages((prev) => prev.filter((m) => !m.loading).concat(assistantMsg));
    } catch {
      const errMsg: Message = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        text: t.ask.errorResponse,
        error: true,
      };
      setMessages((prev) => prev.filter((m) => !m.loading).concat(errMsg));
    } finally {
      setLoading(false);
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }

  return (
    <KeyboardAvoidingView
      style={[styles.container, { paddingTop: insets.top }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScreenHeader title={t.ask.title} showLanguage />

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        style={styles.list}
        contentContainerStyle={[
          styles.listContent,
          { paddingBottom: insets.bottom + 80 },
        ]}
        ListEmptyComponent={
          <View style={styles.emptyChat}>
            <View style={styles.emptyChatIcon}>
              <MessageCircle size={36} color={Colors.sageSoft} />
            </View>
            <Text style={styles.emptyChatTitle}>{t.ask.subtitle}</Text>
            <Text style={styles.emptyChatHint}>{t.ask.inputHint}</Text>
          </View>
        }
        renderItem={({ item }) => <ChatBubble message={item} />}
      />

      {/* Input row */}
      <View
        style={[
          styles.inputRow,
          { paddingBottom: Math.max(insets.bottom, 8) + 8 },
        ]}
      >
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder={t.ask.inputHint}
          placeholderTextColor={Colors.charcoalLight}
          multiline
          maxLength={500}
          accessibilityLabel={t.ask.inputHint}
          onSubmitEditing={handleSend}
          blurOnSubmit={false}
        />
        <TouchableOpacity
          onPress={handleSend}
          disabled={!input.trim() || loading}
          style={[
            styles.sendBtn,
            (!input.trim() || loading) && styles.sendBtnDisabled,
          ]}
          accessibilityLabel={t.ask.send}
          accessibilityRole="button"
        >
          {loading ? (
            <ActivityIndicator size="small" color={Colors.white} />
          ) : (
            <Send size={18} color={Colors.white} />
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

function ChatBubble({ message }: { message: Message }) {
  const { t } = useTranslation();

  if (message.loading) {
    return (
      <View style={[styles.bubble, styles.bubbleAI]}>
        <View style={styles.typingDots}>
          {[0, 1, 2].map((i) => (
            <View key={i} style={[styles.typingDot, { opacity: 0.4 + i * 0.2 }]} />
          ))}
        </View>
      </View>
    );
  }

  const isUser = message.role === 'user';

  return (
    <View style={[styles.bubbleWrap, isUser ? styles.bubbleWrapUser : styles.bubbleWrapAI]}>
      <View
        style={[
          styles.bubble,
          isUser ? styles.bubbleUser : styles.bubbleAI,
          message.error && styles.bubbleError,
        ]}
      >
        <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>
          {message.text}
        </Text>

        {/* Needs agronomist escalation */}
        {message.needsAgronomist && (
          <View style={styles.escalationNotice}>
            <AlertTriangle size={12} color={Colors.warning} />
            <Text style={styles.escalationNoticeText}>{t.aiResult.needsAgronomist}</Text>
          </View>
        )}

        {/* Disclaimer */}
        {message.disclaimer && (
          <Text style={styles.disclaimerText}>{message.disclaimer}</Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.backgroundWarm },
  list: { flex: 1 },
  listContent: { padding: Spacing.base, gap: Spacing.sm },
  emptyChat: {
    flex: 1,
    alignItems: 'center',
    paddingTop: Spacing.xxxl,
    gap: Spacing.base,
    paddingHorizontal: Spacing.xxxl,
  },
  emptyChatIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.backgroundSage,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyChatTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.h3,
    color: Colors.charcoal,
    textAlign: 'center',
  },
  emptyChatHint: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoalMuted,
    textAlign: 'center',
    lineHeight: 22,
  },
  bubbleWrap: { maxWidth: '82%' },
  bubbleWrapUser: { alignSelf: 'flex-end' },
  bubbleWrapAI: { alignSelf: 'flex-start' },
  bubble: {
    borderRadius: Radius.lg,
    padding: Spacing.base,
    ...Shadow.xs,
  },
  bubbleUser: {
    backgroundColor: Colors.secondaryEmerald,
    borderBottomRightRadius: 4,
  },
  bubbleAI: {
    backgroundColor: Colors.backgroundCard,
    borderBottomLeftRadius: 4,
  },
  bubbleError: { backgroundColor: Colors.errorBg },
  bubbleText: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    lineHeight: 22,
  },
  bubbleTextUser: { color: Colors.white },
  typingDots: {
    flexDirection: 'row',
    gap: 5,
    paddingVertical: 4,
    paddingHorizontal: 4,
  },
  typingDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: Colors.secondaryEmerald,
  },
  escalationNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: Spacing.sm,
    backgroundColor: Colors.warningBg,
    padding: 6,
    borderRadius: Radius.sm,
  },
  escalationNoticeText: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.labelSm,
    color: Colors.warning,
  },
  disclaimerText: {
    fontFamily: FontFamily.regular,
    fontSize: 11,
    color: Colors.charcoalLight,
    marginTop: Spacing.sm,
    fontStyle: 'italic',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: Spacing.sm,
    paddingHorizontal: Spacing.base,
    paddingTop: Spacing.sm,
    backgroundColor: Colors.backgroundCard,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  input: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.body,
    color: Colors.charcoal,
    backgroundColor: Colors.backgroundWarm,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    maxHeight: 100,
    minHeight: 44,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.secondaryEmerald,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: { opacity: 0.5 },
});
