import { createContext } from "react";

export interface User {
    name: string;
    email: string;
    picture: string;
}

export interface AuthContextType {
    isAuthenticated: boolean;
    user: User | null;
    loginWithGoogle: (user: User) => void;
    logout: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);
