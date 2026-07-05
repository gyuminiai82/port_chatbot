"use client";

import { useState, useRef, useEffect } from 'react';
import styles from './page.module.css';

interface MessageSource {
  content: string;
  metadata: any;
}

interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: MessageSource[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'bot', content: '안녕하세요! 무엇을 도와드릴까요?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content })
      });

      if (!response.ok) throw new Error('API request failed');
      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: data.response || 'Error processing response',
        sources: data.sources || undefined
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: '서버와 통신하는 중 오류가 발생했습니다.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className={styles.main}>
      <div className={styles.chatContainer}>
        <header className={styles.header}>
          <div className={styles.headerTitle}>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ filter: 'drop-shadow(0 0 4px rgba(16, 185, 129, 0.5))' }}>
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M8 9l2 6 2-6 2 6 2-6"></path>
              <line x1="7" y1="12" x2="17" y2="12"></line>
              <line x1="7" y1="15" x2="17" y2="15"></line>
            </svg>
            소득세법 챗봇
          </div>
        </header>

        <div className={styles.messageList}>
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`${styles.messageWrapper} ${msg.role === 'user' ? styles.messageWrapperUser : styles.messageWrapperBot}`}
            >
              <div className={`${styles.message} ${msg.role === 'user' ? styles.messageUser : styles.messageBot}`}>
                {msg.content}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className={styles.sourcesContainer}>
                  <div className={styles.sourcesTitle}>참고 문헌</div>
                  <div className={styles.sourcesList}>
                    {msg.sources.map((source, idx) => (
                      <div key={idx} className={styles.sourceItem}>
                        {source.metadata?.source && (
                          <div className={styles.sourceMeta}>
                            [{source.metadata.source}{source.metadata.page ? ` - p.${source.metadata.page}` : ''}]
                          </div>
                        )}
                        <div className={styles.sourceContent}>
                          {source.content.length > 100 ? source.content.substring(0, 100) + '...' : source.content}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className={`${styles.messageWrapper} ${styles.messageWrapperBot}`}>
              <div className={`${styles.message} ${styles.messageBot} ${styles.typingIndicator}`}>
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className={styles.inputForm}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지를 입력하세요..."
            className={styles.input}
            disabled={isLoading}
          />
          <button type="submit" className={styles.sendButton} disabled={isLoading || !input.trim()}>
            전송
          </button>
        </form>
      </div>
    </main>
  );
}
