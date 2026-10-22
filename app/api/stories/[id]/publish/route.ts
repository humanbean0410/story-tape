import { api, publishStory, revokePublication } from '@/lib/story-service';

export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ id: string }> };

export async function POST(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return publishStory(request, params.id);
  });
}

export async function DELETE(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return revokePublication(request, params.id);
  });
}
