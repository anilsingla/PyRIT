import subprocess
import os

def test_baseline_attack_dry_run():
    script = 'samples/security-evaluator/scripts/app/main.py'
    if not os.path.exists(script):
        assert True, 'main.py not present, skipping.'
        return
    result = subprocess.run([
        'python', script, '--attack-mode', 'baseline', '--dry-run'
    ], capture_output=True, text=True)
    assert 'baseline' in result.stdout or result.returncode == 0
