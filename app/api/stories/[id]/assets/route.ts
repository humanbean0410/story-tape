import { api, listAssets, uploadAsset } from '@/lib/story-service';

export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ id: string }> };

export async function GET(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return listAssets(params.id);
  });
}

export async function POST(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return uploadAsset(request, params.id);
  });
}
