import { useState } from "react";
import type { ReactNode } from "react";
import { AuthContext } from "./AuthContext";

export function AuthProvider({ children }: { children: ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState(
        () => localStorage.getItem("nexus_auth") === "true"
    );

    const login = () => {
        localStorage.setItem("nexus_auth", "true");
        setIsAuthenticated(true);
    };

    const logout = () => {
        localStorage.removeItem("nexus_auth");
        setIsAuthenticated(false);
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
