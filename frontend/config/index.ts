export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    timeout: 30000,
  },
  auth: {
    tokenKey: "upscos-auth",
    refreshThreshold: 5 * 60 * 1000,
  },
  app: {
    name: "UPSC OS",
    version: "0.1.0",
  },
  pagination: {
    defaultPageSize: 20,
    maxPageSize: 100,
  },
} as const;
