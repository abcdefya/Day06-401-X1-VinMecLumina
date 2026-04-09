import sys

from src.agents.agent import chat_loop
from src.workflow import run_workflow


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "chat":
        chat_loop()
        return

    # Minimal smoke run for workflow demo.
    result = run_workflow(patient_id="P001")
    print("Patient:", result.get("patient_profile", {}).get("patient_id"))
    print("Severity:", result.get("overall_severity", "UNKNOWN"))
    print("Summary:", result.get("summary", ""))
    print("Suggestions:", result.get("suggestions", []))


if __name__ == "__main__":
    main()
