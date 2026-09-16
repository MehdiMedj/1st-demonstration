import 'reflect-metadata';
import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { WsAdapter } from '@nestjs/platform-ws';
import { AppModule } from './app.module';
import { config } from './config/configuration';

async function bootstrap() {
  const c = config();
  const app = await NestFactory.create(AppModule);

  app.enableCors({ origin: c.corsOrigins, credentials: true });

  // /health and / stay outside the versioned prefix (matches FastAPI).
  app.setGlobalPrefix(c.apiPrefix, { exclude: ['health', ''] });

  app.useGlobalPipes(
    new ValidationPipe({
      transform: true,
      whitelist: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // Native WebSocket adapter (browser-compatible), same wire protocol as FastAPI.
  app.useWebSocketAdapter(new WsAdapter(app));

  await app.listen(c.port, '0.0.0.0');
  console.log(`FleetOS (NestJS) listening on :${c.port} prefix /${c.apiPrefix}`);
}

bootstrap();
