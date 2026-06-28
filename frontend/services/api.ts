import { useAuthStore } from "@/store/auth-store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiOptions extends RequestInit {
  skipAuth?: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    const { accessToken } = useAuthStore.getState();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: "An unexpected error occurred",
      }));
      throw new ApiError(response.status, error.detail || error.message);
    }
    return response.json();
  }

  async get<T>(path: string, options: ApiOptions = {}): Promise<T> {
    const headers = options.skipAuth ? {} : await this.getAuthHeaders();
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "GET",
      headers: { ...headers, ...options.headers },
      ...options,
    });
    return this.handleResponse<T>(response);
  }

  async post<T>(path: string, body?: unknown, options: ApiOptions = {}): Promise<T> {
    const headers = options.skipAuth ? {} : await this.getAuthHeaders();
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { ...headers, ...options.headers },
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
    return this.handleResponse<T>(response);
  }

  async put<T>(path: string, body?: unknown, options: ApiOptions = {}): Promise<T> {
    const headers = options.skipAuth ? {} : await this.getAuthHeaders();
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "PUT",
      headers: { ...headers, ...options.headers },
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
    return this.handleResponse<T>(response);
  }

  async delete<T>(path: string, options: ApiOptions = {}): Promise<T> {
    const headers = options.skipAuth ? {} : await this.getAuthHeaders();
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "DELETE",
      headers: { ...headers, ...options.headers },
      ...options,
    });
    return this.handleResponse<T>(response);
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const api = new ApiClient(API_BASE_URL);
