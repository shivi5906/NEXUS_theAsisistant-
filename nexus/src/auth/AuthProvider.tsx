/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from "react";
import { AuthContext } from "./AuthContext";

const STORAGE_KEY = "nexus_auth";

type User = {
    name: string;
    email: string;
    picture: string;
};

const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return;

        const parsed = JSON.parse(stored);
        setUser(parsed.user);
    }, []);

    const loginWithGoogle = (userData: User) => {
        setUser(userData);
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify({ user: userData })
        );
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem(STORAGE_KEY);
    };

    return (
        <AuthContext.Provider
            value={{
                isAuthenticated: !!user,
                user,
                loginWithGoogle,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export default AuthProvider;
