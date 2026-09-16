export const config = () => ({
  port: parseInt(process.env.PORT ?? '8000', 10),
  apiPrefix: process.env.API_V1_PREFIX ?? 'api/v1',
  corsOrigins: (process.env.BACKEND_CORS_ORIGINS ?? 'http://localhost:3000')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
  db: {
    host: process.env.DATABASE_HOST ?? 'localhost',
    port: parseInt(process.env.DATABASE_PORT ?? '5432', 10),
    username: process.env.DATABASE_USER ?? 'fleetos',
    password: process.env.DATABASE_PASSWORD ?? 'fleetos',
    database: process.env.DATABASE_NAME ?? 'fleetos',
  },
  redisUrl: process.env.REDIS_URL ?? 'redis://localhost:6379/0',
  telemetryChannel: process.env.TELEMETRY_CHANNEL ?? 'fleetos:telemetry',
});

export type AppConfig = ReturnType<typeof config>;
