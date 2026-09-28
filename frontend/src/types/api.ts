export type ApiResponse<T> = { success: boolean; data: T; message: string; error: string | null };

export type Analysis = {
  analysis_id: string;
  soil_type: string;
  confidence: number;
  model_version: string;
  warning?: string;
  top_predictions: { soil_type: string; confidence: number }[];
  property_ranges?: PropertyRange[];
};

export type PropertyRange = {
  name: string;
  typical_value: number;
  range: { min: number; max: number };
  unit: string;
  source: string;
  status: string;
  notes: string;
};

export type Recommendation = {
  crop: string;
  compatibility_score: number;
  season: string;
  matched_factors: string[];
  limiting_factors: string[];
  warning: string;
  references?: string[];
};

export type HistoryItem = {
  id: string;
  soil_type: string;
  confidence: number;
  model_version: string;
  warning?: string;
  created_at: string;
};

export type SoilDeficiency = {
  nutrient: string;
  status: string;
  severity: string;
  description: string;
  visual_signs: string;
};

export type FertilizerRecommendation = {
  fertilizer_name: string;
  type: string;
  dosage: string;
  application_method: string;
  timing: string;
  purpose: string;
  cost_estimate: string;
};

export type CropSuggestion = {
  crop_name: string;
  suitability_score: number;
  season: string;
  reason: string;
  expected_yield: string;
  water_requirement: string;
  growth_duration: string;
  tips: string;
};

export type AiSuggestions = {
  deficiencies: SoilDeficiency[];
  fertilizer_recommendations: FertilizerRecommendation[];
  suitable_crops: CropSuggestion[];
  soil_health_summary: string;
  season: string;
  season_note: string;
  error?: string;
};

export type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
};

export type ChatResponse = {
  message: string;
  language: string;
  model: string;
};
