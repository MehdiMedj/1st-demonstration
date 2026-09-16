import { Injectable, OnModuleDestroy } from '@nestjs/common';
import Redis from 'ioredis';
import { config } from '../config/configuration';

/**
 * Owns two Redis connections: one for publishing telemetry, one dedicated
 * subscriber (ioredis requires a separate connection in subscriber mode).
 */
@Injectable()
export class RedisService implements OnModuleDestroy {
  readonly publisher: Redis;
  readonly subscriber: Redis;
  readonly channel: string;

  constructor() {
    const c = config();
    this.channel = c.telemetryChannel;
    this.publisher = new Redis(c.redisUrl);
    this.subscriber = new Redis(c.redisUrl);
  }

  async publish(message: string): Promise<void> {
    await this.publisher.publish(this.channel, message);
  }

  async onModuleDestroy(): Promise<void> {
    await this.publisher.quit();
    await this.subscriber.quit();
  }
}
