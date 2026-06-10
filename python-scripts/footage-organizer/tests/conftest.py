import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Tests import config (and cli_index, which imports config). config._require
# hard-fails without ANTHROPIC_API_KEY — give it a dummy so import-time checks
# pass. load_dotenv won't override an already-set env var, so a real .env still
# wins on dev machines.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
