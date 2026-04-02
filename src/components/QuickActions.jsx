import React from 'react';

const quickCommands = [
  { label: '🕐 Time', cmd: 'what time is it' },
  { label: '🔋 Battery', cmd: 'battery status' },
  { label: '😂 Joke', cmd: 'tell me a joke' },
  { label: '📸 Screenshot', cmd: 'take screenshot' },
  { label: '🌤️ Weather', cmd: 'weather' },
  { label: '💡 Fun Fact', cmd: 'fun fact' },
  { label: '🎵 Play Music', cmd: 'play music' },
  { label: '🔊 Volume Up', cmd: 'volume up' },
];

export default function QuickActions({ onCommand }) {
  return (
    <div className="quick-actions">
      <div className="quick-actions-label">Quick Actions</div>
      <div className="quick-actions-grid">
        {quickCommands.map((q, i) => (
          <button
            key={i}
            className="quick-chip"
            onClick={() => onCommand(q.cmd)}
            style={{ '--chip-delay': `${i * 0.05}s` }}
          >
            {q.label}
          </button>
        ))}
      </div>
    </div>
  );
}
