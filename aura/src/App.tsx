import "./App.css";

function App() {
    return (
        <div className="app">

            {/* Navbar */}
            <div className="navbar">
                <div className="nav-left">NEXUS</div>
                <div className="nav-right">
                    <span>Account</span>
                    <span>Data</span>
                    <span>Settings</span>
                </div>
            </div>

            {/* Top row */}
            <div className="top">
                <div className="panel voice">
                    <div className="voice-wave speaking">
                        <span />
                        <span />
                        <span />
                        <span />
                        <span />
                    </div>
                </div>
                <div className="panel task">
                    <h3>Current Task</h3>
                    <p>Building Nexus frontend</p>
                </div>
                <div className="panel history">
                    <h3>History</h3>
                    <ul>
                        <li>Opened Chrome</li>
                        <li>Read email</li>
                        <li>Focused for 12 min</li>
                    </ul>
                    <div className="stats">
                        <p>Uptime: 02:14:32</p>
                        <p>
                            Status: <span className="status online">ONLINE</span>
                        </p>
                  </div>
                </div>
            </div>

            {/* Bottom row */}
            <div className="bottom">
                <div className="panel output">
                    <h3>NEXUS</h3>
                    <div className="output-text">
                        <p>[NEXUS] Hello Pushkar.</p>
                        <p>[SYSTEM] All systems are running.</p>
                    </div>
                  <input
                        className="input"
                        placeholder="Type a command..."
                    />
                </div>

                <div className="panel apps">
                    <h3>Apps</h3>
                    <button>Gmail</button>
                    <button>Chrome</button>
                    <button>Calendar</button>
                    <button>Files</button>
                </div>
            </div>
        </div>
    );
}

export default App;
