import sys
from pathlib import Path
from huggingface_hub import snapshot_download

DEST = str(Path.home() / "demos" / "pii-demo-containerized-docker" / "models")
print("Downloading curtburk/pii-masking-demo-models -> %s" % DEST, flush=True)
path = snapshot_download(
    repo_id="curtburk/pii-masking-demo-models",
    local_dir=DEST,
    allow_patterns=["*.gguf"],   # only the two GGUFs the compose mounts
)
print("DONE ->", path, flush=True)
