# Website Template System Spec

**Builds on:** Shared Data Contracts §9 (`WebsiteDraft`), Website Service doc, HTTP API Contracts, Database Architecture.

---

## 1. What the docs already settle

- The draft separates the template from its content: `templateId` plus `content.sections[]`, each with `id`, `type`, `data`.
- Proposed section types: `HERO, ABOUT, EXPERIENCE, EDUCATION, SKILLS, PROJECTS, CONTACT`. Their `data` fields are explicitly "to be agreed".
- Preview renders "structured content using predefined templates and components". AI output is never trusted executable code.
- Publishing turns the approved draft into static HTML/CSS/JS/assets under `published-websites/{slug}/`, served via one CloudFront distribution.
- `templateId` already travels in `POST /api/jobs`, the `profile.ready` event, and the `websites.template_id` column.
- Open items this spec addresses: "final template storage approach", "template-specific content schemas", "preview rendering strategy", "validation of AI-generated content".

What the docs do **not** define: a template list endpoint, a template table, or any way for the frontend to know which templates exist. This spec fills that gap.

## 2. Core idea

A **template is code and metadata, not data in the database.** It is a versioned package in the repo that contains:

1. a manifest (`template.json`) describing the template,
2. React components for each section it supports,
3. a stylesheet and static assets (thumbnail, fonts).

The **draft stays template-agnostic**. The AI fills in section `data` according to a shared section schema, and each template decides how to draw it. This keeps the generator simple: it never writes HTML.

## 3. Where templates are stored

Source of truth is a monorepo package, not Postgres or S3.

```
packages/
  site-renderer/            # the one shared renderer (section 6)
    src/
      render.tsx            # <Site draft template />
      sections/             # default section components
      validate.ts
  templates/
    registry.json           # generated at build time, list of all manifests
    classic/
      template.json
      components/           # optional per-section overrides
      theme.css
      thumbnail.webp
    minimal/
      ...
contracts/schemas/website/
  website-draft.schema.json
  sections/hero.schema.json ... contact.schema.json   # new, section 5
  template-manifest.schema.json                       # new, section 4
```

Why this over a `templates` table:

- Template changes ship through code review and tests, so a bad template cannot appear in production by editing a row.
- The renderer and templates version together, which removes the preview/publish drift problem at the root.
- With only a handful of templates at launch, a DB admin UI would be overhead.

**Runtime access:**

| Consumer | How it gets templates |
| --- | --- |
| Frontend | Bundled with the renderer; list comes from `registry.json` served by the API (section 7) |
| Website Generator | Reads the manifest only (supported sections, limits) to constrain the AI prompt |
| Website Publisher | Imports the same package at the same version to render static files |

Published output pins the version: `websites.template_id` stays `classic`, and a new column `template_version` (for example `1.2.0`) records what was published, so a later template update never silently changes a live site. Needs a small DB addition.

Templates live as versioned code packages in the repo. Third-party or user-uploaded templates are out of v1; they would need a registry table and sandboxing.

## 4. Template manifest

`template.json`, validated by `template-manifest.schema.json`:

```json
{
  "id": "classic",
  "version": "1.0.0",
  "name": "Classic",
  "description": "Single-page layout with a sticky header.",
  "thumbnail": "thumbnail.webp",
  "layout": "single-page",
  "sections": {
    "required": ["HERO", "ABOUT"],
    "optional": ["EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "CONTACT"]
  },
  "order": ["HERO", "ABOUT", "EXPERIENCE", "PROJECTS", "SKILLS", "EDUCATION", "CONTACT"],
  "limits": {
    "PROJECTS": { "maxItems": 6 },
    "SKILLS": { "maxItems": 20 },
    "EXPERIENCE": { "maxItems": 8 }
  },
  "themeOptions": {
    "accent": ["#2563eb", "#16a34a", "#dc2626"]
  }
}
```

Notes:

- `id` matches the existing `templateId` format. The docs use `template-001`; use readable ids like `classic`. Update the `template-001` examples in the contracts.
- `limits` is what stops the AI from producing more than the layout can hold.
- `themeOptions` is optional in v1. skip user theming at launch; keep the field so it can be added without breaking the schema.

## 5. Section data expected from the draft

The draft format is unchanged: `content.sections[] = { id, type, data }`. What is new is a JSON Schema per section type, so "template-compatible" has a testable meaning. All schemas are derived from `CanonicalProfessionalProfile` (Shared Data Contracts §4) so the generator mostly rewrites text rather than restructuring data.

for every field below. Only `HERO.title/subtitle`, `ABOUT.text`, `SKILLS.items`, and `PROJECTS.items[].name/description/url` appear in the existing example.

| Type | `data` fields | Required | Source in unified profile |
| --- | --- | --- | --- |
| `HERO` | `title` (name), `subtitle` (headline), `links?[{label,url}]` | `title` | `fullName`, `headline`, `links` |
| `ABOUT` | `text`, `location?` | `text` | `summary`, `location` |
| `EXPERIENCE` | `items[{company, position, description?, startDate, endDate?, isCurrent?}]` | at least 1 item or section omitted | `workExperience` |
| `EDUCATION` | `items[{institution, degree?, fieldOfStudy?, startDate?, endDate?}]` | same | `education` |
| `SKILLS` | `items[string]`, `groups?[{label, items[]}]` | `items` | `skills` |
| `PROJECTS` | `items[{name, description?, url?, technologies?[]}]` | same | `projects` |
| `CONTACT` | `email?`, `phone?`, `links?[{label,url}]` | at least one field | `email`, `phone`, `links` |

Rules (all unless noted):

1. **Omit empty sections.** If the profile has no education, the generator leaves out the `EDUCATION` section instead of emitting an empty one. This follows the docs' "never invent missing information" rule.
2. **A template renders only the types it lists** in `sections.required` plus `sections.optional`. Unknown types in a draft are skipped with a warning in preview, not a crash.
3. **Section order** in the draft is respected if it appears in the template's `order`; otherwise the template's `order` wins. No editing, reordering or hiding of sections in preview in v1.
4. **Dates** keep the profile's precision (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`); the renderer formats them.
5. **Text is plain text**, not HTML or Markdown. The renderer escapes everything. This is the main protection against AI-generated markup, and it resolves the open "validation of AI-generated HTML" item for v1.
6. **URLs** must be `https:` (or `mailto:` for email). Anything else is dropped at validation.
7. **Images**: no profile photo or user images in v1. If added later, images must be platform-controlled assets, never hotlinked.
8. Add `schemaVersion` bumps for any breaking change to these schemas, as the contract versioning rules in §13.1 already require.

**Validation points:** (a) generator validates the draft against the section schemas plus the template manifest before storing it, (b) the Publisher re-validates before rendering, (c) the renderer itself ignores or escapes anything unexpected.

## 6. One shared renderer

**Goal:** preview and published site come from the same code, so what the user approves is what goes live.

Build one package, `@proofolio/site-renderer`, in TypeScript/React:

```
renderSite({ draft, template, mode }) -> React element tree
```

- **Preview (frontend):** the React app renders `<Site draft={draft} template={template} mode="preview" />` inside an isolated container (iframe recommended, so template CSS cannot leak into the app and vice versa).
- **Publish (Website Publisher):** a build step calls the same function through `renderToStaticMarkup`, wraps it with the template's CSS, and writes:
  ```
  published-websites/{slug}/index.html
  published-websites/{slug}/assets/style.css
  published-websites/{slug}/assets/*        # images
  ```
  This matches the S3 layout already in the Website Service doc. v1 ships **no client-side JavaScript** by default; templates that need interactivity (mobile menu) use CSS only or a small shared script. This keeps published sites fast, cacheable, and low risk.
- `mode` differences are limited to preview-only chrome (draft banner, "unknown section" warnings). Layout and styling never depend on `mode`.

**Parity guarantee:** a CI test renders every template with a set of fixture drafts in both paths and compares the HTML output. If they differ, the build fails. Golden-file snapshot tests per template plus fixtures for edge cases (long names, missing sections, max items).

**How the Publisher runs it.** The Core and AI services are Python, so the renderer runs as a **small Node render worker**. The Publisher sends it the validated draft, template id and version, and receives the HTML and CSS files, which it uploads to S3. The worker is stateless and imports `@proofolio/site-renderer` directly, so preview and publish share one code path. Interface: internal HTTP `POST /render` returning a file map. Deployment: AWS Lambda as a container image, because rendering is stateless, short and bursty (publishes are rare), so there is nothing to keep warm. Revisit Fargate only if renders exceed Lambda limits.

## 7. How the frontend lists templates

New endpoint through the Core Backend, consistent with "frontend talks only to the Core API":

`GET /api/templates` (authenticated)

```json
{
  "templates": [
    {
      "id": "classic",
      "version": "1.0.0",
      "name": "Classic",
      "description": "Single-page layout with a sticky header.",
      "thumbnailUrl": "https://static.ourdomain.com/templates/classic/thumbnail.webp",
      "sections": { "required": ["HERO", "ABOUT"], "optional": ["EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "CONTACT"] }
    }
  ]
}
```

- The Core Backend serves this from `registry.json` bundled at build time (no DB read, no call to the Website Service).
- Thumbnails are static assets on the platform's own CDN path, not the per-user wildcard domain.
- The frontend template picker shows the cards; the chosen `id` goes into `POST /api/jobs` as `templateId`, exactly as the contract already defines.
- Core Backend validates `templateId` against the registry on job creation and returns `400` for unknown ids. The docs' consistency rule "each website uses a valid template identifier" is enforced there.
- Optionally the picker could show a live preview using sample data and the same renderer, instead of a static thumbnail. Cheap to add once the renderer exists; not needed for v1.

## 8. End-to-end flow with templates

1. Frontend loads `GET /api/templates`, user picks one, `POST /api/jobs` with `templateId`.
2. Core Backend validates the id against the registry.
3. `profile.ready` reaches the Generator with `templateId`.
4. Generator loads the manifest, builds the AI prompt from the profile plus allowed sections and limits, validates the result, stores `draft_content` and `template_version`.
5. `GET /api/websites/{id}/preview` returns the `WebsiteDraft`. Frontend renders it with the shared renderer, using the template version from the draft.
6. On publish, the Publisher re-validates, renders with the same renderer version, uploads to `published-websites/{slug}/`.

## 9. Changes this spec implies to existing docs

| Doc | Change |
| --- | --- |
| Shared Data Contracts §9 | Add per-section schemas; add `templateVersion` to `WebsiteDraft` |
| Shared Data Contracts §13 | Add `template-manifest.schema.json` and `sections/*.schema.json` to `contracts/` |
| HTTP API Contracts | Add `GET /api/templates` |
| Database Architecture | Add `websites.template_version` |
| Website Service | Note that the Generator reads manifests and the Publisher uses the shared renderer |

## 10. Decisions

All accepted by Dobi on 2026-11-26.

1. Templates are versioned code packages in the repo, not a database registry.
2. Publishing renders through a small Node render worker, since the backend is Python.
3. Template ids are readable (`classic`).
4. Out of v1: editing in preview, profile photo, third-party templates.

5. Render worker deploys as a Lambda container image.
6. `GET /api/templates` returns the shape in section 7.

Still open: the per-section field lists in section 5 are and need Frontend team review.

## 11. Explicitly out of scope

Custom user CSS or code editing, template marketplace, per-section AI regeneration, multi-page sites, and custom domains beyond `slug.ourdomain.com`.
