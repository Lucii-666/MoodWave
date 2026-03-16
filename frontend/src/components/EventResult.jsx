export default function EventResult({ events, source }) {
  if (!events || !events.length) {
    return (
      <div className="no-events" id="no-events-message">
        <div className="no-events__icon">🎵</div>
        <h3 className="no-events__title">No Upcoming Events Found</h3>
        <p className="no-events__text">
          The agent searched Ticketmaster, Songkick, and Bandsintown but couldn't find upcoming events.
          Try another artist!
        </p>
      </div>
    );
  }

  return (
    <div className="event-result" id="event-results-panel">
      <div className="event-result__header">
        <div className="event-result__header-icon">🎫</div>
        <div className="event-result__header-text">
          <h3>Events Found!</h3>
          <p>Source: {source || 'Live Web'} · {events.length} event{events.length > 1 ? 's' : ''}</p>
        </div>
      </div>
      
      <div className="event-result__items">
        {events.map((event, i) => (
          <div key={i} className="event-item" id={`event-item-${i}`}>
            <div className="event-item__details">
              <h4>{event.event_name || 'Live Event'}</h4>
              <div className="event-item__meta">
                <span>📅 {event.date || 'TBA'}</span>
                {event.time && <span>🕐 {event.time}</span>}
                <span>📍 {event.venue || 'Venue TBA'}</span>
                {event.city && <span>🌍 {event.city}</span>}
              </div>
            </div>
            <div className="event-item__price">
              <span className="event-item__price-value">
                {event.price || 'Price TBA'}
              </span>
              {event.ticket_url && (
                <a
                  href={event.ticket_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="event-item__buy-btn"
                >
                  Buy Tickets →
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
