# AgriGuard Mobile Frontend

React Native (Expo) smartphone application for Rwandan smallholder farmers.

## Stack

- **Framework**: React Native 0.76 with Expo 53 and Expo Router 4
- **Language**: TypeScript
- **State**: Zustand (auth + language)
- **API**: Typed fetch client with JWT Bearer auth
- **i18n**: Custom hook — English + Kinyarwanda (first-class, equal interfaces)
- **Icons**: Lucide React Native (consistent, single library)
- **Fonts**: Inter (humanist sans-serif — renders Kinyarwanda cleanly)

## Colour Palette

| Token | Hex | Usage |
|-------|-----|-------|
| primaryForest | `#1A6B3C` | Brand, sidebar, headings |
| secondaryEmerald | `#16A34A` | Primary buttons, active nav |
| sageSoft | `#A7C4A0` | Subtle backgrounds |
| limeAccent | `#C5E86C` | Highlights, selected states |
| backgroundWarm | `#F9FAF5` | Main app background |
| charcoal | `#17251B` | Primary text |

Severity colours (semantic only — never decorative):
LOW `#6EE7B7` · MEDIUM `#FCD34D` · HIGH `#F97316` · CRITICAL `#EF4444`

## Screens

| Screen | Route | Backend Endpoint |
|--------|-------|-----------------|
| Welcome | `/(auth)/welcome` | — |
| Register | `/(auth)/register` | `POST /auth/register` |
| Login | `/(auth)/login` | `POST /auth/login` |
| Home | `/(farmer)/home` | `GET /reports/my-reports`, `GET /outbreak/alerts`, `GET /farmers/profile` |
| Report Flow + AI | `/(farmer)/report-new` | `GET /crops/`, `POST /reports/`, `POST /reports/{id}/images`, `GET /reports/{code}` |
| My Reports | `/(farmer)/reports` | `GET /reports/my-reports` |
| Report Detail | `/(farmer)/report-detail` | `GET /reports/{code}` |
| Ask AgriGuard | `/(farmer)/ask` | `POST /api/ai/ask` (AI service direct) |
| Community Alerts | `/(farmer)/alerts` | `GET /outbreak/alerts`, `GET /outbreak/risk-score` |
| Profile | `/(farmer)/profile` | `GET /farmers/profile`, `PUT /farmers/profile` |

## Quick Start

```bash
cd frontend
npm install
# or: bun install

# Copy environment file
cp .env.example .env
# Edit .env to point to your backend

# Start development server
npx expo start

# Run on Android
npx expo start --android

# Run on iOS (macOS only)
npx expo start --ios
```

## Prerequisites

- Node.js 18+ or Bun
- Expo CLI: `npm install -g expo-cli`
- For Android: Android Studio + emulator, or physical device with Expo Go
- For iOS (macOS only): Xcode + simulator, or physical device with Expo Go
- Backend running at `http://localhost:8000`
- AI service running at `http://localhost:5000`

## Project Structure

```
frontend/
├── app/                     # Expo Router screens
│   ├── _layout.tsx          # Root layout (hydration, navigation)
│   ├── index.tsx            # Auth redirect
│   ├── (auth)/              # Unauthenticated screens
│   │   ├── welcome.tsx      # Onboarding / landing
│   │   ├── login.tsx        # Login
│   │   └── register.tsx     # Registration
│   └── (farmer)/            # Authenticated farmer screens (tab nav)
│       ├── _layout.tsx      # Tab navigator
│       ├── home.tsx         # Home dashboard
│       ├── report-new.tsx   # Report a problem (5-step + AI result)
│       ├── reports.tsx      # My Reports list
│       ├── report-detail.tsx# Report detail + history
│       ├── ask.tsx          # Ask AgriGuard chat
│       ├── alerts.tsx       # Community alerts
│       └── profile.tsx      # Farmer profile
├── src/
│   ├── api/
│   │   ├── client.ts        # Typed API client (all endpoints)
│   │   └── config.ts        # Base URLs + constants
│   ├── store/
│   │   └── authStore.ts     # Zustand auth store (JWT + language)
│   ├── hooks/
│   │   └── useTranslation.ts# i18n hook
│   ├── i18n/
│   │   ├── en.ts            # English translations
│   │   ├── rw.ts            # Kinyarwanda translations
│   │   └── index.ts
│   ├── theme/
│   │   ├── colors.ts        # AgriGuard colour tokens
│   │   ├── typography.ts    # Font scale
│   │   ├── spacing.ts       # Spacing, radius, shadows
│   │   └── index.ts
│   └── components/
│       └── common/          # Shared UI components
│           ├── Button.tsx
│           ├── Card.tsx
│           ├── Input.tsx
│           ├── SeverityBadge.tsx
│           ├── StatusChip.tsx
│           ├── ConfidenceRing.tsx
│           ├── LanguageToggle.tsx
│           ├── ScreenHeader.tsx
│           ├── EmptyState.tsx
│           ├── ErrorBanner.tsx
│           └── SkeletonLoader.tsx
└── assets/                  # Icons, images, splash screen
```

## Design Decisions

### Language
Both EN and RW are first-class. The language toggle is one tap, persists to storage, and is visible from every screen. The API returns `predicted_pest_rw` and `name_rw` — the UI uses them when RW is selected.

### AI Disclaimer
`is_mock: true` on any AI result shows a "Diagnosis Pending" banner. Mock data is never presented as a confirmed diagnosis.

### Escalation
When `detected_severity` is `HIGH` or `CRITICAL`, a red escalation banner appears: *"An agronomist should inspect this crop urgently."* This matches the backend's `needs_agronomist` logic.

### Error handling
`ApiError` is caught by `ErrorBanner`. Every user-visible message is translated. Raw API error strings are never shown to farmers.

### Offline awareness
`expo-secure-store` caches the JWT token. The crop catalogue is loaded once on first screen visit. Network errors show a friendly banner with a retry button.

### Touch targets
All interactive elements meet the 44×44px minimum. Lucide icons have `accessibilityLabel` on standalone icons.

### Severity colours
Semantic only — never decorative. `severityColorMap` maps `LOW/MEDIUM/HIGH/CRITICAL` and the AI service variants (`Low/Moderate/High/Critical`) to the same colours.
