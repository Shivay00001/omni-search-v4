import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Zap, Globe, Sparkles, Languages, Database } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8089';

export default function Settings() {
  const [languages, setLanguages] = useState([]);
  const [defaultLang, setDefaultLang] = useState(localStorage.getItem('omni_default_lang') || 'en');

  useEffect(() => {
    axios.get(`${API_BASE}/languages`)
      .then(res => setLanguages(res.data))
      .catch(() => {});
  }, []);

  const handleLangChange = (e) => {
    setDefaultLang(e.target.value);
    localStorage.setItem('omni_default_lang', e.target.value);
  };

  return (
    <div className="search-container">
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '8px' }}>Preferences</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Configure your Omni Engine experience.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Search Intelligence */}
        <div className="discover-card" style={{ cursor: 'default' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <Zap size={20} color="var(--accent-color)" />
            <h3 style={{ fontSize: '1.1rem' }}>Search Intelligence</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Current Mode: <strong style={{ color: 'var(--text-primary)' }}>Multi-Step Linear Research</strong><br />
            Uses RL-driven sub-query expansion with agentic task decomposition for deeper insights.
          </p>
        </div>

        {/* Language Settings */}
        <div className="discover-card" style={{ cursor: 'default' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <Languages size={20} color="#8b5cf6" />
            <h3 style={{ fontSize: '1.1rem' }}>Default Language</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
            Responses will be translated to your preferred language. Supports {languages.length || 29} languages.
          </p>
          <select 
            value={defaultLang} 
            onChange={handleLangChange}
            className="lang-select"
            style={{ width: '100%', padding: '10px 14px', fontSize: '0.95rem' }}
          >
            {languages.map(lang => (
              <option key={lang.code} value={lang.code}>
                {lang.flag} {lang.name} ({lang.native})
              </option>
            ))}
          </select>
          
          {/* Language badges */}
          {languages.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '16px' }}>
              {languages.slice(0, 15).map(lang => (
                <span 
                  key={lang.code}
                  style={{ 
                    fontSize: '0.72rem', 
                    padding: '4px 8px', 
                    borderRadius: '6px',
                    background: lang.code === defaultLang ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${lang.code === defaultLang ? 'var(--accent-color)' : 'var(--border-color)'}`,
                    color: lang.code === defaultLang ? 'var(--accent-color)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => { setDefaultLang(lang.code); localStorage.setItem('omni_default_lang', lang.code); }}
                >
                  {lang.flag} {lang.native}
                </span>
              ))}
              {languages.length > 15 && (
                <span style={{ fontSize: '0.72rem', padding: '4px 8px', color: 'var(--text-secondary)' }}>
                  +{languages.length - 15} more
                </span>
              )}
            </div>
          )}
        </div>

        {/* Export Capabilities */}
        <div className="discover-card" style={{ cursor: 'default' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <Database size={20} color="#10b981" />
            <h3 style={{ fontSize: '1.1rem' }}>Export & Storage</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Export research sessions in <strong style={{ color: 'var(--text-primary)' }}>PDF</strong>, <strong style={{ color: 'var(--text-primary)' }}>DOCX</strong>, or <strong style={{ color: 'var(--text-primary)' }}>Markdown</strong> formats.<br />
            All data stored locally in SQLite for full privacy.
          </p>
        </div>

        {/* Privacy */}
        <div className="discover-card" style={{ cursor: 'default' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <Shield size={20} color="#f59e0b" />
            <h3 style={{ fontSize: '1.1rem' }}>Privacy & Security</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Local-first architecture. Your research data never leaves your machine.<br />
            RL feedback loop improves results using <strong style={{ color: 'var(--text-primary)' }}>your</strong> preferences only.
          </p>
        </div>

        {/* Competitive Features */}
        <div className="discover-card" style={{ cursor: 'default' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <Sparkles size={20} color="var(--accent-color)" />
            <h3 style={{ fontSize: '1.1rem' }}>Intelligence Features</h3>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            <div>✅ Multi-step agentic research with sub-query expansion</div>
            <div>✅ Focus Modes: Academic, News, Code, General</div>
            <div>✅ Inline source citations with transparency</div>
            <div>✅ 29+ language translation system</div>
            <div>✅ RL-powered result reranking</div>
            <div>✅ Real-time trending discovery</div>
            <div>✅ Related question generation</div>
            <div>✅ Multi-format export (PDF, DOCX, MD)</div>
          </div>
        </div>
      </div>
    </div>
  );
}
