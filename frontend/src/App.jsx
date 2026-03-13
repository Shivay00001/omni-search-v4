import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Home as HomeIcon, Library as LibraryIcon, Compass as DiscoverIcon, 
  Settings as SettingsIcon, BookOpen, Plus, Sparkles, Zap
} from 'lucide-react';

import ChatView from './components/ChatView';
import Library from './components/Library';
import Discover from './components/Discover';
import Settings from './components/Settings';

function AppContent() {
  const [conversationId, setConversationId] = useState(null);
  const [insights, setInsights] = useState([]);
  const [sources, setSources] = useState([]);
  const [prefillQuery, setPrefillQuery] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const handleSelectConv = (id) => {
    setConversationId(id);
    navigate('/');
  };

  const startNewChat = () => {
    setConversationId(null);
    setInsights([]);
    setSources([]);
    navigate('/');
  };

  return (
    <div className="app-container">
      {/* Sidebar Panel */}
      <aside className="sidebar">
        <div style={{ marginBottom: '32px', padding: '0 8px', cursor: 'pointer' }} onClick={startNewChat}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--accent-color)', letterSpacing: '-0.5px' }}>
            Omni <span style={{ fontSize: '0.7rem', verticalAlign: 'middle', opacity: 0.6, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>V4</span>
          </h2>
          <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: '2px' }}>Agentic Intelligence</p>
        </div>

        <nav style={{ flex: 1 }}>
          <Link to="/" className={`nav-item ${location.pathname === '/' ? 'active' : ''}`} onClick={() => setConversationId(null)}>
            <HomeIcon size={20} /> <span style={{ fontWeight: '500' }}>Home</span>
          </Link>
          <Link to="/discover" className={`nav-item ${location.pathname === '/discover' ? 'active' : ''}`}>
            <DiscoverIcon size={20} /> <span style={{ fontWeight: '500' }}>Discover</span>
          </Link>
          <Link to="/library" className={`nav-item ${location.pathname === '/library' ? 'active' : ''}`}>
            <LibraryIcon size={20} /> <span style={{ fontWeight: '500' }}>Library</span>
          </Link>
        </nav>

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
          <button onClick={startNewChat} className="nav-item" style={{ width: '100%', background: 'rgba(59, 130, 246, 0.1)', border: '1px dashed var(--accent-color)', marginBottom: '16px' }}>
            <Plus size={18} /> <span>New Research</span>
          </button>
          <Link to="/settings" className={`nav-item ${location.pathname === '/settings' ? 'active' : ''}`}>
            <SettingsIcon size={20} /> <span style={{ fontWeight: '500' }}>Settings</span>
          </Link>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={
            <ChatView 
              conversationId={conversationId} 
              setConversationId={setConversationId}
              setInsights={setInsights}
              setSources={setSources}
              prefillQuery={prefillQuery}
              setPrefillQuery={setPrefillQuery}
            />
          } />
          <Route path="/discover" element={
            <Discover onSelectTopic={(t) => {
              setPrefillQuery(t);
              setConversationId(null);
              navigate('/');
            }} />
          } />
          <Route path="/library" element={<Library onSelectConv={handleSelectConv} />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>

      {/* Secondary Panel (Insights & Sources) */}
      <aside className="secondary-pane">
        {/* Insights Section */}
        {insights.length > 0 && (
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Sparkles size={14} color="var(--accent-color)" />
              <h3 style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: '800', letterSpacing: '1px' }}>Extracted Facts</h3>
            </div>
            {insights.map((fact, i) => (
              <div key={i} className="insight-fact-card animate-slide-up" style={{ animationDelay: `${i * 0.08}s` }}>
                {fact}
              </div>
            ))}
          </div>
        )}

        {/* Sources Section */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <BookOpen size={16} color="var(--text-secondary)" />
          <h3 style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '800' }}>
            Sources {sources.length > 0 && <span style={{ color: 'var(--accent-color)', marginLeft: '4px' }}>({sources.length})</span>}
          </h3>
        </div>

        {sources.length > 0 ? (
          <div>
            {sources.map((source, i) => {
              const sourceUrl = source.url || '#';
              let hostname = '';
              try { hostname = new URL(sourceUrl).hostname; } catch { hostname = sourceUrl; }
              
              return (
                <a key={i} href={sourceUrl} target="_blank" rel="noreferrer" className="source-pill animate-slide-up" style={{ animationDelay: `${i * 0.08}s` }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flex: 1, minWidth: 0 }}>
                      {source.index && (
                        <span className="source-score">[{source.index}]</span>
                      )}
                      <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {source.title || 'Source'}
                      </span>
                    </div>
                    {source.score !== undefined && source.score > 0 && (
                      <span className="source-score">
                        <Zap size={10} /> {source.score}
                      </span>
                    )}
                  </div>
                  {source.snippet && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '6px', lineHeight: '1.4', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {source.snippet}
                    </p>
                  )}
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <img 
                      src={`https://www.google.com/s2/favicons?domain=${hostname}&sz=16`} 
                      style={{ width: 12, height: 12, borderRadius: 2 }} 
                      alt=""
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    {hostname}
                  </div>
                </a>
              );
            })}
          </div>
        ) : (
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontStyle: 'italic', textAlign: 'center', padding: '40px 0' }}>
            Sources and intelligence facts will appear here during research.
          </div>
        )}
      </aside>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
