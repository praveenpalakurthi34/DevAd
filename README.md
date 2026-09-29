# DevAd — Memory-Powered Advertising Agent

> **An advertising agent that remembers what worked.**

DevAd turns a campaign brief and an **actual product photo** into a product-grounded static advertisement. Its differentiator is not a generic poster template: Hindsight recalls prior campaign outcomes, Groq reasons over that evidence, and the final poster is rendered locally with the exact uploaded product image and exact deterministic text.

## Product loop

```text
CAMPAIGN BRIEF + PRODUCT PHOTO
            ↓
      HINDSIGHT RECALL
            ↓
       EVIDENCE ENGINE
            ↓
       GROQ STRATEGY
            ↓
  PRODUCT-SPECIFIC CREATIVE
            ↓
   LOCAL PHOTO-BASED POSTER
            ↓
     CAMPAIGN OUTCOME
            ↓
          LESSON
            ↓
     HINDSIGHT RETAIN
            ↓
   BETTER NEXT CAMPAIGN
```

## Final visual scope

The zero-cost final build intentionally focuses on **static image ads and carousels**. It does **not** turn static artwork into a fake Reel and it does not require a paid image/video-generation API.

- **Static image ad:** one polished product-grounded poster.
- **Static carousel ad:** three distinct product-grounded posters.
- **Actual product image:** required for every creative and preserved in the output.
- **Exact marketing text:** rendered by the application, not hallucinated inside an image model.
- **No paid visual API:** poster generation runs locally with Pillow.
- **Groq:** provides strategy, messaging, creative concept and copy.
- **Hindsight:** provides persistent memory, evidence and learning.

The local renderer uses the product photo itself as a photographic backdrop and foreground hero, with soft blur, lighting treatment, shadowing, category-aware visual styling, layout variation and deterministic typography. It is deliberately honest: it does not claim to synthesize a realistic human holding the product when no image-generation API is available.

## Stack

- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + Pydantic + SQLAlchemy + SQLite
- Memory: Hindsight Cloud/API
- Primary LLM: Groq (`openai/gpt-oss-120b` by default)
- Visual creative renderer: local Pillow-based product poster renderer
- Product upload: JPG/PNG/WebP, max 10 MB

## Required APIs

Only these external services are required:

```env
HINDSIGHT_API_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your-key
HINDSIGHT_BANK_ID=DevAD
GROQ_API_KEY=your-key
GROQ_MODEL=openai/gpt-oss-120b
```

No Gemini, Veo, Runway, Luma, OpenAI, or paid video API is required for the final creative flow.

## Setup — Windows

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Groq and Hindsight credentials. Never commit `.env`.

Start the API:

```powershell
python -m uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL shown by the terminal, normally `http://localhost:5173`.

## Demo flow

1. Open **Create Campaign**.
2. Upload the actual product photo.
3. Choose **Static image ad** or **Static carousel ad**.
4. Keep **Memory Mode ON**.
5. Generate the campaign.
6. Review the Hindsight evidence and the strategy.
7. Review/download the product-grounded poster(s).
8. Record a campaign outcome.
9. DevAd extracts a lesson and retains it in Hindsight.
10. Create another related campaign and show how recalled evidence changes the strategy.

## Why Hindsight matters

The visual renderer is deterministic; the **learning loop is the intelligence**.

For example, if a previous campaign outcome records that a short benefit-led headline and a specific audience angle performed well, Hindsight retains that lesson. A later campaign recalls the evidence and Groq can change the messaging angle or creative concept accordingly.

The UI distinguishes:

- Memory OFF — baseline; no recall requested.
- Memory available — Hindsight responded and evidence can be inspected.
- Memory unavailable — the campaign remains a transparent baseline and is never falsely labelled memory-informed.

## Product-grounded creative behavior

DevAd requires an uploaded product image and preserves that exact asset in the final creative. The renderer never invents a replacement bottle, package, logo or product shape.

The poster changes according to the product/category and campaign context. Examples include:

- hydration/beverage → fresh, energetic treatment
- skincare → clean, premium treatment
- technology → modern, technical treatment
- food → warm, appetizing treatment
- fashion → editorial, confident treatment

Carousel variants also use different product placements and compositions rather than repeating one template three times.

## Testing

Backend:

```powershell
python -m compileall -q app
pytest -q
```

Frontend:

```powershell
npx tsc --noEmit
npm run build
```

## Repository hygiene

Do not commit:

- `.env`
- `.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- SQLite databases
- generated media
- Python caches

## Runtime status

`GET /api/system/status` reports Groq and Hindsight readiness plus the local product-poster renderer. FFmpeg is no longer required for the final creative flow.

## Important limitation

This final zero-cost build does **not** claim to generate photorealistic new humans or video. It creates polished static advertising artwork using the user's real product photo, while Groq + Hindsight provide the adaptive intelligence. This keeps the demo reproducible, honest, and free of additional visual-generation API costs.
