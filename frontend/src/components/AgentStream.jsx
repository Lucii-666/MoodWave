import { useEffect, useRef } from 'react';

function getStepIcon(step) {
  const type = step.type || '';
  const content = (step.content || step.message || '').toLowerCase();
  
  if (type === 'error') return '❌';
  if (type === 'complete' || type === 'result') return '✅';
  if (content.includes('navigat') || content.includes('go to') || content.includes('open')) return '🌐';
  if (content.includes('search') || content.includes('find') || content.includes('look')) return '🔍';
  if (content.includes('click') || content.includes('dismiss') || content.includes('cookie') || content.includes('popup')) return '👆';
  if (content.includes('wait') || content.includes('load')) return '⏳';
  if (content.includes('extract') || content.includes('read') || content.includes('pars')) return '📋';
  if (content.includes('ticket') || content.includes('price')) return '🎫';
  if (content.includes('fallback') || content.includes('try')) return '🔄';
  return '🤖';
}

function getStepClass(step) {
  const type = step.type || '';
  if (type === 'error') return 'agent-step--error';
  if (type === 'complete' || type === 'result') return 'agent-step--success';
  if (type === 'action' || type === 'tool_use') return 'agent-step--action';
  return 'agent-step--thinking';
}

export default function AgentStream({ steps, isStreaming, artistName }) {
  const scrollRef = useRef(null);

  // Auto-scroll to bottom as new steps arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps]);

  if (!steps.length && !isStreaming) return null;

  return (
    <div className="agent-stream" id="agent-stream-panel">
      <div className="agent-stream__header">
        <div className="agent-stream__title">
          <span>🤖</span>
          <span>TinyFish Agent — Searching for {artistName}</span>
        </div>
        {isStreaming && (
          <div className="agent-stream__live-badge">
            <span className="agent-stream__live-dot"></span>
            LIVE
          </div>
        )}
      </div>
      
      <div className="agent-stream__steps" ref={scrollRef}>
        {steps.map((step, i) => {
          const content = step.content || step.message || step.text || JSON.stringify(step);
          return (
            <div key={i} className={`agent-step ${getStepClass(step)}`}>
              <span className="agent-step__icon">{getStepIcon(step)}</span>
              <span>{typeof content === 'string' ? content : JSON.stringify(content)}</span>
            </div>
          );
        })}
        {isStreaming && (
          <div className="agent-step agent-step--thinking">
            <span className="agent-step__icon">⏳</span>
            <span>Agent is working…</span>
          </div>
        )}
      </div>
    </div>
  );
}
