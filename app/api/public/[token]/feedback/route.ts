import { api, addFeedback } from '@/lib/story-service';

export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ token: string }> };

export async function POST(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return addFeedback(request, params.token);
  });
}
