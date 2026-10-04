# A Bridge the Token Never Crosses

Slides for the YerevanJS #1 talk. reveal.js 5.2.1, single `index.html`, no build step.

- Open: `npx serve .` (or any static server) → http://localhost:3000 — or just open `index.html`.
- Speaker view: press `S`. Overview: `Esc`. Notes carry the script and cumulative timing per slide.
- Identity: all colours are CSS variables at the top of `index.html` (`--accent`, `--bg`, `--fg`); swap when the YerevanJS theme is ready.
- Placeholders to fill: `assets/qr-contact.png` (LinkedIn/Telegram QR), the joke line on the "Who's talking" slide.
- `assets/qr-ad.png` (ad block on "Who's talking") points at the LinkedIn profile for now; once the consulting post is live, regenerate: `python3 -c "import qrcode; qrcode.make('<POST URL>').save('assets/qr-ad.png')"` (`pip install qrcode[pil]`).
- Appendix slides live after "Thanks" — jump with `#/appendix-jwt`, `#/appendix-chips`, `#/appendix-store`, `#/appendix-fetchmeta`, `#/appendix-authjs`.
- Full speaker script: `TALK.md`. Outline with per-slide notes and timing: `talent-visa/05-build-projects/auth-bridge-talk-yerevanjs-outline.md`.
