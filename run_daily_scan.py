
from agent.automation import run_scan

if __name__ == "__main__":
    result = run_scan()
    print("Daily scan complete.")
    print(f"Sources checked: {result['source_count']}")
    print(f"Raw jobs found: {result['raw_jobs_found']}")
    print(f"New jobs saved: {result['new_jobs_saved']}")
    print(f"High-fit alerts: {result['high_fit_jobs']}")
    print(f"Alert file: {result['alert_file']}")
    if result["errors"]:
        print("Errors:")
        for e in result["errors"]:
            print(f"- {e}")
