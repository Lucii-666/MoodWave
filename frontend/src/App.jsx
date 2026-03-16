import { useState, useCallback } from 'react';
import MoodInput from './components/MoodInput';
import ArtistCard from './components/ArtistCard';
import AgentStream from './components/AgentStream';
import EventResult from './components/EventResult';

const API_BASE = '';

export default function App() {
  // Recommendation state
  const [artists, setArtists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentMood, setCurrentMood] = useState('');

  // Agent state
  const [agentSteps, setAgentSteps] = useState([]);
  const [agentStreaming, setAgentStreaming] = useState(false);
  const [agentArtist, setAgentArtist] = useState('');

  // Event results
  const [eventResult, setEventResult] = useState(null);

  // ── Mood → Artist Recommendation ──────────────────────────────────────
  const handleMoodSubmit = useCallback(async (mood) => {
    setLoading(true);
    setCurrentMood(mood);
    setArtists([]);
    setAgentSteps([]);
    setEventResult(null);

    try {
      const resp = await fetch(`${API_BASE}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mood, top_k: 3 }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `API error ${resp.status}`);
      }

      const data = await resp.json();
      setArtists(data.artists || []);
    } catch (err) {
      console.error('Recommend error:', err);
      setAgentSteps([{ type: 'error', content: `Failed to get recommendations: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Artist → TinyFish Agent (SSE) ─────────────────────────────────────
  const handleFindEvents = useCallback(async (artistName) => {
    setAgentSteps([]);
    setAgentStreaming(true);
    setAgentArtist(artistName);
    setEventResult(null);

    try {
      const resp = await fetch(`${API_BASE}/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ artist: artistName }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Agent error ${resp.status}`);
      }

      // Read SSE stream
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') continue;

            try {
              const event = JSON.parse(dataStr);
              setAgentSteps((prev) => [...prev, event]);

              // Check if this is the final result with events
              if (event.events || event.status === 'found' || event.status === 'no_upcoming_events') {
                setEventResult(event);
              }
            } catch {
              setAgentSteps((prev) => [...prev, { type: 'raw', content: dataStr }]);
            }
          }
        }
      }
    } catch (err) {
      console.error('Agent error:', err);
      setAgentSteps((prev) => [
        ...prev,
        { type: 'error', content: `Agent failed: ${err.message}` },
      ]);
    } finally {
      setAgentStreaming(false);
    }
  }, []);

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="header">
        <div className="header__logo">
          <span className="header__icon">🎵</span>
          <h1 className="header__title">MoodWave</h1>
        </div>
        <p className="header__subtitle">
          AI-powered music curation meets live event discovery.
          Describe a mood — we'll match artists from 1M songs and find real tickets on the web.
        </p>
        <div className="header__badge">
          <span className="header__badge-dot"></span>
          Powered by TinyFish Web Agent · 1M Song Dataset
        </div>
      </header>

      {/* ── Mood Input ─────────────────────────────────────────────────── */}
      <MoodInput onSubmit={handleMoodSubmit} loading={loading} />

      {/* ── Artist Results ─────────────────────────────────────────────── */}
      {artists.length > 0 && (
        <>
          <h2 className="section-title">
            <span className="section-title__icon">🎤</span>
            Top Artists for "{currentMood}"
          </h2>
          <div className="artists-grid">
            {artists.map((artist, i) => (
              <ArtistCard
                key={artist.artist}
                artist={artist}
                rank={i + 1}
                onFindEvents={handleFindEvents}
                agentLoading={agentStreaming}
              />
            ))}
          </div>
        </>
      )}

      {/* ── Agent Stream ───────────────────────────────────────────────── */}
      <AgentStream
        steps={agentSteps}
        isStreaming={agentStreaming}
        artistName={agentArtist}
      />

      {/* ── Event Results ──────────────────────────────────────────────── */}
      {eventResult && !agentStreaming && (
        <>
          <h2 className="section-title">
            <span className="section-title__icon">🎫</span>
            Live Events
          </h2>
          <EventResult
            events={eventResult.events || []}
            source={eventResult.source}
          />
        </>
      )}
    </div>
  );
}
