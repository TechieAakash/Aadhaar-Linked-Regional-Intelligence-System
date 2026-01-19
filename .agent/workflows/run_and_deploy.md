---
description: How to run and deploy the ALRIS serverless project
---

# Running and Deploying ALRIS

Since the project has been refactored into modular Vercel Serverless APIs, you should use the **Vercel CLI** for the best experience.

## 1. Install Vercel CLI
If you haven't already, install the Vercel CLI globally using npm:
```bash
npm i -g vercel
```

## 2. Local Development
To run the project locally with full serverless function support and routing:
// turbo
1. Open your terminal in the project root.
2. Run the development server:
   ```bash
   vercel dev
   ```
3. Your app will be available at `http://localhost:3000`.

## 3. Deployment
To deploy your changes to Vercel production:
1. Ensure all changes are committed and pushed to GitHub (Vercel usually deploys automatically on push).
2. Alternatively, use the CLI:
   ```bash
   vercel --prod
   ```

## 4. Environment Variables
Ensure you have set the `UIDAI_API_KEY` in your Vercel Dashboard under **Project Settings > Environment Variables**.
