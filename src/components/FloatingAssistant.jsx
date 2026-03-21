import React, { useState, useEffect, useRef, useCallback } from 'react';
import ChatPanel from './ChatPanel';
import CommandInput from './CommandInput';
import QuickActions from './QuickActions';

export default function FloatingAssistant({ history, onSendCommand, isProcessing, onCommand }) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const prevLength = useRef(history.length);
  const recognitionRef = useRef(null);

  // Flash notification dot on new message
  useEffect(() => {
    if (history.length > prevLength.current && !isOpen) {
      setHasNewMessage(true);
    }
    prevLength.current = history.length;
  }, [history, isOpen]);

  // Init speech recognition for the chat panel mic button
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-IN';
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setIsListening(false);
        onSendCommand(transcript);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, [onSendCommand]);

  const handleMicClick = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    if (isListening) {
      recognition.abort();
      setIsListening(false);
    } else {
      try {
        recognition.start();
        setIsListening(true);
      } catch (e) {
        setIsListening(false);
      }
    }
  }, [isListening]);

  const handleOpen = () => {
    setIsOpen(true);
    setHasNewMessage(false);
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        className={`fab-btn ${hasNewMessage ? 'has-notification' : ''} ${isOpen ? 'fab-hidden' : ''}`}
        onClick={handleOpen}
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
            <span className="fp-title">Nova Assistant</span>
          </div>
          <button className="fp-close" onClick={() => setIsOpen(false)} aria-label="Close panel">✕</button>
        </div>

        <div className="fp-chat-area">
          <ChatPanel history={history} />
        </div>

        <div className="fp-input-area">
          <div className="fp-input-row">
            <CommandInput onSend={onSendCommand} disabled={isProcessing} />
            <button
              className={`fp-mic-btn ${isListening ? 'listening' : ''}`}
              onClick={handleMicClick}
              aria-label="Voice input"
              title={isListening ? 'Listening... click to stop' : 'Click to speak'}
            >
              {isListening ? '🔴' : '🎤'}
            </button>
          </div>
          <div className="fp-quick">
            <QuickActions onCommand={onCommand} />
          </div>
        </div>
      </div>

      {/* Overlay */}
      {isOpen && <div className="fp-overlay" onClick={() => setIsOpen(false)} />}
    </>
  );
}
