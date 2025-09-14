import React, { useState, useRef, useEffect } from 'react';
import './Terminal.css';

const GITHUB_URL = "https://github.com/ajeevani/f1-ml-simulator";

export default function Terminal() {
  // States
  const [output, setOutput] = useState('');
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeInput, setActiveInput] = useState(false);
  const inputRef = useRef(null);

  // Responsive: show labels if window > 700px
  const [showLabels, setShowLabels] = useState(window.innerWidth > 700);
  useEffect(() => {
    const resize = () => setShowLabels(window.innerWidth > 700);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

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
    // Simulate loading from Render cold start
    setTimeout(() => {
      setConnected(true);
      setLoading(false);
      setOutput('Welcome to F1 ML Simulator!\nAvailable Tracks:\nMonaco\nSilverstone\nMonza\nSpa\nSuzuka\n');
    }, 1800);
  }, []);

  // Render loading banner at top until real output arrives
  const showRenderBanner = loading || !output;

  // Actual send logic
  const handleSend = () => {
    if (!input.trim()) return;
    setOutput(prev => prev + '\n> ' + input);
    setInput('');
    setActiveInput(false);
    // TODO: Replace with actual backend send logic
  };

  // Enter key triggers send
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSend();
  };

  // Click prompt to focus input
  const handlePromptClick = () => {
    setActiveInput(true);
    setTimeout(() => {
      inputRef.current && inputRef.current.focus();
    }, 0);
  };

  return (
    <div className="terminal-outer">
      {showRenderBanner && (
        <div className="render-banner">
          <span className="loader"></span>
          <span>Connecting to Render backend...</span>
        </div>
      )}
      <div className="terminal-main-card">
        <div className="terminal-header">
          <div className="terminal-title">{showLabels ? "F1 ML Simulator" : "F1 ML"}</div>
          <button
            className="icon-btn"
            title="Source Code"
            onClick={() => window.open(GITHUB_URL, '_blank')}
          >
            <span role="img" aria-label="Source">📁</span>
            {showLabels && <span className="btn-label">Source</span>}
          </button>
        </div>
        <div className="terminal-body">
          <div className="terminal-output-area">
            {(output || loading) ? (
              output.split('\n').map((line, i) => (
                <div key={i} className="terminal-line">{line}</div>
              ))
            ) : (
              <div className="terminal-placeholder">
                <span className="terminal-placeholder-text">
                  <span role="img" aria-label="F1">🏁</span> Ready for input...
                </span>
              </div>
            )}
          </div>
          <div className="terminal-input-area">
            {activeInput ? (
              <div className="input-row">
                <span className="prompt-text">&gt;</span>
                <input
                  ref={inputRef}
                  className="terminal-input"
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your command..."
                  spellCheck={false}
                  autoFocus
                  enterKeyHint="send"
                />
                <button className="icon-btn send-btn" title="Send" onClick={handleSend}>
                  <span role="img" aria-label="Send">➤</span>
                  {showLabels && <span className="btn-label">Send</span>}
                </button>
              </div>
            ) : (
              <div
                className="prompt-row"
                onClick={handlePromptClick}
                tabIndex={0}
                role="button"
                aria-label="Activate input"
              >
                <span className="prompt-text">&gt;</span>
                <span className="blinking-cursor"></span>
                <span className="tap-to-type">{showLabels ? "Tap or click to type..." : ""}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}