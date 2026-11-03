from agentic_workflows.blueprints.secops_office import run_office, triage

FAKE_KEY = "AKIA" + "IOSFODNN7EXAMPLE"  # split so scanners ignore this test file


def test_triage_plans_by_files():
    assert triage({"files": {}}) == []
    assert triage({"files": {"a.py": "x"}}) == ["secret_scan"]
    assert "dependency_audit" in triage({"files": {"requirements.txt": ""}})


def test_clean_change_is_approved():
    r = run_office({"files": {"a.py": "x = 1"}})
    assert r.verdict == "approve" and r.findings == []


def test_secret_blocks():
    r = run_office({"files": {"cfg.py": f'KEY = "{FAKE_KEY}"'}})
    assert r.verdict == "block" and "aws-access-key" in r.findings[0].message


def test_vulnerable_dependency_blocks():
    r = run_office({"files": {"requirements.txt": "examplelib==1.0.0\nrequests==2.0\n"}})
    assert r.verdict == "block"
    assert "EX-2024-001" in r.findings[0].message


def test_fixed_dependency_passes_and_unpinned_warns():
    ok = run_office({"files": {"requirements.txt": "examplelib==2.1.0"}})
    assert ok.verdict == "approve"
    warn = run_office({"files": {"requirements.txt": "examplelib"}})
    assert warn.verdict == "request_changes"


def test_licence_allowlist():
    r = run_office({"files": {"requirements.txt": "x==1"}, "licences": {"x": "GPL-3.0", "y": "MIT"}})
    assert r.verdict == "block" and len(r.findings) == 1
