export default function ArtistCard({ artist, rank, onFindEvents, agentLoading }) {
  return (
    <div className="artist-card" id={`artist-card-${rank}`}>
      <div className="artist-card__rank">#{rank}</div>
      <h3 className="artist-card__name">{artist.artist}</h3>
      <div className="artist-card__tags">
        <span className="artist-card__tag artist-card__tag--genre">
          🎵 {artist.genre}
        </span>
        <span className="artist-card__tag artist-card__tag--emotion">
          💜 {artist.primary_emotion}
        </span>
        <span className="artist-card__tag">
          {artist.song_count} songs
        </span>
      </div>
      <div className="artist-card__footer">
        <span className="artist-card__score">
          Match: <span className="artist-card__score-value">{(artist.score * 100).toFixed(1)}%</span>
        </span>
        <button
          className="artist-card__action"
          onClick={() => onFindEvents(artist.artist)}
          disabled={agentLoading}
          id={`find-events-btn-${rank}`}
        >
          🔍 Find Events
        </button>
      </div>
    </div>
  );
}
