/**
 * AgriGuard API Configuration
 *
 * Backend API: http://localhost:8000/api/v1  (Person 3's FastAPI backend)
 * AI Service:  http://localhost:5000/api/ai  (Person 2's AI FastAPI service)
 *
 * The UI calls the Backend for all data operations.
 * The UI calls the AI Service ONLY for the Ask AgriGuard chat feature.
 * The Backend handles all other AI analysis internally.
 */

// Use environment variable or fallback for development
export const BACKEND_BASE_URL =
  process.env.EXPO_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

export const AI_SERVICE_BASE_URL =
  process.env.EXPO_PUBLIC_AI_URL ?? 'http://localhost:5000';

export const API_V1 = `${BACKEND_BASE_URL}/api/v1`;
export const AI_API = `${AI_SERVICE_BASE_URL}/api/ai`;

/** Request timeout in milliseconds */
export const REQUEST_TIMEOUT = 30_000;

/** Image upload size limit: 10 MB (matches backend MAX_IMAGE_SIZE_MB) */
export const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;

/** Supported image MIME types */
export const SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'] as const;
