# Development Guide

[Project home](../README.md) · [Product overview](product-overview.md) · [中文介绍](../README.zh-CN.md)

## Local setup

Use Node.js **22.13 or newer** and npm.

```bash
git clone https://github.com/humanbean0410/story-tape.git
cd story-tape
npm ci
npm run dev
```

The default development address is `http://localhost:5173`; follow the terminal's loopback address if it differs. No model-provider credentials are needed to try the authored sets.

```bash
npm run build
```

## Routes

| Route | Purpose |
| --- | --- |
| `/` | Product entry and scene selection. |
| `/previs` | Scene plans, camera design, playback, audio, and exports. |
| `/previs?guide=1` | Workbench with the onboarding guide. |
| `/film/` | Original cassette-led interactive piece. |
| `/studio` | Separate interactive-story editor. |
| `/watch/<token>` | A published interactive story. |

The story editor and previs workbench have different persistence flows. Publishing a cloud story does not automatically publish a local previs project.

## Architecture

- **Application:** React, TypeScript, Vinext / Vite.
- **3D:** Blender-authored GLB sets rendered with Three.js.
- **Sound and output:** Web Audio, Canvas, and MediaRecorder.
- **Server:** Cloudflare Workers, D1 story data, and R2 cloud uploads.
- **Local previs:** localStorage project data and IndexedDB media.

```text
app/                  Pages, routes, and server APIs
components/           Scene gallery, previs, story editor, and provider UI
lib/                  Project data, references, cameras, audio, and model tasks
public/film/          Interactive piece, runtime, models, textures, and audio
public/scene-thumbs/   Existing set renders
public/references/    Photographic references
build/                Sites / Workers integration
scripts/              Development and build helpers
checks/               Focused behavior and data checks
db/                   Cloud data schema
drizzle/              Database migrations
```

## Deployment boundaries

This repository contains a full-stack application. The existing integration targets Sites / Cloudflare Workers. GitHub Pages alone does not run the server APIs, authentication, D1, or R2 features.

For another host, adapt the worker entry, authentication, database and object-storage bindings, and migrations. `.openai/hosting.json` identifies the original hosting project; it does not transfer that project or grant access to its production data. GitHub commits do not automatically redeploy the original live Site.

Local emulation does not provide the original production database, cloud media, or login session. The source snapshot does not contain production credentials, model API keys, or browser drafts.

## Export and browser behavior

WebM export uses browser MediaRecorder at 24 fps, with a 180-second limit per export. Browser and device performance determine actual playback and recording smoothness. Mixed-aspect exports use the first shot's output aspect ratio and letterbox other shots.

Project JSON carries parameters and asset descriptions, not imported media files. Keep those originals when transferring a project. Browser storage can be cleared, so export settings and retain originals for work you want to keep.

The model-provider UI is a preparation surface, not a connected generation backend. Adding a provider name or entering configuration does not implement model requests.

## Focused checks

```bash
node --experimental-vm-modules checks/previs-model.mjs
node --experimental-vm-modules checks/previs-playback.mjs
node --experimental-vm-modules checks/product-runtime.mjs
node checks/sound-timing.mjs
node checks/story-playback.mjs
node checks/music-playback.mjs
npx tsc --noEmit
```

These cover data constraints, playback scopes, camera displacement, pause/resume behavior, opening and closing compositions, audio timing, and selected film behaviors. They do not replace browser checks, creator testing, or validation against a real filming location.

## Report a reproducible problem

Include the route, scene, camera/shot settings, playback scope, expected behavior, actual behavior, and browser/device. For missing local media, say whether the project was imported from JSON or opened in another browser. Avoid attaching credentials or private source media to a public issue.
