# Channel API Spike: findings (issue #1)

Date: 2026-09-30. Desk research against official docs where available; third-party
sources are marked. **Items marked 🔬 still need a live API call** once credentials exist.

## Summary

| Channel | Verdict | Key finding | Cost |
|---|---|---|---|
| **LinkedIn** | ✅ Go (wave 1) | Text, image and **PDF document (carousel) posts on a personal profile** are documented. **Per-post analytics for personal profiles now exist** | Free |
| **X** | ✅ Go (wave 2), **link-free posts** | Pay-per-use since Feb 2026: **$0.015/post, $0.20 if it contains a URL** | ~$1–2/month link-free |
| **Instagram** | ✅ Go (wave 3) | Carousels 2–10 items, 100 API posts/24h; needs app review | Free |
| **Threads** | ✅ Go (wave 3) | Carousels 2–20 items, 250 posts/24h | Free |
| **Facebook Page** | ✅ Go (wave 3) | Page posts only (not personal profiles); app review | Free |
| **Bluesky** | ✅ Go (wave 2) | Generous limits; 4 images per post | Free |
| **Slack / Telegram / Discord** | ✅ Go (wave 1) | Webhook / bot APIs, no review | Free |
| **WhatsApp** | ⚠️ Digest only (wave 4) | **No official API for WhatsApp Channels.** Opt-in template broadcast only, paid per message | ≈ ₹0.86/msg (India) + provider markup |

## LinkedIn

**Posting.** Official docs: the Documents API accepts a `urn:li:person:{id}` owner
("for documents with person URN owners, the caller must match the document owner") and
lists `w_member_social` ("post … on behalf of authenticated member"). Flow:
`POST /rest/documents?action=initializeUpload` → upload to `uploadUrl` → poll until
`AVAILABLE` → `POST /rest/posts` with `content.media.id = urn:li:document:…`.
Limits: **100 MB, 300 pages**; PDF, PPT(X), DOC(X).
([Documents API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api?view=li-lms-2026-09))

- 🔬 The Documents API is documented under Community Management. Confirm that an app
  with only the self-serve **"Share on LinkedIn"** product can call `/rest/documents`.
  If not, apply for the **Community Management API** product. Fallback: a multi-image post.
- Some third-party blogs claim "document uploads aren't supported". This contradicts
  the official docs, so treat it as outdated. The live call decides.

**Analytics.** `GET /rest/memberCreatorPostAnalytics` with permission
`r_member_postAnalytics` returns per-post and aggregate metrics for the authenticated
member: IMPRESSION, MEMBERS_REACHED, RESHARE, REACTION, COMMENT, POST_SAVE, POST_SEND,
LINK_CLICKS, **FOLLOWER_GAINED_FROM_CONTENT**, **PROFILE_VIEW_FROM_CONTENT**
([Member Post Statistics](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics?view=li-lms-2026-09)).

- This is better than the plan assumed. **Brand metrics (followers and profile views
  gained per post) are directly measurable**, so the learning loop can optimise for
  brand growth, not just likes.
- 🔬 How access is granted (self-serve vs. Community Management approval) isn't stated.
  Third-party sources describe "approved" access, so apply early.
- Docs note that the aggregate RESHARE/REACTION/COMMENT counts "are not consistent with
  UI". Prefer per-post (`q=entity`) queries.

**Versioning.** Every call sends `Linkedin-Version: YYYYMM`. Versions sunset after about
a year (202510 sunsets 2026-10-15). Pin a recent version in config, and have the
watchdog alert about 60 days before its sunset.

**Tokens.** The personal-app 60-day token with no refresh is unchanged. Keep the ported
`check_token_expiry` logic.

## X (Twitter)

- Pay-per-use only for new sign-ups since Feb 2026 (no free/basic tier): **$0.015 per
  post, $0.20 per post containing a URL**, $0.005 per read. *(Third-party sources,
  consistent across several; confirm in the developer console.)*
- **Design decision:** X variants are **link-free by default** (≈13× cheaper). They point
  to the profile/blog in words; links are allowed only for top-tier posts within budget.
  At 3 link-free posts a day that's ≈ $1.35/month.
- Carousels become threads with up to 4 images per post.

## Meta: Instagram, Threads, Facebook

- **Instagram:** requires an Instagram Professional account, a linked Facebook Page, a
  Meta developer app, and **app review** for the content-publish permission. 100
  API-published posts per 24h (a carousel counts as 1). Carousels have **2–10 items and
  are cropped to the first item's aspect ratio**. *(Third-party.)*
- **Threads:** carousels of 2–20 items; 250 posts per 24h per profile. *(Third-party.)*
- **Facebook:** Page posts only. The API can't post to personal profiles. It needs a
  "Manohar Papasani" Page and `pages_manage_posts`.
- **Design decision:** render every carousel at **4:5, 1080×1350**. That's native for
  Instagram and Threads and reads well on LinkedIn mobile. One master render feeds all
  channels.
- **Action:** app review takes weeks, so start it now (owner: Meta Business account +
  Page + Instagram Professional account).

## Bluesky

- About 5,000 points/hour and 35,000/day per account (create = 3 points), so volume is
  irrelevant for us. `createSession` is capped at 30 per 5 minutes: **reuse sessions**,
  never log in per post. Use an app password. *(Third-party.)*

## WhatsApp

- **The official Cloud API has no endpoint for WhatsApp Channels.** Third-party
  "channel APIs" work through unofficial web sessions. **Rejected:** that's a ToS
  violation and a ban risk for the owner's number.
- What's possible: marketing **template** messages to **opted-in** subscribers,
  **₹0.8631 per message in India** (from Jan 2026) plus provider markup. There's no volume
  discount. *(Third-party pricing sources.)* A weekly digest to 500 subscribers costs
  about ₹1,700/month.
- Keep it in wave 4, weekly, opt-in page required.

## Slack / Telegram / Discord

Incoming webhooks (Slack, Discord) and the Telegram Bot API are free and need no review.
They're the simplest wave-1 channels.

## Changes to the plan

1. Learning loop: optimise on `FOLLOWER_GAINED_FROM_CONTENT` and `PROFILE_VIEW_FROM_CONTENT`
   (brand metrics), with reactions and comments as secondary signals.
2. X variants are link-free by default (cost).
3. Carousels have one master render at 4:5, 1080×1350.
4. WhatsApp: official template digest only. Channels are out of scope unless Meta ships an API.
5. LinkedIn API version is pinned in config, with a watchdog sunset alert.

## Owner actions

| # | Action | Needed for |
|---|---|---|
| 1 | Create a LinkedIn developer app, add **Share on LinkedIn**, and **request Community Management API** access (documents + analytics) | Sprint 6 |
| 2 | Create a Meta Business account + "Manohar Papasani" Facebook Page + Instagram Professional account, then start app review | Wave 3 (weeks of lead time) |
| 3 | X developer account with pay-per-use credits (**paid: confirm first**) | Wave 2 |
| 4 | Bluesky account + app password | Wave 2 |

## Sources

- LinkedIn Documents API (official): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api?view=li-lms-2026-09
- LinkedIn Member Post Statistics (official): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics?view=li-lms-2026-09
- X pricing: https://postproxy.dev/blog/x-api-pricing-2026/ · https://www.outstand.so/blog/x-api-pricing
- Instagram: https://postproxy.dev/blog/post-to-instagram-via-api/ · https://www.blotato.com/blog/instagram-posting-api
- Threads: https://www.socialcrawl.dev/blog/threads-api
- Bluesky: https://adaptlypost.com/blog/bluesky-api-rate-limit
- WhatsApp pricing: https://myoperator.com/blog/whatsapp-business-api-pricing-india-2026
- WhatsApp Channels (no official API): https://whapi.cloud/blog/whatsapp-channel-api-automation
