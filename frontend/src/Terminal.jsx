import React, { useState, useEffect, useRef } from 'react';

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0; // Convert to 32-bit integer
  }
  return hash;
}

const Terminal = () => {
  const [output, setOutput] = useState('');
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [messageHashes, setMessageHashes] = useState(new Set());
  const [lastMessageTime, setLastMessageTime] = useState(0);
  const wsRef = useRef(null);
  const terminalRef = useRef(null);
  const inputRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const GITHUB_URL = 'https://github.com/ajeevani/f1-ml-simulator';

  const connectToBackend = () => {
    const wsUrl = process.env.NODE_ENV === 'production' 
      ? 'wss://f1-ml-simulator-production.up.railway.app/ws'
      : 'ws://localhost:8000/ws';
    
    console.log('🔗 Connecting to:', wsUrl);

    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Connected to Railway backend');
      setConnected(true);
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket connection failed:', error);
      setConnected(false);
    };

    ws.onclose = (event) => {
      console.log('🔌 Connection closed:', event.code, event.reason);
      setConnected(false);
    };

    ws.onmessage = (event) => {
      const currentTime = Date.now();
      if (currentTime - lastMessageTime < 50) {
        return;
      }
      setLastMessageTime(currentTime);

      try {
        const message = JSON.parse(event.data);
        if (message.type === 'output') {
          const data = message.data;
          const messageHash = hashString(data);

          if (messageHashes.has(messageHash)) {
            console.log('Skipping duplicate message');
            return;
          }

          // Add to seen messages (keep only recent ones)
          setMessageHashes(prev => {
            const newHashes = new Set(prev);
            newHashes.add(messageHash);
            // Keep only last 100 hashes to prevent memory growth
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
            setMessageHashes(new Set([messageHash])); // Reset with current message
          } else {
            setOutput(prev => prev + processedData);
          }
        }
      } catch (error) {
        // Handle non-JSON messages
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

  useEffect(() => {
    if (connected && inputRef.current) {
      inputRef.current.focus();
    }
  }, [connected]);

  const handleInput = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();

      if (!connected) {
        setOutput(prev => prev + '❌ Not connected to backend\n');
        return;
      }

      if (!input || !input.trim()) {
        return;
      }

      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setOutput(prev => prev + '❌ WebSocket connection not ready\n');
        connectToBackend();
        return;
      }

      try {
        // Show user input in terminal
        setOutput(prev => prev + `> ${input.trim()}\n`);

        // Send to backend
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
    }
  };

  const handleManualReconnect = () => {
    setMessageHashes(new Set()); // Reset message tracking
    connectToBackend();
  };

  const openSourceCode = () => {
    window.open(GITHUB_URL, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="terminal-window">
      <div className="window-header">
        <div className="window-title">🏎️ F1 Professional ML Simulator v2.0</div>
        <div className="window-controls">
          <button 
            className="source-code-btn" 
            onClick={openSourceCode}
            title="View source code on GitHub"
          >
            <span>📁</span>
            <span>Source</span>
          </button>
          <button className="control-btn minimize">−</button>
          <button className="control-btn maximize">□</button>
          <button className="control-btn close">✕</button>
        </div>
      </div>
      
      <div className="terminal-body" ref={terminalRef}>
        <pre className="terminal-content">{output}</pre>
        
        {connected && (
          <div className="input-line">
            <span className="prompt"></span>
            <input
              ref={inputRef}
              className="terminal-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleInput}
              autoFocus
            />
          </div>
        )}
        
        {!connected && (
          <div className="connection-status">
            <p>🔌 F1 Simulator Backend Disconnected</p>
            <p>Start backend: <code>python backend/server.py</code></p>
            <button className="reconnect-btn" onClick={handleManualReconnect}>
              🔄 Reconnect
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Terminal;
