# BaniOnline — Frontend (site)

Site-ul static al cursului **BaniOnline**, construit cu [Astro](https://astro.build)
și Tailwind CSS v4, deployat pe Cloudflare Pages.

## Cerințe

- Node.js >= 22.12

## Dezvoltare

```sh
npm install
npm run dev        # server de dezvoltare la http://localhost:4321
```

Configurația locală merge în `.env` (vezi `.env.example`):

```sh
PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Build

```sh
npm run build      # produce dist/ (folosit de Cloudflare Pages)
npm run preview    # previzualizează build-ul
```

Build-ul în mod production încarcă automat `.env.production` (ruta API-ului real):

```sh
PUBLIC_API_URL=https://api.banionline.ro/api/v1
```

> `.env` și `.env.production` sunt ignorate de git. La deploy, Cloudflare Pages
> injectează `PUBLIC_API_URL` (via variabile de mediu sau `wrangler.toml`
> `[env.production]`) — verifică că ruta API-ului din build este cea de producție.

## Structură

- `src/pages/` — rutele site-ului (`/`, `/curs/…`, `/blog`, `/pricing`,
  `/login`, `/signup`, `/success`, `/termeni`, `/privacy`, `/afiliati`, `404`)
- `src/content/` — colecțiile de conținut (modulele cursului, fișiere `.md` din rădăcină)
- `src/components/` — componente UI (Navbar, Footer, PricingCard, ModuleGrid ș.a.)
- `src/lib/` — logica client (API client, gating lecții)
- `public/` — fișiere statice (favicon, robots.txt, sitemap.xml, og.svg)

## Deploy

```sh
npx wrangler pages deploy dist --project-name banionline
```

Sau cu variabile de mediu definite în `wrangler.toml` / dashboard-ul Cloudflare Pages.
