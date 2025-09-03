# Resume Upload Issue Fix

## Problem Summary
The resume upload is failing with a **Row-Level Security (RLS) policy violation** for the `resumes` table in Supabase.

**Error**: `new row violates row-level security policy for table "resumes"`

## Root Cause
The `resumes` table exists in Supabase but the RLS policies are either missing or incorrectly configured, preventing users from inserting their own resume data.

## Solution

### 1. Fix RLS Policies (REQUIRED)
Run the SQL script in your **Supabase Dashboard > SQL Editor**:

```sql
-- Copy and paste the contents of fix_rls_policies.sql
```

Or manually copy from `fix_rls_policies.sql` file.

### 2. Next.js API Route Fix (COMPLETED ✅)
Fixed the async params issue in `frontend/src/app/api/profile/[userId]/route.ts` by changing:
```typescript
{ params }: { params: { userId: string } }
```
to:
```typescript
{ params }: { params: Promise<{ userId: string }> }
```

### 3. Database Schema Update (COMPLETED ✅)
Updated `backend/migrations/supabase-schema.sql` to include the `resumes` table definition.

## Testing Steps

1. **Apply the RLS policies** by running `fix_rls_policies.sql` in Supabase SQL Editor
2. **Restart your backend** to ensure clean state
3. **Test resume upload** through the onboarding flow
4. **Check logs** for any remaining issues

## Files Modified

- ✅ `frontend/src/app/api/profile/[userId]/route.ts` - Fixed async params
- ✅ `backend/migrations/supabase-schema.sql` - Added resumes table
- ✅ `fix_rls_policies.sql` - Created RLS fix script
- ✅ `fix_resume_upload_issue.py` - Created diagnostic script

## Expected Result

After applying the RLS policies, resume uploads should work without the `42501` error, and users should be able to complete the onboarding flow successfully.

## Verification

You can verify the fix worked by:
1. No more `HTTP 500` errors in the backend logs
2. No more `42501` RLS policy violation errors
3. Successful resume upload and processing
4. User can proceed past the resume upload step in onboarding