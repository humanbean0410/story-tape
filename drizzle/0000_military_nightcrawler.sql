CREATE TABLE `story_assets` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`object_key` text NOT NULL,
	`name` text NOT NULL,
	`type` text NOT NULL,
	`size` integer NOT NULL,
	`ready` integer DEFAULT 0 NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`story_id`) REFERENCES `stories`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `assets_story` ON `story_assets` (`story_id`);--> statement-breakpoint
CREATE TABLE `story_events` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`publication_time` integer NOT NULL,
	`session_hash` text NOT NULL,
	`event` text NOT NULL,
	`chapter_id` text DEFAULT '' NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`story_id`) REFERENCES `stories`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `events_dedup` ON `story_events` (`story_id`,`publication_time`,`session_hash`,`event`,`chapter_id`);--> statement-breakpoint
CREATE INDEX `events_publication` ON `story_events` (`story_id`,`publication_time`);--> statement-breakpoint
CREATE TABLE `story_feedback` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`publication_time` integer NOT NULL,
	`session_hash` text NOT NULL,
	`choice` text NOT NULL,
	`note` text DEFAULT '' NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`story_id`) REFERENCES `stories`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `feedback_dedup` ON `story_feedback` (`story_id`,`publication_time`,`session_hash`);--> statement-breakpoint
CREATE INDEX `feedback_publication` ON `story_feedback` (`story_id`,`publication_time`);--> statement-breakpoint
CREATE TABLE `publications` (
	`token` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`data` text NOT NULL,
	`source_revision` integer NOT NULL,
	`published_at` integer NOT NULL,
	`active` integer DEFAULT 1 NOT NULL,
	FOREIGN KEY (`story_id`) REFERENCES `stories`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `publications_story_unique` ON `publications` (`story_id`);--> statement-breakpoint
CREATE TABLE `stories` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`data` text NOT NULL,
	`revision` integer DEFAULT 1 NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `stories_owner_updated` ON `stories` (`owner_id`,`updated_at`);