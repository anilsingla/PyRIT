import os
import pytest

def test_env_local_exists():
    assert os.path.exists('samples/security-evaluator/.env.local') or \
           os.path.exists('samples/security-evaluator/config/.env.local.example')

def test_pyrit_config_exists():
    assert os.path.exists('samples/security-evaluator/.pyrit_config') or \
           os.path.exists('samples/security-evaluator/config/.pyrit_config.example')

def test_sqlite_db_path():
    db_path = 'samples/security-evaluator/reports/pyrit_ollama_demo.db'
    assert os.path.exists(db_path) or os.path.exists(db_path.replace('/', '\\'))
