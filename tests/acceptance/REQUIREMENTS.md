# Requirement specification - smvc-api

This document is the **canonical** product and integration specification. Acceptance tests in this folder are written against these requirements. Short IDs (**U1**, **N2**, **A1**, ...) map directly to criteria below.

**Related:** [Project overview & local setup](../../README.md)

---

## Context

Creators often have travel-style video on Instagram and want those clips on **MileTribe** (see [MileTribe API docs](https://api.development.miletribe.app/docs)). This service sits **in between**: it talks to Instagram, filters clips so only **scenery-focused** videos are kept, uploads them to MileTribe, and publishes them as impressions.

---

## Design decisions

| Topic | Decision | Why it matters |
|------|-----------|----------------|
| HTTP pattern | The client starts work with **`POST /v1/transfers`**. The server answers immediately with **HTTP 202 Accepted** and a **`transfer_id`** - it does *not* wait until Instagram, classification, and MileTribe are finished. The client (or UI) learns progress by calling **`GET /v1/transfers/{transfer_id}`** until status is terminal (completed / failed / completed with errors). Timeouts on the initial request should not kill a long job; only the job record's status reflects real progress. | Listing + ML + uploads can take minutes - don't hold one HTTP connection open until everything finishes. |
| MileTribe publish | For each Instagram media item that passes the scenery filter, first **`POST /impression-videos/`** to MileTribe with the video file. Then **`POST /impressions/`** to create the visible impression, passing **`impression_video_id`** from the upload response. Set **`external_id`** to **`INSTAGRAM/{instagram_media_id}`** (same id every time for that clip). If the worker retries after a crash or MileTribe returns a duplicate (**409**), that **`external_id`** ties the publish to "this Instagram clip," so you don't stack duplicate impressions for one source video. | Retries and partial failures must not create duplicate posts for the same logical clip; MileTribe uses **`external_id`** for that story. |
| Instagram scope | Only these types are *in scope* for this product version: **feed posts whose media type is video**, and **Reels**. Implement listing/download against Meta's APIs (or your chosen integration) for those types only; other surfaces (Stories, DMs, archived folders, etc.) are **out of scope** unless you change this table. | Scope is what you code and test; expanding later is a deliberate spec change, not an accident. |
| Admin targeting | When an admin runs a cross-account transfer, the request body must identify the MileTribe destination with **`target_miletribe_user_id`** - the MileTribe **user id** string their API uses internally - not an email, display name, or Instagram handle. The admin request separately names the **source Instagram account** to read from. | One unambiguous destination field avoids bugs ("which user did we mean?") and keeps admin tooling aligned with MileTribe's identifiers. |

---

## What you're building

**Normal user**

Someone who has linked their Instagram account (OAuth tokens stored and refreshed by this service - details TBD in implementation). They hit **one API** that:

1. Lists candidate videos from Instagram.
2. Runs the **scenery classifier** (ML or rules - implementation detail).
3. Uploads each passing clip to MileTribe.
4. Publishes impressions according to the locked publish step above.

They should **not** have to manually pick files or click through MileTribe for the happy path.

**Admin**

A trusted operator who can run the **same pipeline** for **any** source Instagram account and send results to **any** MileTribe user ID (`target_miletribe_user_id`). That power needs auth + audit (see **A** items below).

---

## Hard constraints

These come from platforms and reality, not preference:

- **Instagram / Meta** - Use an integration you're allowed to ship (e.g. Instagram Graph API with approved permissions). The spec stays vague on *how* you auth so you can swap implementations; it stays strict on *not* baking in brittle scraping assumptions.
- **Legal & privacy** - Automated download and re-upload must respect Meta policies, user consent, and retention. Prefer **least privilege** (fewest OAuth scopes) and **auditability** (who triggered what, when).
- **MileTribe contract** - Follow their OpenAPI: **`multipart/form-data`** with field **`video`**, JSON for impressions, stable **`external_id`**, and correct handling of **401**, **422**, **409**.
- **Classifier** - It will be wrong sometimes. The spec asks for measurable behavior (thresholds, golden set, optional human review) - not "the model is always right."

---

## Acceptance criteria

### User flow

- **U1** - Only the **owner** of the linked Instagram identity may start that user's transfer; otherwise **403** (don't leak whether another account exists - pick **403** consistently).
- **U2** - If Instagram isn't connected or tokens are unusable, return a **clear error** plus a **next step** (e.g. "complete Instagram connection", link or doc id) - not a generic 500.
- **U3** - The transfer endpoint returns **202** and the work continues **without** the user babysitting the request.
- **U4** - Non–scenery-only clips are **not** uploaded; record **why** they were skipped (classifier score, rule, etc.) for debugging and reports.
- **U5** - For each selected clip, upload via MileTribe **`POST /impression-videos/`**; one clip failing should not necessarily kill the whole batch (**N3**). Retries/backoff belong here.
- **U6** - Publish with **`external_id`**; if MileTribe returns **409** for a duplicate of the same logical impression, treat it as **success** for idempotency.

### Admin flow

- **A1** - Admin-only routes require provable **admin** credentials; everyone else gets **403**.
- **A2** - Request identifies **source Instagram** and **`target_miletribe_user_id`** explicitly.
- **A3** - Persist an **audit record**: admin identity, source, target, timestamp, and high-level outcome (counts / errors).

### Observability

- **O1** - Every run exposes a **`transfer_id`** and a status view with **counts** (discovered -> scenery-selected -> uploaded -> failed) and **errors** per item when useful.

### Non-functional

- **N1** - Secrets (tokens, passwords, client secrets) never appear in logs or API bodies; encrypt material at rest.
- **N2** - Honor Instagram and MileTribe rate limits; when you throttle clients, prefer **429** and **`Retry-After`** when you can.
- **N3** - Prefer **completed_with_errors** over failing the entire job when some clips fail - unless you later define all-or-nothing batches.
- **N4** - Bound work: max duration and/or max videos per invocation so workers and gateways don't wedge.

### Classifier

- **M1** - Agree a written definition of **"scenery-only"** (what counts as people, faces, vlog, etc.).
- **M2** - Each decision exposes at least **score**, **label**, and optionally **explanation**; **threshold** is configurable.
- **M3** - Below threshold -> **skip** upload; when in doubt, favor **false negatives** if privacy-sensitive.
- **M4** - Keep a **golden** labeled set; run offline evaluation in CI; optional expensive E2E stays separate.

---

## MileTribe integration (Bearer JWT)

MileTribe is OAuth2-style: your service obtains a **Bearer token** for the **target** MileTribe user (exact login flow depends on your deployment).

Typical sequence:

1. **`POST /impression-videos/`** - send the file as **`multipart/form-data`**, field name **`video`**.
2. **`POST /impressions/`** - JSON includes **`description`**, **`location`**, **`is_public`**, plus **`impression_video_id`** from step 1 and **`external_id`** for deduplication.

**Token lifecycle** matters as much as **`external_id`**: Instagram and MileTribe tokens expire and get revoked - define refresh, failure messages, and tests for those paths, not only the first successful call.

---

## Test strategy

- **Contract tests** - Mock MileTribe HTTP: correct **`video`** multipart part, JSON shape for impressions, behavior on **401 / 409 / 422**. (`test_miletribe_contract.py`)
- **HTTP acceptance** - User vs admin routes and auth (`test_transfer_rbac.py`).
- **Classifier** - Fixtures and threshold edge cases (`test_classifier_acceptance.py`).
- **E2E** - Optional; real dev MileTribe + Meta sandbox is slow - keep a tiny smoke set if you use it.
