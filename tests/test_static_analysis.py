from analyze_code import analyze_code


def test_static_analysis_has_no_issues():
    issues = analyze_code("explorer.py") + analyze_code("clipboard_helpers.py")
    assert issues == []
