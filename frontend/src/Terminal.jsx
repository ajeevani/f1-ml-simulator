import React, { useState, useEffect, useRef } from 'react';
import './Terminal.css';

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

const Terminal = () => {
  const [output, setOutput] = useState('');
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [renderColdStart, setRenderColdStart] = useState(true);
  const [messageHashes, setMessageHashes] = useState(new Set());
  const [lastMessageTime, setLastMessageTime] = useState(0);
  const [inputFocused, setInputFocused] = useState(false);
  
  const wsRef = useRef(null);
  const terminalRef = useRef(null);
  const inputRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  const GITHUB_URL = 'https://github.com/ajeevani/f1-ml-simulator';

  const connectToBackend = () => {
    setLoading(true);
    const wsUrl = process.env.NODE_ENV === 'production' 
      ? 'wss://f1-ml-simulator.onrender.com/ws'
      : 'ws://localhost:8001/ws';
    
    console.log('🔗 Connecting to:', wsUrl);
    
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('✅ Connected to backend');
      setConnected(true);
      setLoading(false);
    };
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket connection failed:', error);
      setConnected(false);
      setLoading(false);
    };
    
    ws.onclose = (event) => {
      console.log('🔌 Connection closed:', event.code, event.reason);
      setConnected(false);
      setLoading(false);
    };
    
    ws.onmessage = (event) => {
      const currentTime = Date.now();
      if (currentTime - lastMessageTime < 50) return;
      
      setLastMessageTime(currentTime);
      setRenderColdStart(false); // Hide cold start message on first output
      
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'output') {
          const data = message.data;
          const messageHash = hashString(data);
          
          if (messageHashes.has(messageHash)) {
            console.log('Skipping duplicate message');
            return;
          }
          
          setMessageHashes(prev => {
            const newHashes = new Set(prev);
            newHashes.add(messageHash);
            if (newHashes.size > 100) {
              const hashArray = Array.from(newHashes);
              return new Set(hashArray.slice(-50));
            }
            return newHashes;
          });
          
          let processedData = data;
          
          // Add race prompt if missing
          const isRaceEnd = (
            data.includes('🏆') && 
            (data.includes('VICTORY!') || data.includes('WINS!') || data.includes('CHAMPION!'))
          );
          
          if (isRaceEnd && !output.includes('Race another championship? (y/n):')) {
            processedData = data + '\n\n🏁 Race another championship? (y/n): ';
          }
          
          // Smart terminal clearing
          const shouldClear = (
            data.includes('F1 PROFESSIONAL CHAMPIONSHIP RACE - LIGHTS OUT!') ||
            data.includes('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀') ||
            data.includes('🏁 TRACK & WEATHER SELECTION') ||
            data.includes('Available F1 Circuits:') ||
            (data.includes('🚀 Initializing F1 Professional Simulator...') && output.length > 100)
          );
          
          if (shouldClear) {
            console.log('🧹 Clearing terminal for fresh start');
            setOutput(processedData);
            setMessageHashes(new Set([messageHash]));
          } else {
            setOutput(prev => prev + processedData);
          }
        }
      } catch (error) {
        const messageHash = hashString(event.data);
        if (!messageHashes.has(messageHash)) {
          setOutput(prev => prev + event.data);
          setMessageHashes(prev => new Set([...prev, messageHash]));
        }
      }
    };
  };

  useEffect(() => {
    connectToBackend();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.onopen = null;
        wsRef.current.onmessage = null;
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);

  const handlePromptClick = () => {
    if (inputRef.current) {
      inputRef.current.focus();
      setInputFocused(true);
    }
  };

  const handleInputFocus = () => setInputFocused(true);
  const handleInputBlur = () => setInputFocused(false);

  const sendInput = () => {
    if (!connected) {
      setOutput(prev => prev + '❌ Not connected to backend\n');
      return;
    }
    
    if (!input || !input.trim()) return;
    
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setOutput(prev => prev + '❌ WebSocket connection not ready\n');
      connectToBackend();
      return;
    }
    
    try {
      setOutput(prev => prev + `> ${input.trim()}\n`);
      wsRef.current.send(JSON.stringify({ 
        type: 'input', 
        data: input.trim() 
      }));
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
      setOutput(prev => prev + `❌ Send error: ${error.message}\n`);
      connectToBackend();
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      sendInput();
    }
  };

  const handleReconnect = () => {
    setOutput('');
    setMessageHashes(new Set());
    setConnected(false);
    setLoading(true);
    setRenderColdStart(true);
    connectToBackend();
  };

  const openGitHub = () => {
    window.open(GITHUB_URL, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="terminal-container">
      <div className="terminal-window">
        {/* Header */}
        <div className="terminal-header">
          <div className="window-controls">
            <span className="control close"></span>
            <span className="control minimize"></span>
            <span className="control maximize"></span>
          </div>
          <div className="terminal-title">
            <i className="fas fa-flag-checkered"></i>
            <span className="title-text">F1 ML Simulator</span>
          </div>
          <div className="header-actions">
            <button className="action-btn" onClick={openGitHub} title="View Source Code">
              <i className="fab fa-github"></i>
              <span className="btn-text">Source</span>
            </button>
            <button className="action-btn" onClick={handleReconnect} title="Reconnect">
              <i className="fas fa-sync-alt"></i>
              <span className="btn-text">Reset</span>
            </button>
          </div>
        </div>

        {/* Terminal Body */}
        <div className="terminal-body" ref={terminalRef}>
          {/* Cold Start Loading */}
          {renderColdStart && (
            <div className="cold-start-banner">
              <div className="loading-spinner"></div>
              <div className="loading-text">
                <div className="loading-title">🚀 Starting F1 Simulator...</div>
                <div className="loading-subtitle">
                  Render is warming up the engine • This may take 30-60 seconds
                </div>
              </div>
            </div>
          )}

          {/* Connection Status */}
          {!renderColdStart && !connected && (
            <div className="connection-status error">
              <i className="fas fa-exclamation-triangle"></i>
              <span>Connection lost • Click reset to reconnect</span>
            </div>
          )}

          {/* Terminal Output */}
          {output && (
            <div className="terminal-output">
              <pre className="output-text">{output}</pre>
            </div>
          )}

          {/* Input Prompt */}
          {connected && !renderColdStart && (
            <>
              <div className="input-break-line"></div>
              
              <div className="terminal-prompt" onClick={handlePromptClick}>
                <span className="prompt-symbol">></span>
                <span className={`cursor ${inputFocused ? 'blink' : ''}`}>|</span>
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onFocus={handleInputFocus}
                  onBlur={handleInputBlur}
                  className="prompt-input"
                  placeholder="Enter command..."
                  autoComplete="off"
                  spellCheck="false"
                />
                <button className="send-btn" onClick={sendInput} title="Send Command">
                  <i className="fas fa-paper-plane"></i>
                </button>
              </div>
              
              {/* Break line after input */}
              <div className="input-break-line"></div>
            </>
          )}
        </div>

        {/* Status Bar */}
        <div className="status-bar">
          <div className="status-left">
            <span className={`connection-indicator ${connected ? 'connected' : 'disconnected'}`}>
              <i className={`fas ${connected ? 'fa-circle' : 'fa-circle'}`}></i>
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="status-right">
            <span className="status-text">F1 Professional Championship</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Terminal;
