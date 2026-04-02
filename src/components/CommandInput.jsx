import React, { useState } from 'react';

export default function CommandInput({ onSend, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <div className="command-input-container">
      <form onSubmit={handleSubmit} className="command-input-wrapper">
        <div className="input-glow" />
        <input
          type="text"
          className="command-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder='Try "open chrome" or "tell me a joke"'
          disabled={disabled}
          id="command-text-input"
          autoComplete="off"
        />
        <button
          type="submit"
          className="command-send-btn"
          disabled={disabled || !input.trim()}
          id="command-send-button"
        >
          <span className="send-icon">↑</span>
        </button>
      </form>
    </div>
  );
}
