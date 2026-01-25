# Bijmantra Landing Page

Simple "Coming Soon" landing page for bijmantra.org.

## Deploy to Cloudflare Pages

### Option 1: Direct Upload (Easiest)

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select your account → Pages
3. Click "Create a project" → "Direct Upload"
4. Upload this `landing` folder
5. Set custom domain to `bijmantra.org`

### Option 2: Git Integration

1. Push this folder to a GitHub repo (or use the main bijmantra repo)
2. In Cloudflare Pages, connect to GitHub
3. Set build settings:
   - Build command: (leave empty)
   - Build output directory: `landing`
4. Deploy

## Email Signup Setup

The form uses [Formspree](https://formspree.io) for email collection.

### Setup Formspree:

1. Go to [formspree.io](https://formspree.io)
2. Create a free account
3. Create a new form
4. Copy your form ID (looks like `f/xyzabc123`)
5. Replace `YOUR_FORM_ID` in `index.html`:
   ```html
   <form action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
   ```

### Alternative: Buttondown

If you prefer Buttondown for newsletter:

1. Sign up at [buttondown.email](https://buttondown.email)
2. Replace the form with:
   ```html
   <form action="https://buttondown.email/api/emails/embed-subscribe/YOUR_USERNAME" method="post">
     <input type="email" name="email" placeholder="your@email.com" required>
     <button type="submit">Join Waitlist</button>
   </form>
   ```

## DNS Configuration

In Cloudflare DNS, add:

```
Type: CNAME
Name: @ (or bijmantra.org)
Target: <your-pages-project>.pages.dev
Proxy: ON (orange cloud)
```

## Files

- `index.html` — Single-file landing page with inline CSS
- `README.md` — This file

## Customization

### Update Stats

Edit the stats section in `index.html`:
```html
<div class="stat">
  <div class="stat-value">220</div>
  <div class="stat-label">Pages</div>
</div>
```

### Update GitHub Link

Replace `denishdholaria/bijmantra` with your actual GitHub username/repo.

### Add OG Image

1. Create a 1200x630px image
2. Save as `og-image.png` in this folder
3. Update the meta tag URL if needed

## Local Preview

Just open `index.html` in a browser. No build step needed.

```bash
open landing/index.html
# or
python -m http.server 8080 --directory landing
```
