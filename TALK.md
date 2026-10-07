# A Bridge the Token Never Crosses — speaker script

> Full spoken text, slide by slide. ~3,600 words ≈ 26–28 min at a calm pace, plus the demo. Slide numbers are the horizontal slide count as the deck's corner shows it (reveal's URL hash is zero-based, so slide N is `#/N-1`); vertical sub-slides are N.1, N.2… **▸ = click (next fragment appears)**; a slide with no ▸ has no fragments.

---

## 1 · Title

Hi. Ok, let's start.
The talk is called "A Bridge the Token Never Crosses", a little bit poetic, but the title is literally the whole talk. I'm going to carry a user's session across an origin boundary — from a page that has it to an iframe that doesn't — and the one thing that will never make the trip is the session token itself. Sounds like magic? Follow me, and by the end you'll know exactly what *does* cross, and why that turns out to be enough.

## 2 · Disclaimer *(joke)*

Before we start, a disclaimer. This talk might cause an uncontrolled desire for snacks — we'll be talking about cookies and chips for twenty-five minutes, and none of them are edible. ▸ …and diabetes. *(beat)*

## 3 · Who's talking

I'm Azat. I'm a software architect and tech lead, and I've been writing JavaScript for a bit over ten years. One thing up front: tonight is about a pattern, not a product. If you walk out of here and hand-roll your own version — that's a win, as long as it passes the checklist I'll give you later.

*[your joke line]*

▸ *(the ad block appears)* — "Vibe-coded your JS app and not sure it's safe? Better call Azat." One line, no more.

## 4 · Origin story

This came out of a real project. An enterprise AI assistant for a large pharma company — one Next.js codebase, two ways of reaching users.

▸ Inside SharePoint and Teams the assistant ran inside an iframe. The user was signed in on the host — SharePoint knew who they were. But inside our iframe, they were anonymous. Our app couldn't see the host's session at all.

▸ Same app on iOS, inside a WebView. The user is already signed in in Safari, passkeys are on the phone — and the WebView can't see any of that.

Two platforms, two separate bug reports. And it took me a while to notice that it was the same bug. ▸ Session lives next door, our app is anonymous, and we must not ask them to log in again.

Once you see it as one shape, the fix is one shape too.

## 5 · That shape is the bridge *(meme)*

That shape is the bridge. *(beat — let the room react, then move on)*

## 6 · What you'll leave with

Four things. ▸ A mental model — a one-time ticket across a gap you don't trust. Everything else is transport. ▸ Five rules you can hold up against *any* popup-or-iframe auth scheme. ▸ Where CHIPS — partitioned cookies — helps, and where it doesn't. ▸ And working wiring for both Auth.js and Better Auth, so you can see the pattern is not tied to a library.

---

## 7 · The setup

Here's the situation. Your Next.js app lives inside somebody else's page. SharePoint web part, Teams tab, Salesforce Lightning component, ServiceNow, Confluence — choose your fighter. The host already has the user signed in against a shared identity provider — in the Microsoft world that's Entra.

Ten years ago this was boring. The iframe just saw the same cookies as the host, and life went on.

## 8 · Your cookie became a third-party cookie

What changed is that your cookie became a *third-party* cookie — and to see why that's fatal, look at what the browser is actually fighting. ▸ A third-party cookie is the primitive of cross-site tracking: one ad pixel embedded on a thousand sites, one cookie, one profile of you. Browsers decided to kill that.

▸ And here's the problem for us: your embedded app, to the browser, is the same shape. A foreign origin, inside someone else's page, asking for its cookies. ▸ The browser can't tell the two apart, so the fix was blunt — no cookies for foreign origins inside a page. We're collateral damage of anti-tracking.

▸ Safari blocked this years ago — ITP in 2017, a full block by 2020. Firefox partitions by default. Chrome kept third-party cookies — except incognito and enterprise policy, which is exactly where this app lives. You cannot rely on them. Full stop. And every fix that tries to "get the cookie back" is fighting the browser.

## 9 · Four obvious fixes

So what do people try? Four things, and each one breaks either the UX or the architecture.

▸ **Sign in again inside the iframe.** The first instinct. Three reasons it fails: it's a redundant login — the user signed in thirty seconds ago; the identity provider very often refuses to render inside a frame at all — `X-Frame-Options`, `frame-ancestors`, you've seen the blank box; and — the one people miss — even if the redirect completes, the cookie it sets is *still* a third-party cookie. You're back where you started.

▸ **The Storage Access API.** `document.requestStorageAccess()`. A real API, designed for roughly this situation, and it doesn't fit: it needs a user gesture *and* shows a permission prompt — and silent SSO with a prompt is not silent. Support is uneven. And more fundamentally, it solves *access* — "let my frame read its own cookies" — not *inheritance*. It won't give you the host's session.

▸ **The vendor SDK.** Auth0, Okta, Clerk — they all solve this, inside their own ecosystem. And that's the trade: you now rent your identity, which is precisely the thing self-hosted cookie-session auth — Auth.js, Better Auth — exists to avoid. Not a bad choice for some teams. Just name the trade honestly.

▸ **CHIPS.** Cookies with the `Partitioned` attribute. Someone on the team reads the spec and says "we just set `Partitioned` and we're done". Hold that thought — next slide.

## 10 · CHIPS: a cookie your frame can keep

Back to CHIPS, because this is the one that matters. A partitioned cookie is a cookie your frame *can keep*. ▸ It is not a cookie your frame *already has*. ▸ Your partition — keyed by your origin plus the host's top-level site — starts empty. CHIPS gives you a place to store a session in the embedded context. It does nothing to create one.

▸ Hold onto that jar, because we *will* use it — on the far side of the bridge.

## 11 · What we actually want

So here's the spec. Inherit the *existing* host SSO — not a new login. Silently — no prompt. No session token anywhere it can leak. And no vendor lock-in. Keep these four on your mental clipboard. We'll check them off at the end.

---

## 12 · The one realisation

Everything that follows comes from one sentence.

The iframe is the wrong place to do OAuth. A popup runs in the *top-level* browsing context. And in the top-level context, the identity provider's cookies are *first-party*. The user's existing session is right there.

That's it. That's the trick. Everything else is making it safe.

## 13 · The bridge, step by step

### 13.1 · Step one
Let me walk the flow. Four lanes: the iframe — your app, embedded; the popup — also your app, but top-level; your app's server; and the identity provider.

The iframe opens a popup to `/auth/popup` — on *your* origin, not the host's. The host never runs any of your code. That's why the same pattern ports to SharePoint, Teams, Salesforce, whatever.

### 13.2 · Step two
In that popup, your auth library does a completely normal OAuth sign-in. Nothing custom. The popup is top-level, so the IdP sees its own first-party cookies, finds the live session, and comes back with no prompt. Your server sets a session cookie — in the popup's first-party jar. The only new thing is *where* this runs.

### 13.3 · Step three
This is where the title happens.

The popup calls `POST /auth/bridge`. The server checks there is a real session, parks it for sixty seconds, and returns a one-time ticket. The popup never gets the token — only the ticket.

### 13.4 · Step four
The popup `postMessage`s that ticket to the iframe — with an explicit target origin, never `*`. The iframe checks the sender's origin *and* the sender's window. Why both — in a few minutes.

### 13.5 · Step five
The iframe redeems the ticket: `fetch('/auth/consume?code=…', { credentials: 'include' })`. The server deletes it on first read and answers with `Set-Cookie` — `Partitioned` — into the jar we said was empty. CHIPS couldn't create the session; it can keep the one we just delivered.

The popup closes. The user saw a flash for under a second. The iframe reloads, signed in.

## 14 · The whole shape

Same trick as OAuth: a short-lived code crosses the untrusted bit, the real session is swapped for it on the server. We just moved the boundary — not browser to IdP, but popup to iframe. Native apps do this too; I'll come back to that.

## 15 · Demo

Let me show you it's real. *(live)*

Two deployments, two Vercel origins, one self-hosted Keycloak — so the cross-site handoff is genuine, not faked on a single origin. Both run on an open-source reference implementation of the pattern that I wrote; I'll come back to it at the end — for now it's just "the repo". I sign in on the host… and the embedded app signs itself in. Open DevTools, Application, Cookies — there's the session cookie, and there's the `Partitioned` column.

Second deployment — same flow, same bridge, but the app underneath is Better Auth instead of Auth.js. Hold that thought; we'll come back to it.

*(If the network is dead: narrate it over the diagram — "this is where the popup would flash" — and move on. Don't fight it.)*

---

## 16 · Five rules

Now the part I actually care about: five rules. Remove *any one* of them and the bridge becomes a hole. I'll go through them with one question: what breaks without it? This list works against any popup-and-iframe scheme, not just mine.

### 16.1 · Rule 1 — verify the session first

The bridge route issues a ticket only *after* your auth library confirms a real session. Not on a header, not on a "I'm inside an iframe" signal, not on anything the client says about itself. No session — 401, nothing issued.

▸ What breaks without it: anyone who can spoof a context header gets a ticket for free, and a ticket is a session. I'll say this twice because it's the one that gets skipped under deadline: middleware is routing; the server check is the boundary.

### 16.2 · Rule 2 — the ticket is not the key

The ticket is not the key. Two hundred fifty-six random bits, one use, sixty seconds — if you configure a longer TTL, construction *throws*. Be honest about what sits in that store: the real session cookie, for up to sixty seconds. Treat the store like your session database. First consume, a cookie. Second consume of the same ticket — 4xx, nothing. A leaked ticket is inert.

### 16.3 · Rule 3 — trust the sender twice

The `postMessage` receiver. Two checks. `event.origin` must be in the allowlist — everyone does this one. *And* `event.source` must be the popup window you actually opened.

▸ Wrong origin — dropped, obviously. ▸ But why the second check? Because of the same-origin racer. Another tab, another frame, *of your own origin*, can post to the opener. The origin check passes it — it's your origin! Pinning the source is the second lock. ▸ And a dropped message must not settle the flow — a later valid one still should. This is the one almost nobody tests.

▸ One gotcha on this leg that cost me an afternoon: it's not navigation that severs `window.opener` — a popup can go to the IdP and back and keep it. What severs it is `Cross-Origin-Opener-Policy: same-origin`. If your app or your IdP sets that header on the popup, the opener is null, there's nobody to post the code to, and the bridge fails silently. Check it in two engines before you build on it.

### 16.4 · Rule 4 — zero tokens in URLs, for the whole roundtrip

No session token in any URL, response body, or message. The *only* thing allowed in a URL is the ticket, in `?code=`. A token in a URL lives forever — history, logs, referrers, screenshots.

▸ "Whole roundtrip" matters: each piece can look fine while together they leak. So the end-to-end test sweeps every URL the client builds, not per component.

### 16.5 · Rule 5 — only a same-origin fetch may redeem

This one I added *after* shipping, so it gets its own story.

The ticket was already one-time and sixty seconds. And that was not enough. Think about login CSRF: I, the attacker, sign in with *my* account, mint a ticket for *my* session — legitimately — and send you a link to `/auth/consume?code=…`. You click. The ticket is valid. You're now signed in as me, and whatever you type into the app lands in my account.

▸ The fix is Fetch Metadata. The consume route accepts only a `fetch()` from the app's own page — `Sec-Fetch-Site: same-origin`, `Sec-Fetch-Dest: empty`. A top-level navigation, an `<img>` load, a cross-site fetch — all 4xx. The store isn't touched, so the real ticket survives for the real opener. Browsers set these headers; page script can't fake them.

### 16.6 · The checklist

Here's the whole list on one slide. Take a photo. Session first. One-time, sixty seconds, 256 bits. Origin *and* source. No token in any URL — at roundtrip level. Same-origin-fetch-only redemption. In the reference implementation's threat model these are called invariants, and each one is backed by a negative test. If you have a popup auth scheme in production, go through these five tomorrow.

### 16.7 · What the tests don't prove

And the honest boundary. The Node tests prove we emit `Partitioned`, that data flows, and every negative case I just listed. They do *not* prove a real browser *isolates* the partition — I had to check that in a browser. I did: two live origins, written down in the repo. Also that `fetch` — not a navigation — actually sets the cookie in the iframe's jar.

If you adopt the pattern, run that live check in *your* browsers. CHIPS is Chrome and Edge 114, Firefox 130, Safari 18.

---

## 17 · Where the library lives

Now the "two libraries" promise. Here's the entire configuration. Where does the auth library live in it? Two values: `verifySession` and `cookieName`. The store, the origin allowlist, the routes, the popup, the client helpers — none of it knows which library you use.

This is also *why* the bridge copies the cookie instead of minting a fresh session on the far side. "Create a session for user X" is a deeply library-specific operation — Auth.js doesn't expose one for the JWT strategy, Better Auth has one but it's its own shape. "Copy the cookie your library already issued" works with any cookie-session library. The seam is two values precisely because the bridge moves a cookie, not an identity.

Why does this matter? Auth.js — NextAuth — is effectively in maintenance mode, and the ecosystem's momentum has moved to Better Auth. If your auth library is a thing you might swap in two years, the piece that carries your session across contexts must not be the piece that pins you.

### 17.1 · Better Auth — the two lines

Same config, Better Auth. Watch what moves. `verifySession` becomes `auth.api.getSession` with the request headers. `cookieName` becomes `getBetterAuthCookieName({ secure: true })` — derived, not hardcoded, because the `__Secure-` prefix rule bit me once; there's a `__Secure-__Secure-` bug in the changelog. Everything else is byte-identical. Any other cookie-session library plugs into the same two values.

### 17.2 · Wiring in 20 lines

Two routes. A popup page. A few lines in the iframe. That's the whole wiring.

## 18 · Where the same bridge goes next

Back to the origin story. The other half of that task was iOS — a WebView that can't see the device's passkeys, autofill, or the Safari login sitting next door. Same shape: session lives next door, our app needs its own. Same store, a different transport — the system browser instead of a popup, a URL callback instead of `postMessage`. That's RFC 8252, OAuth for native apps. The bridge is what you get when you take that RFC seriously on both platforms. One shape, two transports. That's the next talk.

## 19 · Back to the four constraints

The clipboard. Inherit the existing host SSO — yes, the popup inherits it. Silently — one sub-second flash, no prompt. No token where it can leak — only a sixty-second, single-use ticket ever crosses. No lock-in — two libraries, two live demos, two lines of difference.

## 20 · Where the work ended up

Three things I owe you. The popup-bridge pattern was co-developed with Kirill Evtushenko. Working it through — the rules, the tests, the two libraries — turned into a package: `next-auth-bridge`, my generalisation of the pattern. It's version 0.3.1, a few months old, no meaningful adoption yet — a reference implementation, not battle-tested infrastructure; treat it as one way to express the idea. And it's a clean-room build — no employer code; everything you saw on screen is from the public repo and the two Keycloak demos.

## 21 · Thanks

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
