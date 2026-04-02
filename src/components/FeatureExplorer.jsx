import React, { useState } from 'react';

const categories = [
  {
    name: 'System', icon: '⚙️', color: '#6366f1',
    commands: [
      { cmd: 'Open Chrome', desc: 'Launch apps' },
      { cmd: 'Volume up', desc: 'Control volume' },
      { cmd: 'Battery status', desc: 'Check battery' },
      { cmd: 'System info', desc: 'PC diagnostics' },
      { cmd: 'Lock screen', desc: 'Lock PC' },
      { cmd: 'CPU usage', desc: 'Processor stats' },
      { cmd: 'IP address', desc: 'Network info' },
    ]
  },
  {
    name: 'Web', icon: '🌐', color: '#06b6d4',
    commands: [
      { cmd: 'Search Google for...', desc: 'Google search' },
      { cmd: 'Search YouTube for...', desc: 'YouTube search' },
      { cmd: 'Wikipedia...', desc: 'Look up topics' },
      { cmd: 'Open website...', desc: 'Visit any site' },
    ]
  },
  {
    name: 'Media', icon: '🎵', color: '#8b5cf6',
    commands: [
      { cmd: 'Play music', desc: 'Toggle playback' },
      { cmd: 'Next song', desc: 'Skip track' },
      { cmd: 'Previous song', desc: 'Go back' },
    ]
  },
  {
    name: 'Utils', icon: '🛠️', color: '#f59e0b',
    commands: [
      { cmd: 'Take screenshot', desc: 'Capture screen' },
      { cmd: 'Set timer 5 min', desc: 'Countdown' },
      { cmd: 'Calculate 5+3', desc: 'Math' },
      { cmd: 'Take note', desc: 'Save notes' },
    ]
  },
  {
    name: 'Info', icon: '📚', color: '#10b981',
    commands: [
      { cmd: 'Weather', desc: 'Forecasts' },
      { cmd: 'Tell me a joke', desc: 'Humor' },
      { cmd: 'Fun fact', desc: 'Trivia' },
      { cmd: 'Motivational quote', desc: 'Inspiration' },
      { cmd: 'Flip a coin', desc: 'Random' },
    ]
  },
  {
    name: 'AI Chat', icon: '🤖', color: '#ec4899',
    commands: [
      { cmd: 'Tell me about...', desc: 'Ask anything' },
      { cmd: 'Explain...', desc: 'Deep answers' },
      { cmd: 'How to...', desc: 'Get advice' },
    ]
  },
];

export default function FeatureExplorer({ onCommandClick, compact }) {
  const [activeCategory, setActiveCategory] = useState(0);

  return (
    <div className={`feature-explorer ${compact ? 'compact' : ''}`}>
      <div className="fe-header">
        <span className="fe-title">{compact ? 'Commands' : '🎯 All Commands'}</span>
        <span className="fe-count">45+ commands</span>
      </div>

      {/* Category tabs */}
      <div className="fe-tabs">
        {categories.map((cat, i) => (
          <button
            key={i}
            className={`fe-tab ${activeCategory === i ? 'active' : ''}`}
            onClick={() => setActiveCategory(i)}
            style={{ '--tab-color': cat.color }}
          >
            <span className="fe-tab-icon">{cat.icon}</span>
            <span className="fe-tab-name">{cat.name}</span>
          </button>
        ))}
      </div>

      {/* Command list */}
      <div className="fe-commands">
        {categories[activeCategory].commands.map((cmd, i) => (
          <button
            key={i}
            className="fe-cmd"
            onClick={() => onCommandClick?.(cmd.cmd)}
            style={{ '--cmd-delay': `${i * 0.04}s`, '--cmd-color': categories[activeCategory].color }}
          >
            <span className="fe-cmd-text">{cmd.cmd}</span>
            <span className="fe-cmd-desc">{cmd.desc}</span>
            <span className="fe-cmd-arrow">→</span>
          </button>
        ))}
      </div>
    </div>
  );
}
