import { api, getAsset } from '@/lib/story-service';

export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ assetId: string }> };

export async function GET(request: Request, context: Context): Promise<Response> {
  return api(async () => {
    const params = await context.params;
    return getAsset(request, params.assetId);
  });
}
