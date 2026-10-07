# A Bridge the Token Never Crosses — speaker script

> Full spoken text, slide by slide. ~3,600 words ≈ 26–28 min at a calm pace, plus the demo. Sections marked **[cut-candidate]** are the first to go if the rehearsal runs long; dropping all of them lands at ~22 min. Slide numbers are the horizontal slide count as the deck's corner shows it (reveal's URL hash is zero-based, so slide N is `#/N-1`); vertical sub-slides are N.1, N.2… **▸ = click (next fragment appears)**; a slide with no ▸ has no fragments.

---

## 1 · Title

Hi. Ok, let's start.
The talk is called "A Bridge the Token Never Crosses", a little bit poetic, but the title is literally the whole talk. I'm going to carry a user's session across an origin boundary — from a page that has it to an iframe that doesn't — and the one thing that will never make the trip is the session token itself. Sounds like a magic? Follow me, and by the end you'll know exactly what *does* cross, and why that turns out to be enough.

## 2 · Disclaimer *(joke)*

Before we start, a disclaimer. This talk might cause an uncontrolled desire for snacks — we'll be talking about cookies and chips for twenty-five minutes, and none of them are edible. ▸ …and diabetes. *(beat)*

## 3 · Who's talking

I'm Azat. I'm a software architect and tech lead, and I've been writing JavaScript for a bit over ten years. One thing up front: tonight is about a pattern, not a product. If you walk out of here and hand-roll your own version — that's a win, as long as it passes the checklist I'll give you later.

*[your joke line]*

▸ *(the ad block appears)* — "Vibe-coded your JS app and not sure it's safe? Better call Azat." One line, no more.

## 4 · Origin story

This came out of a real project. An enterprise AI assistant for a large pharma company — one Next.js codebase, two ways of reaching users.

▸ Inside SharePoint and Teams assistant ran  inside iframe. The user was signed in on the host — SharePoint knew who they were. But inside our iframe, they were anonymous. Our app couldn't see the host's session at all.

▸ On iOS it shipped as a wrapped PWA — a WKWebView. For people who don't know what it is, it's like iframe inside RN app. And a WKWebView is an isolated web process: its own cookie store, and no access to the device's credential store. Passkeys live at the device level — in the Keychain, behind the platform authenticator — and the WebView simply can't reach them. Same for autofill, same for the login the user already has in Safari. All out of reach.

Two platforms, two separate bug reports. And it took me a while to notice that it was the same bug. ▸ In both cases there's a *primary* session that lives in one browsing context, and a *secondary* context that needs a session of its own — without asking the user to sign in again.

Once you see it as one shape, the fix is one shape too.

## 5 · That shape is the bridge *(meme)*

That shape is the bridge. *(beat — let the room react, then move on)*

## 6 · What you'll leave with

Four things. ▸ A mental model — cross-context auth is a one-time code across a trust boundary, and everything else is transport detail. ▸ An invariant checklist you can hold up against *any* popup-or-iframe auth scheme. ▸ A clear picture of where CHIPS — partitioned cookies — helps (besides wathching movies), and where it doesn't. ▸ And working wiring for both Auth.js and Better Auth, so you can see the pattern is not tied to a library.

---

## 7 · The setup

Here's the situation. Your Next.js app lives inside somebody else's page. SharePoint web part, Teams tab, Salesforce Lightning component, ServiceNow, Confluence — chose your fighter. The host already has the user signed in against a shared identity provider — in the Microsoft world that's Entra.

Ten years ago this was boring. The iframe just saw the same cookies as the host, and life went on.

## 8 · Why third-party cookies had to go

A quick detour into why, because it explains every failed fix we're about to see. ▸ A third-party cookie is the primitive of cross-site tracking: one ad pixel embedded on a thousand sites, one cookie, one profile of you. Browsers decided to kill that.

▸ And here's the problem for us: the browser cannot tell your embedded app from that pixel. Same shape — a foreign origin, inside someone else's page, asking for its cookies. ▸ So the fix was blunt: no cookies for foreign origins inside a page. ▸ Safari went first with ITP in 2017 and a full block by 2020. Firefox partitions everything by default since 2022. Chrome announced, delayed, trialled, pivoted, and in the end kept them — but blocks them in incognito and under enterprise policy. We're collateral damage of anti-tracking, and every fix that tries to "get the cookie back" is fighting the browser.

## 9 · What changed

What changed is that your cookie became a *third-party* cookie. ▸ From the browser's point of view, your app's session cookie, inside someone else's page, is exactly the shape of cross-site tracking it has spent a decade trying to kill.

Safari has blocked this for years with ITP. Firefox partitions it by default. Chrome — well, Chrome's deprecation timeline is its own soap opera, but it doesn't matter: in incognito it's blocked, under enterprise policy it's blocked, and the enterprise browser matrix is exactly where this app lives. So the practical truth is simple: you cannot rely on third-party cookies today. Full stop.

## 10 · Four obvious fixes

So what do people try? Four things, and each one breaks either the UX or the architecture.

### 10.1 · Sign in again inside the iframe

The first instinct: just run the sign-in flow inside the iframe. Three independent reasons that fails. ▸ One, it's a redundant login — the user *already* signed in, on the host, thirty seconds ago. ▸ Two, the identity provider will very often refuse to render inside a frame at all — `X-Frame-Options`, `frame-ancestors`, you've seen the blank box. ▸ And three — this is the one people miss — even if the redirect somehow completes, the cookie it sets is *still* a third-party cookie. You're back where you started.

### 10.2 · Storage Access API

Second: the Storage Access API. ▸ `document.requestStorageAccess()`. It's a real API, it's designed for roughly this situation, and it doesn't fit. ▸ It needs a user gesture *and* shows a permission prompt — and silent SSO with a prompt is not silent. ▸ Support is uneven. ▸ And more fundamentally, it solves *access* — "let my frame read its own cookies" — not *inheritance*. It won't give you the host's session.

### 10.3 · CHIPS

Third: CHIPS — cookies with the `Partitioned` attribute. Someone on the team reads the spec and says: "we just set `Partitioned` and we're done."

Here's the thing. ▸ A partitioned cookie is a cookie your frame *can keep*. ▸ It is not a cookie your frame *already has*. ▸ Your partition — keyed by your origin plus the host's top-level site — starts empty. CHIPS gives you a place to store a session in the embedded context. It does nothing to mint one.

Hold onto that, because we *will* use CHIPS — on the far side of the bridge.

### 10.4 · Vendor SDK

Fourth: use the vendor SDK. ▸ Auth0, Okta, Clerk — they all solve this, inside their own ecosystem. ▸ And that's the trade: you now rent your identity. ▸ Which is precisely the thing self-hosted cookie-session auth — Auth.js, Better Auth — exists to avoid. Not a bad choice for some teams. Just name the trade honestly.

## 11 · What we actually want

So here's the spec. Inherit the *existing* host SSO — not a new login. Silently — no prompt. No session token anywhere it can leak. And no vendor lock-in. Keep these four on your mental clipboard. We'll check them off at the end.

---

## 12 · The one realisation

Everything that follows comes from one sentence.

The iframe is the wrong place to do OAuth. A popup runs in the *top-level* browsing context. And in the top-level context, the identity provider's cookies are *first-party*. The user's existing session is right there.

That's it. That's the trick. Everything else is making it safe.

## 13 · The bridge, step by step

Let me walk the flow. Four lanes: the iframe — that's your app, embedded; the popup — also your app, but top-level; your app's server; and the identity provider.

▸ **Step one.** The iframe opens a popup to `/auth/popup` — on *your* origin, not the host's. This matters: the host never runs any of your code. That's why the same pattern ports to SharePoint, Teams, Salesforce, whatever.

▸ **Step two.** In that popup, your auth library does its completely normal OAuth sign-in. Nothing custom. Because the popup is top-level, the IdP sees its own first-party cookies, finds the live session, and returns an authorization code with no prompt. PKCE, state — all handled by the library exactly as always. Your server completes the exchange and sets a session cookie — in the popup's first-party jar. So far the only new thing is *where* this runs.

▸ **Step three.** This is where the title happens. The popup calls `POST /auth/bridge`. The request carries the popup's session cookie — that's just the browser doing its normal thing. The server verifies that there really is a session, and only then does two things: it takes the session cookie's value out of that request and *parks it server-side* — in a transfer store, Redis or KV, for at most sixty seconds, readable exactly once — and it mints a one-time code that points at that parked entry. Two hundred fifty-six bits from a CSPRNG. It returns `{ code }` — and nothing else.

So where is the session right now? In two places. Still in the popup's own cookie jar, where it always was. And parked on the server, under a key that's worthless to anyone who can't redeem it in the next sixty seconds. Notice what the popup does *not* get: the token. It never holds it in JavaScript, never puts it in a URL, never puts it in a message. It gets a claim ticket.

▸ **Step four.** The popup `postMessage`s that code to the iframe — with an explicit target origin, never `*`. The iframe checks the sender's origin *and* the sender's window identity. Why both — in a few minutes.

▸ **Step five.** The iframe redeems the code: `fetch('/auth/consume?code=…', { credentials: 'include' })`. The server deletes the code on first read, pulls the parked cookie value out of the store, and responds with `Set-Cookie` — the same session, now written into *this* context — and *this* cookie carries `Partitioned`. It lands in the partition we said was empty five minutes ago. CHIPS couldn't mint the session; it can absolutely keep the one we just delivered.

The popup closes. The user saw a flash for under a second. The iframe reloads, signed in.

## 14 · The whole shape

Compressed to one sentence: a server-side handle store mediates a one-time-code exchange across a trust boundary. Everything else is transport.

And if that figure feels familiar — it should. It's the OAuth authorization code: a short-lived, single-use code crosses the untrusted leg, and the real credential is exchanged for it on the back end. RFC 6749, section 4.1. We've just moved the boundary from "browser ↔ IdP" to "top-level ↔ iframe". RFC 8252 does the same move for native apps, and we'll meet it again at the end. Remember that sentence — we'll see the *same* shape with a different transport.

## 15 · Demo

Let me show you it's real. *(live)*

Two deployments, two Vercel origins, one self-hosted Keycloak — so the cross-site handoff is genuine, not faked on a single origin. Both run on an open-source reference implementation of the pattern that I wrote; I'll come back to it at the end — for now it's just "the repo". I sign in on the host… and the embedded app signs itself in. Open DevTools, Application, Cookies — there's the session cookie, and there's the `Partitioned` column.

Second deployment — same flow, same bridge, but the app underneath is Better Auth instead of Auth.js. Hold that thought; we'll come back to it.

*(If the network is dead: narrate it over the diagram — "this is where the popup would flash" — and move on. Don't fight it.)*

---

## 16 · Remove one condition…

Now the part I actually care about. Everything I just showed is held together by a handful of invariants, and if you remove *any one* of them, the bridge becomes a hole. I want to go through them one at a time, each with the question "what breaks without it?" — because this list works against any popup-and-iframe scheme, not just mine. In the reference implementation's threat model each of these is a numbered row, and each row is backed by a currently-green negative test.

### 16.1 · Invariant 1 — verify the session first

The bridge route mints a code only *after* your auth library confirms a real session. Not on a header, not on a "I'm inside an iframe" signal, not on anything the client says about itself. No session — 401, nothing minted.

▸ What breaks without it: anyone who can spoof a context header gets a code for free, and a code is a session. Middleware is routing. The server-side session check is the boundary. I'll say that twice because it's the one that gets skipped under deadline: middleware is routing; the server check is the boundary.

### 16.2 · Invariant 2 — the code is a receipt, not a key

▸ The code itself: 256 bits of CSPRNG output — `randomBytes(32)`, one entropy site, never hand-rolled. ▸ Single use — delete-on-read in memory, atomic `GETDEL` in KV. ▸ And a TTL capped at sixty seconds — and if you configure a longer one, construction *throws*. No silent clamp. That last bit is deliberate: a config that quietly extends sixty seconds to ten minutes is exactly how "short-lived" stops being true without anyone noticing.

▸ And be honest with yourself about what sits in that store: the session cookie's value. The actual token, for up to sixty seconds. Which means the transfer store has to be trusted exactly like your session database — same network boundary, same access rules. The TTL cap and delete-on-read aren't pedantry; they're what keeps that window small. Encrypting the parked value with a server-side key is a follow-up I haven't shipped yet — I'd rather say that than pretend it's there.

▸ So: first consume, 302 and a cookie. Second consume of the same code — 4xx, no cookie. A leaked or replayed code is inert.

### 16.3 · Invariant 3 — trust the sender twice

The `postMessage` receiver. Two checks. `event.origin` must be in the allowlist — everyone does this one. *And* `event.source` must be the popup window you actually opened.

▸ Wrong origin — dropped, obviously. ▸ But why the second check? Because of the same-origin racer. Another tab, another frame, *of your own origin*, can post to the opener. The origin check passes it — it's your origin! Pinning the source is the second lock. ▸ And a dropped message must not settle the flow — a later valid one still should. This is the one almost nobody tests.

### 16.4 · Invariant 4 — zero tokens in URLs, for the whole roundtrip

No session token in any client-constructed URL, response body, or message payload. The *only* thing permitted in a URL is the opaque code, in `?code=`. A token in a URL lives forever — history, logs, referrers, screenshots.

▸ The subtle part is the phrase "whole roundtrip". Every component can pass its own test while the *composition* leaks — one helper builds a URL from another's output. So the end-to-end test sweeps every URL the client builds across the whole flow, not per component.

### 16.5 · Invariant 5 — redirect hygiene **[cut-candidate]**

The `?next=` parameter after sign-in. One function, `sanitizeNext`: anything under `/auth` or `/api/auth` is rejected — that's the auth-loop case; absolute URLs, protocol-relative `//evil`, and — the one you'd miss — backslash `/\evil`, which some parsers normalise to a protocol-relative URL. All fall back to `/`. Open redirect and auth loop, closed in one place.

### 16.6 · Invariant 6 — only a same-origin fetch may redeem

This one I added *after* shipping, so it gets its own story.

The code was already one-time and sixty seconds. And that was not enough. Think about login CSRF: I, the attacker, sign in to the app with *my* account, mint a code for *my* session — legitimately — and send you a link to `/auth/consume?code=…`. You click. The code is valid. You're now signed in as me, and whatever you type into the app lands in my account.

▸ The fix is Fetch Metadata. The consume route accepts only `Sec-Fetch-Site: same-origin` and `Sec-Fetch-Dest: empty` — that is, a `fetch()` from the app's own page. ▸ A top-level navigation, an `<img>` load, a cross-site fetch — all 4xx. The store isn't even touched, so the real code survives for the real opener. And the rejection is byte-identical to a forged-code rejection — no oracle. Browsers set these headers; page script can't set or strip them.

One honest note: a request with *no* Fetch Metadata at all falls through to the Origin check. Every supported browser sends it, so you can't trigger that from a browser; it exists so the test bench and non-browser clients don't break. A future major may close it. The proper structural fix — binding the code to the window that opened the popup, PKCE-style — is the planned follow-up.

### 16.7 · The checklist

Here's the whole list on one slide. Take a photo. Session first. One-time, sixty seconds, 256 bits. Origin *and* source. No token in any URL — at roundtrip level. Redirect hygiene. Same-origin-fetch-only redemption. If you have a popup auth scheme in production, go through these six tomorrow.

### 16.8 · What the tests don't prove

And the honest boundary. The Node test suite proves the `Partitioned` attribute is *emitted*, that data flows end-to-end, and every negative case I just listed. It does *not* prove that a real browser *isolates* the partition — that's a property of the browser's CHIPS implementation, and you can only check it in a browser. I did: two live origins, positive and negative case, written down in the repo. Also: that a credentialed `fetch` — not a navigation — commits the cookie under the right top-level site. That was an open question until I tried it.

If you adopt the pattern, run that live check in *your* browser matrix. CHIPS is Chrome and Edge 114, Firefox 130, Safari 18.

---

## 17 · Where the library lives

Now the "two libraries" promise. Here's the entire configuration. Where does the auth library live in it? Two values: `verifySession` and `cookieName`. The store, the origin allowlist, the routes, the popup, the client helpers — none of it knows which library you use.

This is also *why* the bridge copies the cookie instead of minting a fresh session on the far side. "Create a session for user X" is a deeply library-specific operation — Auth.js doesn't expose one for the JWT strategy, Better Auth has one but it's its own shape. "Copy the cookie your library already issued" works with any cookie-session library. The seam is two values precisely because the bridge moves a cookie, not an identity.

Why does this matter? Auth.js — NextAuth — is effectively in maintenance mode, and the ecosystem's momentum has moved to Better Auth. If your auth library is a thing you might swap in two years, the piece that carries your session across contexts must not be the piece that pins you.

### 17.1 · Better Auth — the two lines

Same config, Better Auth. Watch what moves. `verifySession` becomes `auth.api.getSession` with the request headers. `cookieName` becomes `getBetterAuthCookieName({ secure: true })` — derived, not hardcoded, because the `__Secure-` prefix rule bit me once; there's a `__Secure-__Secure-` bug in the changelog. Everything else is byte-identical. Any other cookie-session library plugs into the same two values.

### 17.2 · Wiring in 20 lines **[go fast]**

For completeness, the rest of the wiring. Two route files, one line each — `bridge` and `consume` are plain `Request → Response` functions. A middleware that does *UX routing only* — it rewrites unauthenticated embedded requests to the popup entry page; it is not a security boundary, we covered that. It imports from the `/middleware` subpath because the package root reaches `node:crypto` and won't bundle for Edge. The popup page: `runPopupFlow`, then `window.close()`. And the launcher in the iframe: `openAuthPopup`, then `fetch` consume with `credentials: 'include'` — that's what commits the cookie under the right partition — then reload. There's no magic. The volume is small.

### 17.3 · Cold start **[cut-candidate]**

One more case: a first-time user with no app session at all, but a live host SSO. ▸ The demo apps' popup handles it with exactly one `prompt=none` attempt against the shared IdP, ▸ with a one-shot guard so it can't loop. ▸ If it comes back `login_required`, you get a "sign in on the host first" notice — never an interactive login inside the popup. ▸ Scoping note: this only works when host and app share an identity provider — Entra in Microsoft 365, Keycloak in my demos. The warm handoff is the fully general core; this is a nice extra.

---

## 18 · The afternoon I lost to `window.opener`

One bug story, because it taught me the lesson I most want you to leave with.

▸ The cold-start path *navigates* the popup — off to the IdP and back — before it can `postMessage` the code to its opener. I was *certain* this would break the bridge. My mental model said: navigate the popup, `window.opener` becomes null, the popup loses its reference to the iframe, the code has nowhere to go. So I built an elaborate fallback — stash the code server-side, poll for it from the opener.

▸ Then I actually tested it. Chrome, and Safari in private mode. `window.opener` survived the entire redirect round-trip. The code posted fine. The fallback was dead code.

▸ What I'd confused: it's not *navigation* that severs the opener relationship. It's COOP — `Cross-Origin-Opener-Policy: same-origin`. That header puts the page in a fresh browsing-context group and *that* nulls the opener. A plain redirect, no COOP, keeps it. I'd attributed to "navigation" a behaviour that belongs to a specific security header.

▸ I deleted the fallback. ▸ And the lesson: when a cross-context assumption feels obvious, the browser is the only authority worth trusting. Verify it in two engines before you build around it. — And the practical corollary: if your IdP or your app *does* set COOP `same-origin`, *then* you have this problem, and now you know why.

## 19 · Where the same bridge goes next

Back to the origin story. The other half of that task was iOS — a WKWebView that has no access to the device's passkeys, autofill, or the session the user already has in Safari. Same shape: a primary session in one context, a secondary context that needs its own. The same handle store, a different transport — the system auth session instead of a popup, and a URL callback instead of `postMessage`. That transport isn't my invention: it's RFC 8252, OAuth 2.0 for Native Apps — the system browser instead of a WebView, a one-time code coming back over a redirect. The bridge is what you get when you take that RFC seriously on both platforms. One shape, two transports. That's the next talk.

## 20 · Back to the four constraints

The clipboard. Inherit the existing host SSO — yes, the popup inherits it. Silently — one sub-second flash, no prompt. No token where it can leak — only a sixty-second, single-use receipt ever crosses. No lock-in — two libraries, two live demos, two lines of difference.

## 21 · Where the work ended up

Three things I owe you. The popup-bridge pattern was co-developed with Kirill Evtushenko. Working it through — the invariants, the tests, the two libraries — turned into a package: `next-auth-bridge`, my generalisation of the pattern. It's version 0.3.1, a few months old, no meaningful adoption yet — a reference implementation, not battle-tested infrastructure; treat it as one way to express the idea. And it's a clean-room build — no employer code; everything you saw on screen is from the public repo and the two Keycloak demos.

## 22 · Thanks

That's the bridge. The repo, the threat model, and both demos are at the QR — and RFC 8252, if you want to read where the native half comes from. Questions — and if nobody has one, I'll start with the one I always get: "why not just put a JWT in the URL?"

---

## Appendix — Q&A pocket answers

**Why not a JWT in the URL or in `postMessage`?** A token in a URL lives in history, logs, referrers and screenshots. A token in a message payload is a bearer sitting in JavaScript. The code is worthless after one use and sixty seconds; the token isn't. That asymmetry is the whole design.

**Older Safari / no CHIPS?** Chrome/Edge 114+, Firefox 130+, Safari 18+. Below that, fall back to the Storage Access prompt or a host-level "sign in first" notice — degraded, not broken.

**Why cap the TTL at construction instead of clamping?** Because a clamp is silent and a throw is loud. Security config that fails quietly drifts.

**What about the no-Fetch-Metadata fall-through?** Every supported browser sends `Sec-Fetch-*`; the fall-through exists for the Node bench and non-browser clients. It's covered by a test and may flip to fail-closed in a future major.

**Logout — the session is now in two cookie jars.** The popup's first-party jar (the popup closed, the cookie didn't) and the iframe's partitioned jar hold the same session. Signing out in one context clears one cookie. With database sessions the server-side invalidation covers both; with JWT sessions both copies stay valid until expiry — same as any multi-tab JWT setup. If that matters to you, keep sessions server-side.

**Does this need Next.js?** No. Two server routes, a popup page, a `postMessage` listener. Any framework with server routes.

**Auth.js status?** Effectively maintenance mode in 2026; momentum has moved to Better Auth. Which is exactly why the seam is two values and not a plugin.
