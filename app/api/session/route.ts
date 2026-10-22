import { api, session } from '@/lib/story-service';

export const dynamic = 'force-dynamic';

export async function GET(): Promise<Response> {
  return api(async () => {
    return session();
  });
}
