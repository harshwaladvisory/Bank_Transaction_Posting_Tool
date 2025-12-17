# Deployment Guide - Bank Transaction Posting Tool

## Quick Fix Summary

The following issues have been resolved to fix the "Verifying..." deployment hang:

### ✅ Fixes Applied

1. **Added `pymongo` to requirements.txt**
   - MongoDB support is now properly declared as a dependency

2. **Removed Local File Dependencies**
   - ❌ Removed: `custom_master_data.json` (now using MongoDB only)
   - ❌ Removed: `uploads/` folder (files processed in-memory with tempfile)
   - ✅ All data now stored in MongoDB or processed in-memory

3. **Non-Blocking MongoDB Connection**
   - Changed from blocking 5-second timeout to lazy initialization
   - App starts immediately even if MongoDB is unavailable
   - Reduced timeout from 5000ms to 2000ms
   - Connection cached and reused across requests
   - Graceful fallback to static data if MongoDB unavailable

4. **Fixed Port Configuration**
   - Centralized in `config.py` using environment variables
   - Default port: 8587 (configurable via `PORT` env var)
   - Default host: 0.0.0.0 (listens on all interfaces)

## Deployment Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `pymongo>=4.0.0` - MongoDB driver (REQUIRED)
- `flask>=2.0.0` - Web framework
- `pandas>=1.5.0` - Data processing
- `openpyxl>=3.0.0` - Excel handling
- `pdfplumber>=0.7.0` - PDF parsing

### 2. Set Environment Variables

Configure these on your deployment server:

```bash
# MongoDB Configuration (REQUIRED)
export MONGODB_URI="mongodb://your-server:27017/"
export MONGODB_DATABASE="bank_posting_tool"

# Flask Configuration (OPTIONAL)
export PORT=8587                    # Default: 8587
export FLASK_DEBUG="False"          # Default: False (use "True" for dev)
```

**For Windows:**
```cmd
set MONGODB_URI=mongodb://your-server:27017/
set MONGODB_DATABASE=bank_posting_tool
set PORT=8587
set FLASK_DEBUG=False
```

### 3. Start the Application

```bash
# Option 1: Direct Python
python app.py

# Option 2: Via main.py with web flag
python main.py --web

# Option 3: Production with Gunicorn (Linux)
gunicorn -w 4 -b 0.0.0.0:8587 app:app
```

### 4. Verify Deployment

Open your browser and navigate to:
```
http://your-server-ip:8587
```

Or test the API health check:
```bash
curl http://your-server-ip:8587/api/status
```

Expected response:
```json
{
  "status": "ok",
  "mongodb": "connected",
  "database": "bank_posting_tool",
  "timestamp": "2025-12-17T..."
}
```

## MongoDB Setup

### Option 1: MongoDB Atlas (Cloud - Recommended for Deployment)

1. Create a free cluster at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Get connection string (looks like `mongodb+srv://user:pass@cluster.mongodb.net/`)
3. Set environment variable:
   ```bash
   export MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net/"
   ```

### Option 2: Local MongoDB

1. Install MongoDB: [mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
2. Start MongoDB:
   ```bash
   # Linux/Mac
   mongod

   # Windows
   "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe"
   ```
3. Use default URI (already configured):
   ```bash
   mongodb://localhost:27017/
   ```

### Option 3: Docker MongoDB

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_DATABASE=bank_posting_tool \
  mongo:latest
```

## Troubleshooting

### Issue: "Verifying..." screen takes too long

**Root Cause:** MongoDB connection timeout blocking app startup

**Solutions:**
1. ✅ **Fixed in code** - Connection is now lazy and non-blocking
2. Verify MongoDB is accessible from your server
3. Check firewall rules allow port 27017
4. Test MongoDB connection manually:
   ```bash
   mongosh "mongodb://your-server:27017/"
   ```

### Issue: App works but data doesn't persist

**Root Cause:** MongoDB not connected, using static data only

**Solutions:**
1. Check MongoDB URI in environment variables
2. Verify MongoDB is running:
   ```bash
   # Check if MongoDB is listening
   netstat -an | grep 27017  # Linux/Mac
   netstat -an | findstr 27017  # Windows
   ```
3. Check app logs for MongoDB connection messages

### Issue: pymongo import error

**Root Cause:** Missing dependency

**Solution:**
```bash
pip install pymongo>=4.0.0
```

### Issue: Port already in use

**Root Cause:** Another process using port 8587

**Solution:**
```bash
# Change port via environment variable
export PORT=8588

# Or find and kill the process using port 8587
# Linux/Mac:
lsof -ti:8587 | xargs kill -9

# Windows:
netstat -ano | findstr :8587
taskkill /PID <PID> /F
```

## Performance Optimization

### 1. MongoDB Connection Pooling

Already configured with optimal settings:
- `serverSelectionTimeoutMS=2000` - Quick timeout
- `connectTimeoutMS=2000` - Fast connection attempt
- `socketTimeoutMS=2000` - Prevent hung connections

### 2. Enable Production Mode

```bash
export FLASK_DEBUG="False"
```

### 3. Use Production Server (Recommended)

Instead of Flask's built-in server, use Gunicorn or uWSGI:

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:8587 --timeout 120 app:app
```

### 4. MongoDB Indexes

Indexes are created automatically on first use with `background=True` to avoid blocking.

## Security Recommendations

1. **Change Secret Key** in production:
   ```python
   # In app.py, use environment variable
   app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')
   ```

2. **Enable MongoDB Authentication**:
   ```bash
   export MONGODB_URI="mongodb://username:password@your-server:27017/"
   ```

3. **Use HTTPS** in production (configure reverse proxy like Nginx)

4. **Restrict FLASK_HOST** if not needed publicly:
   ```bash
   export FLASK_HOST="127.0.0.1"  # localhost only
   ```

## Monitoring

### Check App Status

```bash
curl http://your-server:8587/api/status
```

### Check MongoDB Connection

```bash
curl http://your-server:8587/api/stats
```

### View Logs

Application prints connection status on startup:
- `✓ MongoDB connected:` - Connection successful
- `✗ MongoDB connection failed:` - Connection failed, using static data
- `→ Application running without MongoDB` - No MongoDB available

## Production Checklist

- [ ] `pymongo` installed (`pip install -r requirements.txt`)
- [ ] MongoDB URI configured (`MONGODB_URI` environment variable)
- [ ] MongoDB database configured (`MONGODB_DATABASE` environment variable)
- [ ] MongoDB is accessible from server
- [ ] Port configured (`PORT` environment variable)
- [ ] Debug mode disabled (`FLASK_DEBUG="False"`)
- [ ] Secret key changed (for production)
- [ ] Firewall allows incoming connections on configured port
- [ ] Application starts without blocking
- [ ] `/api/status` endpoint returns `"mongodb": "connected"`

## Quick Start (Local Testing)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start MongoDB (if using local)
mongod

# 3. Run app (in another terminal)
python app.py

# 4. Open browser
# Navigate to http://localhost:8587
```

## Architecture Changes Summary

### Before (Had Issues)
- ❌ Files saved to `uploads/` folder (local dependency)
- ❌ Custom data in `custom_master_data.json` (local dependency)
- ❌ MongoDB connection blocking at startup (5-second hang)
- ❌ Duplicate writes to both MongoDB and local files
- ❌ Missing `pymongo` in requirements.txt

### After (Fixed)
- ✅ Files processed in-memory with `tempfile` (no local storage)
- ✅ All custom data in MongoDB only (no JSON files)
- ✅ Lazy MongoDB connection (non-blocking, 2-second timeout)
- ✅ Single source of truth: MongoDB for persistence, static lists for fallback
- ✅ `pymongo>=4.0.0` in requirements.txt
- ✅ Graceful degradation if MongoDB unavailable

---

**Last Updated:** December 17, 2025
**Version:** 2.0 - MongoDB Enhanced, Zero Local Dependencies
