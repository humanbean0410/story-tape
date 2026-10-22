import { sqliteTable, text, integer, index, uniqueIndex } from 'drizzle-orm/sqlite-core';

export const stories = sqliteTable('stories', {
  id: text('id').primaryKey(),
  ownerId: text('owner_id').notNull(),
  data: text('data').notNull(),
  revision: integer('revision').notNull().default(1),
  createdAt: integer('created_at').notNull(),
  updatedAt: integer('updated_at').notNull(),
}, table => [index('stories_owner_updated').on(table.ownerId, table.updatedAt)]);

export const publications = sqliteTable('publications', {
  token: text('token').primaryKey(),
  storyId: text('story_id').notNull().references(() => stories.id, { onDelete: 'cascade' }),
  data: text('data').notNull(),
  sourceRevision: integer('source_revision').notNull(),
  publishedAt: integer('published_at').notNull(),
  active: integer('active').notNull().default(1),
}, table => [uniqueIndex('publications_story_unique').on(table.storyId)]);

export const assets = sqliteTable('story_assets', {
  id: text('id').primaryKey(),
  storyId: text('story_id').notNull().references(() => stories.id, { onDelete: 'cascade' }),
  key: text('object_key').notNull(),
  name: text('name').notNull(),
  type: text('type').notNull(),
  size: integer('size').notNull(),
  ready: integer('ready').notNull().default(0),
  createdAt: integer('created_at').notNull(),
}, table => [index('assets_story').on(table.storyId)]);

export const events = sqliteTable('story_events', {
  id: text('id').primaryKey(),
  storyId: text('story_id').notNull().references(() => stories.id, { onDelete: 'cascade' }),
  publicationTime: integer('publication_time').notNull(),
  sessionHash: text('session_hash').notNull(),
  event: text('event').notNull(),
  chapterId: text('chapter_id').notNull().default(''),
  createdAt: integer('created_at').notNull(),
}, table => [
  uniqueIndex('events_dedup').on(table.storyId, table.publicationTime, table.sessionHash, table.event, table.chapterId),
  index('events_publication').on(table.storyId, table.publicationTime),
]);

export const feedback = sqliteTable('story_feedback', {
  id: text('id').primaryKey(),
  storyId: text('story_id').notNull().references(() => stories.id, { onDelete: 'cascade' }),
  publicationTime: integer('publication_time').notNull(),
  sessionHash: text('session_hash').notNull(),
  choice: text('choice').notNull(),
  note: text('note').notNull().default(''),
  createdAt: integer('created_at').notNull(),
}, table => [
  uniqueIndex('feedback_dedup').on(table.storyId, table.publicationTime, table.sessionHash),
  index('feedback_publication').on(table.storyId, table.publicationTime),
]);
