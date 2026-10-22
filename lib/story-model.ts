import { z } from 'zod';

export const SceneId = z.enum(['casa', 'station', 'interior', 'courtyard', 'diner', 'alley']);
export const BeatSchema = z.object({
  id: z.string().min(1).max(80),
  speaker: z.string().max(40).default('独白'),
  text: z.string().max(500),
  shot: z.string().min(1).max(40).default('master'),
  seconds: z.number().min(2).max(30).default(7),
});
export const ChapterSchema = z.object({
  id: z.string().min(1).max(80),
  scene: SceneId,
  title: z.string().min(1).max(60),
  note: z.string().max(300).default(''),
  beats: z.array(BeatSchema).min(1).max(30),
  sound: z.enum(['ambience', 'silent', 'upload']).default('ambience'),
  audioAssetId: z.string().max(80).nullable().default(null),
  photoAssetId: z.string().max(80).nullable().default(null),
});
export const StorySchema = z.object({
  schemaVersion: z.literal(1),
  title: z.string().min(1).max(80),
  subtitle: z.string().max(140).default(''),
  author: z.string().max(60).default(''),
  dedication: z.string().max(200).default(''),
  template: z.string().max(60).default('blank'),
  chapters: z.array(ChapterSchema).min(1).max(6),
  opening: z.boolean().default(true),
  feedback: z.boolean().default(true),
});
export type Story = z.infer<typeof StorySchema>;
export type Chapter = z.infer<typeof ChapterSchema>;
export type Beat = z.infer<typeof BeatSchema>;
export type StoryRecord = { id: string; data: Story; revision: number; updatedAt: number; createdAt: number; publication: {token: string; publishedAt: number} | null };
export const durationOf = (story: Story) => story.chapters.reduce((total, chapter) => total + chapter.beats.reduce((sum, beat) => sum + beat.seconds, 0) + 4, 0);

// Schema normalization also gives a stable content fingerprint regardless of JSON field order.
export const storyFingerprint = (input: Story): string => {const parsed=StorySchema.safeParse(input);return JSON.stringify(parsed.success?parsed.data:input);};
