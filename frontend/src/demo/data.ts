/**
 * AgriGuard Demo Mode — Sample Data
 *
 * All records are FICTIONAL. They exist solely for the interactive demonstration.
 * No real farmers, real AI predictions, or real outbreak events are represented.
 * Every record carries a demoLabel identifying it as sample data.
 *
 * Rules:
 * - Never present a demo record as a real AI prediction.
 * - Never claim that sample outbreaks are currently happening in Rwanda.
 * - Never use real personal information.
 * - Every type mirrors the matching backend schema exactly.
 */

import type {
  CropResponse,
  CropReportResponse,
  AlertResponse,
  FarmerProfileResponse,
  RiskScoreResponse,
  AskResponse,
} from '../api/client';

// ── Demo flag ────────────────────────────────────────────────────────────────
export const DEMO_MODE = true;

// ── Sample crops (matches GET /crops/ response shape) ────────────────────────
export const DEMO_CROPS: CropResponse[] = [
  { id: 1, name_en: 'Maize', name_rw: 'Ibigori', scientific_name: 'Zea mays', category: 'CEREAL', description: 'Staple cereal crop widely grown across Rwanda.', common_pests: ['Fall Armyworm', 'Maize Streak Virus', 'Stalk Borer'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
  { id: 2, name_en: 'Beans', name_rw: 'Ibishyimbo', scientific_name: 'Phaseolus vulgaris', category: 'LEGUME', description: 'Important protein-rich legume for Rwandan households.', common_pests: ['Bean Rust', 'Angular Leaf Spot', 'Bean Fly'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
  { id: 3, name_en: 'Irish Potato', name_rw: 'Ibirayi', scientific_name: 'Solanum tuberosum', category: 'TUBER', description: 'High-value tuber crop, especially in northern highlands.', common_pests: ['Late Blight', 'Early Blight', 'Potato Moth'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
  { id: 4, name_en: 'Banana', name_rw: 'Igitoki', scientific_name: 'Musa spp.', category: 'FRUIT', description: 'Major food and income source for Rwandan farmers.', common_pests: ['Banana Wilt', 'Black Sigatoka', 'Banana Weevil'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
  { id: 5, name_en: 'Cassava', name_rw: 'Imyumbati', scientific_name: 'Manihot esculenta', category: 'TUBER', description: 'Drought-tolerant root crop providing food security.', common_pests: ['Cassava Mosaic Virus', 'Cassava Brown Streak', 'Mealybug'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
  { id: 6, name_en: 'Rice', name_rw: 'Umuceli', scientific_name: 'Oryza sativa', category: 'CEREAL', description: 'Grown in valley floors and marshlands.', common_pests: ['Rice Blast', 'Brown Plant Hopper', 'Rice Yellow Mottle Virus'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
  { id: 7, name_en: 'Tomato', name_rw: 'Inyanya', scientific_name: 'Solanum lycopersicum', category: 'VEGETABLE', description: 'High-value vegetable crop with strong market demand.', common_pests: ['Early Blight', 'Late Blight', 'Tomato Yellow Leaf Curl Virus'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
  { id: 8, name_en: 'Coffee', name_rw: 'Ikawa', scientific_name: 'Coffea arabica', category: 'CASH_CROP', description: 'Major export crop, primarily Arabica variety.', common_pests: ['Coffee Berry Borer', 'Coffee Leaf Rust', 'Antestia Bug'], is_active: true, created_at: '2024-01-01T00:00:00Z' },
];

// ── Sample profile ────────────────────────────────────────────────────────────
export const DEMO_PROFILE: FarmerProfileResponse = {
  id: 1,
  user_id: 1,
  phone_number: '+250788000001',
  full_name: 'Uwase Marie',
  email: undefined,
  preferred_language: 'rw',
  national_id: undefined,
  cooperative_name: 'Musanze Farmers Cooperative',
  is_phone_verified: true,
  locations: [
    {
      id: 1,
      farmer_id: 1,
      province: 'Northern Province',
      district: 'Musanze',
      sector: 'Muhoza',
      cell: 'Mpenge',
      village: 'Gasharu',
      latitude: -1.4994,
      longitude: 29.6334,
      is_primary: true,
      created_at: '2024-03-10T07:00:00Z',
    },
  ],
  total_reports: 5,
  created_at: '2024-03-10T07:00:00Z',
};

// ── Sample reports (matches CropReportResponse) ───────────────────────────────
export const DEMO_REPORTS: CropReportResponse[] = [
  {
    id: 1,
    report_code: 'AG0001',
    farmer_id: 1,
    farmer_name: 'Uwase Marie',
    farmer_phone: '+250788000001',
    crop_id: 1,
    crop_name_en: 'Maize',
    crop_name_rw: 'Ibigori',
    channel: 'APP',
    description: 'Leaves have irregular holes and there are small worm-like insects visible inside the stem.',
    symptoms: ['holes_in_leaves', 'stem_rot', 'pest_visible'],
    district: 'Musanze',
    sector: 'Muhoza',
    cell: 'Mpenge',
    village: 'Gasharu',
    latitude: -1.4994,
    longitude: 29.6334,
    severity: 'HIGH',
    status: 'AI_ANALYZED',
    agronomist_notes: undefined,
    verified_at: undefined,
    images: [],
    ai_result: {
      id: 1,
      model_name: 'agriguard-classifier-v1',
      predicted_pest_en: 'Fall Armyworm',
      predicted_pest_rw: 'Inzige zo mu Rwanda',
      confidence_score: 0.87,
      detected_severity: 'HIGH',
      recommendations: [
        'Apply recommended pesticide (e.g. Emamectin Benzoate) in the early morning or late evening.',
        'Remove and destroy heavily infested plants to prevent spread.',
        'Monitor neighbouring fields and report new cases immediately.',
        'Contact your local agriculture extension officer for community spray coordination.',
      ],
      is_mock: true,
      is_verified_correct: undefined,
    },
    history: [
      { id: 1, previous_status: undefined, new_status: 'PENDING', action_type: 'REPORT_CREATED', notes: 'Report submitted via AgriGuard app.', created_at: '2024-05-10T08:14:00Z' },
      { id: 2, previous_status: 'PENDING', new_status: 'AI_ANALYZED', action_type: 'AI_ANALYSIS_COMPLETE', notes: 'AI identified Fall Armyworm with 87% confidence.', created_at: '2024-05-10T08:14:35Z' },
    ],
    created_at: '2024-05-10T08:14:00Z',
    updated_at: '2024-05-10T08:14:35Z',
  },
  {
    id: 2,
    report_code: 'AG0002',
    farmer_id: 1,
    farmer_name: 'Uwase Marie',
    farmer_phone: '+250788000001',
    crop_id: 3,
    crop_name_en: 'Irish Potato',
    crop_name_rw: 'Ibirayi',
    channel: 'APP',
    description: 'Brown and black spots appearing on leaves. Some leaves are wilting and turning yellow at the edges.',
    symptoms: ['brown_spots', 'wilting', 'yellowing_leaves', 'discoloration'],
    district: 'Musanze',
    sector: 'Muhoza',
    cell: 'Mpenge',
    village: 'Gasharu',
    latitude: -1.4994,
    longitude: 29.6334,
    severity: 'MEDIUM',
    status: 'VERIFIED',
    agronomist_notes: 'Confirmed Late Blight (Phytophthora infestans). Recommend Mancozeb-based fungicide application. Remove affected foliage and avoid overhead irrigation. Check neighbouring farms.',
    verified_at: '2024-05-08T14:30:00Z',
    images: [],
    ai_result: {
      id: 2,
      model_name: 'agriguard-classifier-v1',
      predicted_pest_en: 'Late Blight',
      predicted_pest_rw: 'Indwara ya Ibirayi',
      confidence_score: 0.91,
      detected_severity: 'MEDIUM',
      recommendations: [
        'Apply Mancozeb or Metalaxyl fungicide according to label instructions.',
        'Remove and bury affected leaves; do not compost them.',
        'Avoid watering leaves — irrigate at the base of the plant.',
        'Rotate crops in the next season to break the disease cycle.',
      ],
      is_mock: true,
      is_verified_correct: true,
    },
    history: [
      { id: 3, previous_status: undefined, new_status: 'PENDING', action_type: 'REPORT_CREATED', notes: 'Report submitted via AgriGuard app.', created_at: '2024-05-07T09:00:00Z' },
      { id: 4, previous_status: 'PENDING', new_status: 'AI_ANALYZED', action_type: 'AI_ANALYSIS_COMPLETE', notes: 'AI identified Late Blight with 91% confidence.', created_at: '2024-05-07T09:00:40Z' },
      { id: 5, previous_status: 'AI_ANALYZED', new_status: 'VERIFIED', action_type: 'AGRONOMIST_VERIFIED', notes: 'Diagnosis confirmed by agronomist. Treatment plan issued.', created_at: '2024-05-08T14:30:00Z' },
    ],
    created_at: '2024-05-07T09:00:00Z',
    updated_at: '2024-05-08T14:30:00Z',
  },
  {
    id: 3,
    report_code: 'AG0003',
    farmer_id: 1,
    farmer_name: 'Uwase Marie',
    farmer_phone: '+250788000001',
    crop_id: 2,
    crop_name_en: 'Beans',
    crop_name_rw: 'Ibishyimbo',
    channel: 'APP',
    description: 'Reddish-brown powder on the underside of leaves. Some leaves are dropping early.',
    symptoms: ['brown_spots', 'discoloration', 'leaf_curl'],
    district: 'Musanze',
    sector: 'Muhoza',
    cell: 'Mpenge',
    village: 'Gasharu',
    latitude: -1.4994,
    longitude: 29.6334,
    severity: 'LOW',
    status: 'PENDING',
    agronomist_notes: undefined,
    verified_at: undefined,
    images: [],
    ai_result: {
      id: 3,
      model_name: 'agriguard-classifier-v1',
      predicted_pest_en: 'Bean Rust',
      predicted_pest_rw: 'Utunyazizi tw\'Ibishyimbo',
      confidence_score: 0.78,
      detected_severity: 'LOW',
      recommendations: [
        'Apply a sulphur-based fungicide to affected plants.',
        'Increase airflow between plants by removing excess foliage.',
        'Avoid working in the field when leaves are wet to prevent spreading spores.',
        'Plant resistant bean varieties in the next season.',
      ],
      is_mock: true,
      is_verified_correct: undefined,
    },
    history: [
      { id: 6, previous_status: undefined, new_status: 'PENDING', action_type: 'REPORT_CREATED', notes: 'Report submitted via AgriGuard app.', created_at: '2024-05-12T11:20:00Z' },
    ],
    created_at: '2024-05-12T11:20:00Z',
    updated_at: '2024-05-12T11:20:00Z',
  },
  {
    id: 4,
    report_code: 'AG0004',
    farmer_id: 1,
    farmer_name: 'Uwase Marie',
    farmer_phone: '+250788000001',
    crop_id: 7,
    crop_name_en: 'Tomato',
    crop_name_rw: 'Inyanya',
    channel: 'APP',
    description: 'Yellow leaves with dark brown patches. Fruit developing black sunken spots on the bottom.',
    symptoms: ['yellowing_leaves', 'brown_spots', 'discoloration'],
    district: 'Musanze',
    sector: 'Muhoza',
    cell: undefined,
    village: undefined,
    latitude: -1.4994,
    longitude: 29.6334,
    severity: 'CRITICAL',
    status: 'ESCALATED',
    agronomist_notes: 'Escalated for urgent field visit. Multiple fields affected in Muhoza sector.',
    verified_at: undefined,
    images: [],
    ai_result: {
      id: 4,
      model_name: 'agriguard-classifier-v1',
      predicted_pest_en: 'Early Blight',
      predicted_pest_rw: 'Indwara y\'Inyanya',
      confidence_score: 0.82,
      detected_severity: 'CRITICAL',
      recommendations: [
        'Immediately apply Chlorothalonil or Copper-based fungicide.',
        'Remove and destroy all affected fruit and foliage.',
        'Do not sell or consume visibly affected tomatoes.',
        'Report cluster size to your extension officer — potential community outbreak.',
      ],
      is_mock: true,
      is_verified_correct: undefined,
    },
    history: [
      { id: 7, previous_status: undefined, new_status: 'PENDING', action_type: 'REPORT_CREATED', notes: 'Report submitted.', created_at: '2024-05-13T07:30:00Z' },
      { id: 8, previous_status: 'PENDING', new_status: 'AI_ANALYZED', action_type: 'AI_ANALYSIS_COMPLETE', notes: 'Critical severity detected.', created_at: '2024-05-13T07:31:00Z' },
      { id: 9, previous_status: 'AI_ANALYZED', new_status: 'ESCALATED', action_type: 'ESCALATED_TO_AGRONOMIST', notes: 'Critical severity auto-escalated.', created_at: '2024-05-13T07:31:05Z' },
    ],
    created_at: '2024-05-13T07:30:00Z',
    updated_at: '2024-05-13T07:31:05Z',
  },
  {
    id: 5,
    report_code: 'AG0005',
    farmer_id: 1,
    farmer_name: 'Uwase Marie',
    farmer_phone: '+250788000001',
    crop_id: 1,
    crop_name_en: 'Maize',
    crop_name_rw: 'Ibigori',
    channel: 'APP',
    description: 'Yellow and white streaks running along the leaves. Stunted growth in one section of the field.',
    symptoms: ['yellowing_leaves', 'stunted_growth', 'discoloration'],
    district: 'Musanze',
    sector: 'Kinigi',
    cell: undefined,
    village: undefined,
    latitude: -1.5273,
    longitude: 29.5924,
    severity: 'MEDIUM',
    status: 'AI_ANALYZED',
    agronomist_notes: undefined,
    verified_at: undefined,
    images: [],
    ai_result: {
      id: 5,
      model_name: 'agriguard-classifier-v1',
      predicted_pest_en: 'Maize Streak Virus',
      predicted_pest_rw: 'Virusi y\'Ibigori',
      confidence_score: 0.72,
      detected_severity: 'MEDIUM',
      recommendations: [
        'Control leafhopper insects (the virus vectors) with approved insecticide.',
        'Remove infected plants from the field to reduce viral load.',
        'Plant virus-resistant maize varieties in the next season.',
        'Avoid planting near grass weeds that can harbour leafhoppers.',
      ],
      is_mock: true,
      is_verified_correct: undefined,
    },
    history: [
      { id: 10, previous_status: undefined, new_status: 'PENDING', action_type: 'REPORT_CREATED', notes: 'Report submitted.', created_at: '2024-05-14T10:00:00Z' },
      { id: 11, previous_status: 'PENDING', new_status: 'AI_ANALYZED', action_type: 'AI_ANALYSIS_COMPLETE', notes: 'AI identified Maize Streak Virus.', created_at: '2024-05-14T10:00:50Z' },
    ],
    created_at: '2024-05-14T10:00:00Z',
    updated_at: '2024-05-14T10:00:50Z',
  },
];

// ── Sample alerts ─────────────────────────────────────────────────────────────
export const DEMO_ALERTS: AlertResponse[] = [
  {
    id: 1,
    title_en: 'Fall Armyworm Alert — Musanze District',
    title_rw: 'Inzige zo mu Rwanda — Akarere ka Musanze',
    pest_name: 'Fall Armyworm',
    target_district: 'Musanze',
    target_sector: 'Muhoza',
    severity: 'HIGH',
    status: 'ACTIVE',
    affected_report_count: 14,
    source_report_id: 1,
    created_at: '2024-05-10T09:00:00Z',
  },
  {
    id: 2,
    title_en: 'Late Blight Outbreak — Nyabihu District',
    title_rw: 'Indwara ya Ibirayi — Akarere ka Nyabihu',
    pest_name: 'Late Blight',
    target_district: 'Nyabihu',
    target_sector: undefined,
    severity: 'MEDIUM',
    status: 'ACTIVE',
    affected_report_count: 8,
    source_report_id: 2,
    created_at: '2024-05-08T12:00:00Z',
  },
  {
    id: 3,
    title_en: 'Tomato Blight Warning — Rubavu District',
    title_rw: 'Indwara y\'Inyanya — Akarere ka Rubavu',
    pest_name: 'Early Blight',
    target_district: 'Rubavu',
    target_sector: undefined,
    severity: 'CRITICAL',
    status: 'ACTIVE',
    affected_report_count: 23,
    source_report_id: 4,
    created_at: '2024-05-13T08:00:00Z',
  },
  {
    id: 4,
    title_en: 'Bean Rust Advisory — Gicumbi District',
    title_rw: 'Utunyazizi tw\'Ibishyimbo — Akarere ka Gicumbi',
    pest_name: 'Bean Rust',
    target_district: 'Gicumbi',
    target_sector: undefined,
    severity: 'LOW',
    status: 'ACTIVE',
    affected_report_count: 5,
    source_report_id: 3,
    created_at: '2024-05-11T10:00:00Z',
  },
];

// ── Sample risk score ─────────────────────────────────────────────────────────
export const DEMO_RISK: RiskScoreResponse = {
  district: 'Musanze',
  pest_name: 'Fall Armyworm',
  crop_id: 1,
  risk_score: 0.72,
  contributing_report_count: 14,
  threshold: 0.4,
  above_threshold: true,
};

// ── Sample Ask AgriGuard responses ────────────────────────────────────────────
export const DEMO_ASK_RESPONSES: Array<{ keywords: string[]; response: AskResponse }> = [
  {
    keywords: ['fall armyworm', 'armyworm', 'worm', 'inzige'],
    response: {
      success: true,
      data: {
        answer: 'Fall Armyworm (Spodoptera frugiperda) is one of the most damaging pests for maize in Rwanda. Signs include irregular holes in leaves, sawdust-like frass inside the funnel, and visible larvae. Recommended actions: (1) Apply Emamectin Benzoate or Lambda-cyhalothrin early morning or late evening. (2) Practice intercropping with legumes. (3) Report clusters immediately to AgriGuard so your community is alerted. Early detection reduces crop losses by up to 60%.',
        language: 'en',
        sources: ['Rwanda Agriculture Board — Pest Management Guide 2023', 'FAO Fall Armyworm Response'],
        disclaimer: 'This is a sample AgriGuard response for demonstration purposes. For confirmed pest outbreaks, always consult a certified agricultural extension officer.',
        needsAgronomist: false,
      },
    },
  },
  {
    keywords: ['late blight', 'potato', 'ibirayi', 'blight'],
    response: {
      success: true,
      data: {
        answer: 'Late Blight (Phytophthora infestans) is the most serious potato disease in Rwanda\'s highland areas. It spreads rapidly in cool, wet conditions. Look for water-soaked lesions on leaves that quickly turn brown with a white fungal growth on the underside. Treatment: Apply Metalaxyl+Mancozeb fungicide preventively before rains. Remove and bury (do not compost) infected material. Avoid overhead irrigation. Use certified seed potatoes in the next season.',
        language: 'en',
        sources: ['Rwanda Agriculture Board — Potato Disease Guide', 'CIP (International Potato Center)'],
        disclaimer: 'Sample AgriGuard response for demonstration. Confirm with your local extension officer.',
        needsAgronomist: false,
      },
    },
  },
  {
    keywords: ['maize', 'ibigori', 'corn'],
    response: {
      success: true,
      data: {
        answer: 'Common maize problems in Rwanda include Fall Armyworm, Maize Streak Virus, and Stalk Borer. For healthy maize: plant certified seed, apply nitrogen fertiliser in splits (at planting and 4 weeks later), scout fields weekly for pests, and report any unusual symptoms through AgriGuard immediately. Early-season problems cost the most yield — a report in the first week saves up to 40% more crop than a report in week three.',
        language: 'en',
        sources: ['ISAR Rwanda Maize Production Guide', 'Rwanda Agriculture Board'],
        disclaimer: 'Sample AgriGuard response for demonstration.',
        needsAgronomist: false,
      },
    },
  },
  {
    keywords: ['prevention', 'prevent', 'protect', 'protect crop'],
    response: {
      success: true,
      data: {
        answer: 'General crop protection principles for Rwanda: (1) Use certified, disease-resistant seed varieties. (2) Practice crop rotation — do not grow the same crop in the same field two seasons in a row. (3) Remove crop residues after harvest to reduce pest reservoirs. (4) Use AgriGuard to report early — community alerts help your neighbours protect their crops too. (5) Join a farmer cooperative to access group inputs and extension services at lower cost.',
        language: 'en',
        sources: ['Rwanda Agricultural Board Extension Services'],
        disclaimer: 'Sample AgriGuard response for demonstration.',
        needsAgronomist: false,
      },
    },
  },
];

// ── Sample submitted report (what comes back after demo submission) ────────────
export function buildDemoSubmittedReport(
  cropId: number,
  symptoms: string[],
  description: string,
  severity: string,
  district: string,
  sector: string,
): CropReportResponse {
  const crop = DEMO_CROPS.find((c) => c.id === cropId) ?? DEMO_CROPS[0];
  const pestMap: Record<number, { en: string; rw: string; confidence: number }> = {
    1: { en: 'Fall Armyworm', rw: 'Inzige zo mu Rwanda', confidence: 0.84 },
    2: { en: 'Bean Rust', rw: 'Utunyazizi tw\'Ibishyimbo', confidence: 0.79 },
    3: { en: 'Late Blight', rw: 'Indwara ya Ibirayi', confidence: 0.88 },
    4: { en: 'Banana Wilt', rw: 'Indwara y\'Igitoki', confidence: 0.76 },
    5: { en: 'Cassava Mosaic Virus', rw: 'Virusi y\'Imyumbati', confidence: 0.81 },
    6: { en: 'Rice Blast', rw: 'Indwara y\'Umuceli', confidence: 0.73 },
    7: { en: 'Early Blight', rw: 'Indwara y\'Inyanya', confidence: 0.85 },
    8: { en: 'Coffee Leaf Rust', rw: 'Indwara y\'Ikawa', confidence: 0.80 },
  };
  const pest = pestMap[cropId] ?? { en: 'Unknown Pest', rw: 'Ibyorezo bitazwi', confidence: 0.55 };
  const severityUpper = severity.toUpperCase() as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

  return {
    id: 99,
    report_code: `AG${String(Math.floor(1000 + Math.random() * 8999)).padStart(4, '0')}`,
    farmer_id: 1,
    farmer_name: 'Uwase Marie (Demo)',
    farmer_phone: '+250788000001',
    crop_id: cropId,
    crop_name_en: crop.name_en,
    crop_name_rw: crop.name_rw,
    channel: 'APP',
    description: description || 'Demonstration report — no description provided.',
    symptoms,
    district: district || 'Musanze',
    sector: sector || 'Muhoza',
    cell: undefined,
    village: undefined,
    latitude: undefined,
    longitude: undefined,
    severity: severityUpper,
    status: 'AI_ANALYZED',
    agronomist_notes: undefined,
    verified_at: undefined,
    images: [],
    ai_result: {
      id: 99,
      model_name: 'agriguard-classifier-v1 (demo)',
      predicted_pest_en: pest.en,
      predicted_pest_rw: pest.rw,
      confidence_score: pest.confidence,
      detected_severity: severityUpper,
      recommendations: [
        'Monitor the field closely over the next 48 hours.',
        'Apply recommended treatment as advised by your agricultural extension officer.',
        'Report any spread to neighbouring plants through AgriGuard.',
        'Keep this report reference code for follow-up with an agronomist.',
      ],
      is_mock: true,
      is_verified_correct: undefined,
    },
    history: [
      { id: 1, previous_status: undefined, new_status: 'PENDING', action_type: 'REPORT_CREATED', notes: 'Demo report submitted.', created_at: new Date().toISOString() },
      { id: 2, previous_status: 'PENDING', new_status: 'AI_ANALYZED', action_type: 'AI_ANALYSIS_COMPLETE', notes: `Simulated AI result: ${pest.en}.`, created_at: new Date().toISOString() },
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

// ── Fallback Ask response for unrecognised questions ─────────────────────────
export function getDemoAskResponse(question: string, language: 'en' | 'rw'): AskResponse {
  const q = question.toLowerCase();
  for (const { keywords, response } of DEMO_ASK_RESPONSES) {
    if (keywords.some((k) => q.includes(k))) return response;
  }
  return {
    success: true,
    data: {
      answer: language === 'rw'
        ? `AgriGuard irashobora gufasha gusobanura ibibazo by'ubuhinzi. Muri demo mode, igisubizo kinini kiragaragara: Reba imyaka yawe buri munsi kandi uherekeze ikibazo cya mbere ukoresheje AgriGuard.`
        : `AgriGuard helps identify crop pests and diseases common in Rwanda. In this demonstration, our sample data covers maize (Fall Armyworm), potato (Late Blight), beans (Bean Rust), and tomato (Early Blight). Try asking about one of these crops or pests for a detailed sample response.`,
      language,
      sources: [],
      disclaimer: language === 'rw'
        ? 'Ibi ni ibisubizo bya demo — ntabwo ariyo makuru y\'ukuri.'
        : 'This is a demo response. For verified agricultural advice, contact your local extension officer.',
      needsAgronomist: false,
    },
  };
}

// ── Dashboard stats ───────────────────────────────────────────────────────────
export const DEMO_STATS = {
  totalFarmers: 2847,
  totalReports: 1234,
  pendingReports: 87,
  aiAnalyzed: 1089,
  highCriticalCount: 156,
  activeAlerts: 4,
  recentReports: DEMO_REPORTS.slice(0, 3),
  recentAlerts: DEMO_ALERTS.slice(0, 2),
};

// ── Agricultural advice articles ─────────────────────────────────────────────
export const DEMO_ADVICE = [
  {
    id: 1,
    crop: 'Maize',
    crop_rw: 'Ibigori',
    title: 'Preventing Fall Armyworm on Maize',
    title_rw: 'Kurinda Ibigori ku Nzige',
    summary: 'Fall Armyworm can destroy up to 80% of a maize crop if untreated. Early scouting and reporting are the most effective defence.',
    steps: [
      'Scout fields twice per week from germination to harvest.',
      'Look for small holes in leaves and sawdust-like frass in the funnel.',
      'Apply Emamectin Benzoate 1.9% EC at first sign of infestation.',
      'Report confirmed cases to AgriGuard for community alert.',
    ],
    severity_risk: 'HIGH',
  },
  {
    id: 2,
    crop: 'Irish Potato',
    crop_rw: 'Ibirayi',
    title: 'Managing Late Blight in Potatoes',
    title_rw: 'Kuvura Indwara ya Ibirayi',
    summary: 'Late Blight spreads extremely fast in Rwanda\'s cool highland climate. Preventive fungicide application is essential.',
    steps: [
      'Apply Mancozeb preventively before the rainy season begins.',
      'Ensure proper plant spacing for airflow.',
      'Avoid overhead irrigation — water at the base only.',
      'Remove and bury (not compost) any infected plant material.',
    ],
    severity_risk: 'MEDIUM',
  },
  {
    id: 3,
    crop: 'Beans',
    crop_rw: 'Ibishyimbo',
    title: 'Controlling Bean Rust',
    title_rw: 'Kuvura Utunyazizi tw\'Ibishyimbo',
    summary: 'Bean rust reduces yields significantly but is manageable with correct fungicide timing and resistant varieties.',
    steps: [
      'Use rust-resistant bean varieties such as RWR 2245.',
      'Apply sulphur-based fungicide at first sign of pustules.',
      'Avoid working in wet fields to limit spore spread.',
      'Rotate beans with cereals in alternating seasons.',
    ],
    severity_risk: 'LOW',
  },
  {
    id: 4,
    crop: 'Tomato',
    crop_rw: 'Inyanya',
    title: 'Early Blight Management in Tomatoes',
    title_rw: 'Kuvura Indwara y\'Inyanya',
    summary: 'Early Blight causes dark spots on lower leaves and can progress to fruit loss. Fungicide rotation is key.',
    steps: [
      'Apply Chlorothalonil or Copper Oxychloride preventively.',
      'Remove lower infected leaves immediately.',
      'Stake plants to improve canopy airflow.',
      'Avoid planting tomatoes in the same field two seasons running.',
    ],
    severity_risk: 'MEDIUM',
  },
];
