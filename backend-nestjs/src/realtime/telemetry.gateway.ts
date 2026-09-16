import { Logger, OnModuleInit } from '@nestjs/common';
import {
  OnGatewayConnection,
  OnGatewayDisconnect,
  WebSocketGateway,
} from '@nestjs/websockets';
import { IncomingMessage } from 'http';
import { WebSocket } from 'ws';
import { RedisService } from '../redis/redis.service';

/**
 * Native-WebSocket gateway (same wire protocol as the FastAPI backend) that
 * streams telemetry to dispatcher clients. Subscribes to Redis so a ping
 * received by any worker reaches clients connected to any worker.
 *
 * Connect: ws://host/api/v1/ws/telemetry?org_id=<uuid>
 */
@WebSocketGateway({ path: '/api/v1/ws/telemetry' })
export class TelemetryGateway
  implements OnGatewayConnection, OnGatewayDisconnect, OnModuleInit
{
  private readonly logger = new Logger(TelemetryGateway.name);
  private readonly clients = new Map<WebSocket, string>();

  constructor(private readonly redis: RedisService) {}

  onModuleInit(): void {
    this.redis.subscriber.subscribe(this.redis.channel).then(() => {
      this.logger.log(`Subscribed to Redis channel ${this.redis.channel}`);
    });
    this.redis.subscriber.on('message', (_channel: string, message: string) => {
      let event: { organization_id?: string };
      try {
        event = JSON.parse(message);
      } catch {
        return;
      }
      const orgId = event.organization_id;
      if (!orgId) return;
      for (const [client, clientOrg] of this.clients.entries()) {
        if (clientOrg === orgId && client.readyState === WebSocket.OPEN) {
          client.send(message);
        }
      }
    });
  }

  handleConnection(client: WebSocket, req: IncomingMessage): void {
    const url = new URL(req.url ?? '', 'http://localhost');
    const orgId = url.searchParams.get('org_id');
    if (!orgId) {
      client.close(1008, 'Missing org_id');
      return;
    }
    this.clients.set(client, orgId);
    this.logger.log(`WS connected org=${orgId} (total=${this.clients.size})`);
  }

  handleDisconnect(client: WebSocket): void {
    this.clients.delete(client);
  }
}
