import React, { useState, useRef, useEffect } from 'react';
import './Terminal.css';

export default function Terminal() {
  const [output, setOutput] = useState('');
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const inputRef = useRef(null);

  // Prevent body scroll on mobile keyboard
  useEffect(() => {
    const handleFocus = () => document.body.style.overflow = 'hidden';
    const handleBlur = () => document.body.style.overflow = '';
    if (inputRef.current) {
      inputRef.current.addEventListener('focus', handleFocus);
      inputRef.current.addEventListener('blur', handleBlur);
    }
    return () => {
      if (inputRef.current) {
        inputRef.current.removeEventListener('focus', handleFocus);
        inputRef.current.removeEventListener('blur', handleBlur);
      }
    };
  }, []);

  // Simulate backend connection for demo; replace with actual logic in your app
  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
      setConnected(true);
      setOutput('Welcome to F1 ML Simulator!\nAvailable Tracks:\nMonaco\nSilverstone\nMonza\nSpa\nSuzuka\n');
    }, 1000);
  }, []);

  // Actual send logic
  const handleSend = () => {
    if (!input.trim()) return;
    // Replace with actual backend send logic:
    setOutput(prev => prev + '\n> ' + input);
    setInput('');
    // On real backend, send 'input', then update output when response arrives
  };

  // Enter key triggers send
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSend();
  };

  // Responsive: show labels if window > 700px
  const [showLabels, setShowLabels] = useState(window.innerWidth > 700);
  useEffect(() => {
    const resize = () => setShowLabels(window.innerWidth > 700);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  return (
    <div className="terminal-card">
      <div className="terminal-header">
        <span className="terminal-title">{showLabels ? "F1 ML Simulator" : "F1 ML"}</span>
        <button
          className="icon-btn"
          title="Source Code"
          onClick={() => window.open('https://github.com/ajeevani/f1-ml-simulator', '_blank')}
        >
          <span role="img" aria-label="Source">📁</span>
          {showLabels && <span className="btn-label">Source</span>}
        </button>
      </div>
      <div className="terminal-main">
        {loading ? (
          <div className="terminal-loading">
            <span className="loader"></span>
            <span>⏳ Waiting for Render backend connection...</span>
          </div>
        ) : (
          <div className="terminal-output">
            {output.split('\n').map((line, i) => (
              <div key={i} className="terminal-line">{line}</div>
            ))}
          </div>
        )}
      </div>
      {connected && (
        <div className="terminal-inputbar">
          <input
            ref={inputRef}
            className="terminal-input"
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type command..."
            autoFocus
            enterKeyHint="send"
          />
          <button className="icon-btn send-btn" title="Send" onClick={handleSend}>
            <span role="img" aria-label="Send">➤</span>
            {showLabels && <span className="btn-label">Send</span>}
          </button>
        </div>
      )}
    </div>
  );
}