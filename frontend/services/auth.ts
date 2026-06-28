import { api } from "./api";

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  fullName?: string;
}

interface AuthResponse {
  user: {
    id: string;
    email: string;
    fullName?: string;
    role: string;
    isActive: boolean;
    isVerified: boolean;
    createdAt: string;
  };
  tokens: {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    expiresIn: number;
  };
}

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    return api.post<AuthResponse>("/api/v1/auth/login", data, { skipAuth: true });
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    return api.post<AuthResponse>("/api/v1/auth/register", data, { skipAuth: true });
  },

  async logout(refreshToken: string): Promise<void> {
    return api.post("/api/v1/auth/logout", { refreshToken });
  },

  async refreshToken(refreshToken: string) {
    return api.post("/api/v1/auth/refresh", { refreshToken }, { skipAuth: true });
  },

  async getCurrentUser() {
    return api.get("/api/v1/users/me");
  },
};
