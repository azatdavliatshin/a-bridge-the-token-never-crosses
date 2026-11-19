# A Bridge the Token Never Crosses -- speaker script

> Full spoken text, slide by slide. ~3,600 words ≈ 26–28 min at a calm pace, plus the demo. Slide numbers are the horizontal slide count as the deck's corner shows it (reveal's URL hash is zero-based, so slide N is `#/N-1`); vertical sub-slides are N.1, N.2… **▸ = click (next fragment appears)**; a slide with no ▸ has no fragments.

---

## 1 · Title

Hi.
The talk is called "A Bridge the Token Never Crosses". The title is the thesis. I'm gonna carry a user's session across an origin boundary -- from a page that has it to an iframe that doesn't -- and the session token itself never makes the trip. By the end you'll know exactly what does cross, and why that's enough.

## 2 · Disclaimer *(joke)*

Disclaimer. Half an hour of cookies and chips. May make you want a snack. ▸ The food stand is right over there. *(point)*

## 3 · Who's talking

I'm Azat. I'm a software architect and tech lead at Quantori -- we build software for life-science and healthcare companies -- and I've been writing JavaScript for a bit over ten years. Lately I spend most of my time on one question: how sessions and tokens cross trust boundaries -- between browser contexts, and between AI agents. Today is the browser half.

## 4 · Origin story

This came out of a real project. An enterprise AI assistant for a large pharma company -- one Next.js codebase, two ways of reaching users.

▸ Inside SharePoint and Teams the assistant ran inside an iframe. The user was signed in on the host -- SharePoint knew who they were. But inside our iframe, they were anonymous. Our app couldn't see the host's session at all.

▸ Same app on iOS, inside a WebView. The user is already signed in in Safari, passkeys are on the phone -- and the WebView can't see any of that.

Two platforms, two separate bug reports. And it took me a while to notice that it was the same bug. ▸ Session lives next door, our app is anonymous, and we must not ask them to log in again.

Once you see it as one shape, the fix is one shape too.

## 5 · That shape is the bridge *(meme)*

That shape is the bridge. A request walks up to it, and all it carries is a ticket.

▸ The keeper asks his questions. Answer wrong, and you don't cross.

▸ Answer right, and you get a cookie. Notice what never showed up in this scene: the token.

## 6 · What you'll leave with

Four things. ▸ A mental model -- a one-time ticket across a gap you don't trust. Everything else is transport. ▸ Five invariants that *any* popup-or-iframe auth scheme has to hold. ▸ Where CHIPS -- partitioned cookies -- helps, and where it doesn't. ▸ And working wiring for Auth.js and Better Auth -- two open-source auth libraries for JavaScript apps, where the session lives in your own cookie, not at a vendor -- so you can see the pattern is not tied to a library.

---

## 7 · Same cookie, different page

Before the problem itself, one definition -- because the whole talk stands on it: "first-party" and "third-party" are not kinds of cookies. They're a property of the *page*. ▸ Open `app.example` in a tab -- that's the address bar -- and the cookie your server set for `app.example` is first-party. The browser sends it. ▸ Now open `host.example`, which loads `app.example` in an iframe. Same cookie, same server, same user. But the address bar says `host.example`, so to the browser that cookie is now third-party -- and it's blocked. ▸ Nothing about the cookie changed. The context did. Your cookie became a third-party cookie: the browser re-classified it based on who's in the address bar.

## 8 · The setup

Here's the situation. Your web app -- mine was Next.js, but nothing here depends on it -- lives inside somebody else's page. SharePoint web part, Teams tab, Salesforce Lightning component, ServiceNow, Confluence -- choose your fighter. The host already has the user signed in against a shared identity provider -- in the Microsoft world that's Entra.

Ten years ago this was boring. The iframe just saw the same cookies as the host, and life went on. Now you know why it doesn't: that cookie is third-party here.

## 9 · Your cookie became a third-party cookie

What changed is that your cookie became a *third-party* cookie -- and to see why that's fatal, look at what the browser is actually fighting. 
▸ A third-party cookie is the primitive of cross-site tracking: one ad pixel embedded on a thousand sites, one cookie, one profile of you. Browsers decided to kill that.

▸ And here's the problem for us: your embedded app, to the browser, is the same shape. A foreign origin, inside someone else's page, asking for its cookies. 
▸ The browser can't tell the two apart, so the fix was blunt -- no cookies for foreign origins inside a page. We're collateral damage of anti-tracking.

▸ Safari blocked this years ago -- ITP in 2017, a full block by 2020. Firefox partitions by default. Chrome kept third-party cookies -- except incognito and enterprise policy, which is exactly where this app lives. You cannot rely on them. Full stop. And every fix that tries to "get the cookie back" is fighting the browser.

## 10 · Four obvious fixes

So what do people try? Four things, and each one breaks either the UX or the architecture.

▸ **Sign in again inside the iframe.** The first instinct. Three reasons it fails: it's a redundant login -- the user signed in thirty seconds ago; the identity provider very often refuses to render inside a frame at all -- `X-Frame-Options`, `frame-ancestors`, you've seen the blank box; and -- the one people miss -- even if the redirect completes, the cookie it sets is *still* a third-party cookie. You're back where you started.

▸ **The Storage Access API.** `document.requestStorageAccess()`. A real API, designed for roughly this situation, and it doesn't fit: it needs a user gesture *and* shows a permission prompt -- and silent SSO with a prompt is not silent. Support is uneven. And more fundamentally, it solves *access* -- "let my frame read its own cookies" -- not *inheritance*. It won't give you the host's session.

▸ **The vendor SDK.** Auth0, Okta, Clerk -- they all solve this, inside their own ecosystem. And that's the trade: you now rent your identity, which is precisely the thing self-hosted cookie-session auth -- Auth.js, Better Auth -- exists to avoid. Not a bad choice for some teams. Just name the trade honestly.

▸ **CHIPS.** Cookies with the Partitioned attribute. This one we actually keep. It still doesn't sign the user in though.

## 11 · CHIPS: a cookie your frame can keep

CHIPS gets its own slide, because it's the one that matters. A partitioned cookie is a cookie your frame *can keep*.
▸ It is not a cookie your frame *already has*.
▸ Your partition -- keyed by your origin plus the host's top-level site -- starts empty. CHIPS gives you a place to store a session in the embedded context. It does nothing to create one.

▸ Hold onto that jar, because we *will* use it -- on the far side of the bridge.

## 12 · What we actually want

So here's the spec.
▸ Inherit the *existing* host SSO -- not a new login.
▸ Silently -- no prompt.
▸ No session token anywhere it can leak. 
▸ And no vendor lock-in. Keep these four on your mental clipboard. We'll check them off at the end.

---

## 13 · The one realisation

Everything that follows comes from one sentence.

The iframe is the wrong place to do OAuth. A popup runs in the *top-level* browsing context. And in the top-level context, the identity provider's cookies are *first-party*. The user's existing session is right there.

That's it. That's the trick. Everything else is making it safe.

## 14 · The bridge, step by step

### 14.1 · Step one
Let me walk the flow. Four lanes: the iframe -- your app, embedded; the popup -- also your app, but top-level; your app's server; and the identity provider.

The iframe opens a popup to `/auth/popup` -- on *your* origin, not the host's. The host never runs any of your code. That's why the same pattern ports to SharePoint, Teams, Salesforce, whatever.

### 14.2 · Step two
In that popup, your auth library does a completely normal OAuth sign-in. Nothing custom. The popup is top-level, so the IdP sees its own first-party cookies, finds the live session, and comes back with no prompt. Your server sets a session cookie -- in the popup's first-party jar. The only new thing is *where* this runs. Two of our four requirements are already met: we inherited the host's sign-in, and nobody was prompted. You'll see them turn green at the bottom of the slide.

### 14.3 · Step three
This is where the title happens.

The popup calls `POST /auth/bridge`. The server checks there is a real session, parks it for sixty seconds, and returns a one-time ticket. The popup never gets the token -- only the ticket.

### 14.4 · Step four
The popup `postMessage`s that ticket to the iframe -- with an explicit target origin, never `*`. The iframe checks the sender's origin *and* the sender's window. Why both -- in a few minutes.

### 14.5 · Step five
The iframe redeems the ticket: `fetch('/auth/consume?code=…', { credentials: 'include' })`. The server deletes it on first read and answers with `Set-Cookie` -- `Partitioned` -- into the jar we said was empty. CHIPS couldn't create the session; it can keep the one we just delivered.

The popup closes. The user saw a flash for under a second. The iframe reloads, signed in. And the third requirement is met: the token never left the server side -- only the ticket crossed.

## 15 · The whole shape

Same trick as OAuth: a short-lived code crosses the untrusted bit, the real session is swapped for it on the server. We just moved the boundary -- not browser to IdP, but popup to iframe. Native apps do this too, btw, and we'll come back to it at the end.

## 16 · Demo

Let me show you it's real. *(live)*

Two deployments, two Vercel origins, one self-hosted Keycloak -- so the cross-site handoff is genuine, not faked on a single origin. Both run on an open-source reference implementation of the pattern that I wrote. I sign in on the host… and the embedded app signs itself in. Open DevTools, Application, Cookies -- there's the session cookie, and there's the `Partitioned` column.

Second deployment -- same flow, same bridge, but the app underneath is Better Auth instead of Auth.js. Hold that thought; we'll come back to it.

*(If the network is dead: narrate it over the diagram -- "this is where the popup would flash" -- and move on. Don't fight it.)*

---

## 17 · Five invariants

Now the part I actually care about: five invariants -- five things that must be true every single time. Remove *any one* of them and the bridge becomes a hole. I'll go through them with one question: what breaks without it? This list works against any popup-and-iframe scheme, not just mine.

### 17.1 · Invariant 1 -- verify the session first

The bridge route issues a ticket only ▸ *after* your auth library confirms a real session. Not on a header, not on a "I'm inside an iframe" signal, not on anything the client says about itself. No session -- 401, nothing issued.

▸ What breaks without it: anyone who can spoof a context header gets a ticket for free, and a ticket is a session. I'll say this twice because it's the one that gets skipped under deadline: middleware is routing; the server check is the boundary.

### 17.2 · Invariant 2 -- the ticket is not the key

The ticket is not the key.
▸ Two hundred fifty-six random bits.
▸ One use.
▸ Sixty seconds -- if you configure a longer TTL, construction *throws*.
▸ Be honest about what sits in that store: the real session cookie, for up to sixty seconds. Treat the store like your session database. 
▸ First consume, a cookie. Second consume of the same ticket -- 4xx, nothing. A leaked ticket is inert.

### 17.3 · Invariant 3 -- trust the sender twice

The `postMessage` receiver. Two checks. `event.origin` must be in the allowlist -- everyone does this one. *And* `event.source` must be the popup window you actually opened.

▸ Wrong origin -- dropped, obviously.
▸ But why the second check? Because of the same-origin racer. Another tab, another frame, *of your own origin*, can post to the opener. The origin check passes it -- it's your origin! Pinning the source is the second lock.
▸ And a dropped message must not settle the flow -- a later valid one still should. This is the one almost nobody tests.

### 17.4 · Invariant 4 -- zero tokens in URLs, for the whole roundtrip

No session token in any URL, response body, or message. The *only* thing allowed in a URL is the ticket, in `?code=`. A token in a URL lives forever -- history, logs, referrers, screenshots.

▸ "Whole roundtrip" matters: each piece can look fine while together they leak. So the end-to-end test sweeps every URL the client builds, not per component.

### 17.5 · Invariant 5 -- only a same-origin fetch may redeem

This one I added *after* shipping, so it gets its own story.

The ticket was already one-time and sixty seconds. And that was not enough. Think about login CSRF: I, the attacker, sign in with *my* account, mint a ticket for *my* session -- legitimately -- and send you a link to `/auth/consume?code=…`. You click. The ticket is valid. You're now signed in as me, and whatever you type into the app lands in my account.

▸ The fix is Fetch Metadata. The consume route accepts only a `fetch()` from the app's own page -- `Sec-Fetch-Site: same-origin`, `Sec-Fetch-Dest: empty`. 

▸ A top-level navigation, an `<img>` load, a cross-site fetch -- all 4xx. The store isn't touched, so the real ticket survives for the real opener. Browsers set these headers; page script can't fake them.

### 17.6 · The checklist

Here's all five. Each row has a test behind it, and that test runs in Node.

### 17.7 · What the tests don't prove

Those Node tests prove we emit `Partitioned`, that data flows, and every negative case I just listed. They do not prove a real browser *isolates* the partition -- I had to check that in a browser. I did, in Chrome: two live origins, written down in the repo. I also checked there that a `fetch`, not a navigation, actually sets the cookie in the iframe's jar.

If you adopt the pattern, run that live check in *your* browsers -- and check the versions. CHIPS is Chrome and Edge 114, Firefox 141, Safari 26.2. And it did not arrive in a straight line: in both Safari and Firefox it showed up, went away, and came back between releases.

---

## 18 · The reference implementation

Here's the repo I've been calling "the reference implementation": `next-auth-bridge`, on npm and GitHub, MIT. It's the pattern you just saw, with the five invariants written down as a threat model and a negative test behind each one. It runs on Auth.js and on Better Auth, and the two live demos are deployed from it. How do you put it into a Next.js app?

### 18.1 · Adding the bridge to a Next.js app

Enough theory. `npm install`, six files. The numbers next to the files are the bridge steps you already saw. ▸ One config -- store, origins, and the auth-library seam.
▸ Two routes -- bridge and consume.
▸ One popup page -- runs top-level, posts the ticket, closes.
▸ One launcher -- opens the popup, redeems the ticket, reloads.
▸ One middleware -- sends embedded, unauthenticated users to the popup entry.

### 18.2 · The config -- where the auth library lives

First file: the config. One call, `createAuthBridge`, and it gives you the two handlers you'll see next. Most of it is plumbing -- where tickets are stored, which origins are allowed.
▸ The part that matters is two values: `verifySession` and `cookieName`. With Auth.js the second one is the default, so you see one line. That's the whole library-specific part -- everything else has no idea whether this is Auth.js. And notice what's missing: nothing here creates a session. Creating a session is different in every library, so the bridge doesn't do it: it copies the cookie your library already set.

### 18.3 · Better Auth -- the two lines

Watch what moves -- two lines. That's the point: this piece doesn't pin you to Auth.js. And that's the last item on the clipboard: no lock-in. All four green.

### 18.4 · The routes

The server side is two route files, and each one is a one-liner: it hands the request to the library.
▸ `bridge` is step three from the diagram: verify the session, park the cookie, mint the ticket.
▸ `consume` is step five: redeem the ticket, set the partitioned cookie. Both are plain request in, response out -- nothing Next-specific, so the same two handlers run in any framework with server routes.

### 18.5 · The popup page

This is the flash. Sign-in runs here because it's top-level.
▸ Then `runPopupFlow` posts the ticket -- never `*` -- and the window closes.

▸ One gotcha when you wire this, and it's that `window.opener` on the screen. The popup leaves for the IdP and comes back, and I spent an afternoon sure that the opener died on the way. It doesn't -- redirects keep it. What does null it is `Cross-Origin-Opener-Policy: same-origin` on this page. Then there's nobody to post the ticket to, and the bridge fails silently. So check your headers on `/auth/popup`.

### 18.6 · The launcher

Fourth file: the launcher. This is the code that runs inside the iframe.
▸ It opens the popup and waits for the ticket. That one call is steps one and four from the diagram -- and the origin and source checks from Invariant 3 live inside it.
▸ Then it redeems: a `fetch` to `/auth/consume` with `credentials: "include"`, and a reload. That fetch is Invariant 5 -- only a same-origin fetch may redeem -- and `include` is what puts the cookie in the iframe's jar. If the popup is blocked or closed, you get an error with the reason; that's the line at the bottom.

### 18.7 · The middleware

Last file: the middleware. Its only job is convenience -- an embedded visitor with no session gets routed to the popup entry page.
▸ It has its own import path, because middleware runs on the Edge runtime and the rest of the library needs Node's crypto.
▸ And look at what it checks: that a cookie is *present*. Not that it's valid. So this is routing, not security -- I said it at Invariant 1, and here it is in code. The real gate is `verifySession` on `/auth/bridge`.

## 19 · Where the same bridge goes next

Back to the origin story. The other half of that task was iOS -- a WebView that can't see the device's passkeys, autofill, or the Safari login sitting next door. Same shape: session lives next door, our app needs its own. Same store, a different transport -- the system browser instead of a popup, a URL callback instead of `postMessage`. That's RFC 8252, OAuth for native apps. The bridge is what you get when you take that RFC seriously on both platforms. One shape, two transports. That's the next talk.

## 20 · Back to the four constraints

The clipboard. Inherit the existing host SSO -- yes, the popup inherits it. Silently -- one sub-second flash, no prompt. No token where it can leak -- only a sixty-second, single-use ticket ever crosses. No lock-in -- two libraries, two live demos, two lines of difference.

## 21 · Where the work ended up

Three things I owe you. The pattern was co-developed with Kirill Evtushenko. Working it through became a package, next-auth-bridge, version 0.3.1. And it's clean-room: no employer code. Everything you saw on screen is from the public repo and the two Keycloak demos.

## 22 · Thanks

That's the bridge. The repo, the threat model, and both demos are at the QR -- and RFC 8252, if you want to read where the native half comes from. Questions?

---

## Appendix -- Q&A pocket answers

**Why not a JWT in the URL or in `postMessage`?** A token in a URL lives in history, logs, referrers and screenshots. A token in a message payload is a bearer sitting in JavaScript. The code is worthless after one use and sixty seconds; the token isn't. That asymmetry is the whole design.

**Older Safari / no CHIPS?** Chrome/Edge 114+, Firefox 141+, Safari 26.2+. Safari had it in 18.4 and lost it in 18.5; Firefox listed it in 131 and re-enabled it in 141. Below those versions, fall back to the Storage Access prompt or a host-level "sign in first" notice -- degraded, not broken.

**Why cap the TTL at construction instead of clamping?** Because a clamp is silent and a throw is loud. Security config that fails quietly drifts.

**What about the no-Fetch-Metadata fall-through?** Every supported browser sends `Sec-Fetch-*`; the fall-through exists for the Node bench and non-browser clients. It's covered by a test and may flip to fail-closed in a future major.

**Logout -- the session is now in two cookie jars.** The popup's first-party jar (the popup closed, the cookie didn't) and the iframe's partitioned jar hold the same session. Signing out in one context clears one cookie. With database sessions the server-side invalidation covers both; with JWT sessions both copies stay valid until expiry -- same as any multi-tab JWT setup. If that matters to you, keep sessions server-side.

**Who sets COOP, and what if the IdP does?** Nobody by default -- it's a response header your own server (Next.js headers, `helmet`, CDN config) or the IdP's pages add. Check that `/auth/popup` is served without `Cross-Origin-Opener-Policy: same-origin` (`same-origin-allow-popups` is fine), and look at the IdP's headers once in Network. If the IdP sets `same-origin`, `window.opener` is gone on the way back and the bridge needs a fallback: the popup parks the ticket server-side and the opener polls for it.

**Does this need Next.js?** No. Two server routes, a popup page, a `postMessage` listener. Any framework with server routes.

**Auth.js status?** Effectively maintenance mode in 2026; momentum has moved to Better Auth. Which is exactly why the seam is two values and not a plugin.
