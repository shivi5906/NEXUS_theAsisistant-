import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./useAuth";

const RequireAuth = () => {
    const auth = useAuth();

    if (!auth.isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
};

export default RequireAuth;
