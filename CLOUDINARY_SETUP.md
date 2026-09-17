# Cloudinary image storage setup

This project keeps local filesystem storage for local development, but automatically uses Cloudinary when these environment variables are configured.

Add these variables to the deployment environment (and your local `.env` if you want local uploads to use Cloudinary too):

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

For Vercel, add them under the project's Environment Variables and redeploy.

The API secret must remain server-side and must never be exposed in frontend JavaScript.

What is stored:
- Media Library: `site/<random-id>`
- Product images: `products/<random-id>`
- Category images: `categories/<random-id>`

The database stores the returned permanent Cloudinary HTTPS URL.

If Cloudinary variables are absent:
- local development keeps the existing local `app/static/...` fallback
- Vercel uploads are rejected with a configuration error instead of writing to ephemeral storage

Existing local filesystem images are not automatically copied to Cloudinary. Re-upload them through the Admin Media Library after Cloudinary is configured, or migrate them separately.
