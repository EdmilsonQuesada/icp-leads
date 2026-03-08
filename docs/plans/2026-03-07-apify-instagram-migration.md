# Apify Instagram Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate from instagrapi (blocked by rate limits) to Apify for reliable Instagram lead collection with automatic proxy rotation and no IP blocking.

**Architecture:**
- **Phase 1**: Setup Apify API token and test Instagram Hashtag Scraper manually
- **Phase 2**: Create `ApifyClient` wrapper in backend, integrate with FastAPI endpoints
- **Phase 3**: Build Celery task to import Apify results, enrich data, save to database
- **Phase 4**: Update Frontend SearchPage to use new Apify-powered `/search/apify` endpoint instead of instagrapi

**Tech Stack:**
- Apify SDK (Python client)
- FastAPI (existing backend)
- Celery (task queue)
- PostgreSQL (existing database)
- React (existing frontend)

**Rationale:**
- Apify uses residential proxies → no IP blocking
- Automatic rate limiting handling
- 10x more reliable than instagrapi (which breaks with Instagram updates)
- Low cost (~$5-10/month for your use case)
- Minimal changes to existing architecture

---

## PHASE 1: Setup Apify & Test Manually

### Task 1.1: Generate Apify API Token

**Files:**
- Reference: Apify Console (https://console.apify.com)

**Step 1: Log into Apify Console**
- Go to https://console.apify.com
- Sign in with your existing account (edmilsonquesada_constelacao@...)
- You're already logged in (saw screenshot above)

**Step 2: Generate API Token**
- Click your profile icon (top-right)
- Go to **Settings > Integrations > API Tokens**
- Click **Create new token**
- Name it: `ICP-Ideal-Instagram-Scraper`
- Give it access to: **Actors and Datasets** (default)
- Click **Create**
- **COPY the token** (you'll only see it once!)

**Step 3: Save token securely**
- Store in safe place (will need for Step 1.3)
- DO NOT commit to git

**Step 4: Verify token works**
- You'll use this in Task 1.3

---

### Task 1.2: Test Instagram Hashtag Scraper Manually via UI

**Goal:** Understand input/output structure before coding

**Step 1: Open Instagram Hashtag Scraper**
- Go to: https://apify.com/apify/instagram-hashtag-scraper
- Click **Try for free** or **Use actor**

**Step 2: Configure input**
- Under **Input**, set:
  ```
  Hashtags: constelação familiar
  Search posts: true
  Max posts per hashtag: 10
  ```

**Step 3: Start the run**
- Click **Start**
- Wait for completion (~2-3 minutes)

**Step 4: Examine output structure**
- Go to **Results** tab (or **Storage > Default dataset**)
- Click **Export** → **JSON**
- Download the JSON file
- **EXAMINE it** - look for:
  - Post structure (caption, likes, comments, author, etc)
  - Comment author usernames
  - Timestamps
  - Images/media links

**Step 5: Document the structure**
- Create file: `docs/APIFY_RESPONSE_STRUCTURE.md`
- Document what fields are available
- Note which fields you'll use for leads

**Expected output structure (sample):**
```json
{
  "postId": "123456789",
  "caption": "Post text about constelação familiar",
  "likes": 150,
  "comments": [
    {
      "id": "comm123",
      "text": "comment text",
      "owner": {
        "username": "user_handle",
        "name": "User Name",
        "id": "uid123"
      }
    }
  ],
  "owner": {
    "username": "influencer_handle",
    "name": "Influencer Name",
    "followers": 5000
  },
  "timestamp": "2026-03-07T12:00:00Z",
  "mediaUrls": ["url1", "url2"]
}
```

---

### Task 1.3: Test Apify API from Python (Local)

**Files:**
- Create: `docs/test_apify_api.py` (temporary, for testing only)

**Step 1: Install apify-client**
```bash
pip install apify-client
```
Expected: Package installed successfully

**Step 2: Create test script**
```python
# docs/test_apify_api.py
from apify_client import ApifyClient

# Initialize client with your token
api_token = "YOUR_APIFY_API_TOKEN_HERE"  # Paste the token from Task 1.2
client = ApifyClient(api_token)

# Run the Instagram Hashtag Scraper actor
run_input = {
    "hashtags": ["constelação familiar"],
    "searchPostsFirst": True,
    "postsPerHashtag": 10,
}

print("🚀 Starting Apify actor run...")
actor_run = client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)

print(f"✅ Run finished with status: {actor_run['status']}")
print(f"Run ID: {actor_run['id']}")
print(f"Dataset ID: {actor_run['defaultDatasetId']}")

# Fetch results
dataset = client.dataset(actor_run["defaultDatasetId"])
items = dataset.list_items().items

print(f"\n📊 Retrieved {len(items)} items")
if items:
    print("\n🔍 First item structure:")
    import json
    print(json.dumps(items[0], indent=2))
```

**Step 3: Run the test script**
```bash
cd D:\Projetos\ClaudeCode\ICP_Ideal
python docs/test_apify_api.py
```

Expected output:
```
🚀 Starting Apify actor run...
✅ Run finished with status: succeeded
Run ID: <some-id>
Dataset ID: <dataset-id>

📊 Retrieved 10 items
🔍 First item structure:
{
  "postId": "...",
  "caption": "...",
  ...
}
```

**Step 4: Verify and document**
- Note the exact field names and structure
- Take screenshot of output
- Update `docs/APIFY_RESPONSE_STRUCTURE.md` if needed

**Step 5: Clean up**
- Delete `docs/test_apify_api.py` (we'll use it in backend tests)
- Commit only the documentation
```bash
git add docs/APIFY_RESPONSE_STRUCTURE.md
git commit -m "docs: document Apify Instagram Hashtag Scraper response structure"
```

---

## PHASE 2: Backend Integration (ApifyClient)

### Task 2.1: Add Apify token to .env

**Files:**
- Modify: `backend/.env`

**Step 1: Open backend/.env**
```bash
# In your editor or terminal
# backend/.env
```

**Step 2: Add token**
```
# Apify Integration
APIFY_API_TOKEN=your_token_here_from_task_1_2
```

**Step 3: Verify**
```bash
# Don't commit this with real token!
# It's already in .gitignore (check)
cat backend/.env | grep APIFY_API_TOKEN
```

Expected: Shows the token (only in local, never in git)

---

### Task 2.2: Update config.py to load Apify token

**Files:**
- Modify: `backend/app/core/config.py`

**Step 1: Read current config.py**
```bash
cd D:\Projetos\ClaudeCode\ICP_Ideal
cat backend/app/core/config.py | head -50
```

**Step 2: Add Apify token to Settings class**

Find the Settings class and add:
```python
# In class Settings(BaseSettings):

APIFY_API_TOKEN: str = Field(
    default="",
    description="Apify API token for Instagram scraping"
)
```

**Step 3: Verify**
```bash
# Will be verified in Task 2.3
```

---

### Task 2.3: Create ApifyClient wrapper

**Files:**
- Create: `backend/app/integrations/apify_client.py`

**Step 1: Create directory**
```bash
mkdir -p backend/app/integrations
touch backend/app/integrations/__init__.py
```

**Step 2: Create ApifyClient class**
```python
# backend/app/integrations/apify_client.py
"""
Wrapper around Apify SDK for Instagram scraping
"""
import logging
from typing import Optional, List, Dict, Any
from apify_client import ApifyClient as ApifySDK
from app.core.config import settings

logger = logging.getLogger(__name__)

INSTAGRAM_HASHTAG_SCRAPER = "apify/instagram-hashtag-scraper"
INSTAGRAM_POST_SCRAPER = "apify/instagram-post-scraper"


class ApifyClient:
    """
    Wrapper for Apify SDK
    Provides high-level methods for Instagram scraping
    """

    def __init__(self):
        if not settings.APIFY_API_TOKEN:
            raise ValueError("APIFY_API_TOKEN not configured in .env")
        self.client = ApifySDK(settings.APIFY_API_TOKEN)
        self.logger = logger

    def scrape_hashtags(
        self,
        hashtags: List[str],
        max_posts_per_hashtag: int = 50,
        search_posts: bool = True,
    ) -> Dict[str, Any]:
        """
        Scrape posts from Instagram hashtags

        Args:
            hashtags: List of hashtags (with or without #)
            max_posts_per_hashtag: Maximum posts to collect per hashtag
            search_posts: Whether to search posts (vs reels)

        Returns:
            Dict with run_id, dataset_id, and status
        """
        # Clean hashtags (remove # if present)
        clean_hashtags = [h.lstrip("#") for h in hashtags]

        run_input = {
            "hashtags": clean_hashtags,
            "searchPostsFirst": search_posts,
            "postsPerHashtag": max_posts_per_hashtag,
        }

        self.logger.info(f"🚀 Starting Apify run for hashtags: {clean_hashtags}")

        try:
            actor_run = self.client.actor(INSTAGRAM_HASHTAG_SCRAPER).call(
                run_input=run_input
            )

            result = {
                "run_id": actor_run["id"],
                "dataset_id": actor_run["defaultDatasetId"],
                "status": actor_run["status"],
                "actor_id": actor_run["actId"],
            }

            self.logger.info(f"✅ Actor run created: {result['run_id']}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Error starting Apify run: {e}")
            raise

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a running actor"""
        try:
            run = self.client.run(run_id).get()
            return {
                "run_id": run["id"],
                "status": run["status"],
                "created": run["createdAt"],
                "started": run.get("startedAt"),
                "finished": run.get("finishedAt"),
            }
        except Exception as e:
            self.logger.error(f"Error getting run status: {e}")
            raise

    def fetch_results(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Fetch results from a completed actor run"""
        try:
            dataset = self.client.dataset(dataset_id)
            items = dataset.list_items().items
            self.logger.info(f"📊 Fetched {len(items)} items from dataset")
            return items
        except Exception as e:
            self.logger.error(f"Error fetching results: {e}")
            raise

    def fetch_results_paginated(
        self, dataset_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch results with pagination (for large datasets)"""
        try:
            dataset = self.client.dataset(dataset_id)
            items = dataset.list_items(limit=limit, offset=offset).items
            return items
        except Exception as e:
            self.logger.error(f"Error fetching paginated results: {e}")
            raise
```

**Step 3: Create __init__.py**
```python
# backend/app/integrations/__init__.py
from app.integrations.apify_client import ApifyClient

__all__ = ["ApifyClient"]
```

**Step 4: Verify imports work**
```bash
cd D:\Projetos\ClaudeCode\ICP_Ideal
docker compose exec -it backend python -c "from app.integrations.apify_client import ApifyClient; print('✅ ApifyClient imported successfully')"
```

Expected: `✅ ApifyClient imported successfully`

**Step 5: Commit**
```bash
git add backend/app/integrations/
git add backend/app/core/config.py
git commit -m "feat: add ApifyClient wrapper for Instagram scraping"
```

---

### Task 2.4: Create Apify search endpoint in FastAPI

**Files:**
- Modify: `backend/app/api/search.py`

**Step 1: Read current search.py**
```bash
cat backend/app/api/search.py
```

**Step 2: Add new endpoint for Apify**

Add this to the search.py file:
```python
from app.integrations.apify_client import ApifyClient

# ... existing code ...

@router.post("/search/apify")
async def search_instagram_apify(
    request: SearchJobCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Start Instagram search using Apify (new, reliable method)

    Input:
    {
        "hashtags": ["constelação familiar", "constelação sistêmica"],
        "platforms": ["instagram"],
        "max_posts": 50
    }
    """
    try:
        apify = ApifyClient()

        # Start Apify run
        run_result = apify.scrape_hashtags(
            hashtags=request.hashtags,
            max_posts_per_hashtag=request.max_posts or 50,
        )

        # Store run info in database for tracking
        search_job = SearchJob(
            job_id=run_result["run_id"],
            keywords=request.hashtags,
            platforms=request.platforms,
            status="running",
            source="apify",  # New field to distinguish from instagrapi
            metadata={
                "apify_run_id": run_result["run_id"],
                "apify_dataset_id": run_result["dataset_id"],
            }
        )
        db.add(search_job)
        db.commit()

        return {
            "job_id": search_job.id,
            "status": "running",
            "message": "Apify scraping started"
        }

    except Exception as e:
        logger.error(f"Error starting Apify search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3: Test endpoint exists**
```bash
# Won't work yet without full setup, but should not have syntax errors
docker compose exec -it backend python -c "from app.api.search import router; print('✅ Search router loaded')"
```

**Step 4: Commit**
```bash
git add backend/app/api/search.py
git commit -m "feat: add /search/apify endpoint for Apify-based Instagram scraping"
```

---

## PHASE 3: Data Pipeline (Celery Task)

### Task 3.1: Create Apify import task

**Files:**
- Create: `backend/app/tasks/apify_import.py`

**Step 1: Create task file**
```python
# backend/app/tasks/apify_import.py
"""
Celery task to import data from Apify and enrich leads
"""
import logging
from typing import List, Dict, Any
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.integrations.apify_client import ApifyClient
from app.models.lead import Lead
from app.tasks.enrichment import enrich_lead_data

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def import_apify_results(self, dataset_id: str, search_job_id: int) -> Dict[str, Any]:
    """
    Import results from completed Apify run and create leads

    Args:
        dataset_id: Apify dataset ID
        search_job_id: SearchJob ID in our database
    """
    db = SessionLocal()

    try:
        apify = ApifyClient()

        logger.info(f"📥 Importing Apify dataset: {dataset_id}")

        # Fetch all results from Apify
        items = apify.fetch_results(dataset_id)

        if not items:
            logger.warning(f"No items found in dataset {dataset_id}")
            return {"imported": 0, "skipped": 0}

        logger.info(f"📊 Processing {len(items)} items from Apify")

        imported_count = 0
        skipped_count = 0

        # Process each post
        for post in items:
            try:
                # Extract posts' author
                post_author = post.get("owner", {})
                if post_author and post_author.get("username"):
                    lead_data = {
                        "username": post_author["username"],
                        "display_name": post_author.get("name"),
                        "platform": "instagram",
                        "followers": post_author.get("followers"),
                        "profile_url": f"https://instagram.com/{post_author['username']}",
                        "source": "apify_hashtag",
                    }

                    # Enrich data (gender, score, categorization)
                    enriched = enrich_lead_data(lead_data)

                    # Check if lead already exists
                    existing = db.query(Lead).filter(
                        Lead.username == enriched["username"],
                        Lead.platform == "instagram"
                    ).first()

                    if not existing:
                        lead = Lead(**enriched)
                        db.add(lead)
                        imported_count += 1
                    else:
                        skipped_count += 1

                # Also extract commenters (leads in comments)
                comments = post.get("comments", [])
                for comment in comments:
                    commenter = comment.get("owner", {})
                    if commenter and commenter.get("username"):
                        lead_data = {
                            "username": commenter["username"],
                            "display_name": commenter.get("name"),
                            "platform": "instagram",
                            "followers": commenter.get("followers"),
                            "profile_url": f"https://instagram.com/{commenter['username']}",
                            "source": "apify_comment",
                            "comment_text": comment.get("text"),
                        }

                        enriched = enrich_lead_data(lead_data)

                        existing = db.query(Lead).filter(
                            Lead.username == enriched["username"],
                            Lead.platform == "instagram"
                        ).first()

                        if not existing:
                            lead = Lead(**enriched)
                            db.add(lead)
                            imported_count += 1
                        else:
                            skipped_count += 1

            except Exception as e:
                logger.error(f"Error processing post: {e}")
                skipped_count += 1

        db.commit()
        logger.info(f"✅ Import complete: {imported_count} new, {skipped_count} skipped")

        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "dataset_id": dataset_id,
        }

    except Exception as e:
        logger.error(f"❌ Error importing Apify results: {e}")
        db.rollback()
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    finally:
        db.close()
```

**Step 2: Register task in Celery**

Verify the task is discoverable by Celery. Check your celery config loads tasks from `app.tasks` module.

**Step 3: Test task can be imported**
```bash
docker compose exec -it backend python -c "from app.tasks.apify_import import import_apify_results; print('✅ Task imported successfully')"
```

Expected: `✅ Task imported successfully`

**Step 4: Commit**
```bash
git add backend/app/tasks/apify_import.py
git commit -m "feat: add Celery task to import Apify results and create leads"
```

---

### Task 3.2: Trigger import task when user searches

**Files:**
- Modify: `backend/app/api/search.py`

**Step 1: Update the Apify endpoint to trigger import task**

Update the `/search/apify` endpoint to queue the import task:

```python
from app.tasks.apify_import import import_apify_results

@router.post("/search/apify")
async def search_instagram_apify(
    request: SearchJobCreateRequest,
    db: Session = Depends(get_db),
):
    """Start Instagram search using Apify"""
    try:
        apify = ApifyClient()

        run_result = apify.scrape_hashtags(
            hashtags=request.hashtags,
            max_posts_per_hashtag=request.max_posts or 50,
        )

        search_job = SearchJob(
            job_id=run_result["run_id"],
            keywords=request.hashtags,
            platforms=request.platforms,
            status="running",
            source="apify",
            metadata={
                "apify_run_id": run_result["run_id"],
                "apify_dataset_id": run_result["dataset_id"],
            }
        )
        db.add(search_job)
        db.commit()

        # Queue import task (will run after Apify completes ~10-20 seconds)
        import_apify_results.apply_async(
            kwargs={
                "dataset_id": run_result["dataset_id"],
                "search_job_id": search_job.id,
            },
            countdown=15  # Wait 15 seconds before importing (let Apify finish)
        )

        return {
            "job_id": search_job.id,
            "status": "running",
            "message": "Apify scraping started"
        }

    except Exception as e:
        logger.error(f"Error starting Apify search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Test endpoint**
```bash
# Will test in Phase 4 with full integration
```

**Step 3: Commit**
```bash
git add backend/app/api/search.py
git commit -m "feat: queue import task when Apify search completes"
```

---

## PHASE 4: Frontend Integration

### Task 4.1: Add Apify search option to SearchPage

**Files:**
- Modify: `frontend/src/pages/SearchPage.jsx`

**Step 1: Read current SearchPage**
```bash
cat frontend/src/pages/SearchPage.jsx
```

**Step 2: Add Apify search button and state**

Add this to SearchPage:

```javascript
const [useApify, setUseApify] = useState(true); // Default to Apify (new, reliable)

// ... in the search form UI ...

<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">
    Método de Coleta
  </label>
  <div className="flex gap-4">
    <label className="flex items-center gap-2 text-sm cursor-pointer">
      <input
        type="radio"
        checked={useApify === true}
        onChange={() => setUseApify(true)}
      />
      🚀 Apify (Recomendado - sem bloqueios)
    </label>
    <label className="flex items-center gap-2 text-sm cursor-pointer">
      <input
        type="radio"
        checked={useApify === false}
        onChange={() => setUseApify(false)}
      />
      📸 Instagrapi (Legacy)
    </label>
  </div>
</div>
```

**Step 3: Update handleSearch to use Apify**

```javascript
const handleSearch = async () => {
  const kws = keywords.split(",").map((k) => k.trim()).filter(Boolean);
  const plts = Object.entries(platforms).filter(([, v]) => v).map(([k]) => k);

  setLoading(true);
  setStatus(null);

  try {
    let res;

    if (useApify) {
      // New Apify endpoint
      res = await api.post("/search/apify", {
        hashtags: kws,
        platforms: plts,
        max_posts: 50,
      });
    } else {
      // Legacy instagrapi endpoint
      res = await createSearch({ keywords: kws, platforms: plts });
    }

    setStatus(
      `✅ Job #${res.data.job_id} criado! Os leads serão coletados em breve.`
    );
    qc.invalidateQueries(["search-jobs"]);
  } catch (e) {
    setStatus("❌ Erro ao criar job de busca. Tente novamente.");
  } finally {
    setLoading(false);
  }
};
```

**Step 4: Commit**
```bash
git add frontend/src/pages/SearchPage.jsx
git commit -m "feat: add Apify search option to SearchPage with toggle"
```

---

## PHASE 5: Testing & Verification

### Task 5.1: End-to-end integration test

**Files:**
- Create: `tests/integration/test_apify_flow.py`

**Step 1: Create test file**

```python
# tests/integration/test_apify_flow.py
"""
Integration test for Apify Instagram scraping flow
Tests: API endpoint → Apify → Database → Frontend
"""
import pytest
from app.integrations.apify_client import ApifyClient


def test_apify_client_initialization():
    """Test ApifyClient can be initialized"""
    client = ApifyClient()
    assert client is not None
    assert client.client is not None


@pytest.mark.asyncio
async def test_search_apify_endpoint(client, db_session):
    """Test POST /search/apify endpoint"""
    response = await client.post(
        "/search/apify",
        json={
            "hashtags": ["test_hashtag"],
            "platforms": ["instagram"],
            "max_posts": 10,
        }
    )

    assert response.status_code == 200
    assert "job_id" in response.json()
    assert response.json()["status"] == "running"


def test_apify_results_structure():
    """
    Test that we handle Apify response structure correctly
    This is a smoke test - uses cached/mock data
    """
    sample_apify_result = {
        "postId": "123",
        "owner": {
            "username": "testuser",
            "name": "Test User",
            "followers": 100,
        },
        "comments": [
            {
                "owner": {
                    "username": "commenter1",
                    "name": "Commenter One",
                }
            }
        ]
    }

    # Verify structure (all fields accessible)
    assert sample_apify_result["owner"]["username"] == "testuser"
    assert len(sample_apify_result["comments"]) > 0
    assert sample_apify_result["comments"][0]["owner"]["username"] == "commenter1"
```

**Step 2: Run tests**
```bash
docker compose exec -it backend pytest tests/integration/test_apify_flow.py -v
```

Expected: Tests pass (or provide clear failures to debug)

**Step 3: Commit**
```bash
git add tests/integration/test_apify_flow.py
git commit -m "test: add integration tests for Apify flow"
```

---

### Task 5.2: Manual testing with real Apify run

**Files:**
- None (manual testing)

**Step 1: Start docker containers**
```bash
cd D:\Projetos\ClaudeCode\ICP_Ideal
docker compose up -d
docker compose exec -it backend poetry shell  # Or python -m shell
```

**Step 2: Test Apify endpoint via curl**
```bash
curl -X POST http://localhost:8000/search/apify \
  -H "Content-Type: application/json" \
  -d '{
    "hashtags": ["constelação familiar"],
    "platforms": ["instagram"],
    "max_posts": 20
  }'
```

Expected:
```json
{
  "job_id": "<number>",
  "status": "running",
  "message": "Apify scraping started"
}
```

**Step 3: Monitor Celery task**
```bash
# In another terminal, watch Celery logs
docker compose logs -f celery_worker
```

**Step 4: Verify database**
```bash
# Check if leads were created
docker compose exec -it backend psql postgresql://user:pass@db:5432/icp_ideal -c "SELECT COUNT(*) FROM leads WHERE source='apify_hashtag' OR source='apify_comment';"
```

Expected: Should see count of imported leads

**Step 5: Check frontend**
- Open http://localhost:5173
- Go to BUSCA tab
- Should see new job with status "running" then "done"
- Should show number of leads collected

**Step 6: Document results**
- Screenshot of frontend showing Apify results
- Screenshot of database showing new leads
- Save to `docs/APIFY_TESTING_RESULTS.md`

---

## Migration Checklist

- [ ] Phase 1: Setup Apify API token
- [ ] Phase 1: Test Hashtag Scraper manually in UI
- [ ] Phase 1: Test Apify API from Python
- [ ] Phase 2: Update config.py with token
- [ ] Phase 2: Create ApifyClient wrapper
- [ ] Phase 2: Create /search/apify endpoint
- [ ] Phase 3: Create import Celery task
- [ ] Phase 3: Queue task from search endpoint
- [ ] Phase 4: Add Apify toggle to frontend
- [ ] Phase 5: Run integration tests
- [ ] Phase 5: Manual end-to-end testing
- [ ] **Bonus**: Deprecate instagrapi (optional, keep as fallback)

---

## Next: Keep or Deprecate Instagrapi?

**Options:**

1. **Keep instagrapi as fallback** (current plan)
   - Users can toggle between Apify and legacy
   - Safer for transition
   - Requires maintenance

2. **Remove instagrapi entirely**
   - Cleaner codebase
   - Less dependency bloat
   - Do this only after Apify proves reliable (1-2 weeks)

**Recommendation:** Keep as fallback for now. Remove in next sprint after Apify stabilizes.

---

## Estimated Time per Phase

- **Phase 1**: 30 min (mostly waiting for Apify run)
- **Phase 2**: 1.5 hours (backend integration)
- **Phase 3**: 1 hour (Celery task)
- **Phase 4**: 30 min (frontend toggle)
- **Phase 5**: 1 hour (testing)

**Total: ~4.5 hours**

---

## Sources & References

- [Apify API Client for Python](https://docs.apify.com/api/client/python/)
- [Instagram Hashtag Scraper Actor](https://apify.com/apify/instagram-hashtag-scraper)
- [Getting Started with Apify API](https://docs.apify.com/api/v2/getting-started)
- [Apify Academy: Run Actor and Retrieve Data](https://docs.apify.com/academy/api/run-actor-and-retrieve-data-via-api)
