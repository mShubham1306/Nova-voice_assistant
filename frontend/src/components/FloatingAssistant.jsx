import React, { useState, useEffect, useRef } from 'react';
import ChatPanel from './ChatPanel';
import CommandInput from './CommandInput';
import QuickActions from './QuickActions';

export default function FloatingAssistant({
  history,
  onSendCommand,
  isProcessing,
  onCommand,
  isOpen: externalIsOpen,
  onClose: externalOnClose,
  // ── Voice props from App.jsx single pipeline ──
  voiceState,
  onMicToggle,
  interimText,
  speechSupported,
}) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const prevLength = useRef(history.length);

  const isOpen    = externalIsOpen !== undefined ? externalIsOpen : internalOpen;
  const closePanel = () => { if (externalOnClose) externalOnClose(); else setInternalOpen(false); };
  const openPanel  = () => { if (!externalIsOpen) setInternalOpen(true); setHasNewMessage(false); };

  // Flash notification dot on new message while closed
  useEffect(() => {
    if (history.length > prevLength.current && !isOpen) setHasNewMessage(true);
    prevLength.current = history.length;
  }, [history, isOpen]);

  const isListening = voiceState === 'listening';

  return (
    <>
      {/* Floating Action Button */}
      <button
        className={`fab-btn ${hasNewMessage ? 'has-notification' : ''} ${isOpen ? 'fab-hidden' : ''}`}
        onClick={openPanel}
        aria-label="Open assistant"
        id="fab-assistant-btn"
      >
        <span className="fab-icon">💬</span>
        <span className="fab-pulse" />
        {hasNewMessage && <span className="fab-dot" />}
      </button>

      {/* Slide-in Panel */}
      <div className={`floating-panel ${isOpen ? 'open' : ''}`}>
        <div className="fp-header">
          <div className="fp-title-row">
            <span className="fp-logo">N</span>
            <div>
              <div className="fp-title">Nova Assistant</div>
              <div className="fp-subtitle">
                {voiceState === 'listening'  && '🔴 Listening...'}
                {voiceState === 'processing' && '⚡ Processing...'}
                {voiceState === 'speaking'   && '🔊 Speaking...'}
                {voiceState === 'idle'       && 'AI Voice Companion'}
              </div>
            </div>
          </div>
          <button className="fp-close" onClick={closePanel} aria-label="Close panel">✕</button>
        </div>

        <div className="fp-chat-area">
          <ChatPanel history={history} />

          {/* Live interim transcript while user speaks */}
          {interimText && (
            <div className="fp-interim-bar">
              <span className="fp-interim-icon">🎙</span>
              <span className="fp-interim-text">{interimText}</span>
              <span className="fp-interim-cursor">|</span>
            </div>
          )}
        </div>

        <div className="fp-input-area">
          <div className="fp-input-row">
            <CommandInput onSend={onSendCommand} disabled={isProcessing} />
            {speechSupported && (
              <button
                className={`fp-mic-btn ${isListening ? 'listening' : ''} ${voiceState === 'processing' ? 'processing' : ''}`}
                onClick={onMicToggle}
                aria-label="Voice input"
                title={isListening ? 'Listening — click to stop' : 'Click to speak'}
              >
                {isListening ? (
                  <span className="fp-mic-wave">
                    <span /><span /><span /><span /><span />
                  </span>
                ) : voiceState === 'processing' ? (
                  <span className="fp-mic-spin">⚡</span>
                ) : (
                  '🎤'
                )}
              </button>
            )}
          </div>
          <div className="fp-quick">
            <QuickActions onCommand={onCommand} />
          </div>
        </div>
      </div>

      {isOpen && <div className="fp-overlay" onClick={closePanel} />}
    </>
  );
}
