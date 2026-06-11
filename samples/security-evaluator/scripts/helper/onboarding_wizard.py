"""
PyRIT Security Evaluator Interactive Setup Wizard
Quickly checks for required config files, environment variables, and Docker setup.
"""
import os

REQUIRED_FILES = [
    ".env.local",
    ".pyrit_config",
    "reports/pyrit_ollama_demo.db"
]

DOCKER_SERVICES = [
    "copyrit", "jupyter", "gui", "pyrit-copyrit-quick"
]

def check_files():
    print("\n[Config File Check]")
    for f in REQUIRED_FILES:
        exists = os.path.exists(f) or os.path.exists(f"samples/security-evaluator/{f}")
        print(f"{'[OK]' if exists else '[MISSING]'} {f}")

def check_env():
    print("\n[Environment Variable Check]")
    for var in [
        "OLLAMA_ENDPOINT", "OLLAMA_TARGET_MODEL", "PYRIT_SQLITE_DB_PATH"
    ]:
        val = os.environ.get(var)
        print(f"{var}: {val if val else '[NOT SET]'}")

def check_docker():
    print("\n[Docker Compose Services]")
    try:
        import subprocess
        result = subprocess.run([
            "docker", "compose", "ps", "--services"
        ], capture_output=True, text=True)
        running = result.stdout.strip().split("\n")
        for svc in DOCKER_SERVICES:
            print(f"{'[RUNNING]' if svc in running else '[NOT RUNNING]'} {svc}")
    except Exception as e:
        print("[!] Docker not available or not running.")

def main():
    print("\n=== PyRIT Security Evaluator Setup Wizard ===")
    check_files()
    check_env()
    check_docker()
    print("\nReview the above. For missing files, copy from config/.env.local.example or .pyrit_config.example.")

if __name__ == "__main__":
    main()
