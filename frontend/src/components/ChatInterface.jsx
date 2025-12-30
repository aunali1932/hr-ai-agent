import { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import MessageBubble from './MessageBubble';
import InputBox from './InputBox';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load session_id from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('chat_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  // Load chat history when session_id is available
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!sessionId) return;
      
      setLoadingHistory(true);
      try {
        const response = await api.get(`/api/chat/history/${sessionId}`);
        const historyMessages = response.data.messages || [];
        
        // Convert history format to message format
        const formattedMessages = [];
        historyMessages.forEach((item) => {
          formattedMessages.push({
            role: 'user',
            content: item.message,
          });
          formattedMessages.push({
            role: 'assistant',
            content: item.response,
            intent: item.intent,
          });
        });
        
        setMessages(formattedMessages);
      } catch (error) {
        console.error('Error loading chat history:', error);
        // If history doesn't exist or error, just continue with empty messages
      } finally {
        setLoadingHistory(false);
      }
    };

    loadChatHistory();
  }, [sessionId]);

  const handleSendMessage = async (message) => {
    if (!message.trim()) return;

    // Add user message
    const userMessage = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await api.post('/api/chat', {
        message,
        session_id: sessionId,
      });

      // Update session ID if provided and save to localStorage
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
        localStorage.setItem('chat_session_id', response.data.session_id);
      }

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        intent: response.data.intent,
        data: response.data.data,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loadingHistory && (
          <div className="text-center text-gray-500 mt-8">
            <p>Loading conversation history...</p>
          </div>
        )}
        {!loadingHistory && messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg font-semibold mb-2">Welcome to HR AI Agent!</p>
            <p>Ask me about company policies or request leave.</p>
            <p className="text-sm mt-4">Try: "What is the work from home policy?" or "I need to take leave tomorrow"</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3 max-w-xs">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <InputBox onSend={handleSendMessage} disabled={loading} />
    </div>
  );
};

export default ChatInterface;


