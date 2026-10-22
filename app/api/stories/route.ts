import { api, listStories, createStory } from '@/lib/story-service';

export const dynamic = 'force-dynamic';

export async function GET(): Promise<Response> {
  return api(async () => {
    return listStories();
  });
}

export async function POST(request: Request): Promise<Response> {
  return api(async () => {
    return createStory(request);
  });
}
