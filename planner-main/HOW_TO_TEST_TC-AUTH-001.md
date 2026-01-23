# How to Test TC-AUTH-001: Generate Token Successfully

This guide shows you how to test the token generation endpoint using different methods.

## Test Case Details

- **Test ID:** TC-AUTH-001
- **Endpoint:** `POST /token`
- **Input:** `subject=test_user&expires_minutes=60`
- **Expected:** 200 OK, returns access_token, token_type, expires_in_minutes, subject
- **Validation:** Token is valid JWT, contains subject claim

## Prerequisites

1. API server must be running:
   ```powershell
   .\start_api.ps1
   ```

2. Verify API is accessible:
   ```powershell
   # Check health endpoint
   Invoke-WebRequest -Uri "http://localhost:8000/health"
   ```

## Method 1: Using Swagger UI (Easiest)

1. **Open Swagger UI:**
   - Navigate to: `http://localhost:8000/docs`
   - Or: `http://localhost:8000/redoc`

2. **Find the Token Endpoint:**
   - Scroll to find `POST /token` endpoint
   - It's under the "authentication" tag
   - This endpoint does NOT require authentication (it's public)

3. **Click "Try it out"**

4. **Enter Parameters:**
   - **subject:** `test_user`
   - **expires_minutes:** `60`

5. **Click "Execute"**

6. **Verify Response:**
   - Status: `200`
   - Response body should contain:
     ```json
     {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "token_type": "bearer",
       "expires_in_minutes": 60,
       "subject": "test_user"
     }
     ```

7. **Validate Token:**
   - Copy the `access_token` value
   - It should be a long JWT string starting with `eyJ...`
   - The token contains the subject claim

## Method 2: Using Postman (Detailed Guide)

### Step-by-Step Postman Setup

#### Step 1: Open Postman
- Launch Postman application
- Create a new request or use an existing collection

#### Step 2: Create New Request
1. Click **"New"** → **"HTTP Request"** (or press `Ctrl+N`)
2. Name the request: `TC-AUTH-001: Generate Token`

#### Step 3: Configure Request
1. **Set Method:**
   - Select **POST** from the dropdown (default is GET)

2. **Enter URL:**
   - URL: `http://localhost:8000/token`
   - Or use full URL with query params: `http://localhost:8000/token?subject=test_user&expires_minutes=60`

3. **Add Query Parameters (Alternative Method):**
   - Click **"Params"** tab
   - Add parameter:
     - **Key:** `subject` → **Value:** `test_user`
     - **Key:** `expires_minutes` → **Value:** `60`
   - Postman will automatically append to URL: `?subject=test_user&expires_minutes=60`

#### Step 4: Configure Headers (Optional)
- Go to **"Headers"** tab
- No headers required for this endpoint (it's public)
- Postman will automatically add `Content-Type` if needed

#### Step 5: Send Request
1. Click the blue **"Send"** button
2. Wait for response (should be instant)

#### Step 6: Verify Response

**Check Response Status:**
- Status code should be: **200 OK**
- Status text: "OK"

**Check Response Body:**
- Go to **"Body"** tab
- Select **"Pretty"** view for formatted JSON
- Response should look like:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJpYXQiOjE3Njg0Nzg4MjAsImV4cCI6MTc2ODQ4MjQyMH0...",
    "token_type": "bearer",
    "expires_in_minutes": 60,
    "subject": "test_user"
  }
  ```

**Verify Response Fields:**
- ✅ `access_token` exists and is a long string starting with `eyJ`
- ✅ `token_type` equals `"bearer"`
- ✅ `expires_in_minutes` equals `60`
- ✅ `subject` equals `"test_user"`

#### Step 7: Save Token for Future Use

**Option A: Copy Token Manually**
1. In the response body, copy the `access_token` value
2. Store it in a safe place (notepad, environment variable, etc.)

**Option B: Use Postman Environment Variables (Recommended)**
1. Click **"Environments"** in left sidebar (or `Ctrl+E`)
2. Create new environment: **"Planner API Local"**
3. Add variable:
   - **Variable:** `access_token`
   - **Initial Value:** (leave empty)
   - **Current Value:** (leave empty)
4. In the response, click on `access_token` value
5. Select **"Set: Planner API Local > access_token"**
6. Token is now saved in environment

**Option C: Use Postman Tests (Automated)**
1. Go to **"Tests"** tab in the request
2. Add this test script:
   ```javascript
   // Parse response
   var jsonData = pm.response.json();
   
   // Save token to environment
   pm.environment.set("access_token", jsonData.access_token);
   
   // Validate response
   pm.test("Status code is 200", function () {
       pm.response.to.have.status(200);
   });
   
   pm.test("Response has access_token", function () {
       pm.expect(jsonData).to.have.property('access_token');
   });
   
   pm.test("Token is valid JWT format", function () {
       pm.expect(jsonData.access_token).to.match(/^eyJ/);
   });
   
   pm.test("Token type is bearer", function () {
       pm.expect(jsonData.token_type).to.eql('bearer');
   });
   
   pm.test("Subject matches input", function () {
       pm.expect(jsonData.subject).to.eql('test_user');
   });
   
   pm.test("Expires in 60 minutes", function () {
       pm.expect(jsonData.expires_in_minutes).to.eql(60);
   });
   ```
3. Send request again
4. Check **"Test Results"** tab - all tests should pass ✅

#### Step 8: Use Token in Other Requests

**Method 1: Manual Authorization Header**
1. Create a new request (e.g., `POST /plan`)
2. Go to **"Authorization"** tab
3. Type: Select **"Bearer Token"**
4. Token: Paste your token or use `{{access_token}}` if saved in environment
5. Send request

**Method 2: Environment Variable (Automatic)**
1. If you saved token in environment (Step 7, Option B or C)
2. In any request, go to **"Authorization"** tab
3. Type: Select **"Bearer Token"**
4. Token: Enter `{{access_token}}`
5. Postman will automatically use the saved token

### Postman Collection Setup

**Create a Collection:**
1. Click **"New"** → **"Collection"**
2. Name: **"Planner Agent API Tests"**
3. Add description: "Test cases for Planner Agent API"
4. Add the token request to this collection

**Organize Tests:**
- Create folder: **"Authentication"**
- Move token request to this folder
- Create more requests for other test cases

### Postman Pre-request Script (Optional)

To automatically generate a fresh token before each request:

1. In your collection, go to **"Pre-request Script"** tab
2. Add this script:
   ```javascript
   // Generate token if not exists or expired
   if (!pm.environment.get("access_token")) {
       pm.sendRequest({
           url: pm.environment.get("base_url") + '/token',
           method: 'POST',
           header: {
               'Content-Type': 'application/json'
           },
           body: {
               mode: 'urlencoded',
               urlencoded: [
                   {key: 'subject', value: 'test_user'},
                   {key: 'expires_minutes', value: '60'}
               ]
           }
       }, function (err, res) {
           if (!err) {
               var jsonData = res.json();
               pm.environment.set("access_token", jsonData.access_token);
           }
       });
   }
   ```

### Postman Test Scripts for Validation

**Add to "Tests" tab for automatic validation:**

```javascript
// TC-AUTH-001: Generate Token Successfully

// Test 1: Status Code
pm.test("TC-AUTH-001: Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Response Time
pm.test("TC-AUTH-001: Response time is less than 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

// Test 3: Response has JSON body
pm.test("TC-AUTH-001: Response has JSON body", function () {
    pm.response.to.be.json;
});

// Test 4: Parse response
var jsonData = pm.response.json();

// Test 5: Required fields exist
pm.test("TC-AUTH-001: Response has access_token field", function () {
    pm.expect(jsonData).to.have.property('access_token');
});

pm.test("TC-AUTH-001: Response has token_type field", function () {
    pm.expect(jsonData).to.have.property('token_type');
});

pm.test("TC-AUTH-001: Response has expires_in_minutes field", function () {
    pm.expect(jsonData).to.have.property('expires_in_minutes');
});

pm.test("TC-AUTH-001: Response has subject field", function () {
    pm.expect(jsonData).to.have.property('subject');
});

// Test 6: Token format validation
pm.test("TC-AUTH-001: Token is valid JWT format (starts with eyJ)", function () {
    pm.expect(jsonData.access_token).to.match(/^eyJ/);
});

pm.test("TC-AUTH-001: Token has three parts (header.payload.signature)", function () {
    var parts = jsonData.access_token.split('.');
    pm.expect(parts.length).to.eql(3);
});

// Test 7: Token type validation
pm.test("TC-AUTH-001: Token type is bearer", function () {
    pm.expect(jsonData.token_type).to.eql('bearer');
});

// Test 8: Expiration validation
pm.test("TC-AUTH-001: Expires in 60 minutes", function () {
    pm.expect(jsonData.expires_in_minutes).to.eql(60);
});

// Test 9: Subject validation
pm.test("TC-AUTH-001: Subject matches input (test_user)", function () {
    pm.expect(jsonData.subject).to.eql('test_user');
});

// Test 10: Save token to environment
pm.test("TC-AUTH-001: Save token to environment", function () {
    pm.environment.set("access_token", jsonData.access_token);
    pm.expect(pm.environment.get("access_token")).to.not.be.empty;
});

// Test 11: Token is not empty
pm.test("TC-AUTH-001: Token is not empty", function () {
    pm.expect(jsonData.access_token).to.not.be.empty;
    pm.expect(jsonData.access_token.length).to.be.above(50);
});
```

**After sending request, check "Test Results" tab:**
- All 11 tests should show ✅ (green checkmark)
- If any test fails, it will show ❌ with error message

### Postman Screenshots Guide

**Request Configuration:**
```
Method: POST
URL: http://localhost:8000/token
Params Tab:
  - subject: test_user
  - expires_minutes: 60
```

**Expected Response:**
```
Status: 200 OK
Time: < 100ms
Body (JSON):
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in_minutes": 60,
  "subject": "test_user"
}
```

### Troubleshooting in Postman

**Issue: "Could not get response"**
- Check if API server is running: `.\start_api.ps1`
- Verify URL is correct: `http://localhost:8000/token`
- Check network connectivity

**Issue: "404 Not Found"**
- Verify endpoint path: `/token` (not `/tokens` or `/token/`)
- Check base URL: `http://localhost:8000`

**Issue: "Invalid JSON response"**
- Check if API returned HTML error page
- Verify API is running and accessible
- Check response in "Raw" tab

**Issue: Token not saved in environment**
- Make sure environment is selected (top right dropdown)
- Check environment variable name matches: `access_token`
- Verify test script executed successfully

### Postman Collection Export

**Export your collection:**
1. Click on collection name
2. Click **"..."** (three dots) → **"Export"**
3. Select **"Collection v2.1"**
4. Save as `Planner_Agent_API_Tests.postman_collection.json`

**Share with team:**
- Export includes all requests, tests, and scripts
- Others can import and use immediately

## Method 3: Using PowerShell

```powershell
# Generate token
$response = Invoke-RestMethod -Uri "http://localhost:8000/token?subject=test_user&expires_minutes=60" -Method POST

# Display response
$response | ConvertTo-Json

# Extract token
$token = $response.access_token
Write-Host "Token: $token"

# Verify token structure (should start with eyJ)
if ($token -match "^eyJ") {
    Write-Host "[PASS] Token is valid JWT format" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Token is not valid JWT format" -ForegroundColor Red
}

# Verify subject
if ($response.subject -eq "test_user") {
    Write-Host "[PASS] Subject matches input" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Subject mismatch" -ForegroundColor Red
}
```

**Expected Output:**
```
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60,
  "subject": "test_user"
}

Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[PASS] Token is valid JWT format
[PASS] Subject matches input
```

## Method 4: Using Python

```python
import requests

# Generate token
response = requests.post(
    "http://localhost:8000/token",
    params={"subject": "test_user", "expires_minutes": 60}
)

# Check status
if response.status_code == 200:
    print("[PASS] Status code: 200 OK")
else:
    print(f"[FAIL] Status code: {response.status_code}")
    exit(1)

# Parse response
data = response.json()
print(f"Response: {data}")

# Validate token
token = data.get("access_token")
if token and token.startswith("eyJ"):
    print("[PASS] Token is valid JWT format")
else:
    print("[FAIL] Token is not valid JWT format")

# Validate subject
if data.get("subject") == "test_user":
    print("[PASS] Subject matches input")
else:
    print("[FAIL] Subject mismatch")

# Validate required fields
required_fields = ["access_token", "token_type", "expires_in_minutes", "subject"]
missing = [field for field in required_fields if field not in data]
if not missing:
    print("[PASS] All required fields present")
else:
    print(f"[FAIL] Missing fields: {missing}")
```

## Method 5: Using curl (Command Line)

```bash
# Generate token
curl -X POST "http://localhost:8000/token?subject=test_user&expires_minutes=60"

# With pretty JSON output
curl -X POST "http://localhost:8000/token?subject=test_user&expires_minutes=60" | python -m json.tool
```

**Expected Output:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60,
  "subject": "test_user"
}
```

## Method 6: Using Automated Test Script

Run the provided test script:

```powershell
# PowerShell version
.\test_api_scenarios.ps1

# Python version
python test_api_scenarios.py
```

The script will automatically:
- Generate token
- Validate response
- Check token format
- Verify subject claim
- Display pass/fail result

## Validation Checklist

After executing the test, verify:

- [ ] **Status Code:** 200 OK
- [ ] **Response Contains:**
  - [ ] `access_token` field (JWT string)
  - [ ] `token_type` field (value: "bearer")
  - [ ] `expires_in_minutes` field (value: 60)
  - [ ] `subject` field (value: "test_user")
- [ ] **Token Format:**
  - [ ] Starts with `eyJ` (base64 encoded JWT header)
  - [ ] Contains three parts separated by dots (header.payload.signature)
- [ ] **Token Content:**
  - [ ] Contains subject claim matching input
  - [ ] Token is not expired (check `exp` claim if decoded)

## Decoding JWT Token (Optional Verification)

To verify the token contents, you can decode it:

**Online Tool:**
- Visit: https://jwt.io
- Paste your token
- Verify the payload contains:
  ```json
  {
    "sub": "test_user",
    "iat": <timestamp>,
    "exp": <timestamp>
  }
  ```

**Using PowerShell:**
```powershell
$token = $response.access_token
$parts = $token.Split('.')
$payload = $parts[1]

# Decode base64 (add padding if needed)
$payloadBytes = [Convert]::FromBase64String($payload.PadRight($payload.Length + (4 - $payload.Length % 4) % 4, '='))
$payloadJson = [System.Text.Encoding]::UTF8.GetString($payloadBytes)
$payloadJson | ConvertFrom-Json
```

## Troubleshooting

### Issue: Connection Refused
**Solution:** Make sure API server is running:
```powershell
.\start_api.ps1
```

### Issue: 404 Not Found
**Solution:** Check the URL is correct: `http://localhost:8000/token`

### Issue: No Response
**Solution:** Check if API is accessible:
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health"
```

### Issue: Invalid Token Format
**Solution:** 
- Verify the response contains `access_token` field
- Check if token starts with `eyJ`
- Ensure no extra characters or encoding issues

## Next Steps

After successfully generating a token:

1. **Use Token for Authenticated Requests:**
   ```powershell
   $headers = @{Authorization = "Bearer $token"}
   Invoke-RestMethod -Uri "http://localhost:8000/plan" -Method POST -Headers $headers -Body $body
   ```

2. **Test Other Authentication Scenarios:**
   - TC-AUTH-002: Generate Token with Custom Subject
   - TC-AUTH-003: Access Protected Endpoint Without Token
   - TC-AUTH-004: Access Protected Endpoint with Invalid Token

3. **Continue with Plan Generation Tests:**
   - Use the token to test protected endpoints
   - See `api_test_plan.md` for complete test scenarios

## Quick Test Command

**One-liner to test and validate:**
```powershell
$r = Invoke-RestMethod -Uri "http://localhost:8000/token?subject=test_user&expires_minutes=60" -Method POST; if ($r.access_token -match "^eyJ" -and $r.subject -eq "test_user") { Write-Host "[PASS] TC-AUTH-001" -ForegroundColor Green } else { Write-Host "[FAIL] TC-AUTH-001" -ForegroundColor Red }
```

