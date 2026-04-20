# SME Agentic Stack — v2 Spec (Leaner, Shippable)

**Date:** 2026-04-18
**Status:** Revised after red-team review — ready for implementation planning

---

## 1. Product Overview

A multi-tenant SaaS platform that gives solo trade businesses (handymen, locksmiths, plumbers, HVAC technicians) a professional online presence and automated customer intake. The platform answers the question: "How does a one-person trade business compete for customers when they're always on the job?" It does this by handling the phone-and-website layer so the owner never has to leave a job to answer an inquiry.

The operator (Jonathan) onboards each client manually — builds the website, connects the calendar, provisions the phone number, and hands the owner a login. After that, the platform runs with minimal owner interaction. It is not autonomous; it is low-maintenance.

**What the platform does:**
- Gives the business a professional 3-page website with online booking
- Sends automated SMS confirmations and reminders to customers
- Lets customers cancel or reschedule via SMS keyword replies
- Provides an AI chat widget that answers FAQs and collects booking intent 24/7
- Notifies the owner instantly when a new job is booked
- Shows the owner their day's jobs in a clean mobile dashboard
- Phase 2 (separate): Answers inbound calls with an AI voice agent

**What the platform does not do (v1):**
- Respond to Google reviews automatically (legal/TOS risk — deferred)
- Display or manage reviews (no data pipeline exists in v1)
- Send email (SMS is sufficient for trade ICP; email adds complexity)
- Sync from Google Calendar into the platform (one-way only: platform writes to Google Calendar)
- Support Apple or Outlook calendar (Google OAuth only in v1)
- Provide analytics charts (numbers only)
- Handle voice calls (Phase 2)

---

## 2. Narrowed ICP

**Primary:** Solo trade operator, 0–2 employees, US-based, English-speaking, owns a smartphone, has a Google account or is willing to create one. Specifically: handymen, locksmiths, independent plumbers, electricians, HVAC technicians. They have no website or a broken/outdated one. They schedule jobs by text message or phone call. They miss jobs because they're on-site when calls come in.

**Not the ICP (v1):** Multi-worker shops with dispatching needs. Businesses with existing software (Jobber, ServiceTitan). Businesses with a dedicated admin/office staff. Businesses outside the US (A2P registration is US-specific; international is a Phase 4 problem).

**ICP validation requirement:** Before implementation starts, confirm at least 2 real conversations with solo trade operators who expressed willingness to pay $299/month for this specific set of capabilities.

---

## 3. Pricing and Packaging

| Tier | Setup Fee | Monthly (post-trial) | Annual Option |
|------|-----------|---------------------|---------------|
| Foundation (Phase 1) | $500 | $299/month | $2,990/year ($249/mo) |
| Foundation + Voice (Phase 2 add-on) | Included in $500 | +$149/month | +$1,490/year |

**Trial:** 30 days free, starting on go-live date (not on payment date). Stripe subscription activates automatically at trial end.

**Setup fee covers:** 2 hours of operator time to build website via Claude Design, provision Twilio TFN, connect Google Calendar, configure AI system prompt, and hand off dashboard login.

**Upsell trigger for voice add-on:** Show owner their missed call metric after 30 days (only available after Phase 2 is built). If > 10 missed calls, offer voice add-on in the dashboard with one-tap upgrade.

**What $299/month is not:** It is not a seat license, not usage-based, not tiered by features. One flat price for one business.

---

## 4. Architecture

### Hosting and deployment
- **Next.js 14 (App Router)** — all web surfaces: client websites, owner dashboard, admin panel, API routes
- **Vercel** — deployment and wildcard subdomain routing (`*.platform.com`)
- **Railway** (Phase 2 only) — persistent WebSocket server for voice pipeline; cannot use Vercel for this

### Data and auth
- **Supabase Postgres** — primary database, row-level security (RLS) per tenant
- **Supabase Auth** — owner login, admin login
- **Supabase Storage** — business photos and logo uploads
- **Supabase Realtime** — live dashboard updates (new bookings appear without refresh)

### Communications
- **Twilio Programmable SMS** — all SMS: outbound confirmations/reminders and inbound keyword handling
- **Twilio Voice + Media Streams** (Phase 2) — inbound call handling, audio streaming

### AI
- **Claude Haiku (Anthropic)** — chat widget, conversation summaries, inbound SMS context replies
- **Deepgram Nova-2** (Phase 2) — speech-to-text, streaming
- **Deepgram Aura-2** (Phase 2) — text-to-speech

### Calendar
- **Google Calendar API (OAuth2)** — write-only from platform in v1 (appointments are written to calendar; calendar is never read for availability)
- CalDAV deferred to Phase 3

### Background jobs
- **Inngest** — scheduled jobs: 24-hour reminder SMS, post-job follow-up SMS, daily summary generation. Inngest is required in v1; without it, reminders never fire.

### Billing
- **Stripe** — subscriptions, setup fees, trial management, webhook-driven status updates

### Tech stack summary table

| Layer | Technology |
|-------|-----------|
| Web / API | Next.js 14 App Router |
| Database | Supabase Postgres (RLS) |
| Auth | Supabase Auth |
| Storage | Supabase Storage |
| Realtime | Supabase Realtime |
| Hosting | Vercel |
| SMS | Twilio Programmable SMS |
| AI (text) | Claude Haiku |
| Background jobs | Inngest |
| Billing | Stripe |
| Calendar | Google Calendar API (write-only, v1) |
| Voice infra (P2) | Twilio Voice + Media Streams |
| STT (P2) | Deepgram Nova-2 |
| TTS (P2) | Deepgram Aura-2 |
| Voice server (P2) | Node.js on Railway |

---

## 5. Multi-Tenancy Model

Each client is one row in `tenants`. Supabase RLS ensures tenants cannot access each other's data. The operator uses a server-side service role key (never exposed client-side) to manage all tenants.

Each tenant has:
- A unique slug → subdomain `slug.platform.com` (optional custom domain via CNAME)
- One Twilio Toll-Free Number (provisioned at onboarding, A2P-registered before go-live)
- One Google Calendar OAuth connection (token stored encrypted, refresh handled automatically)
- One Stripe subscription
- One AI configuration (services, service area, business hours, owner name, timezone)

**Google OAuth token refresh:** The platform checks token expiry on every calendar write. If within 7 days of expiry or already expired, it auto-refreshes using the stored refresh token. If refresh fails (user revoked access), a notification is sent to the owner's phone and the admin panel flags the tenant.

---

## 6. Revised Data Model

```sql
tenants
  id                    uuid PK
  slug                  text UNIQUE
  name                  text                -- business display name
  owner_name            text
  owner_email           text
  owner_mobile_phone    text                -- for urgent SMS notifications and call forwarding (P2)
  phone                 text                -- Twilio TFN (customer-facing number)
  address               text
  service_area          text
  timezone              text NOT NULL       -- e.g. 'America/Chicago' — REQUIRED
  business_hours        jsonb               -- {mon: {open:'08:00', close:'18:00'}, ...}
  active                boolean DEFAULT true
  plan                  text                -- 'foundation' | 'foundation_voice'
  trial_ends_at         timestamptz
  stripe_customer_id    text
  stripe_subscription_id text
  calendar_id           text                -- Google Calendar ID (not always 'primary')
  google_oauth_token    jsonb               -- encrypted access + refresh token
  ai_config             jsonb               -- tone, FAQ overrides, max_price_quote flag
  created_at            timestamptz DEFAULT now()

services
  id                    uuid PK
  tenant_id             uuid FK → tenants
  name                  text
  description           text
  price_range           text                -- e.g. '$75–$200'
  duration_minutes      int                 -- used to set calendar event end time
  active                boolean DEFAULT true

contacts
  id                    uuid PK
  tenant_id             uuid FK → tenants
  name                  text
  phone                 text                -- primary identifier (phone-first, not email)
  email                 text
  address               text                -- customer's home/job address if known
  preferred_contact     text DEFAULT 'sms'  -- 'sms' | 'email'
  created_at            timestamptz DEFAULT now()

appointments
  id                    uuid PK
  tenant_id             uuid FK → tenants
  contact_id            uuid FK → contacts
  service_id            uuid FK → services
  scheduled_date        date NOT NULL
  time_window           text NOT NULL       -- 'morning' | 'afternoon' | 'flexible' | 'exact'
  scheduled_time        time                -- only populated if time_window = 'exact'
  duration_minutes      int                 -- copied from service at booking time
  address               text NOT NULL       -- where the job is
  job_notes             text                -- customer free text
  status                text DEFAULT 'pending'  -- 'pending'|'confirmed'|'in_progress'|'completed'|'cancelled'
  calendar_event_id     text                -- Google Calendar event ID (for deletion/update)
  booked_via            text                -- 'web_form'|'chat'|'sms'|'voice'
  created_at            timestamptz DEFAULT now()
  updated_at            timestamptz DEFAULT now()

conversations
  id                    uuid PK
  tenant_id             uuid FK → tenants
  contact_id            uuid FK → contacts
  appointment_id        uuid FK → appointments  -- null if no booking resulted
  channel               text                -- 'chat'|'sms'|'voice'
  started_at            timestamptz
  ended_at              timestamptz
  summary               text                -- AI-generated, 1–3 sentences
  full_transcript       jsonb               -- array of {role, content, timestamp}
  created_at            timestamptz DEFAULT now()

notifications
  id                    uuid PK
  tenant_id             uuid FK → tenants
  type                  text                -- 'new_booking'|'cancellation'|'urgent_call'|'system_alert'
  message               text
  read                  boolean DEFAULT false
  action_url            text                -- deep link into dashboard
  created_at            timestamptz DEFAULT now()

users
  id                    uuid PK
  tenant_id             uuid FK → tenants    -- null for super-admin
  email                 text UNIQUE
  role                  text                -- 'owner' | 'admin'
  push_token            text                -- for push notifications
  created_at            timestamptz DEFAULT now()
```

---

## 7. Revised Booking Lifecycle

**Source of truth:** The platform database is the only authoritative record of appointments. Google Calendar is a display convenience. The owner's phone calendar is not trusted for availability.

**Booking form fields (6, not 4):**
1. Service (dropdown from tenant services)
2. Date (date picker)
3. Time preference (morning 8am–12pm / afternoon 12pm–5pm / flexible)
4. Job address (text input, required)
5. Your name
6. Your phone number

**Availability logic (v1):**
- No real-time availability check against Google Calendar
- Platform checks: are there already 2+ confirmed appointments in the requested time window on the requested date?
- If yes: show alternative dates with fewer bookings
- If no: accept booking
- This is simple and robust. The owner can always manually decline or reschedule via SMS or dashboard.

Rationale: True availability checking requires bidirectional calendar sync, which is error-prone. In v1, the owner is the final arbiter of their schedule. The platform handles intake and notification; the owner confirms or adjusts as needed.

**Booking flow:**
1. Customer submits 6-field form
2. Platform creates `contact` record (upsert by phone number) + `appointment` record (status: pending)
3. Send SMS to customer: "Hi [name], we've received your request for [service] at [address] on [date] ([time window]). [Owner name] will confirm shortly. Reply CANCEL to cancel."
4. Send push notification + SMS to owner: "New booking: [service] at [address] on [date] ([time window]). Tap to confirm."
5. Owner taps "Confirm" in dashboard → appointment status → confirmed → calendar event created in Google Calendar → customer receives confirmation SMS: "Your appointment with [business] is confirmed for [date] ([time window]). We'll remind you the day before."
6. Inngest fires at T-24h: reminder SMS to customer
7. Inngest fires at T+24h: follow-up SMS to customer: "Thanks for choosing [business]! How did everything go? Reply back anytime if you need us."

**Cancellation:**
- Customer replies CANCEL → appointment marked cancelled, Google Calendar event deleted, owner notified via push + SMS
- Owner cancels in dashboard → same outcome + customer notified

**Rescheduling:**
- Customer replies RESCHEDULE → SMS asks for new preferred date and time window → creates new pending appointment → follows same confirmation flow
- In v1, reschedule via SMS is a simple 2-step exchange (Claude Haiku handles it inline)

---

## 8. Revised Channel Strategy

**v1: SMS is the primary channel. Everything else is secondary.**

| Channel | v1 Role | Notes |
|---------|---------|-------|
| SMS (Twilio TFN) | Primary — all customer communication | Booking confirmations, reminders, follow-ups, inbound handling |
| AI chat widget | Secondary — website only | FAQ + booking intent; hands off to booking form |
| Email (Resend) | Not in v1 | Defer — SMS covers 100% of ICP needs |
| Phone calls | Not in v1 | Phase 2 |

**SMS registration:** Every tenant gets a Toll-Free Number. TFN verification is submitted at onboarding. Client does not go live until TFN is verified. This is a hard operational rule — no exceptions.

**Inbound SMS handling:**
- CANCEL → cancel matching appointment (match by contact phone number + nearest future appointment)
- RESCHEDULE → 2-turn AI conversation to collect new date/window, then create new pending appointment
- Any other content → Claude Haiku responds with context (knows their appointment history and the business's services/hours). Response is limited to: appointment status, business hours, service area. Haiku does not make new bookings via inbound SMS — it directs to the website.
- All inbound SMS stored as conversation records

**AI chat widget:**
- Handles: service questions, business hours, service area, rough price ranges from services table
- Can collect booking intent (all 6 fields) and create a pending appointment directly
- Hard guardrail: widget does not make availability promises. It books with status: pending and sets expectation that owner confirms.
- Hard guardrail: widget does not quote exact prices. It uses the price_range field: "Typically $X–$Y, confirmed on-site."
- Hard guardrail: widget does not discuss any topic unrelated to the business's services. If asked about anything off-topic, responds: "I can only help with [business name] inquiries."
- Hard guardrail: if the widget cannot answer after 3 attempts, it says "I'll have [owner name] follow up with you. Can I confirm your phone number?" and creates a notification for the owner.

---

## 9. Hard Guardrails for AI Behavior

These rules are enforced via system prompt and are not soft suggestions.

**Chat widget:**
1. Never quote exact prices — always use price_range from services table with "confirmed on-site" caveat
2. Never confirm availability for a specific time — always say "we'll confirm your preferred time shortly"
3. Never discuss competitors, legal matters, or complaints about past work
4. Never invent services not in the tenant's services table
5. Never claim the business is available outside configured business_hours
6. After 3 failed attempts to understand a request, collect phone number and escalate to owner
7. Collect all 6 booking fields before creating an appointment record

**Inbound SMS:**
1. Only respond to messages from contacts with an existing appointment or a number that has booked before
2. First-time inbound from unknown number → respond with booking link only
3. Never send more than 2 SMS messages in response to a single inbound message
4. Never discuss pricing in SMS — direct to website for quotes

**All AI-generated content:**
1. Never post anything externally without human approval (reviews, social media — not in v1)
2. Summaries use past tense and are factual, not interpretive: "Customer asked about [service] pricing. They booked for [date]." Not "Customer seemed interested in upgrading."

---

## 10. Phase 1 — Implementation Plan (8 weeks)

**Week 1–2: Foundation**
- Supabase schema (all tables from revised data model above)
- Supabase Auth (owner + admin roles)
- Next.js monorepo with App Router
- Wildcard subdomain routing on Vercel
- Admin panel: tenant list + provision form
- Stripe integration: subscription creation, webhook handling, trial management
- Google Calendar OAuth: connect flow + encrypted token storage + auto-refresh logic

**Week 3–4: Booking engine + SMS**
- 6-field booking form (public, per tenant)
- Appointment creation with simple availability check (platform-side only)
- Twilio TFN provisioning at onboarding
- Outbound SMS: pending booking notification to owner + customer
- Owner confirm/decline via dashboard → confirmed SMS to customer → Google Calendar event creation
- CANCEL/RESCHEDULE inbound SMS handling
- Inngest: 24h reminder job, 24h post-job follow-up job

**Week 5–6: Client website + chat widget**
- 3-page client website template (Home, About, Contact/Booking) driven by tenant config
- Owner website editor (name, phone, tagline, services, hours, bio, photo only)
- AI chat widget (Claude Haiku streaming, tenant-specific system prompt, hard guardrails)
- Cloudflare Turnstile on booking form + rate limiting (5 submissions/phone/24h)

**Week 7: Owner dashboard**
- Today's jobs list (home screen)
- Upcoming calendar view (appointments from platform DB, not Google Calendar)
- New booking push notifications (Supabase Realtime + push token)
- Tap appointment → contact details, job address, notes, SMS shortcut
- Conversations: AI-summary-first, drill-down to transcript

**Week 8: Polish + onboarding tooling**
- Admin panel: usage overview, billing status, quick impersonate-tenant link
- Error monitoring (Sentry or similar)
- Google OAuth token expiry monitoring + admin alert
- TFN registration status tracking in admin panel
- Internal onboarding checklist per tenant (calendar connected? TFN verified? services added?)
- First real client onboarded by end of week 8

---

## 11. Phase 2 — Voice AI (Weeks 9–16, separate scope)

Voice is architecturally isolated. The only Phase 1 code it calls is the booking engine and the notification dispatcher. No Phase 1 code changes are required.

New infrastructure: Railway Node.js WebSocket server, Deepgram STT/TTS, extended Claude Haiku context for voice calls.

Voice add-on is sold separately (+$149/month). It is not bundled with Phase 1. Target: first voice client after at least 2 Phase 1 clients have been live for 30+ days and the booking engine is stable.

**Voice AI hard guardrails (in addition to all Phase 1 guardrails):**
1. Urgency detection runs on every conversation turn, not just the first
2. If 3 consecutive turns produce low-confidence transcription, offer callback and end call
3. If booking cannot be confirmed within 10 turns, offer to call the owner back
4. All calls recorded (with compliant disclosure at call start: "This call may be recorded")
5. Call recording two-party consent: for states requiring it (CA, IL, FL, PA, WA, MD, CT, NV), disclosure plays automatically based on area code

---

## 12. Top Remaining Risks

| Risk | Likelihood | Impact | Status |
|------|-----------|--------|--------|
| TFN verification takes longer than 7 days | Medium | High | Mitigation: submit at provisioning, do not go live until verified |
| Google OAuth token refresh fails silently | Low | High | Mitigation: monitoring + admin alert + retry logic defined in spec |
| Owner doesn't confirm appointments within 24h | High | Medium | Mitigation: booking confirmation email/SMS to customer sets expectation of owner confirmation; owner gets escalating reminders |
| Booking form collects wrong address (customer types incomplete address) | High | Medium | Mitigation: no geocoding in v1; owner calls customer if address seems wrong. Address validation (Google Maps API) is Phase 2 |
| AI chat widget confabulates service details | Medium | Medium | Mitigation: hard guardrails in system prompt; widget only uses data from services table |
| Inngest job failure (reminder SMS not sent) | Low | Medium | Mitigation: Inngest has built-in retry + dead letter queue; add monitoring alert for failed jobs |
| First client churns during trial | Medium | High | Mitigation: do a 30-minute check-in call at day 7 and day 21 during every client's trial |
| Acquisition: no clients after build | Medium | Fatal | Must have 2 committed prospects before writing a single line of code |
