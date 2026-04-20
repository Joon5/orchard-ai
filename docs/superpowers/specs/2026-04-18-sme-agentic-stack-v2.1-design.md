# SME Agentic Stack — v2.1 Spec (Implementation Grade)

**Date:** 2026-04-18
**Status:** Implementation-ready. Supersedes v2. (Final hardening pass applied.)

---

## 1. Product Definition

A multi-tenant SaaS platform that handles customer intake and scheduling for solo US-based trade businesses. The operator onboards each client; after go-live the platform operates without daily operator involvement.

**Core delivery:**
- A 3-page business website with online booking form
- SMS-based customer communication (confirmations, reminders, follow-ups)
- AI chat widget for FAQ and booking intake
- Mobile dashboard for the owner to see and confirm jobs
- Google Calendar event creation per confirmed appointment

**Phase 2 (separate delivery, separate pricing):** Inbound call handling via AI voice agent.

---

## 2. What This Product Is NOT

- Not a field service management system in v1 (no job tracking, invoicing, routing, or multi-worker dispatch at launch). The architecture and data boundaries must be designed so job tracking, invoicing, and routing can be added later without re-platforming.
- Not a CRM (no pipeline, lead scoring, or outreach)
- Not autonomous (every booking requires explicit owner confirmation before it becomes real)
- Not a review management tool (no review collection, display, or response in v1)
- Not a phone answering service (Phase 2 only)
- Not available outside the United States in v1
- Not a calendar (Google Calendar is the calendar; this platform writes to it, does not replace it)
- Not a multi-user product (one login per business in v1)

---

## 3. ICP

**Who this is for:** Solo trade operator, 0–2 employees, US-based, English-speaking, smartphone owner, has or will create a Google account. Target trades: handyman, locksmith, independent plumber, electrician, HVAC technician. Has no functioning website. Books jobs by answering calls or texts manually.

**Who this is not for:** Shops with office staff, existing scheduling software, or > 3 employees. Any business outside the US.

**Gate before implementation:** At least 2 identified prospects who have verbally agreed to pay $349/month after a free first month for this specific feature set. No prospects = no build.

---

## 4. Pricing

| Tier | Setup Fee | Pricing |
|------|-----------|---------|
| Foundation | $500 | First month free, then $349/month starting in month 2 |
| Foundation + Voice | $500 | First month free, then $498/month starting in month 2 ($349 + $149) |

**Trial:** The first month is free, starting on the go-live date. Monthly billing begins in month 2. If the client does not convert after the free first month, the subscription is cancelled.

**Setup fee:** Covers operator time. Non-refundable after website goes live. Collected via Stripe Payment Intent at onboarding before any work begins.

---

## 5. Architecture

| Layer | Technology | Notes |
|-------|-----------|-------|
| Web / API | Next.js 14 App Router | All web surfaces |
| Database | Supabase Postgres | RLS enforced per tenant |
| Auth | Supabase Auth | Owner + admin roles only |
| Storage | Supabase Storage | Photos / logos |
| Realtime | Supabase Realtime | Dashboard live updates |
| Hosting | Vercel | Wildcard subdomain routing |
| SMS | Twilio Programmable SMS | TFN per tenant |
| Push notifications | OneSignal | Web push; SMS fallback if token absent |
| AI | Claude Haiku | Chat widget + SMS context + summaries |
| Background jobs | Inngest | All scheduled and async work |
| Billing | Stripe | Subscriptions + setup fees |
| Calendar | Google Calendar API v3 | Write-only; OAuth2 per tenant |
| Error monitoring | Sentry | Required from week 1 |
| Voice (Phase 2) | Twilio Voice + Media Streams + Deepgram + Railway | Separate delivery |

**Push notification delivery rule:** Attempt OneSignal push first. If `push_token` is null, or OneSignal delivery returns a non-success status within 30 seconds, send SMS to `tenants.owner_mobile_phone` immediately. Do not wait. Log both attempts in `events`.

**Future extension points:** The v1 architecture must preserve clean extension points for future job tracking, invoicing, and routing, even though those capabilities are explicitly out of scope for launch.

**Vercel + Next.js constraint:** No long-running processes on Vercel. All Twilio webhook handlers, Inngest job handlers, and Stripe webhook handlers must complete within Vercel's function timeout (10s default, 60s max on Pro). Voice WebSocket server runs on Railway (Phase 2 only).

---

## 6. Multi-Tenancy

Each tenant is one row in `tenants`. Supabase RLS is the enforcement mechanism — no application-layer tenant filtering is trusted as a security control.

Operator uses a server-side service role key that bypasses RLS. This key is never exposed client-side or in browser bundles.

Each tenant has one Twilio TFN, one Google Calendar OAuth connection, one Stripe subscription, one subdomain, and one `max_jobs_per_window` threshold.

**Google OAuth token lifecycle:**
1. On every calendar write, check token expiry
2. If access token expires within 7 days: auto-refresh using stored refresh token
3. If refresh fails (revoked, expired refresh token): set `tenants.calendar_status = 'disconnected'`, write an event row, send push/SMS alert to owner, flag in admin panel
4. No calendar write is attempted on a disconnected tenant — log the failure, create event row, alert admin

---

## 7. Revised Data Model

```sql
-- ─────────────────────────────────────────────
-- TENANTS
-- ─────────────────────────────────────────────
tenants
  id                      uuid PK DEFAULT gen_random_uuid()
  slug                    text UNIQUE NOT NULL
  name                    text NOT NULL
  owner_name              text NOT NULL
  owner_email             text NOT NULL
  owner_mobile_phone      text NOT NULL        -- SMS fallback + urgent alerts; must be E.164; must differ from tenants.phone (TFN); validated at application layer on tenant creation
  phone                   text                 -- Twilio TFN (customer-facing)
  address                 text
  service_area            text NOT NULL
  timezone                text NOT NULL        -- IANA e.g. 'America/Chicago'
  business_hours          jsonb NOT NULL       -- {mon:{open:'08:00',close:'18:00'}, ...}
                                               -- 'closed' value means no open/close
  max_jobs_per_window     int NOT NULL DEFAULT 2  -- availability threshold per time window
  active                  boolean NOT NULL DEFAULT true
  plan                    text NOT NULL DEFAULT 'foundation'  -- 'foundation'|'foundation_voice'
  trial_ends_at           timestamptz              -- end of free first month (go-live date + 1 calendar month)
  stripe_customer_id      text
  stripe_subscription_id  text
  stripe_status           text                 -- mirrors Stripe subscription status
  calendar_id             text NOT NULL DEFAULT 'primary'
  calendar_status         text NOT NULL DEFAULT 'connected'  -- 'connected'|'disconnected'
  google_oauth_token      jsonb                -- AES-256 encrypted {access_token, refresh_token, expiry}
  tfn_verification_status text NOT NULL DEFAULT 'unsubmitted'
                                               -- 'unsubmitted'|'pending'|'approved'|'rejected'
  ai_config               jsonb                -- {tone, faq_overrides[]}
  website_config          jsonb                -- {colors, tagline, hero_copy, font}
  created_at              timestamptz NOT NULL DEFAULT now()
  updated_at              timestamptz NOT NULL DEFAULT now()

-- ─────────────────────────────────────────────
-- SERVICES
-- ─────────────────────────────────────────────
services
  id                uuid PK DEFAULT gen_random_uuid()
  tenant_id         uuid NOT NULL FK → tenants
  name              text NOT NULL
  description       text
  price_range       text                -- '$75–$200'; null → AI uses fallback phrase
  duration_minutes  int NOT NULL DEFAULT 120  -- default 2h; used for calendar end time
  display_order     int NOT NULL DEFAULT 0
  active            boolean NOT NULL DEFAULT true

-- ─────────────────────────────────────────────
-- CONTACTS
-- ─────────────────────────────────────────────
contacts
  id          uuid PK DEFAULT gen_random_uuid()
  tenant_id   uuid NOT NULL FK → tenants
  name        text
  phone       text NOT NULL              -- primary key for identity; must be E.164
              CHECK (phone ~ '^\+1[2-9][0-9]{9}$')  -- US E.164 enforced at DB level
  address     text                       -- customer's home address if known
  created_at  timestamptz NOT NULL DEFAULT now()
  UNIQUE (tenant_id, phone)

-- ─────────────────────────────────────────────
-- APPOINTMENTS
-- ─────────────────────────────────────────────
appointments
  id                  uuid PK DEFAULT gen_random_uuid()
  tenant_id           uuid NOT NULL FK → tenants
  contact_id          uuid NOT NULL FK → contacts
  service_id          uuid FK → services      -- nullable: 'other' catch-all if not matched
  scheduled_date      date NOT NULL
  time_window         text NOT NULL
                      -- 'morning' (08:00–12:00) | 'afternoon' (12:00–17:00) | 'flexible'
  duration_minutes    int NOT NULL            -- copied from service at booking time
  address             text NOT NULL           -- where the job is
  job_notes           text                    -- customer-provided issue description
  status              text NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','confirmed','declined','expired','in_progress','completed','cancelled','rescheduled'))
                      -- 'pending'        : received, awaiting owner confirmation
                      -- 'confirmed'      : owner confirmed
                      -- 'declined'       : owner explicitly rejected
                      -- 'expired'        : confirmation SLA elapsed with no owner action
                      -- 'in_progress'    : reserved for Phase 2 / future use
                      -- 'completed'      : job done
                      -- 'cancelled'      : cancelled by customer or owner post-confirmation
                      -- 'rescheduled'    : superseded by a new appointment
  confirm_by          timestamptz NOT NULL    -- SLA deadline: see booking lifecycle section
  confirmed_at        timestamptz
  declined_at         timestamptz
  cancelled_at        timestamptz
  calendar_event_id   text                    -- Google Calendar event ID; null until confirmed
  booked_via          text NOT NULL DEFAULT 'web_form'
                      -- 'web_form'|'chat'|'sms'  (voice added in Phase 2)
  rescheduled_to_id   uuid FK → appointments  -- set when status = 'rescheduled'
  created_at          timestamptz NOT NULL DEFAULT now()
  updated_at          timestamptz NOT NULL DEFAULT now()

-- ─────────────────────────────────────────────
-- CONVERSATIONS
-- ─────────────────────────────────────────────
conversations
  id              uuid PK DEFAULT gen_random_uuid()
  tenant_id       uuid NOT NULL FK → tenants
  contact_id      uuid FK → contacts          -- null if contact not yet created
  appointment_id  uuid FK → appointments      -- null if no booking resulted
  channel         text NOT NULL               -- 'chat'|'sms' (voice added in Phase 2)
  started_at      timestamptz NOT NULL DEFAULT now()
  ended_at        timestamptz
  summary         text                        -- AI-generated; populated async after conversation ends
  full_transcript jsonb                       -- [{role:'user'|'assistant', content, ts}]
  created_at      timestamptz NOT NULL DEFAULT now()

-- ─────────────────────────────────────────────
-- NOTIFICATIONS
-- ─────────────────────────────────────────────
notifications
  id          uuid PK DEFAULT gen_random_uuid()
  tenant_id   uuid NOT NULL FK → tenants
  type        text NOT NULL
              -- 'new_booking'|'booking_confirmed'|'booking_declined'|'booking_expired'
              -- |'booking_cancelled'|'system_alert'
  message     text NOT NULL
  read        boolean NOT NULL DEFAULT false
  action_url  text
  created_at  timestamptz NOT NULL DEFAULT now()

-- ─────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────
users
  id          uuid PK DEFAULT gen_random_uuid()
  tenant_id   uuid FK → tenants               -- null = super-admin (operator)
  email       text NOT NULL UNIQUE
  role        text NOT NULL                   -- 'owner'|'admin'
  push_token  text                            -- OneSignal player ID; null if not granted
  created_at  timestamptz NOT NULL DEFAULT now()

-- ─────────────────────────────────────────────
-- EVENTS (audit log)
-- ─────────────────────────────────────────────
events
  id            uuid PK DEFAULT gen_random_uuid()
  tenant_id     uuid FK → tenants             -- null for platform-level events
  entity_type   text NOT NULL                 -- 'appointment'|'sms'|'calendar'|'webhook'|'job'|'auth'
  entity_id     uuid                          -- FK to relevant row (appointment, conversation, etc.)
  action        text NOT NULL                 -- e.g. 'status_changed'|'sms_sent'|'sms_failed'|'job_fired'
  actor         text NOT NULL                 -- 'system'|'owner'|'customer'|'admin'
  payload       jsonb                         -- before/after state or raw data
  error         text                          -- populated on failures
  created_at    timestamptz NOT NULL DEFAULT now()

-- Index for debugging: events by entity
CREATE INDEX events_entity_idx ON events(entity_type, entity_id);
CREATE INDEX events_tenant_created_idx ON events(tenant_id, created_at DESC);
```

---

## 8. Revised Booking Lifecycle

### Booking form fields (exactly 6)

| # | Field | Type | Required | Notes |
|---|-------|------|----------|-------|
| 1 | Service | Dropdown | Yes | From active services for this tenant |
| 2 | Date | Date picker | Yes | No dates in the past; no dates > 60 days out |
| 3 | Time preference | Radio | Yes | Morning (8am–12pm) / Afternoon (12pm–5pm) / Flexible |
| 4 | Job address | Text | Yes | Label: "Where is the job?" No geocoding in v1. |
| 5 | Your name | Text | Yes | |
| 6 | Your phone number | Tel | Yes | E.164 format enforced; shown as: (555) 555-5555 |

Plus: optional "Describe the issue" free-text area (labeled as optional). Maps to `job_notes`. Not required but surfaced prominently. Placeholder: "e.g. Leaking pipe under kitchen sink, noisy furnace, garage door won't open."

### Availability check

Check: `SELECT COUNT(*) FROM appointments WHERE tenant_id = $1 AND scheduled_date = $2 AND time_window IN ($3, 'flexible') AND status IN ('pending', 'confirmed')`.

If count >= `tenants.max_jobs_per_window`: reject this time window, show next 3 available date/window combinations. Do not block booking entirely — offer alternatives immediately.

If count < `tenants.max_jobs_per_window`: accept.

### Confirmation SLA

`confirm_by` is set at booking creation time:

```
If booking submitted during business hours:
  confirm_by = booking_time + 4 hours (capped at end of today's business hours)

If booking submitted outside business hours:
  confirm_by = next business day open time + 2 hours

'Next business day' algorithm:
  start_day = tomorrow (in tenant timezone)
  for i in 0..6:
    candidate = start_day + i days
    if business_hours[candidate.weekday].open != 'closed':
      return candidate at open time + 2h
  fallback = booking_time + 7 days  // handles extended closures
```

This handles weekends, multi-day holiday gaps, and tenants with non-standard schedules (e.g., Mon–Wed–Fri only).

### Booking flow (exact steps)

**Step 1 — Submission**
- Validate form (all required fields, phone E.164, date not past, not > 60 days)
- Rate limit: 3 submissions per phone per 24h per tenant (return HTTP 429, show "Too many requests. Call us directly at [tenant phone].")
- Cloudflare Turnstile on form (bot protection)
- Upsert contact by `(tenant_id, phone)`
- Create appointment record: `status='pending'`, `confirm_by` calculated per SLA above
- Write event: `{entity_type:'appointment', action:'created', actor:'customer'}`

**Step 2 — Notify customer**
- SMS to customer (Twilio TFN): "Hi [name], [business name] received your request for [service] at [address] on [date] ([time window]). [Owner name] will confirm shortly. Reply CANCEL to cancel. Msg&data rates apply. Reply STOP to opt out."
- Note: STOP opt-out disclosure is required on first SMS to any new number (TCPA)
- Write event: `{entity_type:'sms', action:'sms_sent', payload:{to, body, twilio_sid}}`

**Step 3 — Notify owner**
- Create notification row: type='new_booking'
- Attempt OneSignal push to owner's push_token
- Log attempt in events regardless of outcome
- If push_token is null OR OneSignal returns non-success within 30s: send SMS to `owner_mobile_phone` immediately
- Write event for each delivery attempt with outcome

**Step 3a — T-1h escalation (Inngest job)**
- At booking creation, Inngest schedules a `appointment.confirm-warning` event for `confirm_by - 1 hour`
- At fire time: if appointment is still `status='pending'`:
  - Send SMS to `owner_mobile_phone`: "⚠ Action needed: [customer name] is waiting on your confirmation for [service] on [date]. Confirm or decline now: [dashboard url]. SLA expires at [time]."
  - Write event: `{entity_type:'sms', action:'sms_sent', payload:{to:owner_mobile_phone, type:'confirm_warning'}}`
- If appointment is no longer `pending` at fire time: no-op; write event: `{action:'confirm_warning_skipped', payload:{current_status}}`

**Step 4 — Owner confirms**
- Owner taps "Confirm" in dashboard
- Set `status='confirmed'`, `confirmed_at=now()`
- Write event: `{action:'status_changed', payload:{from:'pending', to:'confirmed'}, actor:'owner'}`
- Create Google Calendar event (see Calendar section)
- Send SMS to customer: "Confirmed! [Business name] will be at [address] on [date] ([time window]). See you then. Reply CANCEL to cancel."
- Write event for calendar creation outcome (success or failure)
- Create notification row: type='booking_confirmed'

**Step 4b — Owner declines**
- Owner taps "Decline" in dashboard
- Set `status='declined'`, `declined_at=now()`
- Write event: `{action:'status_changed', payload:{from:'pending', to:'declined'}, actor:'owner'}`
- Send SMS to customer: "Hi [name], unfortunately [business name] isn't available for that slot. Please rebook at [website url] or call [business phone]."
- Create notification row: type='booking_declined'

**Step 4c — SLA expires (Inngest job)**
- Inngest job `check-pending-confirmations` runs every 30 minutes
- Finds all appointments where `status='pending' AND confirm_by < now()`
- For each:
  - Set `status='expired'`
  - Write event: `{action:'status_changed', payload:{from:'pending', to:'expired'}, actor:'system'}`
  - Send SMS to customer: "Hi [name], [business name] wasn't able to confirm your booking in time. Please rebook at [website url] or call [business phone] directly."
  - Send push/SMS to owner: "⚠ Booking expired: [service] at [address] on [date]. Customer was notified. Tap to view."
  - Create notification row: type='booking_expired'

**Step 5 — Reminder (Inngest job)**
- Fires at T-24h from `scheduled_date` start of `time_window`
- Only fires if `status='confirmed'`
- SMS copy varies by `time_window`:
  - `morning`: "Reminder: [business name] is coming to [address] tomorrow morning (8am–12pm). Reply CANCEL to cancel."
  - `afternoon`: "Reminder: [business name] is coming to [address] tomorrow afternoon (12pm–5pm). Reply CANCEL to cancel."
  - `flexible`: "Reminder: [business name] is coming to [address] tomorrow. [Owner name] will be in touch to confirm a specific time. Reply CANCEL to cancel."
- Write event on send

**Step 6 — Post-job follow-up (Inngest job)**
- Fires at T+24h from `scheduled_date` end of `time_window`
- Only fires if `status='confirmed'` or `status='completed'`
- SMS to customer: "Thanks for choosing [business name]! We hope everything went well. Need us again? Book at [website url]."
- Write event on send
- No review solicitation in v1

### Cancellation

**Customer cancels (SMS CANCEL):**
- Match by `(tenant_id, contact.phone)` → nearest future `confirmed` or `pending` appointment
- If no match: respond "We didn't find an active booking. Need help? Call [tenant phone]."
- Set `status='cancelled'`, `cancelled_at=now()`
- If `calendar_event_id` is not null: delete Google Calendar event; log outcome in events
- SMS to customer: "Cancelled. Your booking with [business name] on [date] has been cancelled. Book again anytime at [website url]."
- Push/SMS to owner: "Booking cancelled: [service] at [address] on [date]."
- Write events for all actions

**Owner cancels (dashboard):**
- Same as above, `actor='owner'` in events
- Customer notified via SMS

### Rescheduling (inbound SMS RESCHEDULE)

1. Customer sends RESCHEDULE
2. AI (Claude Haiku, 2-turn max) asks: "What date works for you?" then "Morning or afternoon?"
3. Create new appointment: `status='pending'`, `confirm_by` calculated fresh
4. Set original appointment: `status='rescheduled'`, `rescheduled_to_id = new_appointment.id`
4a. If original appointment `calendar_event_id` is not null: delete the Google Calendar event immediately; log outcome in events; set `calendar_event_id = null` on original appointment. (The new appointment creates its own event only after its own confirmation.)
5. Write events on both appointments
6. New appointment follows standard booking flow from Step 2

### Google Calendar event rules

- Created only when appointment transitions to `confirmed`
- Event title: "[Service name] — [Contact name]"
- Event description: "[address]\n[job_notes]\nBooked via [platform name]"
- Start: `scheduled_date` at window start time (08:00 for morning, 12:00 for afternoon, 08:00 for flexible)
- End: start + `appointments.duration_minutes`
- If Calendar API returns error: set `calendar_event_id = null`, write event with error payload, send push/SMS alert to admin (not owner), retry once after 5 minutes via Inngest
- Appointment remains `confirmed` regardless of calendar failure — calendar is a convenience, not a requirement

---

## 9. Channel Policy

**v1 channels: SMS only for customers. Push + SMS for owner.**

| Channel | Who | Use |
|---------|-----|-----|
| SMS outbound | Customers | Booking pending/confirmed/declined/expired/reminder/post-job/cancellation |
| SMS inbound | Customers | CANCEL, RESCHEDULE, general inquiry (Claude Haiku context reply) |
| SMS outbound | Owner | All push fallbacks + escalating confirmation reminders |
| Push (OneSignal) | Owner | New booking, cancellation, expiry, system alerts |
| AI chat widget | Customers | FAQ, booking intake on website |
| Email | Nobody | Not in v1. No Resend. No email anywhere. |
| Voice | Nobody | Phase 2 only. |

**SMS opt-out compliance:**
- Every first SMS to a new contact phone number must include: "Msg&data rates may apply. Reply STOP to unsubscribe."
- STOP reply: immediately suppress that phone number from all future outbound SMS for that tenant. Write event. Do not respond with further SMS (except one TCPA-compliant "You have unsubscribed" confirmation).
- Contacts table does not need a `sms_opted_out` field in v1 — use Twilio's opt-out management natively and check their API before sending.

**TFN verification requirements (what the operator must submit to Twilio):**
- Business legal name
- Business website URL (client's new platform subdomain is acceptable)
- Use case description: "Appointment scheduling confirmations, reminders, and follow-ups for a local trade service business. Messages sent only to customers who provided their number via a booking form."
- Estimated monthly SMS volume (use 500 as default)
- Sample message 1: "Hi [name], [business] received your booking for [service] on [date]. Reply CANCEL to cancel. Msg&data rates apply. Reply STOP to opt out."
- Sample message 2: "Reminder: [business] is coming tomorrow ([time window]). Reply CANCEL to cancel."
- TFN verification timeline: 3–10 business days. Status tracked in `tenants.tfn_verification_status`.
- If `tfn_verification_status = 'rejected'`: operator corrects submission fields and resubmits. Do not go live until `'approved'`.
- Interim during TFN verification: do not send any SMS. Onboarding checklist blocks go-live if `tfn_verification_status != 'approved'`.

**Inbound SMS routing:**
| Pattern | Action |
|---------|--------|
| `CANCEL` (case-insensitive) | Cancel nearest future confirmed/pending appointment |
| `RESCHEDULE` (case-insensitive) | Start 2-turn reschedule flow |
| `STOP` | Delegate to Twilio opt-out; send one confirmation; write event |
| `HELP` | Respond: "For help, call [business phone]." Write event. |
| Any other content, known contact | Claude Haiku response (see guardrails). Max 2 SMS per inbound. Write conversation record. |
| Any other content, unknown contact | Respond: "Hi, thanks for reaching out to [business name]. Book online: [url], or call [business phone] for immediate help." Create contact record. Write conversation record. |

---

## 10. AI Guardrails (Non-Negotiable)

These are system prompt rules, enforced in every Claude Haiku call. They are not configurable by tenants.

**Chat widget and inbound SMS — universal rules:**
1. `price_range` is not null: respond "Typically [price_range], with final pricing confirmed on-site."
2. `price_range` is null: respond "Pricing depends on the job — we'll give you a firm quote before starting work."
3. Never state or imply a specific time slot is available. Use: "We'll confirm your preferred time shortly."
4. Never discuss services not present and `active=true` in `services` table.
5. Never claim availability outside `tenants.business_hours`.
6. Never discuss competitors, ongoing disputes, or prior complaints.
7. If 3 turns produce no clear intent: "I'll have [owner_name] follow up with you directly. What's the best number to reach you?" → collect phone if not already known → create notification.
8. System prompt is injected server-side. The tenant's `ai_config.faq_overrides` can ADD entries but cannot remove or modify rules 1–7.

**Booking intake (chat widget):**
9. Do not create an appointment record until all 6 required fields are collected.
10. Confirm collected fields back to user before creating: "Just to confirm — [service] at [address] on [date] ([time window])?"
11. After creating appointment: "Your request has been sent. [Owner name] will confirm shortly."

**All AI output:**
12. Never fabricate business details (address, license numbers, years in business, certifications).
13. AI summaries are factual past-tense descriptions of what occurred: "Customer inquired about [service] pricing. Booked for [date]." No sentiment, no interpretation.

---

## 11. Non-Negotiable Operational Rules

These are platform rules enforced at the infrastructure or process level, not negotiable per client:

1. **No client goes live until `tfn_verification_status = 'approved'`** — enforced by onboarding checklist gate in admin panel; provision button is locked until approved.
2. **No client goes live until `calendar_status = 'connected'`** — same gate.
3. **No Stripe subscription is created until setup fee is collected** — Stripe Payment Intent must succeed before tenant record is created.
4. **All inbound Twilio webhooks are verified using Twilio's request signature** — reject unsigned webhook calls with HTTP 403.
5. **All outbound SMS to new contacts include STOP opt-out language** — enforced in the SMS send utility, not left to individual call sites.
6. **Google OAuth refresh token is encrypted at rest** — using AES-256 with a key stored in Vercel environment, not in the database.
7. **Service role key (Supabase) never leaves the server** — any client-side Supabase calls use anon key + RLS only.
8. **Inngest jobs for reminders are idempotent** — running the same job twice produces the same outcome; guarded by checking `events` table before sending.
9. **All appointment state transitions are written to `events`** — no status column change without a corresponding event row.
10. **Owner dashboard shows only `confirmed` + `pending` appointments on home screen** — `expired`, `declined`, `cancelled`, `rescheduled` are visible in a separate "Past" view, not the daily work view.

---

## 12. Revised Risk Table

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TFN verification rejected or delayed > 10 days | Medium | High | Correct and resubmit immediately. Admin panel surfaces rejection reason. Client launch blocked until approved — this is communicated upfront at sale. |
| Owner doesn't confirm within SLA | High | Medium | Inngest `check-pending-confirmations` job runs every 30 min. Customer auto-notified on expiry. Owner escalation SMS at T-1h before SLA. |
| Google OAuth refresh fails silently | Low | High | Calendar status field + monitoring. Admin alert fires within 10 min of failure. No calendar writes attempted on disconnected tenants. |
| AI chat widget produces inaccurate service or pricing info | Medium | Medium | Guardrails limit AI to services table data. Price fallback defined for null values. Sentry captures Claude API errors. |
| Inngest job failure (reminder not sent) | Low | Medium | Inngest retry + dead letter queue. Sentry alert for DLQ entries. Admin panel shows job health. |
| Contact submits booking with incomplete address | High | Medium | Owner sees raw address field in dashboard; calls customer if unclear. No geocoding in v1 — this is an accepted limitation. |
| First client churns during trial | Medium | High | Operator check-in calls at day 7 and day 21 of every trial. If owner hasn't logged in within 5 days of go-live, send them an SMS: "Your dashboard has new activity — [url]." |
| No paying clients after build | Medium | Fatal | Pre-requisite: 2 committed prospects before build starts. |
| Client surprised by billing starting in month 2 | Low | Medium | Stripe sends a payment-upcoming email at T-7 days before free month ends. Operator also sends a personal SMS at T-5 days. |
| Push notifications not working for iOS users | Medium | Medium | OneSignal push + immediate SMS fallback covers this. Documented behavior. |

---

## 13. Phase 1 Implementation Plan (8 Weeks)

**Week 1–2: Infrastructure + auth**
- Supabase schema (all tables in section 7, including `events`)
- Supabase Auth (owner + admin roles, RLS policies)
- Next.js monorepo + App Router + wildcard subdomain routing on Vercel
- Admin panel: tenant list, provision form (creates tenant + Stripe customer + initiates TFN via Twilio API)
- Stripe: setup fee Payment Intent + subscription creation + webhook handler (status sync)
- Sentry: error monitoring from day 1
- Google Calendar OAuth: auth flow + encrypted token storage + auto-refresh + disconnect detection

**Week 3–4: Booking engine + SMS**
- 6-field booking form (public, per tenant subdomain)
- Availability check (platform-side, uses `max_jobs_per_window`)
- Appointment CRUD with full state machine and `events` logging
- Twilio TFN outbound SMS: pending, confirmed, declined, expired, cancelled, reminder, post-job
- STOP/CANCEL/RESCHEDULE/HELP inbound SMS handling
- General inbound SMS: Claude Haiku context reply (known + unknown contact paths)
- Inngest: `check-pending-confirmations` (every 30 min), `appointment.confirm-warning` (scheduled event at confirm_by - 1h), `send-reminder` (T-24h), `send-follow-up` (T+24h)
- Cloudflare Turnstile + rate limiting on booking form

**Week 5–6: Client website + chat widget**
- 3-page website template driven by tenant config (Home, About, Contact/Booking)
- Owner website editor: name, phone, tagline, services, hours, bio, photo
- AI chat widget: Claude Haiku streaming, tenant system prompt, all guardrails, rate limiting on chat endpoint
- Services management in owner dashboard

**Week 7: Owner dashboard**
- Home screen: today's jobs timeline
- Upcoming view: next 7 days
- Confirm/decline buttons on pending appointments
- Notifications feed (Supabase Realtime)
- OneSignal push integration + SMS fallback
- Conversations: AI summary feed, drill-down to transcript
- Past appointments view (expired, declined, cancelled, rescheduled)

**Week 8: Hardening + first client**
- Admin panel: TFN status tracking, calendar status, billing overview, impersonate link
- Onboarding checklist (blocks go-live until TFN approved + calendar connected + services added)
- Google OAuth token expiry monitoring + admin alert
- Inngest DLQ monitoring alert (Sentry)
- Internal runbook: TFN rejected recovery, Google OAuth disconnect recovery
- First real client onboarded, go-live checklist completed

---

## 14. Phase 2: Voice AI (Weeks 9–16)

Separate delivery. No Phase 1 code modified. Voice pipeline calls `POST /api/internal/book` (same booking engine endpoint) and `POST /api/internal/notify` (same notification dispatcher).

New infra: Railway WebSocket server, Deepgram STT/TTS, Twilio Voice + Media Streams.

Voice add-on enabled by setting `tenants.plan = 'foundation_voice'` — no other schema change.

Target: first voice client only after 2 Phase 1 clients have been live for 30+ days without booking engine failures.

---

## 15. Documented Edge Cases and Accepted Behaviors

These are known behaviors that are intentional or explicitly accepted in v1. Engineering does not need to solve them — just understand them.

| Edge case | Behavior | Rationale |
|-----------|----------|-----------|
| Post-job follow-up (Step 6) fires for `confirmed` appointments | In v1, `completed` status is never set (there is no job-done flow). All jobs remain `confirmed` until they are cancelled or rescheduled. Step 6 fires correctly for `confirmed`. If `completed` is reached (e.g., via admin), it also fires. This is intentional. | No job-done mechanism in v1. Accepted. |
| Owner declines → customer can immediately rebook | No lockout after decline. Customer can submit a new booking via the web form. Owner can decline again. | Owner is in control via confirm/decline. No need for lockout logic. |
| Availability check race condition | Two concurrent submissions for the same slot can both pass the `COUNT` check before either inserts. Mitigated with `SELECT FOR UPDATE` on the availability check row. See implementation note in Week 3–4. | The `SELECT FOR UPDATE` approach is sufficient at expected concurrency levels (1–5 concurrent submissions per tenant). |
| `confirm_by` falls on a day with no open window within 7 days | Fallback: `confirm_by = booking_time + 7 days`. Owner and customer both receive the standard SLA messaging. | Protects against infinite loops in edge cases (e.g., tenant forgot to configure hours). |

---

## 16. Acceptance Criteria for Engineering

These are the exit conditions for v1 Phase 1. All 16 must pass before declaring the build shippable.

1. A booking submitted on the public form appears in the owner's dashboard within 5 seconds via Supabase Realtime.
2. The owner receives an SMS notification within 60 seconds of a new booking when `push_token` is null.
3. A pending appointment expires within 35 minutes of `confirm_by` passing in production (Inngest job polls every 30 minutes; up to 5 minutes of processing overhead is acceptable). Verified in CI by setting `confirm_by = now() - 1 minute` and triggering the Inngest job manually.
4. Customer receives "expired" SMS within 30 seconds of appointment expiry.
5a. Customer "CANCEL" SMS on a `pending` appointment results in `status='cancelled'`, owner notified, and no Google Calendar deletion (no event exists yet) — all within 60 seconds.
5b. Customer "CANCEL" SMS on a `confirmed` appointment results in `status='cancelled'`, Google Calendar event deleted (when `calendar_event_id` is not null), and owner notified — all within 60 seconds.
6. Customer "RESCHEDULE" SMS completes the 2-turn AI exchange, creates a new `pending` appointment, and sets original to `rescheduled` with `rescheduled_to_id` populated.
7. When a booking is confirmed and Google Calendar API is unavailable, the appointment status remains `confirmed`, an event row is written with the error, and the admin receives an alert.
8. Booking form rejects a 4th submission from the same phone number within 24 hours with HTTP 429 (rate limit is 3 per phone per 24h per tenant; the 4th attempt hits the limit).
9. An unsigned Twilio webhook request returns HTTP 403.
10. Two different tenants — logged in simultaneously — cannot read each other's appointments, contacts, or conversations (verified via Supabase RLS policy test).
11. Sending "STOP" from a contact phone number suppresses all future outbound SMS to that number for that tenant.
12. A tenant with `tfn_verification_status != 'approved'` cannot be marked active in the admin panel's go-live checklist.
13. All 8 appointment status transitions on an existing row (pending→confirmed, pending→declined, pending→expired, confirmed→cancelled, confirmed→completed, confirmed→rescheduled, pending→cancelled, pending→rescheduled) produce a corresponding row in the `events` table. Note: a rescheduled appointment creates a new row (status='pending'); this is covered by AC #6, not a transition of the original row.
14. The AI chat widget responds with the `price_range` fallback phrase ("we'll give you a firm quote before starting work") when a service has `price_range = null`.
15. Reminder SMS for a confirmed appointment is not sent if the appointment is cancelled after the Inngest job is scheduled (idempotency check passes).
16. The `appointment.confirm-warning` Inngest job fires at `confirm_by - 1 hour` and sends an escalation SMS to `owner_mobile_phone` only when the appointment is still `pending`; it is a no-op (with event logged) if the appointment has already been confirmed, declined, or expired.
