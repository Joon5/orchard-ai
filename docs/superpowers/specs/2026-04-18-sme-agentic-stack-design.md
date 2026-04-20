# SME Agentic Stack — Design Spec

**Date:** 2026-04-18
**Status:** Approved for implementation planning

---

## 1. Product Overview

A multi-tenant SaaS platform that acts as a virtual office manager for small trade businesses (handymen, locksmiths, plumbers, electricians, HVAC, etc.). The platform handles everything a business owner doesn't have time or technical skill to do: a professional website, online booking, AI-powered customer communication across all channels, calendar management, and analytics. The trade professional focuses entirely on doing the work.

### Target customer

Independent or small-team trade businesses with 1–5 employees. They typically have no website, answer calls personally (or miss them), and schedule jobs via text messages or mental notes. They are rarely at a desk. All interaction with the platform must be possible from a phone in under 3 taps.

### Operator role (you, Jonathan)

You onboard each client, set up their website using Claude Design and an AI agent, connect their calendar and phone number, and hand them the dashboard. Ongoing, the system is nearly autonomous. You manage all clients through a super-admin panel.

---

## 2. Pricing

| Tier | Setup Fee | Monthly |
|------|-----------|---------|
| Phase 1 — Foundation | $500 (one-time) | $349/month |
| Phase 2 — Voice Add-on | Included in Phase 1 setup | +$149/month |

**Free trial:** First month free for all new clients.

**Suggested upsell moment:** After 30 days, show the client their missed call count. If it's meaningful, offer the voice add-on.

---

## 3. Architecture

The platform is a Next.js monorepo deployed on Vercel with Supabase as the data and auth layer. All client-facing websites are served from subdomains (`client-slug.platform.com`) with optional custom domain support. Phase 2 voice AI plugs into the same booking engine as Phase 1 — it is an input adapter, not a redesign.

### Tech stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Web / API | Next.js 14 (App Router) | All web surfaces: client sites, dashboards, API routes |
| Database | Supabase Postgres (RLS) | Multi-tenant data, row-level security per tenant |
| Auth | Supabase Auth | Business owner login, admin login |
| Storage | Supabase Storage | Business photos, logo uploads |
| Realtime | Supabase Realtime | Live dashboard updates (new bookings, notifications) |
| Hosting | Vercel | Web + API deployment, subdomain routing via wildcard |
| SMS | Twilio Programmable SMS | Outbound confirmations, reminders, inbound replies |
| Email | Resend | Booking confirmations, digests |
| AI — all tasks | Claude Haiku (Anthropic) | Chat widget, summaries, SMS replies, review responses, quote logic |
| Billing | Stripe | Subscription management ($349 + $149 add-on), setup fee |
| Calendar — primary | Google Calendar API (OAuth) | Default, recommended to all clients |
| Calendar — fallback | CalDAV | Apple Calendar, Outlook compatibility |
| Website design workflow | Claude Design (claude.ai/design) | Operator-side tool for designing each client's site |

### Phase 2 — Voice AI additions

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Voice infrastructure | Twilio Voice + Media Streams | Receive inbound calls, stream raw audio via WebSocket |
| Speech-to-text | Deepgram Nova-2 (streaming) | Transcribe customer speech in real time |
| LLM (voice calls) | Claude Haiku | Booking logic, FAQs, rough quotes, escalation detection |
| Text-to-speech | Deepgram Aura-2 | Synthesize AI responses, return audio to Twilio |

---

## 4. Multi-Tenancy Model

Each client (tenant) is a row in a `tenants` table. Supabase Row Level Security ensures complete data isolation — a tenant can only read and write their own data. The operator (super-admin) bypasses RLS using a service role key only accessible server-side.

Each tenant gets:
- A unique slug (`joes-plumbing`) → subdomain `joes-plumbing.platform.com`
- Optional custom domain (CNAME to Vercel)
- Their own Twilio phone number (provisioned at onboarding)
- Their own calendar connection (OAuth token stored encrypted)
- Their own Stripe subscription
- Their own AI configuration (services list, service area, business hours, tone)

---

## 5. Data Model (core tables)

```
tenants              — one row per client business
  id, slug, name, phone, address, service_area, business_hours, active, plan

services             — services offered by each tenant
  id, tenant_id, name, description, price_range, duration_estimate

contacts             — end customers (homeowners, etc.)
  id, tenant_id, name, phone, email, created_at

appointments         — booked jobs
  id, tenant_id, contact_id, service_id, scheduled_at, status, notes, calendar_event_id

conversations        — all AI-handled interactions (phone, SMS, chat)
  id, tenant_id, contact_id, channel (phone|sms|chat|email), started_at, summary, full_transcript

notifications        — push/SMS alerts sent to business owner
  id, tenant_id, type, message, read, created_at

reviews              — reviews collected/monitored per tenant
  id, tenant_id, source (google|yelp), rating, body, ai_response, owner_override, created_at

users                — business owner accounts
  id, tenant_id, email, role (owner|admin)
```

---

## 6. Phase 1 — Foundation (target: 6–8 weeks)

### 6.1 Client-facing website (per tenant)

Three-page site served at `[slug].platform.com` or custom domain. All content is populated from the tenant record in Supabase. The operator sets up and styles the site using Claude Design — the business owner never touches HTML or CSS.

**Home page sections (in order):**
1. Navigation bar — business name, logo, phone number, "Book Now" CTA button
2. Hero — headline ("Your trusted local plumber"), subheadline, photo, "Book Now" button
3. Services — card grid pulled from the `services` table (shown on both Home and Booking page)
4. Reviews — pulled from `reviews` table, displayed as testimonial cards
5. Footer — address, phone, service area, link to booking page

**About page sections:**
1. Owner photo + bio
2. Years in business, certifications, service area
3. "Book Now" CTA

**Contact & Booking page sections:**
1. Services list (same data as Home)
2. Booking form — 4 fields: service (dropdown from tenant services), preferred date/time, name, phone
3. Contact info — phone, email, address
4. AI chat widget (bottom-right corner, persistent across all pages)

**Chat widget behavior:**
- Powered by Claude Haiku with a tenant-specific system prompt (services, hours, service area, tone)
- Handles: FAQs, booking intent collection, rough quote questions
- If user wants to book, guides them to the booking form or collects details inline
- All conversations stored in `conversations` table with AI-generated summary

### 6.2 Booking engine

The booking engine is the core of the system. Everything — web form, chat widget, SMS, and Phase 2 voice — writes to and reads from it.

**Flow:**
1. Customer submits booking form (service, date/time, name, phone)
2. API checks calendar availability for requested time slot
3. If available: create appointment record → create Google Calendar event → send SMS confirmation to customer → send push notification to owner
4. If unavailable: suggest 2–3 alternative times (nearest open slots from calendar)
5. On confirmation: send reminder SMS 24 hours before appointment

**Cancellation / rescheduling:**
- Customer replies "CANCEL" to any SMS → appointment marked cancelled, calendar event deleted, owner notified
- Customer replies "RESCHEDULE" → AI SMS conversation to find new time

### 6.3 Communications layer

**Outbound SMS (Twilio):**
- Booking confirmation: immediately after booking
- Reminder: 24 hours before appointment
- Follow-up: 24 hours after appointment ("How did it go? We'd love a review: [link]")
- Urgent flag: if owner is alerted to a priority situation

**Inbound SMS:**
- CONFIRM / CANCEL / RESCHEDULE keywords handled automatically
- Any other inbound SMS → Claude Haiku responds in context (knows appointment history for that contact)
- All SMS threads stored in `conversations` table

**Email (Resend):**
- Booking confirmation (fallback if no phone number)
- Owner: weekly digest (bookings, calls handled, missed calls, reviews)

### 6.4 Owner dashboard

Mobile-first. The owner uses this on their phone between jobs.

**Home screen:**
- Today's appointments in a timeline list (time, customer name, job type, address)
- Count of new notifications since last visit
- Quick stats: this week's bookings, open inquiries

**Calendar view:**
- Month/week/day toggle
- All appointments synced bidirectionally with their connected calendar
- Tap any appointment to see contact details, job notes, call/text shortcut

**Conversations (AI summary view):**
- Default: AI-generated daily summary ("3 new inquiries today — 2 booked, 1 asked about pricing for deck repair")
- Tap to expand: full list of conversations that day
- Tap any conversation to see full transcript (chat, SMS, or call — Phase 2)

**Reviews:**
- List of reviews with AI-generated responses shown
- Badge on any review flagged as important (1–2 stars, mentions a specific complaint)
- Owner can override AI response and submit their own (this feature is present but not prominently displayed in the UI — accessible via a secondary action)

**Analytics:**
- Weekly / monthly view: total inquiries, bookings made, conversion rate, missed contacts
- Simple bar charts — no overwhelming dashboards

**Notifications:**
- New booking arrives → push notification + SMS to owner
- Review flagged as important → push notification
- Weekly digest SMS (opt-in)

**Website editor (minimal):**
- Business name, phone number, tagline
- Services list (add/remove/edit name and price range)
- Owner bio and photo upload
- Business hours
- Nothing else — all design/layout is locked and managed by the operator

### 6.5 Admin panel (operator view)

Accessible only to the super-admin (you, Jonathan).

**Client list:**
- All tenants with status (active, trial, churned), plan tier, next billing date
- Quick links: open their dashboard, open their public site, view billing

**Provision new client:**
- Form: business name, owner name, email, phone, services (comma-separated), service area, calendar type
- On submit: creates tenant record, provisions Twilio number, sends owner a "Your site is live" email with login link
- Website content populated from the form — you then use Claude Design to style and refine it

**Usage overview:**
- Calls handled (Phase 2), SMS sent, bookings made across all clients this month

---

## 7. Phase 2 — Voice AI Extension (target: weeks 8–16)

Voice is a new input channel. It reuses all of Phase 1's booking engine, calendar integration, and notification system without modification. The voice pipeline is isolated behind a single internal API: `POST /api/voice/handle-turn` which accepts `{ tenant_id, transcript, call_context }` and returns `{ response_text, action }`.

### 7.1 Inbound call flow

1. Customer calls the tenant's Twilio phone number
2. Twilio webhook fires → `POST /api/voice/inbound`
3. **Keyword router:** first 3 seconds of speech analyzed for urgency signals ("emergency", "flooding", "locked out of my car right now") → if detected, immediately forward to owner's personal mobile number via Twilio `<Dial>`
4. Otherwise: connect to Media Streams WebSocket
5. WebSocket server receives raw audio → streams to Deepgram Nova-2 STT
6. On speech segment complete → send transcript to Claude Haiku with conversation context
7. Haiku response → Deepgram Aura-2 TTS → audio chunks → back to Twilio → caller hears response
8. If booking intent confirmed: call booking engine (same function as web form), send SMS confirmation to caller
9. On call end: full transcript stored in `conversations` table → Claude Haiku generates summary → dashboard updated

### 7.2 Voice agent capabilities

The voice AI can:
- Greet caller, identify the business by name ("Thank you for calling Joe's Plumbing")
- Collect service request, preferred date/time, caller name and phone
- Answer FAQs from the tenant's configured knowledge base (services, hours, service area)
- Provide rough price ranges from the `services` table
- Book an appointment end-to-end (calls the booking engine)
- Detect urgency and escalate (forward call to owner)
- Handle "I'm an existing customer" flows: look up by phone number, confirm/reschedule/cancel

The voice AI cannot:
- Provide exact prices (always says "from approximately $X — we'll confirm when we see the job")
- Make commitments outside business hours without owner approval
- Handle complex multi-leg conversations beyond 10 turns without offering to call back

### 7.3 Call routing rules (per tenant, configurable)

- Business hours: calls during hours → AI agent. After hours → AI agent with "we're closed, I can book for tomorrow" messaging
- Urgent keywords: always forward to owner regardless of hours
- Owner unavailable (forwarded call not answered): AI takes a message, sends owner an SMS summary

### 7.4 WebSocket server

A standalone Node.js WebSocket server deployed as a persistent process (Railway or Fly.io — NOT Vercel, which has a 10-second execution limit incompatible with 5-minute phone calls). It handles the real-time audio stream between Twilio, Deepgram, and Claude. This is the most latency-sensitive and the only non-serverless component in the stack.

Estimated cost: ~$5–10/month on Railway free/hobby tier, shared across all voice clients.

Target: end-to-end latency from speech-end to response-audio-start < 2 seconds.

---

## 8. UX Principles

### Business owner (your client)

- **Mobile-first, always.** Every screen designed for a 390px phone screen first. Desktop is secondary.
- **Maximum 3 taps** to complete any common action (see today's jobs, confirm a booking, view a review)
- **Push-first information delivery.** The owner should not need to open the app to stay informed. Push notifications and SMS digests deliver what matters
- **AI does the reading.** The owner sees summaries, not raw data. Full transcripts are available on demand but never shown by default
- **Locked design.** They cannot break the website. The operator (you) controls layout and styling via Claude Design

### End customer (homeowner booking a job)

- **No account, no app, no friction.** They arrive, they book, they get a confirmation. Done.
- **4-field booking form maximum.** Service, date/time, name, phone. Nothing else.
- **Immediate confirmation.** SMS within seconds of booking. No "we'll confirm within 24 hours."
- **The platform is invisible.** Branded entirely as the trade business. No mention of the platform.
- **24/7 AI response.** If they chat or SMS at 11pm, they get a real answer immediately — not a voicemail

---

## 9. Website Design Workflow (Operator)

When onboarding a new client:
1. Collect: business name, owner name, phone, services list, service area, business hours, owner bio, 1–2 photos
2. Use **Claude Design** (claude.ai/design) to generate a clean, mobile-optimized design matching the business type (trade-specific color palette, professional but approachable)
3. Export design decisions (colors, fonts, hero copy) → enter into admin panel's website config for that tenant
4. The Next.js client site template applies those values at render time — no manual HTML

Target: a complete, live, beautiful website for a new client in under 2 hours of operator time.

---

## 10. Unit Economics (per client per month)

### Phase 1 — Foundation ($349/month)

| Cost Item | Monthly |
|-----------|---------|
| Twilio phone + SMS | ~$2.73 |
| Claude Haiku (chat, summaries, SMS) | ~$3.00 |
| Resend email | ~$0.50 |
| Supabase (amortized across clients) | ~$1.50 |
| Vercel hosting (amortized) | ~$1.00 |
| **Total infra** | **~$9/month** |
| **Gross margin** | **97%** |

### Phase 2 — Voice Add-on (+$149/month)

| Additional Cost Item | Monthly (medium: 150 calls) |
|-----------|---------|
| Twilio Voice inbound (750 min) | ~$6.38 |
| Deepgram STT (750 min) | ~$3.23 |
| Deepgram TTS | ~$3.00 |
| Claude Haiku (voice logic) | ~$1.50 |
| **Additional infra** | **~$14/month** |
| **Voice add-on margin** | **91%** |

### Combined Phase 2 client: ~$23/month infra, $498/month revenue = 95% gross margin

---

## 11. Key Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Voice AI latency unacceptable in production | Medium | High | Build Phase 1 first; validate booking engine before adding voice. Can swap to Vapi/Retell if needed without changing anything else. |
| Twilio A2P 10DLC SMS registration delays | High | Medium | Start registration at client onboarding. Budget 2–4 weeks per client. Phase 1 works without it via short codes or toll-free as interim. |
| Google Business Profile API access denied | Medium | Low | Phase 1 review feature works with manually entered reviews; Google API is an enhancement, not a blocker |
| Client churn after free trial | Medium | High | Prove ROI clearly — show "X calls handled, Y bookings made" on the dashboard from day 1 of the trial |
| Conversation AI gives wrong information | Medium | Medium | All AI responses include a soft disclaimer ("pricing confirmed on-site"); urgent matters always escalated to owner |
| Competing with Jobber / Housecall Pro | Low (short term) | Medium | Those tools target office managers, not trade people. This targets the solo operator who wants zero admin. Different positioning. |

---

## 12. Scope Boundaries

### In scope (Phase 1)
- Multi-tenant Next.js platform with subdomain routing
- 3-page client website (Home, About, Contact/Booking)
- Online booking form with calendar availability check
- Google Calendar OAuth integration (CalDAV fallback)
- Automated SMS (Twilio): confirmations, reminders, follow-ups, inbound handling
- Email confirmations (Resend)
- AI chat widget (Claude Haiku, streaming)
- Owner dashboard: calendar, AI summaries, analytics, notifications, minimal editor
- Admin panel: client list, provisioning, billing management
- Stripe subscription billing ($500 setup + $349/month)
- AI review management (display + auto-respond)

### In scope (Phase 2)
- Twilio Voice inbound + Media Streams
- Deepgram Nova-2 STT + Aura-2 TTS
- Voice agent (booking, FAQs, quotes, urgency escalation)
- Call transcripts + summaries in dashboard
- Configurable call routing rules per tenant

### Secrets & environment management

All API keys (Twilio, Deepgram, Anthropic, Stripe, Resend) stored as Vercel environment variables. Per-tenant OAuth tokens (Google Calendar) stored encrypted in Supabase using a server-side encryption key. No secrets in source code or client-side bundles.

### Out of scope (future phases)
- Outbound calling / follow-up calls
- Invoicing and payment collection
- Job photo uploads by owner
- Customer-facing booking app (native mobile)
- Multi-worker scheduling (multiple employees)
- Yelp / other review platform integrations beyond read-only
