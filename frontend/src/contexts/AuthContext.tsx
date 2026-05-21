'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface User {
    id: string;
    email: string;
    full_name: string | null;
    role: string;
    is_active: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null; // Kept for backwards compatibility, always null under HTTP-only cookies
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, fullName?: string) => Promise<void>;
    logout: () => void;
    refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

import { getApiBaseUrl } from '@/lib/api-url';

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    const logout = useCallback(async () => {
        try {
            await fetch(`${getApiBaseUrl()}/auth/logout`, {
                method: 'POST',
                credentials: 'include',
            });
        } catch (error) {
            console.error('Failed to logout on server:', error);
        }
        setUser(null);
        router.push('/login');
    }, [router]);

    const refreshPromiseRef = React.useRef<Promise<boolean> | null>(null);

    const refreshTokenFn = useCallback(async () => {
        if (refreshPromiseRef.current) {
            await refreshPromiseRef.current;
            return;
        }

        const runRefresh = async () => {
            try {
                const response = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({}),
                });

                if (response.ok) {
                    const meResponse = await fetch(`${getApiBaseUrl()}/auth/me`, {
                        credentials: 'include',
                    });
                    if (meResponse.ok) {
                        const userData = await meResponse.json();
                        setUser(userData);
                        return true;
                    }
                }
                await logout();
                return false;
            } catch (error) {
                console.error('Failed to refresh token:', error);
                await logout();
                return false;
            } finally {
                refreshPromiseRef.current = null;
            }
        };

        refreshPromiseRef.current = runRefresh();
        await refreshPromiseRef.current;
    }, [logout]);

    const fetchUser = useCallback(async () => {
        try {
            const response = await fetch(`${getApiBaseUrl()}/auth/me`, {
                credentials: 'include',
            });

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else {
                // Access token invalid/expired, try refreshing
                await refreshTokenFn();
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
            await logout();
        } finally {
            setIsLoading(false);
        }
    }, [refreshTokenFn, logout]);

    // Load active session on mount
    useEffect(() => {
        fetchUser();
    }, [fetchUser]);

    const login = async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            credentials: 'include',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        await fetchUser();
        router.push('/dashboard');
    };

    const register = async (email: string, password: string, fullName?: string) => {
        const response = await fetch(`${getApiBaseUrl()}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                email,
                password,
                full_name: fullName,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        // Auto-login after registration
        await login(email, password);
    };

    const value = {
        user,
        token: null, // No longer exposing tokens in JavaScript context for security
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshToken: refreshTokenFn,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

// HOC for protected routes
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
    return function AuthenticatedComponent(props: P) {
        const { isAuthenticated, isLoading } = useAuth();
        const router = useRouter();

        useEffect(() => {
            if (!isLoading && !isAuthenticated) {
                router.push('/login');
            }
        }, [isLoading, isAuthenticated, router]);

        if (isLoading) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-[#0a0a0b]">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            );
        }

        if (!isAuthenticated) {
            return null;
        }

        return <Component {...props} />;
    };
}
