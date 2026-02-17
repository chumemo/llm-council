import { useState, useEffect } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <img src="/logo.png" alt="Logo" style={{ height: '40px', marginBottom: '10px' }} />
        <h1>Consejo CrediBusiness LLM</h1>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + Nueva conversación
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">Aún no hay conversaciones</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${conv.id === currentConversationId ? 'active' : ''
                }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">
                {conv.title || 'Nueva conversación'}
              </div>
              <div className="conversation-meta">
                {conv.message_count} mensajes
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
