import { api, getStory, updateStory, deleteStory } from '@/lib/story-service';

export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ id: string }> };

export async function GET(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return getStory(params.id);
  });
}

export async function PUT(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return updateStory(request, params.id);
  });
}

export async function DELETE(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return deleteStory(request, params.id);
  });
}
