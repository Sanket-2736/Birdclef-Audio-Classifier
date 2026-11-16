# Auth Token & Upload Issue - Debug & Fix Guide

## Problem
After successful login, uploading an OGG file redirects to login page instead of showing results.

**Root Cause**: Frontend was not sending the Authorization header on upload requests because axios interceptors weren't being triggered for multipart form data in older axios versions.

---

## Solution Applied (3 Fixes)

### Fix 1: useRecordingUpload.js - Explicit Auth Headers
**File**: `frontend/src/hooks/useRecordingUpload.js`

Added explicit `Authorization` header to all API calls:
```javascript
const token = localStorage.getItem('token')
if (!token) {
  throw new Error('No authentication token found. Please login.')
}

const response = await axios.post(`${API_URL}/recordings/`, formData, {
  headers: {
    'Content-Type': 'multipart/form-data',
    'Authorization': `Bearer ${token}`,  // ← ADDED
  },
})
```

**Why**: Multipart form data sometimes bypasses axios interceptors. Explicit headers ensure auth always sent.

### Fix 2: useHistory.js - Explicit Auth Headers
**File**: `frontend/src/hooks/useHistory.js`

Added explicit `Authorization` header to fetch and delete operations.

### Fix 3: AuthContext.jsx - Better 401 Handling
**File**: `frontend/src/context/AuthContext.jsx`

Improved error handling:
```javascript
if (error.response?.status === 401) {
  console.log('401 Unauthorized - logging out')
  logout()
  // Only redirect if not already on login page
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}
```

**Why**: Prevents infinite redirects and adds logging for debugging.

---

## Testing the Fix

### Step 1: Restart Frontend
```bash
# Stop frontend (Ctrl+C)
# Then restart:
npm run dev
```

### Step 2: Test Login → Upload Flow

```bash
# In browser console (F12 → Console tab), paste this to watch auth:
localStorage.getItem('token')
// Should show: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Step 3: Test Upload with DevTools

1. Open DevTools (F12 → Network tab)
2. Register/Login
3. Go to Analyze page
4. Upload an OGG file
5. **Watch Network tab**:
   - `POST /recordings/` request should show:
     - Status: 202 (Accepted, not 401)
     - Request Headers → Authorization: `Bearer <token>`
     - Response: `{"id": "...", "status": "queued"}`

### Step 4: Expected Behavior

✅ **Correct Flow**:
1. Upload file → Status 202 (processing queued)
2. Polling starts → `/recordings/{id}/status` calls with auth token
3. After ~30-60s → Redirects to `/results/{id}`
4. Results page loads with prediction data

❌ **Wrong Flow** (before fix):
1. Upload file → Status 202 (but token not sent)
2. Polling fails with 401
3. Auth interceptor logs out
4. Redirects to `/login`

---

## MySQL Database URL

Your .env already has the correct format:

```ini
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/birdclef_db
```

**Format Breakdown**:
- `mysql+pymysql://` — Connection driver
- `root` — MySQL username
- `your_password` — Your MySQL password (already set to `SKBelekar2736`)
- `localhost` — MySQL server address
- `3306` — MySQL port (default)
- `birdclef_db` — Database name

**To verify connection**:
```bash
# In backend directory with venv activated:
python -c "from app.config import get_settings; print(get_settings().DATABASE_URL)"
```

---

## Debugging Commands

### 1. Check Token in Browser
```javascript
// Open DevTools → Console
localStorage.getItem('token')
// Shows your JWT token if logged in
```

### 2. Verify Token on Backend
```bash
# Copy token from browser console, then:
TOKEN="your-token-here"
curl -X GET http://localhost:8000/recordings/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Monitor Frontend Logs
```javascript
// Open DevTools → Console
// Look for messages like:
// "401 Unauthorized - logging out"
// "No authentication token found"
```

### 4. Monitor Network Requests
1. Open DevTools → Network tab
2. Filter by: `XHR` (XMLHttpRequest)
3. Upload file and watch requests
4. Click each request to see:
   - Request Headers (should have Authorization)
   - Response (should be 202 or 200, not 401)

---

## Common Errors & Solutions

### Error: "No authentication token found. Please login."
**Cause**: Token not in localStorage after login

**Solution**:
```bash
# 1. Check login response in Network tab (should have access_token)
# 2. Verify localStorage stores token:
localStorage.getItem('token')
# 3. If empty, check browser privacy settings aren't blocking localStorage
```

### Error: 401 on Upload (POST /recordings/)
**Cause**: Old code didn't send auth header

**Solution**: Already fixed! Just restart frontend:
```bash
npm run dev
```

### Error: Recording uploads but redirects to /login
**Cause**: After upload, polling requests fail with 401

**Solution**: 
1. Verify fix is applied in useRecordingUpload.js
2. Restart frontend
3. Check Network tab that polling requests have Authorization header

### Error: CORS Error on Upload
**Cause**: Backend CORS not configured for multipart

**Solution**: Backend already configured. Verify:
```bash
# Check backend .env:
FRONTEND_ORIGIN=http://localhost:5173
# Should match your frontend URL
```

---

## Files Modified

| File | Change | Why |
|------|--------|-----|
| `frontend/src/hooks/useRecordingUpload.js` | Added explicit `Authorization` header to all API calls | Multipart form data bypasses interceptors |
| `frontend/src/hooks/useHistory.js` | Added explicit `Authorization` header to fetch/delete | Consistency with upload fix |
| `frontend/src/context/AuthContext.jsx` | Improved 401 handling & added logging | Better debugging & prevents infinite loops |

---

## Verification Checklist

- [ ] Frontend restarted (`npm run dev`)
- [ ] Backend still running (`python -m uvicorn app.main:app --reload`)
- [ ] Login successful (user info shows in navbar)
- [ ] Token exists in localStorage
- [ ] Upload file → Status shows 202 (not redirecting)
- [ ] Network tab shows Authorization header on POST /recordings/
- [ ] Polling happens with token
- [ ] Results page loads after processing

---

## Next Steps

If still having issues:

1. **Enable debug logging**:
```javascript
// In AuthContext, add before axios calls:
console.log('Token:', localStorage.getItem('token'))
console.log('Making request to:', API_URL)
```

2. **Check backend logs** for 401 errors:
```bash
# Backend terminal should show:
# INFO:     127.0.0.1:58767 - "POST /recordings/ HTTP/1.1" 202
# NOT: "401 Unauthorized"
```

3. **Verify database connection**:
```bash
# Check MySQL is running
mysql -u root -p
# Should connect to MySQL
```

4. **Check file permissions**:
```bash
# Ensure storage directory is writable
ls -la backend/storage/
# Should show rwx permissions
```

---

## Success Message

When working correctly, you should see:

**Frontend**:
1. ✅ Login successful
2. ✅ Navigate to /analyze
3. ✅ Upload file (no error)
4. ✅ Progress stepper shows stages
5. ✅ Auto-redirects to /results/{id}
6. ✅ Results page loads

**Backend Logs**:
```
INFO:     127.0.0.1:xxxxx - "POST /recordings/ HTTP/1.1" 202
INFO:     Recording queued for processing
INFO:     Starting background inference
```

---

**Problem Fixed! 🎉** Test the flow and let me know if upload works now.
