import React from 'react';

export default function Header({ isRunning, backendOnline, onShowFeatures }) {
  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">
          <span className="header-logo-letter">N</span>
          <div className="header-logo-ring" />
        </div>
        <div>
          <div className="header-title">NOVA</div>
          <div className="header-subtitle">AI Voice Assistant</div>
        </div>
      </div>

      <div className="header-center">
        <div className="header-indicators">
          <div className={`indicator ${backendOnline ? 'online' : 'offline'}`}>
            <span className="indicator-dot" />
            <span className="indicator-label">{backendOnline ? 'Backend Online' : 'Backend Offline'}</span>
          </div>
          <div className={`indicator ${isRunning ? 'online' : ''}`}>
            <span className="indicator-dot" />
            <span className="indicator-label">{isRunning ? 'Listening' : 'Standby'}</span>
          </div>
        </div>
      </div>

      <div className="header-actions">
        <button className="header-btn" onClick={onShowFeatures} id="features-btn">
          <span>🎯</span>
          <span>All Commands</span>
        </button>
      </div>
    </header>
  );
}
