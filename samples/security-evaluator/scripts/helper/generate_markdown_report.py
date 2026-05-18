"""
Basic Markdown Report Generator for PyRIT Security Evaluator
Reads run_report.json and outputs a Markdown summary.
"""
import json
import os

REPORT_PATH = "reports/run_report.json"
OUTPUT_MD = "reports/summary_report.md"

def main():
    if not os.path.exists(REPORT_PATH):
        print(f"[!] {REPORT_PATH} not found. Run an evaluation first.")
        return
    with open(REPORT_PATH, "r") as f:
        data = json.load(f)
    with open(OUTPUT_MD, "w") as out:
        out.write(f"# PyRIT Security Evaluation Summary\n\n")
        out.write(f"**Total Scenarios:** {len(data)}\n\n")
        for i, entry in enumerate(data):
            out.write(f"## Scenario {i+1}\n")
            for k, v in entry.items():
                out.write(f"- **{k}**: {v}\n")
            out.write("\n")
    print(f"[+] Markdown report written to {OUTPUT_MD}")

if __name__ == "__main__":
    main()
