import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import { api, session } from './services/api';
import type { AiSuggestions, Analysis, Recommendation, HistoryItem, ChatMessage } from './types/api';

// ==========================================
// Language mapping: code <-> display name
// ==========================================
const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'ml', label: 'മലയാളം' },
];

// ==========================================
// Property display helpers
// ==========================================
const PROPERTY_ICONS: Record<string, string> = {
  ph: '🧪',
  nitrogen: '🟢',
  phosphorus: '🔵',
  potassium: '🟠',
  moisture: '💧',
  organic_carbon: '🍂',
  electrical_conductivity: '⚡',
};

const PROPERTY_LABELS: Record<string, string> = {
  ph: 'pH',
  nitrogen: 'Nitrogen (N)',
  phosphorus: 'Phosphorus (P)',
  potassium: 'Potassium (K)',
  moisture: 'Moisture',
  organic_carbon: 'Organic Carbon',
  electrical_conductivity: 'EC',
};

// Scale max values for horizontal bar visualization
const PROPERTY_SCALE_MAX: Record<string, number> = {
  ph: 14,
  nitrogen: 500,
  phosphorus: 60,
  potassium: 500,
  moisture: 60,
  organic_carbon: 5,
  electrical_conductivity: 8,
};

// ==========================================
// Chatbot Component
// ==========================================
const Chatbot = ({ analysisContext }: { analysisContext?: Analysis | null }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([{
    role: 'assistant',
    content: "Hello! I'm the SoilWise Assistant. I can explain your soil analysis, soil properties, crop recommendations, and provide farming guidance. How can I help you?",
    timestamp: Date.now()
  }]);
  const [input, setInput] = useState('');
  const [langCode, setLangCode] = useState('en');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestions = [
    "Explain my soil",
    "Explain my pH",
    "Explain NPK",
    "Which crop is best?",
    "Explain my recommendations",
    "Which season is suitable?",
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const handleSend = async (text: string = input) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = { role: 'user', content: text, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const formattedHistory = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await api.chat(text, langCode, analysisContext, formattedHistory);

      if (response.success && response.data) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: response.data.message,
          timestamp: Date.now()
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: response.message || 'Assistant is temporarily unavailable. Please try again.',
          timestamp: Date.now()
        }]);
      }
    } catch (err: any) {
      const errorMsg = err.message?.includes('401') || err.message?.includes('Unauthorized')
        ? 'Please log in to use the assistant.'
        : err.message?.includes('429')
        ? 'Too many requests. Please wait a moment and try again.'
        : err.message?.includes('503') || err.message?.includes('not configured')
        ? 'The AI assistant is not configured. Please contact the administrator.'
        : 'Assistant is temporarily unavailable. Please try again.';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: errorMsg,
        timestamp: Date.now()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button className="chat-fab" onClick={() => setIsOpen(!isOpen)} aria-label="Toggle Chat">
        {isOpen ? '✕' : '💬'}
      </button>

      {isOpen && (
        <div className="chat-panel">
          <div className="chat-header">
            <h3 style={{ margin: 0, fontSize: '1rem' }}>🌱 SoilWise Assistant</h3>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <select
                value={langCode}
                onChange={(e) => setLangCode(e.target.value)}
                className="chat-lang-select"
              >
                {LANGUAGES.map(l => (
                  <option key={l.code} value={l.code} style={{ color: 'black' }}>{l.label}</option>
                ))}
              </select>
              <button onClick={() => setIsOpen(false)} className="chat-close-btn">✕</button>
            </div>
          </div>

          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {loading && (
              <div className="chat-message assistant chat-typing">
                <span className="typing-dots">
                  <span>●</span><span>●</span><span>●</span>
                </span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length < 4 && (
            <div className="chat-suggestions">
              {suggestions.map(s => (
                <button key={s} className="chat-suggestion" onClick={() => handleSend(s)}>{s}</button>
              ))}
            </div>
          )}

          <div className="chat-input-area">
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Ask about your soil…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                style={{ padding: '0.5rem' }}
              />
              <button className="btn btn-primary" onClick={() => handleSend()} disabled={loading || !input.trim()}>
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};


// ==========================================
// Soil Properties Card Component
// ==========================================
const getParameterStatus = (name: string, value: number): { label: string; color: string } => {
  const statusMap: Record<string, (v: number) => { label: string; color: string }> = {
    ph: (v) => v < 5.5 ? { label: 'Strongly Acidic', color: 'var(--color-danger)' }
      : v < 6.5 ? { label: 'Slightly Acidic', color: 'var(--color-warning)' }
      : v <= 7.5 ? { label: 'Optimal', color: 'var(--color-success)' }
      : v <= 8.5 ? { label: 'Slightly Alkaline', color: 'var(--color-warning)' }
      : { label: 'Strongly Alkaline', color: 'var(--color-danger)' },
    nitrogen: (v) => v < 150 ? { label: 'Low', color: 'var(--color-danger)' }
      : v <= 300 ? { label: 'Medium', color: 'var(--color-warning)' }
      : { label: 'High', color: 'var(--color-success)' },
    phosphorus: (v) => v < 10 ? { label: 'Low', color: 'var(--color-danger)' }
      : v <= 25 ? { label: 'Medium', color: 'var(--color-warning)' }
      : { label: 'High', color: 'var(--color-success)' },
    potassium: (v) => v < 120 ? { label: 'Low', color: 'var(--color-danger)' }
      : v <= 280 ? { label: 'Medium', color: 'var(--color-warning)' }
      : { label: 'High', color: 'var(--color-success)' },
    moisture: (v) => v < 15 ? { label: 'Dry', color: 'var(--color-danger)' }
      : v <= 35 ? { label: 'Moderate', color: 'var(--color-success)' }
      : { label: 'Wet', color: 'var(--color-warning)' },
    organic_carbon: (v) => v < 0.5 ? { label: 'Low', color: 'var(--color-danger)' }
      : v <= 1.0 ? { label: 'Medium', color: 'var(--color-warning)' }
      : { label: 'High', color: 'var(--color-success)' },
    electrical_conductivity: (v) => v < 0.8 ? { label: 'Normal', color: 'var(--color-success)' }
      : v <= 2.0 ? { label: 'Moderate', color: 'var(--color-warning)' }
      : { label: 'Saline', color: 'var(--color-danger)' },
  };
  return (statusMap[name] || (() => ({ label: 'N/A', color: 'var(--color-text-muted)' })))(value);
};

const SoilPropertiesSection = ({ properties, soilType }: { properties: Analysis['property_ranges']; soilType?: string }) => {
  if (!properties || properties.length === 0) return null;

  return (
    <div className="card soil-params-card">
      <div className="card-header" style={{ borderBottom: '2px solid var(--color-primary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.3rem' }}>🧪</span>
          <div>
            <h4 style={{ margin: 0 }}>Detected Soil Parameters</h4>
            <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.15rem' }}>
              Approximate values based on {soilType ? soilType.replace(/_/g, ' ') : 'detected soil type'} analysis
            </p>
          </div>
        </div>
      </div>
      <div className="card-body">
        <div className="property-grid">
          {properties.map((prop, i) => {
            const icon = PROPERTY_ICONS[prop.name] || '📋';
            const label = PROPERTY_LABELS[prop.name] || prop.name;
            const scaleMax = PROPERTY_SCALE_MAX[prop.name] || 100;
            const barPercent = Math.min((prop.typical_value / scaleMax) * 100, 100);
            const status = getParameterStatus(prop.name, prop.typical_value);

            return (
              <div key={i} className="property-card">
                <div className="property-header">
                  <span className="property-icon">{icon}</span>
                  <span className="property-label">{label}</span>
                </div>
                <div className="property-value">
                  <span className="property-number">{prop.typical_value}</span>
                  {prop.unit && <span className="property-unit">{prop.unit}</span>}
                </div>
                <div className="property-status-badge" style={{ backgroundColor: status.color }}>
                  {status.label}
                </div>
                <div className="property-bar-container">
                  <div className="property-bar" style={{ width: `${barPercent}%`, backgroundColor: status.color }} />
                </div>
                <div className="property-range">
                  Range: {prop.range.min} – {prop.range.max} {prop.unit}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};


// ==========================================
// AI Suggestions Section Component
// ==========================================
const SEVERITY_COLORS: Record<string, string> = {
  Severe: 'var(--color-danger)',
  Moderate: 'var(--color-warning)',
  Mild: 'var(--color-success)',
};

const SUITABILITY_COLOR = (score: number) =>
  score >= 80 ? 'var(--color-success)' : score >= 60 ? 'var(--color-primary)' : score >= 40 ? 'var(--color-warning)' : 'var(--color-danger)';

const AiSuggestionsSection = ({ suggestions, loading, error, onRetry }: {
  suggestions: AiSuggestions | null;
  loading: boolean;
  error: string;
  onRetry: () => void;
}) => {
  const [activeTab, setActiveTab] = useState<'deficiencies' | 'fertilizers' | 'crops'>('deficiencies');

  if (loading) {
    return (
      <div className="card">
        <div className="card-header" style={{ borderBottom: '2px solid var(--color-accent)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.3rem' }}>🤖</span>
            <h4 style={{ margin: 0 }}>AI-Powered Suggestions</h4>
          </div>
        </div>
        <div className="card-body" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: '1rem' }} className="text-muted">Generating AI suggestions using Gemini...</p>
          <p className="text-muted" style={{ fontSize: '0.8rem' }}>Analyzing soil deficiencies, fertilizers & suitable crops</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-header" style={{ borderBottom: '2px solid var(--color-danger)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.3rem' }}>🤖</span>
            <h4 style={{ margin: 0 }}>AI-Powered Suggestions</h4>
          </div>
        </div>
        <div className="card-body" style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ color: 'var(--color-danger)', marginBottom: '1rem' }}>{error}</p>
          <button className="btn btn-primary" onClick={onRetry}>🔄 Retry</button>
        </div>
      </div>
    );
  }

  if (!suggestions) return null;

  return (
    <div className="card ai-suggestions-card">
      <div className="card-header" style={{ borderBottom: '2px solid var(--color-accent)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.3rem' }}>🤖</span>
            <div>
              <h4 style={{ margin: 0 }}>AI-Powered Suggestions</h4>
              <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.15rem' }}>
                Season: <strong>{suggestions.season}</strong> · Powered by Google Gemini
              </p>
            </div>
          </div>
          <button className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }} onClick={onRetry}>🔄 Refresh</button>
        </div>
      </div>

      {/* Health Summary */}
      {suggestions.soil_health_summary && (
        <div style={{ padding: '1rem 1.25rem', background: 'linear-gradient(135deg, rgba(23,60,44,0.05), rgba(197,106,43,0.05))', borderBottom: '1px solid var(--color-border)' }}>
          <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>
            <strong>🏥 Soil Health Summary:</strong> {suggestions.soil_health_summary}
          </p>
        </div>
      )}

      {/* Season Note */}
      {suggestions.season_note && (
        <div style={{ padding: '0.75rem 1.25rem', background: 'rgba(197,106,43,0.05)', borderBottom: '1px solid var(--color-border)' }}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-accent)' }}>
            <strong>📅 Season Note:</strong> {suggestions.season_note}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="ai-tabs">
        <button className={`ai-tab ${activeTab === 'deficiencies' ? 'active' : ''}`} onClick={() => setActiveTab('deficiencies')}>
          🔍 Deficiencies ({suggestions.deficiencies.length})
        </button>
        <button className={`ai-tab ${activeTab === 'fertilizers' ? 'active' : ''}`} onClick={() => setActiveTab('fertilizers')}>
          🧴 Fertilizers ({suggestions.fertilizer_recommendations.length})
        </button>
        <button className={`ai-tab ${activeTab === 'crops' ? 'active' : ''}`} onClick={() => setActiveTab('crops')}>
          🌾 Crops ({suggestions.suitable_crops.length})
        </button>
      </div>

      <div className="card-body">
        {/* Deficiencies Tab */}
        {activeTab === 'deficiencies' && (
          <div className="ai-tab-content">
            {suggestions.deficiencies.map((d, i) => (
              <div key={i} className="ai-deficiency-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <strong style={{ fontSize: '1.05rem' }}>{d.nutrient}</strong>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <span className="badge" style={{ backgroundColor: SEVERITY_COLORS[d.severity] || 'var(--color-text-muted)', color: 'white', fontSize: '0.75rem' }}>
                      {d.severity}
                    </span>
                    <span className="badge badge-primary" style={{ fontSize: '0.75rem' }}>{d.status}</span>
                  </div>
                </div>
                <p style={{ margin: '0.25rem 0', fontSize: '0.9rem', lineHeight: 1.5 }}>{d.description}</p>
                {d.visual_signs && (
                  <p className="text-muted" style={{ margin: '0.25rem 0 0', fontSize: '0.8rem' }}>
                    👁️ <em>Visual signs: {d.visual_signs}</em>
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Fertilizers Tab */}
        {activeTab === 'fertilizers' && (
          <div className="ai-tab-content">
            {suggestions.fertilizer_recommendations.map((f, i) => (
              <div key={i} className="ai-fertilizer-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <strong style={{ fontSize: '1.05rem' }}>{f.fertilizer_name}</strong>
                  <span className="badge badge-primary" style={{ fontSize: '0.75rem' }}>{f.type}</span>
                </div>
                <div className="ai-detail-grid">
                  <div><span className="text-muted">💊 Dosage:</span> {f.dosage}</div>
                  <div><span className="text-muted">🎯 Purpose:</span> {f.purpose}</div>
                  <div><span className="text-muted">📋 Method:</span> {f.application_method}</div>
                  <div><span className="text-muted">⏰ Timing:</span> {f.timing}</div>
                  {f.cost_estimate && <div><span className="text-muted">💰 Cost:</span> {f.cost_estimate}</div>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Crops Tab */}
        {activeTab === 'crops' && (
          <div className="ai-tab-content">
            {suggestions.suitable_crops.map((c, i) => (
              <div key={i} className="ai-crop-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <strong style={{ fontSize: '1.05rem' }}>{c.crop_name}</strong>
                  <span className="badge" style={{ backgroundColor: SUITABILITY_COLOR(c.suitability_score), color: 'white', fontSize: '0.75rem' }}>
                    {c.suitability_score}% suitable
                  </span>
                </div>
                <div className="meter-container" style={{ marginBottom: '0.5rem' }}>
                  <div className="meter-fill" style={{ width: `${c.suitability_score}%`, backgroundColor: SUITABILITY_COLOR(c.suitability_score) }} />
                </div>
                <p style={{ margin: '0.25rem 0', fontSize: '0.9rem', lineHeight: 1.5 }}>{c.reason}</p>
                <div className="ai-detail-grid" style={{ marginTop: '0.5rem' }}>
                  <div><span className="text-muted">📅 Season:</span> {c.season}</div>
                  <div><span className="text-muted">💧 Water:</span> {c.water_requirement}</div>
                  <div><span className="text-muted">📈 Yield:</span> {c.expected_yield}</div>
                  <div><span className="text-muted">⏱️ Duration:</span> {c.growth_duration}</div>
                </div>
                {c.tips && (
                  <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', padding: '0.5rem', background: 'rgba(23,60,44,0.04)', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--color-primary)' }}>
                    💡 <em>{c.tips}</em>
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};


// ==========================================
// Pages
// ==========================================

const LandingPage = () => (
  <div className="container">
    <div className="hero">
      <h1 className="hero-title">AI-Powered<br />Soil Intelligence</h1>
      <p className="hero-subtitle">
        Upload a soil image and get instant classification, property analysis, and crop recommendations powered by deep learning.
      </p>
      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link to="/analyze" className="btn btn-accent" style={{ fontSize: '1.1rem', padding: '0.75rem 2rem' }}>
          Start Analysis
        </Link>
        <Link to="/about" className="btn btn-outline" style={{ fontSize: '1.1rem', padding: '0.75rem 2rem', borderColor: 'rgba(255,255,255,0.4)', color: 'white' }}>
          Learn More
        </Link>
      </div>
    </div>

    <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>What SoilWise Offers</h2>
    <div className="grid grid-cols-3" style={{ marginBottom: '3rem' }}>
      <div className="card feature-card-hover">
        <div className="card-body" style={{ textAlign: 'center' }}>
          <div className="feature-icon-large">📸</div>
          <h3 className="text-primary">AI Soil Classification</h3>
          <p className="text-muted">Advanced computer vision identifies soil types with confidence metrics and visual explanations.</p>
        </div>
      </div>
      <div className="card feature-card-hover">
        <div className="card-body" style={{ textAlign: 'center' }}>
          <div className="feature-icon-large">🧪</div>
          <h3 className="text-primary">Soil Property Analysis</h3>
          <p className="text-muted">Get estimated pH, NPK, moisture, organic carbon, and electrical conductivity for your soil.</p>
        </div>
      </div>
      <div className="card feature-card-hover">
        <div className="card-body" style={{ textAlign: 'center' }}>
          <div className="feature-icon-large">🌾</div>
          <h3 className="text-primary">Crop Recommendations</h3>
          <p className="text-muted">Season-aware crop matching based on soil properties and scientific literature.</p>
        </div>
      </div>
    </div>

    <div className="grid grid-cols-3" style={{ marginBottom: '3rem' }}>
      <div className="card feature-card-hover">
        <div className="card-body" style={{ textAlign: 'center' }}>
          <div className="feature-icon-large">📅</div>
          <h3 className="text-primary">Season-Aware Guidance</h3>
          <p className="text-muted">Kharif, Rabi, or Zaid — recommendations adapt to your growing season.</p>
        </div>
      </div>
      <div className="card feature-card-hover">
        <div className="card-body" style={{ textAlign: 'center' }}>
          <div className="feature-icon-large">📋</div>
          <h3 className="text-primary">Analysis History</h3>
          <p className="text-muted">Track and review all your past soil analyses in one place.</p>
        </div>
      </div>
      <div className="card feature-card-hover">
        <div className="card-body" style={{ textAlign: 'center' }}>
          <div className="feature-icon-large">💬</div>
          <h3 className="text-primary">Multilingual AI Assistant</h3>
          <p className="text-muted">Chat in English, Kannada, Tamil, Telugu, Hindi, or Malayalam.</p>
        </div>
      </div>
    </div>

    {/* How It Works */}
    <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>How It Works</h2>
    <div className="how-it-works-flow" style={{ marginBottom: '3rem' }}>
      <div className="flow-step">
        <div className="flow-step-number">1</div>
        <div className="flow-step-icon">📸</div>
        <p className="flow-step-text">Upload</p>
        <p className="text-muted" style={{ fontSize: '0.8rem' }}>Take a photo of your soil</p>
      </div>
      <div className="flow-arrow">→</div>
      <div className="flow-step">
        <div className="flow-step-number">2</div>
        <div className="flow-step-icon">🔬</div>
        <p className="flow-step-text">Analyze</p>
        <p className="text-muted" style={{ fontSize: '0.8rem' }}>AI classifies your soil</p>
      </div>
      <div className="flow-arrow">→</div>
      <div className="flow-step">
        <div className="flow-step-number">3</div>
        <div className="flow-step-icon">📊</div>
        <p className="flow-step-text">Understand</p>
        <p className="text-muted" style={{ fontSize: '0.8rem' }}>View soil properties</p>
      </div>
      <div className="flow-arrow">→</div>
      <div className="flow-step">
        <div className="flow-step-number">4</div>
        <div className="flow-step-icon">🌾</div>
        <p className="flow-step-text">Recommend</p>
        <p className="text-muted" style={{ fontSize: '0.8rem' }}>Get crop suggestions</p>
      </div>
    </div>

    {/* CTA */}
    <div style={{ textAlign: 'center', padding: '3rem 1rem', background: 'linear-gradient(135deg, rgba(23,60,44,0.05), rgba(197,106,43,0.05))', borderRadius: 'var(--radius-lg)', marginBottom: '2rem' }}>
      <h2>Ready to analyze your soil?</h2>
      <p className="text-muted" style={{ marginBottom: '1.5rem' }}>Join SoilWise and unlock AI-powered soil intelligence.</p>
      <Link to="/auth" className="btn btn-primary" style={{ fontSize: '1.1rem', padding: '0.75rem 2rem' }}>
        Get Started Free
      </Link>
    </div>
  </div>
);

const AuthPage = ({ setAuth }: { setAuth: (val: boolean) => void }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = isLogin ? await api.login(email, password) : await api.register(email, password);
      if (res.success) {
        session.set(res.data.access_token);
        setAuth(true);
        navigate('/analyze');
      } else {
        setError(res.message || 'Authentication failed');
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '500px', marginTop: '4rem' }}>
      <div className="card">
        <div className="card-header">
          <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
          <p className="text-muted">{isLogin ? 'Log in to continue your soil analysis' : 'Sign up to start analyzing soil'}</p>
        </div>
        <div className="card-body">
          {error && <div style={{ color: 'var(--color-danger)', marginBottom: '1rem', padding: '0.5rem', backgroundColor: 'rgba(201,68,61,0.1)', borderRadius: '4px' }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input type="email" required className="form-input" value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input type="password" required className="form-input" value={password} onChange={e => setPassword(e.target.value)} />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginBottom: '1rem' }} disabled={loading}>
              {loading ? 'Processing...' : (isLogin ? 'Log In' : 'Sign Up')}
            </button>
          </form>

          <div style={{ textAlign: 'center' }}>
            <button className="btn btn-outline" style={{ border: 'none' }} onClick={() => setIsLogin(!isLogin)}>
              {isLogin ? 'Need an account? Sign Up' : 'Already have an account? Log In'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const AnalysisPage = ({ setAnalysisContext }: { setAnalysisContext: (a: Analysis | null) => void }) => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [season, setSeason] = useState('Kharif');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [gradCamUrl, setGradCamUrl] = useState<string>('');

  const [aiSuggestions, setAiSuggestions] = useState<AiSuggestions | null>(null);
  const [aiSuggestionsLoading, setAiSuggestionsLoading] = useState(false);
  const [aiSuggestionsError, setAiSuggestionsError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setAnalysis(null);
      setRecommendations([]);
      setError('');
    }
  };

  const fetchAiSuggestions = async (soilType: string, seasonVal: string, props: unknown[]) => {
    setAiSuggestionsLoading(true);
    setAiSuggestionsError('');
    setAiSuggestions(null);
    try {
      const res = await api.aiSuggestions(soilType, seasonVal, props);
      if (res.success && res.data && !res.data.error) {
        setAiSuggestions(res.data);
      } else {
        setAiSuggestionsError(res.data?.error || res.message || 'Failed to generate AI suggestions');
      }
    } catch (err: any) {
      setAiSuggestionsError(err.message || 'Failed to generate AI suggestions');
    } finally {
      setAiSuggestionsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setAnalysis(null);
    setRecommendations([]);
    setGradCamUrl('');
    setAiSuggestions(null);
    setAiSuggestionsError('');

    try {
      const res = await api.analyze(file);
      if (res.success) {
        setAnalysis(res.data);
        setAnalysisContext(res.data);

        // Fetch recommendations with property context
        try {
          const recRes = await api.recommend(res.data.soil_type, season, res.data.property_ranges?.map(p => ({
            name: p.name,
            value: p.typical_value,
            unit: p.unit,
            source: 'REFERENCE_RANGE' as const,
          })) || []);
          if (recRes.success) setRecommendations(recRes.data);
        } catch (e) {
          console.warn("Could not load recommendations");
        }

        // Fetch AI Suggestions
        fetchAiSuggestions(
          res.data.soil_type,
          season,
          res.data.property_ranges?.map(p => ({
            name: p.name,
            typical_value: p.typical_value,
            value: p.typical_value,
            unit: p.unit,
            range: p.range,
          })) || []
        );

        // Fetch Grad-CAM
        try {
          const blob = await api.explanation(res.data.analysis_id);
          setGradCamUrl(URL.createObjectURL(blob));
        } catch (e) {
          console.warn("Could not load Grad-CAM explanation");
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze image');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h2 style={{ marginBottom: '1.5rem' }}>Analyze Your Soil</h2>
      <div className="grid grid-cols-2">
        {/* Left Col: Upload */}
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <h3>Upload Soil Image</h3>
            </div>
            <div className="card-body">
              <div className="upload-area" style={{ marginBottom: '1rem' }}>
                <input type="file" className="upload-input" accept="image/jpeg,image/png,image/webp" onChange={handleFileChange} />
                {preview ? (
                  <img src={preview} alt="Preview" style={{ maxWidth: '100%', maxHeight: '250px', objectFit: 'contain', borderRadius: 'var(--radius-sm)' }} />
                ) : (
                  <div>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📸</div>
                    <p style={{ fontWeight: 500 }}>Click or drag image here</p>
                    <p className="text-muted" style={{ fontSize: '0.8rem' }}>JPEG, PNG, WEBP · Max 8 MB</p>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Growing Season</label>
                <select className="form-select" value={season} onChange={e => setSeason(e.target.value)}>
                  <option value="Kharif">Kharif (Monsoon)</option>
                  <option value="Rabi">Rabi (Winter)</option>
                  <option value="Zaid">Zaid (Summer)</option>
                </select>
              </div>

              <button className="btn btn-primary" style={{ width: '100%', padding: '0.75rem' }} disabled={!file || loading} onClick={handleAnalyze}>
                {loading ? 'Analyzing…' : '🔬 Analyze Soil'}
              </button>
              {error && <p style={{ color: 'var(--color-danger)', marginTop: '0.5rem', fontSize: '0.9rem' }}>{error}</p>}
            </div>
          </div>

          {loading && (
            <div className="card">
              <div className="card-body" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                <div className="spinner"></div>
                <p style={{ marginTop: '1rem' }} className="text-muted">Our AI is analyzing the soil characteristics…</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Col: Results */}
        <div>
          {analysis && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* Primary Result */}
              <div className="card result-highlight">
                <div className="card-body">
                  <h2 className="text-primary" style={{ textTransform: 'capitalize', margin: 0, fontSize: '1.5rem' }}>
                    {analysis.soil_type.replace(/_/g, ' ')}
                  </h2>
                  <div style={{ marginTop: '0.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                      <span>AI Confidence</span>
                      <span style={{ fontWeight: 600 }}>{(analysis.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="meter-container">
                      <div className="meter-fill" style={{ width: `${analysis.confidence * 100}%`, backgroundColor: analysis.confidence > 0.8 ? 'var(--color-success)' : 'var(--color-warning)' }}></div>
                    </div>
                  </div>
                  {analysis.warning && <div className="badge badge-warning" style={{ marginTop: '0.75rem' }}>{analysis.warning}</div>}
                </div>
              </div>

              {/* Soil Parameters - Primary Feature */}
              <SoilPropertiesSection properties={analysis.property_ranges} soilType={analysis.soil_type} />

              {/* Crop Recommendations */}
              {recommendations.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <h4>🌾 Recommended Crops for {season}</h4>
                  </div>
                  <div className="card-body">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {recommendations.slice(0, 5).map((rec, i) => (
                        <div key={i} className="rec-card">
                          <div className="rec-card-header">
                            <strong style={{ fontSize: '1.05rem' }}>{rec.crop}</strong>
                            <span className={`badge ${rec.compatibility_score >= 80 ? 'badge-success' : rec.compatibility_score >= 50 ? 'badge-primary' : 'badge-warning'}`}>
                              {rec.compatibility_score}% match
                            </span>
                          </div>
                          <div className="meter-container" style={{ marginTop: '0.25rem' }}>
                            <div className="meter-fill" style={{
                              width: `${rec.compatibility_score}%`,
                              backgroundColor: rec.compatibility_score >= 80 ? 'var(--color-success)' : rec.compatibility_score >= 50 ? 'var(--color-primary)' : 'var(--color-warning)'
                            }} />
                          </div>
                          {rec.matched_factors.length > 0 && (
                            <div className="rec-factors">
                              {rec.matched_factors.map((f, j) => (
                                <span key={j} className="rec-factor-match">✓ {f}</span>
                              ))}
                            </div>
                          )}
                          {rec.limiting_factors.length > 0 && (
                            <div className="rec-factors">
                              {rec.limiting_factors.map((f, j) => (
                                <span key={j} className="rec-factor-limit">⚠ {f}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* AI-Powered Suggestions */}
              <AiSuggestionsSection
                suggestions={aiSuggestions}
                loading={aiSuggestionsLoading}
                error={aiSuggestionsError}
                onRetry={() => fetchAiSuggestions(
                  analysis.soil_type,
                  season,
                  analysis.property_ranges?.map(p => ({
                    name: p.name,
                    typical_value: p.typical_value,
                    value: p.typical_value,
                    unit: p.unit,
                    range: p.range,
                  })) || []
                )}
              />

              {/* Grad-CAM */}
              {gradCamUrl && (
                <div className="card">
                  <div className="card-header">
                    <h4>🔍 AI Focus Area</h4>
                    <p className="text-muted" style={{ fontSize: '0.8rem' }}>Heatmap showing which image regions influenced the prediction.</p>
                  </div>
                  <div className="card-body" style={{ textAlign: 'center' }}>
                    <img src={gradCamUrl} alt="Model Explanation" style={{ maxWidth: '100%', borderRadius: 'var(--radius-sm)' }} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const HistoryPage = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.history().then(res => {
      if (res.success) setHistory(res.data);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>Analysis History</h2>
        <button className="btn btn-primary" onClick={() => navigate('/analyze')}>New Analysis</button>
      </div>
      {loading ? <div className="spinner"></div> : (
        <div className="card">
          <div className="card-body" style={{ padding: 0 }}>
            {history.length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
                <p className="text-muted" style={{ marginBottom: '1rem' }}>No analyses yet. Start your first soil analysis!</p>
                <button className="btn btn-primary" onClick={() => navigate('/analyze')}>Analyze Soil</button>
              </div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Soil Type</th>
                    <th>Confidence</th>
                    <th>Model</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(item => (
                    <tr key={item.id}>
                      <td>{new Date(item.created_at).toLocaleDateString()}</td>
                      <td style={{ textTransform: 'capitalize', fontWeight: 500 }}>{item.soil_type.replace(/_/g, ' ')}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div className="meter-container" style={{ width: '60px', marginTop: 0 }}>
                            <div className="meter-fill" style={{ width: `${item.confidence * 100}%` }}></div>
                          </div>
                          <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{(item.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="text-muted" style={{ fontSize: '0.8rem' }}>{item.model_version}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const AboutPage = () => (
  <div className="container" style={{ maxWidth: '900px' }}>
    <div style={{ textAlign: 'center', padding: '2rem 0 3rem' }}>
      <h1 style={{ fontSize: '2.2rem' }}>About <span className="text-primary">SoilWise</span></h1>
      <p className="text-muted" style={{ fontSize: '1.1rem', maxWidth: '600px', margin: '0.5rem auto 0' }}>
        AI-powered soil intelligence for modern agriculture
      </p>
    </div>

    {/* What SoilWise Does */}
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="card-body">
        <h3 className="text-primary">What is SoilWise?</h3>
        <p style={{ marginBottom: '1.5rem' }}>
          SoilWise is an AI-powered platform that helps farmers, students, and agronomists understand their soil through
          image analysis. Upload a photo of your soil and receive instant classification, estimated soil properties,
          and tailored crop recommendations — all from your phone or computer.
        </p>

        <h3 className="text-primary" style={{ marginTop: '1.5rem' }}>What SoilWise Does</h3>
        <div className="grid grid-cols-2" style={{ marginTop: '1rem' }}>
          <div className="about-feature">
            <span className="about-feature-icon">📸</span>
            <div>
              <strong>AI Soil Classification</strong>
              <p className="text-muted">Identifies 7 Indian soil types using deep learning computer vision.</p>
            </div>
          </div>
          <div className="about-feature">
            <span className="about-feature-icon">🧪</span>
            <div>
              <strong>Soil Property Analysis</strong>
              <p className="text-muted">Estimates pH, NPK, moisture, organic carbon, and EC from ICAR reference data.</p>
            </div>
          </div>
          <div className="about-feature">
            <span className="about-feature-icon">🌾</span>
            <div>
              <strong>Crop Recommendations</strong>
              <p className="text-muted">Season-aware crop suggestions matched to your soil type and properties.</p>
            </div>
          </div>
          <div className="about-feature">
            <span className="about-feature-icon">📅</span>
            <div>
              <strong>Season-Aware Guidance</strong>
              <p className="text-muted">Supports Kharif, Rabi, and Zaid growing seasons.</p>
            </div>
          </div>
          <div className="about-feature">
            <span className="about-feature-icon">📋</span>
            <div>
              <strong>Soil Analysis History</strong>
              <p className="text-muted">Track and compare all your past analyses over time.</p>
            </div>
          </div>
          <div className="about-feature">
            <span className="about-feature-icon">💬</span>
            <div>
              <strong>Multilingual AI Assistant</strong>
              <p className="text-muted">Ask questions in English, Kannada, Tamil, Telugu, Hindi, or Malayalam.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* How It Works */}
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="card-body">
        <h3 className="text-primary">How It Works</h3>
        <div className="how-it-works-flow" style={{ marginTop: '1.5rem' }}>
          <div className="flow-step">
            <div className="flow-step-number">1</div>
            <div className="flow-step-icon">📸</div>
            <p className="flow-step-text">Upload</p>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">2</div>
            <div className="flow-step-icon">🔬</div>
            <p className="flow-step-text">Analyze</p>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">3</div>
            <div className="flow-step-icon">📊</div>
            <p className="flow-step-text">Understand</p>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">4</div>
            <div className="flow-step-icon">🌾</div>
            <p className="flow-step-text">Recommend</p>
          </div>
        </div>
      </div>
    </div>

    {/* Technology */}
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="card-body">
        <h3 className="text-primary">Technology</h3>
        <div className="grid grid-cols-2" style={{ marginTop: '1rem' }}>
          <div className="tech-item">
            <strong>🧠 Computer Vision</strong>
            <p className="text-muted">MobileNetV3-Small CNN trained on Indian soil datasets</p>
          </div>
          <div className="tech-item">
            <strong>⚡ FastAPI Backend</strong>
            <p className="text-muted">Python backend with SQLAlchemy and NVIDIA NIM integration</p>
          </div>
          <div className="tech-item">
            <strong>⚛️ React Frontend</strong>
            <p className="text-muted">Modern React 18 SPA with TypeScript and Vite</p>
          </div>
          <div className="tech-item">
            <strong>🌐 AI Assistant</strong>
            <p className="text-muted">Llama 3.1 via NVIDIA NIM for multilingual soil guidance</p>
          </div>
        </div>
      </div>
    </div>

    {/* Key Benefits */}
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="card-body">
        <h3 className="text-primary">Key Benefits</h3>
        <div className="grid grid-cols-3" style={{ marginTop: '1rem' }}>
          {[
            { icon: '⚡', text: 'Fast soil analysis' },
            { icon: '📊', text: 'Easy-to-understand results' },
            { icon: '🧪', text: 'Soil property dashboard' },
            { icon: '🌾', text: 'Crop recommendations' },
            { icon: '💬', text: 'Multilingual assistance' },
            { icon: '📋', text: 'Analysis history' },
          ].map((b, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', background: 'var(--color-bg)', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '1.3rem' }}>{b.icon}</span>
              <span style={{ fontWeight: 500 }}>{b.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>

    {/* Soil Types */}
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="card-body">
        <h3 className="text-primary">Soil Types We Identify</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginTop: '1rem' }}>
          {['Alluvial Soil', 'Arid Soil', 'Black Soil', 'Laterite Soil', 'Mountain Soil', 'Red Soil', 'Yellow Soil'].map(s => (
            <span key={s} className="badge badge-primary" style={{ fontSize: '0.85rem', padding: '0.4rem 0.75rem' }}>{s}</span>
          ))}
        </div>
      </div>
    </div>
  </div>
);

// ==========================================
// Layout & Router
// ==========================================

const ProtectedRoute = ({ children, isAuth, demoMode }: { children: React.ReactNode, isAuth: boolean, demoMode: boolean }) => {
  return (isAuth || demoMode) ? <>{children}</> : <Navigate to="/auth" replace />;
};

export default function App() {
  const [isAuth, setIsAuth] = useState(!!session.get());
  const [analysisContext, setAnalysisContext] = useState<Analysis | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    api.health().then(res => {
      if (res.success && res.data?.demo_mode) {
        setDemoMode(true);
      }
    }).catch(() => {});
  }, []);

  const canAccess = isAuth || demoMode;

  const handleLogout = () => {
    api.logout().catch(console.error);
    session.clear();
    setIsAuth(false);
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="container header-content">
          <Link to="/" className="brand">
            🌱 SoilWise
          </Link>
          <nav className="nav">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/about" className="nav-link">About</Link>
            {canAccess && <Link to="/analyze" className="nav-link">Analyze</Link>}
            {canAccess && <Link to="/history" className="nav-link">History</Link>}

            {isAuth ? (
              <button className="btn btn-outline" onClick={handleLogout}>Logout</button>
            ) : !demoMode ? (
              <Link to="/auth" className="btn btn-primary">Login</Link>
            ) : null}
          </nav>
        </div>
      </header>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={isAuth ? <Navigate to="/analyze" /> : <AuthPage setAuth={setIsAuth} />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/analyze" element={<ProtectedRoute isAuth={isAuth} demoMode={demoMode}><AnalysisPage setAnalysisContext={setAnalysisContext} /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute isAuth={isAuth} demoMode={demoMode}><HistoryPage /></ProtectedRoute>} />
        </Routes>
      </main>

      <footer className="footer">
        <div className="container">
          <p>© {new Date().getFullYear()} SoilWise Intelligence · AI-powered soil analysis for modern agriculture.</p>
        </div>
      </footer>

      {/* Floating Chatbot */}
      <Chatbot analysisContext={analysisContext} />
    </div>
  );
}
