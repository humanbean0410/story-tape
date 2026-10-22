import { env } from 'cloudflare:workers';
import { modelStatuses } from '@/lib/model-options';
export const dynamic='force-dynamic';
export function GET(){return Response.json({services:modelStatuses(env as unknown as Record<string,unknown>),executionAvailable:false},{headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});}
