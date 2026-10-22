import { api, addEvent } from '@/lib/story-service';

export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ token: string }> };

export async function POST(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return addEvent(request, params.token);
  });
}
