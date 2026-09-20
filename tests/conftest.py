import os

os.environ.setdefault("AUR_DISABLE_MANAGER", "1")
os.environ.setdefault("AUR_DURABILITY", "file")
os.environ.setdefault("AUR_TRANSPORT", "fake")
os.environ.setdefault("AUR_STATE_DIR", "/tmp/aur-test-state")
os.environ.setdefault("AUR_TRACE_DIR", "/tmp/aur-test-traces")
