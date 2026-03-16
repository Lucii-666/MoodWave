import { useState } from 'react';

const SUGGESTIONS = [
  'Melancholic late night jazz',
  'High energy workout',
  'Chill Sunday morning vibes',
  'Romantic dinner ambiance',
  'Euphoric festival energy',
  'Peaceful acoustic serenity',
];

export default function MoodInput({ onSubmit, loading }) {
  const [mood, setMood] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mood.trim() && !loading) {
      onSubmit(mood.trim());
    }
  };

  const handleSuggestion = (text) => {
    setMood(text);
    if (!loading) onSubmit(text);
  };

  return (
    <div className="mood-input">
      <form onSubmit={handleSubmit}>
        <div className="mood-input__wrapper">
          <input
            id="mood-input-field"
            className="mood-input__field"
            type="text"
            placeholder="Describe a mood... e.g. 'melancholic late night jazz'"
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            disabled={loading}
            autoComplete="off"
          />
          <button
            id="mood-submit-btn"
            type="submit"
            className={`mood-input__btn ${loading ? 'mood-input__btn--loading' : ''}`}
            disabled={!mood.trim() || loading}
          >
            <span className="mood-input__btn-icon">{loading ? '⟳' : '✦'}</span>
            {loading ? 'Searching…' : 'Discover'}
          </button>
        </div>
      </form>

      <div className="mood-input__suggestions">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            className="mood-input__suggestion"
            onClick={() => handleSuggestion(s)}
            disabled={loading}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
