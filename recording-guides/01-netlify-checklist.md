# Video 1 — Put the React portfolio on Netlify

This is the deployment checklist for the first video. The two full spoken scripts are the SQLite and MongoDB guides beside this file. The new site has not been published yet.

## Before recording

1. In the Desktop checkout, run `npm run dev:full`. Check your content, resume, filters, and GitHub lab locally.
2. Run `npm run build`. Confirm `dist/index.html` exists. Netlify publishes **dist**, not `src` or the whole repository.
3. Sign into GitHub, Netlify, and (for a live backend) Render before recording. Keep credentials, environment values containing secrets, and browser account details off-camera.
4. Review `git status` and `git diff`. The supplied resume is intentionally a public-facing download, so verify it is the version you want on your public website.
5. Commit and push the reviewed files to the intended GitHub branch when ready. That push was not performed during preparation. A Netlify site linked to a production branch may automatically deploy on push.

## Suggested 8–12 minute screen sequence

- **0:00:** show the local portfolio. Say: “Localhost runs on my computer. Deploying puts a built copy on a host other people can reach.”
- **1:00:** show `package.json` and run `npm run build`. Explain that Vite bundles the frontend into `dist`; this output is what a static host serves.
- **2:00:** open Netlify and use its current import-from-Git workflow. Select `sparekh14/ADC-Personal-Portfolio`. UI labels may change; follow the repository import option rather than memorizing a button label.
- **3:00:** show build command **npm run build**, publish directory **dist**, repository root as base, and the intended production branch. `netlify.toml` already records the build settings. Node 24 is configured.
- **4:00:** deploy, inspect the build log, and open the resulting HTTPS URL.
- **5:00:** check desktop/mobile layout, project links, resume download, filters, and theme. Open the URL from a separate browser context to prove it is not relying on the dev server.
- **6:00:** explain the GitHub lab. A static site can show the labeled snapshot immediately. Live requests need the separate Python host below.
- **8:00:** show a small content edit and explain the commit → push → automatic deploy workflow if the site is linked to that branch. Avoid committing actual credentials during the recording.
- **Closing:** “Open your deployed URL, check the links, and make sure someone else can visit it. That is the deliverable; localhost alone isn't a public deployment.”

## Connect the live FastAPI backend

Do this before filming, or make it a clearly marked optional segment. React on Netlify and Python on Render are two deployments.

1. In Render, create a Python web service from the same repository, with the repository root as the root directory.
2. Build: `pip install -r backend/requirements.txt`
3. Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Health path: `/health`.
5. Set `ALLOWED_ORIGINS` to the exact Netlify site origin, such as `https://your-site.netlify.app`. For Samarth's existing site, the supplied origin is `https://fascinating-gecko-e92876.netlify.app`. Use whichever origin actually hosts this new build. Include additional custom-domain origins separated by commas if needed.
6. Choose an available hosting plan after reviewing any cost shown by Render. No paid plan was provisioned during preparation.
7. Confirm `https://YOUR_API_HOST/health` returns `{"status":"ok"}` and `/api/github` returns repository JSON.
8. In Netlify, set `VITE_API_BASE_URL=https://YOUR_API_HOST` (no `/api` suffix). Redeploy/rebuild so Vite embeds the value.
9. Open the site and verify the lab shows **Live data** or **Cached data** and repository rows. “Saved snapshot” means the frontend fallback is working; it is not proof of a working live backend.
10. In browser Network tools, inspect the request to the API origin. The response should be JSON and CORS should allow the deployed frontend origin.

`GITHUB_TOKEN` is optional and belongs only on Render. Never put it in `VITE_API_BASE_URL`, a `VITE_` variable, or committed source.

## Fast frontend-only option

If the deadline is only about publishing the portfolio, build with `npm run build` and upload `dist` using Netlify's manual deploy option. Manual uploads do not run your build for you. The core portfolio works and the GitHub lab uses a labeled saved snapshot. You can connect the FastAPI service afterward and rebuild.

## Final recording check

- Public HTTPS URL opens on another device/browser.
- Resume, email, GitHub, LinkedIn, and project destinations work.
- No horizontal page overflow on a phone-sized screen.
- Project filter and theme toggle work.
- GitHub lab accurately labels live/cache/snapshot status.
- No secrets or personal account screens are visible in the recording.
- The classroom SQLite and MongoDB write APIs remain local.

References: [Netlify Vite setup](https://docs.netlify.com/build/frameworks/framework-setup-guides/vite/), [manual and Git deploys](https://docs.netlify.com/deploy/create-deploys/), [Render FastAPI deployment](https://render.com/docs/deploy-fastapi), [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/).
