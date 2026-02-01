import "./App.css";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./auth/useAuth";
import Login from "./pages/Login";

// ---------------- DASHBOARD ----------------
function Dashboard() {
    return (
        <div className="app">
            <div className="app-shell">
                {/* Navbar */}
                <div className="navbar">
                    <div className="nav-left">
                        <div className="profile">
                            <span>PS</span>
                        </div>
                    </div>

                    <div className="nav-center absolute">NEXUS</div>

                    <div className="nav-right">
                        <button className="nav-btn">Data</button>
                        <button className="nav-btn">Settings</button>
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

                        <div className="command-bar">
                            <input
                                className="input"
                                placeholder="Type a command..."
                            />
                            <button className="send-btn">➤</button>
                        </div>
                    </div>

                    <div className="panel apps">
                        <h3>Apps</h3>

                        <div className="apps-grid">
                            {dummyApps.map(app => (
                                <button
                                    key={app.id}
                                    className="app-tile"
                                    title={app.name}
                                    onClick={() => console.log(`Launching ${app.name}`)}
                                >
                                    <span>{app.icon}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ---------------- ROUTES ----------------
export default function App() {
    const { isAuthenticated } = useAuth();
    return (
        <Routes>
            <Route path="/login" element={<Login />} />

            <Route
                path="/"
                element={
                    isAuthenticated
                        ? <Dashboard />
                        : <Navigate to="/login" replace />
                }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
}


// ---------------- TYPES & DATA ----------------
type AppItem = {
    id: number;
    name: string;
    icon: string;
};

const dummyApps: AppItem[] = [
    { id: 1, name: "Mail", icon: "📧" },
    { id: 2, name: "Browser", icon: "🌐" },
    { id: 3, name: "Calendar", icon: "📅" },
    { id: 4, name: "Files", icon: "📁" },
    { id: 5, name: "Notes", icon: "📝" },
    { id: 6, name: "Music", icon: "🎵" },
    { id: 7, name: "Photos", icon: "🖼️" },
    { id: 8, name: "Terminal", icon: "💻" },
    { id: 9, name: "Settings", icon: "⚙️" },
    { id: 10, name: "Tasks", icon: "✅" },
    { id: 11, name: "Clock", icon: "⏰" },
    { id: 12, name: "Maps", icon: "🗺️" },
    { id: 13, name: "Store", icon: "🛒" },
    { id: 14, name: "Chat", icon: "💬" },
    { id: 15, name: "Analytics", icon: "📊" },
    { id: 16, name: "AI Lab", icon: "🧠" },
    { id: 17, name: "Camera", icon: "📷" },
];
