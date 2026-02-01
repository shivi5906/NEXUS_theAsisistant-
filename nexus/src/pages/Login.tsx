import { useAuth } from "../auth/useAuth";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import "./Login.css";

export default function Login() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    const handleLogin = () => {
        setLoading(true);
        setTimeout(() => {
            login();
            navigate("/");
        }, 1200); // fake OAuth delay
    };

    return (
        <div className="login-screen">
            <div className={`login-card ${loading ? "loading" : ""}`}>
                <h1 className="login-title">NEXUS</h1>
                <p className="login-sub">Sign in to continue</p>

                <button
                    className="login-btn"
                    onClick={handleLogin}
                    disabled={loading}
                >
                    {loading ? "Signing in…" : "Continue"}
                </button>

                <span className="login-hint">
                    OAuth will be added here
                </span>
            </div>
        </div>
    );
}
