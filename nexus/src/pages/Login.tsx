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
                <h1 className="login-title">NEXUS</h1>
                <p className="login-sub">Sign in to continue</p>

                <button className="login-btn" onClick={() => login()}>
                    Sign in with Google
                </button>
            </div>
        </div>
    );

};

export default Login;
