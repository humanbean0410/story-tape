# Story Tape — Product Overview

[Project home](../README.md) · [中文介绍](../README.zh-CN.md) · [Try the workbench](https://casa-bellas-action.tb8zssvcd2.chatgpt.site/previs?guide=1)

## The product in one sentence

Story Tape is a browser-based scene design and shot previsualization prototype that helps filmmakers turn references and shooting intent into editable scene plans, look frames, and animatics.

## Who it is for

The initial audience is directors, cinematographers, film students, and independent or small production teams. The initial task is narrow: **prepare and discuss how to shoot one scene before arriving on set**.

For example, a director can explore two approaches to a station scene: a wide establishing shot followed by a slow push-in, or a sequence that uses a passing train as an occlusion. The useful outcome is a proposal a collaborator can inspect and revise, rather than a single attractive image.

Less experienced creators could use presets and templates built on the same scene and shot data. That is an expansion hypothesis, not evidence that one interface already serves every audience.

## The problem it explores

Pre-production decisions are often scattered across reference folders, scripts, still storyboards, music links, and conversations. Each expresses part of the idea, but comparing camera movement, spatial relationships, and timing requires connecting them.

The proposed value is to keep those decisions editable together. A change in focal length or camera path should be visible in the same space; a change in a sound cue should be heard against the same sequence.

## Three layers of the experience

| Layer | User's purpose | Current form |
| --- | --- | --- |
| Discover | Find a setting and understand the result. | Scene gallery with renders and photographic references. |
| Create | Test and revise a shooting approach. | Previs workbench with scene, camera, movement, subtitle, and audio controls. |
| Experience | See the capabilities work together in a piece. | Cassette-led interactive short with six 3D locations. |

The gallery and workbench serve the user directly. Product reasoning belongs in repository documents rather than interrupting the creative interface.

## A concrete workflow

1. **Choose a set.** Select an authored scene. State the intention and constraints.
2. **Add references.** Import images or audio and mark their role: layout, material, light, mood, or sound. They inform the plan; uploading them does not rebuild the set.
3. **Propose a shot.** Start with a camera preset, then adjust framing, lens, target, duration, and light.
4. **Rehearse the move.** Set a static shot or camera movement. Inspect opening, intermediate, and closing compositions.
5. **Build the sequence.** Arrange shots and scenes, add subtitles, and place music, ambience, voice, and event effects.
6. **Compare and share.** Export frames, a plan, or an animatic. Carry editable settings in project JSON, with original local media supplied separately.

Playback scope answers three review questions: current shot for composition and movement; current scene for coverage and timing; whole project for order and rhythm across scenes. Scope does not create a camera move—the shot's movement settings do.

## Why 3D is part of the prototype

The same three-dimensional set supports multiple cameras, parallax, moving occlusion, and repeatable framing. These properties matter when comparing ways to shoot a location.

3D is an implementation choice for those tasks, not the product's sole purpose. A scene plan or storyboard may combine photographs, renders, and other references. The central product object is the editable scene and its shots.

## Where models fit

Story Tape is an application prototype, not a foundation-model product. The existing sets were built in Blender; Three.js renders and previews them in the browser.

Model assistance could eventually interpret references, suggest shot candidates, or generate individual assets. Useful integration would preserve the author's ability to review and modify the result, along with reference provenance and spatial constraints.

**Today, the provider panel only prepares configuration states and task descriptions. OpenAI, Meshy, and Runway appearing in the interface does not mean live generation requests are connected.** Automatic reconstruction, scale recovery, and arbitrary photo-to-scene creation are not current capabilities.

## Current boundaries

| Working in the prototype | Still to build or validate |
| --- | --- |
| Six authored sets and editable camera parameters. | Arbitrary reference-to-3D reconstruction and physical scale accuracy. |
| Camera motion, playback scopes, subtitles, and layered sound. | Character performance, contact-aware animation, and automatic collision avoidance. |
| Local previs persistence and plan / PNG / JSON / WebM exports. | Collaborative revision and cross-device previs synchronization. |
| Separate cloud story-editing and publishing application code. | Portable cloud deployment without adapting authentication and storage. |
| Simple and professional control depths. | Whether those depths fit real creators' decisions and beginners' needs. |

People were removed from the current sets after early character models produced distracting contact and seating problems. Objects, empty seats, and sound retain the narrative context; believable character performance remains unresolved.

## What to learn next

Invite target creators to bring one real scene and produce a plan, frames, and an animatic. Observe where their intended shot becomes hard to express, what they repeatedly revise, and whether a collaborator understands the exported proposal.

Use that evidence to prioritize deeper camera control, better set preparation, or simpler templates. Model integration should follow a demonstrated task bottleneck. The project makes no validated claims about market fit, time saved, retention, or willingness to pay.
