import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Compass, Sparkles } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8089';

export default function Discover({ onSelectTopic }) {
  const [topics, setTopics] = useState([]);

  useEffect(() => {
    axios.get(`${API_BASE}/discover`)
      .then(res => {
        setTopics(res.data);
      });
  }, []);

  return (
    <div className="search-container">
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '8px' }}>Global Intelligence</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Trending research topics across the web.</p>
      </div>

      <div className="discover-grid">
        {topics.map(t => (
          <div key={t.id} className="discover-card animate-slide-up" onClick={() => onSelectTopic(t.topic)}>
            <span style={{ fontSize: '0.7rem', color: 'var(--accent-color)', fontWeight: '700', textTransform: 'uppercase' }}>{t.category}</span>
            <h3 style={{ margin: '8px 0', fontSize: '1.2rem' }}>{t.topic}</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              <Sparkles size={14} />
              <span>Full Agentic Analysis</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
