# A Bridge the Token Never Crosses

Slides for the DevFest Armenia 2026 talk. reveal.js 5.2.1, single `index.html`, no build step.

- Open: `npx serve .` (or any static server) → http://localhost:3000 -- or just open `index.html`.
- Speaker view: press `S`. Overview: `Esc`. The notes are the full script from `TALK.md` (▸ = click), plus a ⏱ cumulative-time marker.
- `TALK.md` is the source of truth for the script. After editing it, run `python3 scripts/sync-notes.py` to copy the text back into the slides' notes.
- Identity: every colour and font is a CSS variable at the top of `index.html`. Two themes share them: light is the default, dark is `html.theme-dark`. Press `T` to switch (the choice is remembered on this machine), or open with `?theme=dark` / `?theme=light`.
- Fonts are local, no network needed: Geist, Geist Mono and EB Garamond in `assets/fonts/` (SIL OFL, licences alongside).
- Appendix slides are hidden from the flow (`data-visibility="hidden"` on `#appendix`); remove that attribute to bring them back. Ids: `#/appendix-jwt`, `#/appendix-chips`, `#/appendix-store`, `#/appendix-fetchmeta`, `#/appendix-authjs`.
- Full speaker script: `TALK.md`. Outline with per-slide notes and timing: `talent-visa/05-build-projects/auth-bridge-talk-yerevanjs-outline.md`.
