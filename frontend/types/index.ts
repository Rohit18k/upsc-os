export interface User {
  id: string;
  email: string;
  fullName?: string;
  role: "admin" | "manager" | "user" | "readonly";
  isActive: boolean;
  isVerified: boolean;
  avatarUrl?: string;
  createdAt: string;
  updatedAt?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  meta?: Record<string, unknown>;
}

export interface PaginationMeta {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  meta: {
    pagination: PaginationMeta;
  };
}

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  traceId: string;
  instance?: string;
  errors?: Array<{
    field: string;
    message: string;
    type: string;
  }>;
}
