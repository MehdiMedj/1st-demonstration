import {
  BadRequestException,
  createParamDecorator,
  ExecutionContext,
} from '@nestjs/common';

/**
 * Resolves the active tenant from the `X-Org-Id` header. Single multi-tenancy
 * chokepoint — swap for a verified JWT claim in production.
 */
export const OrgId = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext): string => {
    const req = ctx.switchToHttp().getRequest();
    const value = req.headers['x-org-id'];
    if (!value || typeof value !== 'string') {
      throw new BadRequestException('Missing X-Org-Id header');
    }
    return value;
  },
);
