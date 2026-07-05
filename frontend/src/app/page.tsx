"use client";

import { useState, useRef, useEffect } from 'react';
import styles from './page.module.css';

interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
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
        content: data.response || 'Error processing response'
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
            <div className={styles.statusDot}></div>
            AI Chatbot
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
