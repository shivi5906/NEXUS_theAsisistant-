import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import AuthProvider from "./auth/AuthProvider";
import App from "./App";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <HashRouter>
                <AuthProvider>
                    <App />
                </AuthProvider>
            </HashRouter>
        </GoogleOAuthProvider>
    </React.StrictMode>
);

console.log("GOOGLE_CLIENT_ID =", GOOGLE_CLIENT_ID);
