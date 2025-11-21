# PrePol Deployment Guide - Vercel + Render

## 📋 Overview
This guide will help you deploy PrePol as a student prototype:
- **Frontend**: Vercel (Free tier)
- **Backend**: Render (Free tier)

---

## 📦 Model Files

Your model files are reasonably sized and can be committed to Git:
- `rf_crime_model_20251119_1852.joblib` (~64 MB)
- `PrePol_panel_2016Q4.parquet` (~1.7 MB - Q4 2016 data only)

**Note**: The panel data is reduced to Q4 2016 (Oct-Dec) to fit within Render's 512MB RAM limit. Full dataset (2013-2016) uses ~2.7GB in memory.

Both are **under GitHub's 100MB limit**, so you can commit them directly! However, if you prefer to keep your repository lean, you can still use GitHub Releases or Git LFS.

### Option A: Commit Directly to Git (Simplest)
```bash
git add model/rf_crime_model_20251119_1852.joblib
git add panels/PrePol_panel_2016Q4.parquet
git commit -m "Add model and data files for deployment"
git push origin main
```
✅ **Recommended for prototype** - No extra configuration needed!

### Option B: GitHub Releases (Alternative)
If you want to keep your repository history clean:
1. Create a GitHub Release in your repository
2. Attach the model and parquet files as release assets
3. Update backend to download them on startup (requires code changes)

### Option C: Git LFS (For Future)
If files grow larger over time, consider using Git Large File Storage

---

## 🚀 Part 1: Deploy Backend to Render

### Step 1: Prepare Repository
```bash
# Make sure all changes are committed
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 2: Commit Model Files (if not already done)

Since your files are under 100MB, you can commit them directly:
```bash
# Check if files are already tracked
git status

# If not, add them
git add model/rf_crime_model_20251119_1852.joblib
git add panels/PrePol_panel_2016Q4.parquet
git commit -m "Add model and data files"
git push origin main
```

### Step 3: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repositories

### Step 4: Create Web Service
1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Select `prepol-project`

### Step 5: Configure Service
**IMPORTANT**: Enter these settings exactly as shown:

```
Name: prepol-api
Region: Oregon (US West) or closest to you
Branch: main
Root Directory: (leave blank)
Runtime: Python 3
Build Command: pip install -r api/requirements.txt
Start Command: gunicorn --chdir api wsgi:app --timeout 120
Instance Type: Free
```

**Common mistake**: Make sure you filled in the **Build Command** field! If it's empty, gunicorn won't be installed.

### Step 6: Environment Variables (REQUIRED)
Click **Advanced** → **Add Environment Variable**:

```
PYTHON_VERSION = 3.11.0
```

**CRITICAL**: scikit-learn 1.3.0 is not compatible with Python 3.13. You MUST set Python version to 3.11 or the build will fail with Cython errors.

**Note:** Since your model files are committed to Git, Render will automatically have access to them. No need for MODEL_URL/PANEL_URL environment variables!

### Step 7: Deploy
1. Click **Create Web Service**
2. Wait 5-10 minutes for first deployment
3. Watch logs for any errors
4. Your backend URL will be:
   - `https://prepol-project.onrender.com`

### Step 8: Test Backend
Visit in browser:
- Health check: `https://prepol-project.onrender.com/api/health`
- Should return: `{"status":"healthy","model_loaded":true,"panel_loaded":true}`

---

## 🎨 Part 2: Deploy Frontend to Vercel

### Step 1: Update Production API URL
Edit `front/.env.production`:
```
VITE_API_URL=https://prepol-project.onrender.com
```

Commit and push:
```bash
git add front/.env.production
git commit -m "Update production API URL"
git push origin main
```

### Step 2: Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Authorize Vercel

### Step 3: Import Project
1. Click **Add New...** → **Project**
2. Import `prepol-project` from GitHub
3. Vercel will auto-detect Vite configuration

### Step 4: Configure Build Settings
```
Framework Preset: Vite
Root Directory: front
Build Command: npm run build
Output Directory: dist
Install Command: npm install
Node.js Version: 18.x
```

### Step 5: Environment Variables
1. Click **Environment Variables** section
2. Add variable:
   ```
   Name: VITE_API_URL
   Value: https://prepol-project.onrender.com
   ```
3. Check all environments: Production, Preview, Development

### Step 6: Deploy
1. Click **Deploy**
2. Wait 2-3 minutes
3. Your frontend will be live at: `https://your-project.vercel.app`

### Step 7: Test Production App
1. Visit: `https://your-project.vercel.app/Map`
2. Click tune icon (⚙️) in top-right
3. Select dates: 2016-12-01 to 2016-12-07
4. Click **Aplicar Filtros**
5. Map should load with crime predictions

---

## 🐛 Troubleshooting

### Backend Issues

**"Application failed to respond"**
- Check Render logs: Dashboard → Your Service → Logs
- Look for Python errors or missing dependencies
- Verify model/data files downloaded successfully

**"Out of memory"**
- Free tier has 512MB RAM limit
- Reduced dataset (Q4 2016) uses ~400MB with model loaded
- If you still encounter OOM:
  - Check Render logs for actual memory usage
  - Consider upgrading to Starter plan ($7/month, 2GB RAM)
  - Or further reduce date range in panel data

**"Operation timed out"**
- Render free tier can be slow for large predictions
- Increase timeout in Procfile: `--timeout 180`
- Or limit date range to 7 days max in frontend

**Backend spins down after 15 minutes**
- Expected on free tier
- First request after idle takes 30-60 seconds
- Consider paid tier for always-on

### Frontend Issues

**"Failed to fetch predictions"**
- Check API URL in `.env.production`
- Verify backend is running (visit health check endpoint)
- Check browser console for CORS errors

**CORS Error**
- Backend CORS should allow all origins (`"*"`)
- If restricting, add your Vercel domain to allowed origins

**Map doesn't render**
- Check browser console for errors
- Verify Leaflet CSS is loaded
- Try hard refresh: Ctrl+Shift+R

### Performance Notes

**Render Free Tier Limitations:**
- 512MB RAM
- Spins down after 15 min inactivity
- 750 hours/month (unlimited for one service)

**Optimization Tips:**
- Limit predictions to 7-day ranges
- Add loading indicators for user feedback
- Consider caching frequent date ranges
- Use Render paid tier ($7/mo) for production

---

## 💰 Cost Summary

| Service | Free Tier | Paid Option |
|---------|-----------|-------------|
| Render | 512MB RAM, Spins down | $7/mo (2GB RAM, always-on) |
| Vercel | 100GB bandwidth, Unlimited sites | $20/mo Pro |
| GitHub | Unlimited repos, 2GB/file releases | Free is enough |
| **Total** | **$0/month** | **$7-27/month** |

For a student prototype, **free tier is perfect**! ✅

---

## 📚 Next Steps

1. **Test thoroughly** with different date ranges
2. **Document** the live URLs in your README.md
3. **Create demo video** showing the application
4. **Share** with classmates and professor
5. **Monitor** Render logs for any issues

### Optional Improvements

- [ ] Add custom domain (Vercel supports free custom domains)
- [ ] Set up error tracking (Sentry free tier)
- [ ] Add Google Analytics
- [ ] Implement rate limiting on backend
- [ ] Add authentication for production use

---

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs**:
   - Render: Dashboard → Logs tab
   - Vercel: Deployment → Function Logs
   - Browser: F12 → Console tab

2. **Common Fixes**:
   - Redeploy: Push new commit to trigger rebuild
   - Clear cache: Hard refresh browser
   - Check environment variables are set correctly

3. **Resources**:
   - [Render Documentation](https://render.com/docs)
   - [Vercel Documentation](https://vercel.com/docs)
   - [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)

---

## ✅ Deployment Checklist

Before presenting:
- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] Predictions working end-to-end
- [ ] Map rendering correctly
- [ ] No console errors
- [ ] Tested with multiple date ranges
- [ ] README.md updated with live URLs
- [ ] Demo screenshots/video ready

Good luck with your prototype demo! 🎓🚀
