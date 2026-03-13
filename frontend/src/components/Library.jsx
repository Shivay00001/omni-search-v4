import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, ChevronRight } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8089';

export default function Library({ onSelectConv }) {
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    axios.get(`${API_BASE}/conversations`)
      .then(res => setConversations(res.data));
  }, []);

  return (
    <div className="search-container">
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '8px' }}>Knowledge Library</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Review and resume your previous research sessions.</p>
      </div>

      <div style={{ marginTop: '24px' }}>
        {conversations.map(c => (
          <div key={c.id} className="history-card animate-slide-up" onClick={() => onSelectConv(c.id)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '4px' }}>{c.title || `Research Session #${c.id}`}</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <Clock size={12} />
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              <ChevronRight size={20} color="var(--text-secondary)" />
            </div>
          </div>
        ))}

        {conversations.length === 0 && (
          <div style={{ textAlign: 'center', padding: '100px 0', opacity: 0.5 }}>
            <p>Your research history will appear here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
