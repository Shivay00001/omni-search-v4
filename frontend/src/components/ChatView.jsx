import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Globe, ArrowUp, Loader2, Layers, BookOpen, 
  ThumbsUp, ThumbsDown, Copy, Check, Download,
  ChevronDown, FileText, FileType, FileCode,
  GraduationCap, Newspaper, Code, Compass,
  Sparkles, ArrowRight
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8089';

const FOCUS_MODES = [
  { id: 'general', label: 'General', icon: <Compass size={14} />, emoji: '🌐' },
  { id: 'academic', label: 'Academic', icon: <GraduationCap size={14} />, emoji: '📚' },
  { id: 'news', label: 'News', icon: <Newspaper size={14} />, emoji: '📰' },
  { id: 'code', label: 'Code', icon: <Code size={14} />, emoji: '💻' },
];

export default function ChatView({ conversationId, setConversationId, setInsights, setSources, prefillQuery, setPrefillQuery }) {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [currentSummary, setCurrentSummary] = useState('');
  const [researchSteps, setResearchSteps] = useState([]);
  const [targetLang, setTargetLang] = useState('en');
  const [focusMode, setFocusMode] = useState('general');
  const [languages, setLanguages] = useState([]);
  const [relatedQuestions, setRelatedQuestions] = useState([]);
  const [feedbackMap, setFeedbackMap] = useState({});
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const chatEndRef = useRef(null);
  const searchRef = useRef(null);

  // Fetch supported languages on mount
  useEffect(() => {
    axios.get(`${API_BASE}/languages`)
      .then(res => setLanguages(res.data))
      .catch(() => {
        setLanguages([
          { code: 'en', name: 'English', native: 'English', flag: '🇺🇸' },
          { code: 'hi', name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
          { code: 'es', name: 'Spanish', native: 'Español', flag: '🇪🇸' },
        ]);
      });
  }, []);

  // Auto-search on prefill from Discover
  useEffect(() => {
    if (prefillQuery) {
      const q = prefillQuery;
      setPrefillQuery('');
      setQuery(q);
      // Trigger search after state update
      setTimeout(() => {
        if (searchRef.current) searchRef.current(q);
      }, 100);
    }
  }, [prefillQuery]);

  // Load existing conversation
  useEffect(() => {
    if (conversationId) {
      axios.get(`${API_BASE}/conversations/${conversationId}`)
        .then(res => {
          setMessages(res.data.messages);
          setRelatedQuestions([]);
        });
    } else {
      setMessages([]);
      setRelatedQuestions([]);
    }
  }, [conversationId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentSummary, researchSteps]);

  const handleSearch = useCallback(async (directQuery) => {
    const userQuery = directQuery || query;
    if (!userQuery.trim() || isSearching) return;

    setQuery('');
    setIsSearching(true);
    setCurrentSummary('');
    setResearchSteps([]);
    setRelatedQuestions([]);
    
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);

    // Parallel fetch for sources sidebar
    axios.get(`${API_BASE}/test_search?q=${encodeURIComponent(userQuery)}`)
      .then(res => setSources(res.data))
      .catch(err => console.error("Sources fetch error", err));

    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: userQuery, 
          conversation_id: conversationId, 
          stream: true,
          target_lang: targetLang,
          focus_mode: focusMode
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let fullText = '';
      let buffer = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Parse special markers
        while (buffer.includes('__CONV_ID__:')) {
          const match = buffer.match(/__CONV_ID__:(\d+)\n/);
          if (match) {
            setConversationId(parseInt(match[1]));
            buffer = buffer.replace(match[0], '');
          } else break;
        }

        while (buffer.includes('__THOUGHT__:')) {
          const match = buffer.match(/__THOUGHT__:(.*?)\n/);
          if (match) {
            setResearchSteps(prev => [...prev, match[1]]);
            buffer = buffer.replace(match[0], '');
          } else break;
        }

        while (buffer.includes('__SOURCES__:')) {
          const match = buffer.match(/__SOURCES__:(.*?)\n/);
          if (match) {
            try {
              const srcs = JSON.parse(match[1]);
              setSources(srcs);
            } catch (e) { /* partial */ }
            buffer = buffer.replace(match[0], '');
          } else break;
        }

        while (buffer.includes('__INSIGHTS__:')) {
          const match = buffer.match(/__INSIGHTS__:(.*?)\n/);
          if (match) {
            try {
              setInsights(JSON.parse(match[1]));
            } catch (e) { /* partial */ }
            buffer = buffer.replace(match[0], '');
          } else break;
        }

        while (buffer.includes('__ERROR__:')) {
          const match = buffer.match(/__ERROR__:(.*?)\n/);
          if (match) {
            fullText += `\n\n**Error:** ${match[1]}`;
            setIsSearching(false);
            buffer = buffer.replace(match[0], '');
          } else break;
        }

        // Summary content
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim() || line.startsWith('__')) continue;
          setCurrentSummary(prev => prev + line + '\n');
          fullText += line + '\n';
        }
      }

      // Finalize
      setMessages(prev => [...prev, { role: 'assistant', content: fullText }]);
      setCurrentSummary('');
      setResearchSteps([]);

      // Fetch related questions
      axios.post(`${API_BASE}/related_questions`, { query: userQuery, context: fullText.slice(0, 500) })
        .then(res => setRelatedQuestions(res.data))
        .catch(() => {});

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'assistant', content: "Error: Failed to reach the intelligence server." }]);
    } finally {
      setIsSearching(false);
    }
  }, [query, isSearching, conversationId, targetLang, focusMode, setConversationId, setSources, setInsights]);

  // Expose handleSearch for prefill
  useEffect(() => {
    searchRef.current = handleSearch;
  }, [handleSearch]);

  const handleCopy = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleFeedback = (index, type, query) => {
    setFeedbackMap(prev => ({ ...prev, [index]: type }));
    axios.post(`${API_BASE}/feedback`, { 
      query: query || '', 
      url: 'response', 
      score: type === 'up' ? 1.0 : -1.0 
    }).catch(() => {});
  };

  const handleExport = (format) => {
    if (!conversationId) return;
    setShowExportMenu(false);
    const url = `${API_BASE}/conversations/${conversationId}/export?format=${format}`;
    
    // For all formats, use a hidden link to trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = `research_${conversationId}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Render markdown with citation links
  const renderWithCitations = (content, sources) => {
    return (
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          // Override text rendering to add citation links
          p: ({ children, ...props }) => {
            return <p {...props}>{processCitations(children, sources)}</p>;
          },
          li: ({ children, ...props }) => {
            return <li {...props}>{processCitations(children, sources)}</li>;
          }
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  const processCitations = (children, sources) => {
    if (!children || !sources || sources.length === 0) return children;
    
    return React.Children.map(children, child => {
      if (typeof child !== 'string') return child;
      
      // Match [1], [2], etc.
      const parts = child.split(/(\[\d+\])/g);
      return parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (match) {
          const idx = parseInt(match[1]) - 1;
          const src = sources[idx];
          if (src) {
            return (
              <a 
                key={i}
                href={src.url} 
                target="_blank" 
                rel="noreferrer"
                className="citation-link"
                title={`${src.title}\n${src.url}`}
              >
                {match[1]}
              </a>
            );
          }
        }
        return part;
      });
    });
  };

  // Get last user query for feedback
  const getLastUserQuery = () => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') return messages[i].content;
    }
    return '';
  };

  return (
    <div className="search-container">
      {!conversationId && messages.length === 0 && (
        <div style={{ textAlign: 'center', marginTop: '12vh', marginBottom: '50px' }}>
          <h1 style={{ fontSize: '3rem', fontWeight: '800', letterSpacing: '-1px', background: 'linear-gradient(135deg, #f8fafc, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Insight begins here.
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', marginTop: '12px' }}>
            Agentic Intelligence &bull; Deep Research &bull; 29 Languages
          </p>

          {/* Focus Mode Chips */}
          <div className="focus-mode-bar" style={{ justifyContent: 'center', marginTop: '32px' }}>
            {FOCUS_MODES.map(mode => (
              <button
                key={mode.id}
                className={`focus-chip ${focusMode === mode.id ? 'active' : ''}`}
                onClick={() => setFocusMode(mode.id)}
              >
                {mode.emoji} {mode.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Top Bar: Export + Language */}
      {conversationId && (
        <div className="export-bar animate-slide-up">
          {/* Export Dropdown */}
          <div className="export-dropdown">
            <button 
              className="nav-item" 
              onClick={() => setShowExportMenu(!showExportMenu)}
              style={{ padding: '6px 14px', fontSize: '0.85rem' }}
            >
              <Download size={15} /> Export <ChevronDown size={12} />
            </button>
            {showExportMenu && (
              <div className="export-menu">
                <button className="export-menu-item" onClick={() => handleExport('md')}>
                  <FileCode size={16} color="var(--accent-color)" /> Markdown (.md)
                </button>
                <button className="export-menu-item" onClick={() => handleExport('pdf')}>
                  <FileText size={16} color="#ef4444" /> PDF Document (.pdf)
                </button>
                <button className="export-menu-item" onClick={() => handleExport('docx')}>
                  <FileType size={16} color="#3b82f6" /> Word Document (.docx)
                </button>
              </div>
            )}
          </div>

          {/* Focus Mode (compact) */}
          <div style={{ display: 'flex', gap: '4px', marginLeft: 'auto' }}>
            {FOCUS_MODES.map(mode => (
              <button
                key={mode.id}
                className={`focus-chip ${focusMode === mode.id ? 'active' : ''}`}
                onClick={() => setFocusMode(mode.id)}
                style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              >
                {mode.emoji}
              </button>
            ))}
          </div>

          {/* Language */}
          <select 
            value={targetLang} 
            onChange={(e) => setTargetLang(e.target.value)}
            className="lang-select"
          >
            {languages.map(lang => (
              <option key={lang.code} value={lang.code}>
                {lang.flag} {lang.native}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Chat Messages */}
      <div className="chat-container">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'message-user' : 'message-assistant'}>
            {m.role === 'user' ? (
              <h3>{m.content}</h3>
            ) : (
              <div>
                <div className="summary-card">
                  {renderWithCitations(m.content, [])}
                </div>
                {/* Response Actions */}
                <div className="response-actions">
                  <button 
                    className={`action-btn ${copiedIndex === i ? 'copied' : ''}`}
                    onClick={() => handleCopy(m.content, i)}
                  >
                    {copiedIndex === i ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy</>}
                  </button>
                  <button 
                    className={`action-btn ${feedbackMap[i] === 'up' ? 'liked' : ''}`}
                    onClick={() => handleFeedback(i, 'up', getLastUserQuery())}
                  >
                    <ThumbsUp size={14} />
                  </button>
                  <button 
                    className={`action-btn ${feedbackMap[i] === 'down' ? 'disliked' : ''}`}
                    onClick={() => handleFeedback(i, 'down', getLastUserQuery())}
                  >
                    <ThumbsDown size={14} />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Live Research Progress */}
        {isSearching && (
          <div className="message-assistant">
            {researchSteps.map((step, i) => (
              <div key={i} className="thought-step animate-slide-up">
                <Layers size={14} color="var(--accent-color)" />
                <span>{step}</span>
              </div>
            ))}
            {currentSummary ? (
              <div className="summary-card animate-slide-up">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentSummary}</ReactMarkdown>
              </div>
            ) : (
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            )}
          </div>
        )}

        {/* Related Questions */}
        {relatedQuestions.length > 0 && !isSearching && (
          <div className="related-questions animate-slide-up">
            {relatedQuestions.map((q, i) => (
              <button 
                key={i} 
                className="related-chip"
                onClick={() => {
                  setQuery(q);
                  handleSearch(q);
                }}
              >
                <Sparkles size={13} color="var(--accent-color)" />
                <span>{q}</span>
                <ArrowRight size={13} color="var(--text-secondary)" />
              </button>
            ))}
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Floating Search Bar */}
      <div style={{ position: 'fixed', bottom: '28px', left: 'var(--sidebar-width)', right: 'var(--secondary-width)', padding: '0 20px', zIndex: 10 }}>
        {/* Initial language selector (when no conversation) */}
        {!conversationId && messages.length === 0 && (
          <div style={{ maxWidth: '800px', margin: '0 auto 8px', display: 'flex', justifyContent: 'flex-end' }}>
            <select 
              value={targetLang} 
              onChange={(e) => setTargetLang(e.target.value)}
              className="lang-select"
              style={{ fontSize: '0.8rem' }}
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.native}
                </option>
              ))}
            </select>
          </div>
        )}
        <form onSubmit={(e) => { e.preventDefault(); handleSearch(); }} className="search-bar" style={{ maxWidth: '800px', margin: '0 auto' }}>
          <Globe color="var(--accent-color)" size={18} />
          <textarea
            className="search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Follow up or ask a new question..."
            rows={1}
            style={{ resize: 'none' }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSearch();
              }
            }}
          />
          <button type="submit" disabled={isSearching} className="search-btn-pro">
            {isSearching ? <Loader2 className="animate-spin" size={18} /> : <ArrowUp size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}
