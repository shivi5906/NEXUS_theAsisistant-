import { useEffect } from "react";
import { useGoogleLogin } from "@react-oauth/google";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import "./Login.css";

const Login = () => {
    const navigate = useNavigate();
    const auth = useAuth();

    useEffect(() => {
        if (auth.isAuthenticated) {
            navigate("/", { replace: true });
        }
    }, [auth.isAuthenticated, navigate]);

    const login = useGoogleLogin({
        scope: "openid profile email",
        onSuccess: async (tokenResponse) => {
            const res = await fetch(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                {
                    headers: {
                        Authorization: `Bearer ${tokenResponse.access_token}`,
                    },
                }
            );

            const userInfo = await res.json();

            auth.loginWithGoogle({
                name: userInfo.name,
                email: userInfo.email,
                picture: userInfo.picture,
            });

            navigate("/", { replace: true });
        },
        onError: () => {
            console.error("Google OAuth failed");
        },
    });

    return (
        <div className="login-screen">
            <div className="login-card">
                <div className="login-header">
                    <h1 className="login-title">NEXUS</h1>

                    <p className="login-tagline">
                        Your intelligent desktop assistant for focused work.
                    </p>

                    <p className="login-sub">
                        Manage tasks, apps, and attention — all in one place.
                    </p>
                </div>

                <button
                    className="login-btn google"
                    onClick={() => login()}
                >
                    <img
                        src="https://developers.google.com/identity/images/g-logo.png"
                        alt="Google"
                    />
                    <span>Sign in with Google</span>
                </button>

                <p className="login-footer">
                    Secure sign-in powered by Google
                </p>
            </div>
        </div>
    );
};

export default Login;
