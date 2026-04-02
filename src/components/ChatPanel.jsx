import React, { useEffect, useRef } from 'react';

export default function ChatPanel({ history }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  return (
    <div className="chat-panel">
      <div className="chat-panel-header">
        <div className="chat-panel-title">
          <span className="chat-icon">💬</span>
          <span>Conversation</span>
        </div>
        <span className="chat-count">{history.length}</span>
      </div>

      <div className="chat-messages">
        {history.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">🚀</div>
            <div className="chat-empty-title">Ready to Chat</div>
            <div className="chat-empty-desc">Send a command to start talking with Nova</div>
          </div>
        ) : (
          history.map((item, idx) => (
            <div key={idx} className={`chat-message ${item.type}`}>
              <div className="chat-bubble user-bubble">
                <span className="chat-badge user-badge">YOU</span>
                <span className="chat-text">{item.query}</span>
              </div>
              <div className={`chat-bubble nova-bubble ${item.type === 'pending' ? 'typing' : ''}`}>
                <span className="chat-badge nova-badge">NOVA</span>
                {item.type === 'pending' ? (
                  <span className="typing-dots">
                    <span /><span /><span />
                  </span>
                ) : (
                  <span className="chat-text">{item.response}</span>
                )}
              </div>
              {item.timestamp && item.type !== 'pending' && (
                <div className="chat-time">{new Date(item.timestamp).toLocaleTimeString()}</div>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
