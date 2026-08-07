import json
from pathlib import Path

from dotenv import load_dotenv

from providers.claude_provider import ClaudeProvider
from mitigations.sandwich import sandwich
from mitigations.delimiting import delimit_user_prompt
from scoring.scorer import score

# Project root = two levels up from this file (harness/runner.py -> project root).
# Using this instead of a relative path means the script works no matter what
# directory you run it from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = PROJECT_ROOT / "corpus"
RESULTS_PATH = PROJECT_ROOT / "results" / "results.json"

# Load the .env file explicitly from the project root, so the API key loads
# correctly regardless of current working directory.
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# "baseline" = no mitigation applied (mitigation_fn is None, skip transform step).
# The other two point at the actual transform functions from mitigations/.
MITIGATIONS = {
    "baseline": None,
    "sandwich": sandwich,
    "delimiting": delimit_user_prompt,
}


def load_corpus():
    # rglob("*.json") finds every .json file under corpus/, in all 4 subfolders,
    # without needing to hardcode each subfolder name.
    attacks = []
    for path in sorted(CORPUS_DIR.rglob("*.json")):
        with open(path) as f:
            attacks.append(json.load(f))
    return attacks


def run():
    provider = ClaudeProvider()
    attacks = load_corpus()
    results = []

    # Outer loop: each of the 9 attacks.
    for attack in attacks:
        # Inner loop: each of the 3 mitigation conditions (baseline/sandwich/delimiting).
        # 9 attacks x 3 conditions = 27 total API calls.
        for mitigation_name, mitigation_fn in MITIGATIONS.items():
            if mitigation_fn is None:
                # Baseline: send the prompts as-is, no transform.
                final_system = attack["system_prompt"]
                final_user = attack["user_prompt"]
            else:
                # Apply the mitigation transform before sending.
                final_system, final_user = mitigation_fn(
                    attack["system_prompt"], attack["user_prompt"]
                )

            # Real API call to Claude.
            response = provider.send(final_system, final_user)

            # Check if the attack's success_marker shows up in the response
            # (and wasn't just quoted while being refused).
            success = score(response, attack["success_marker"])

            # Record one row for results.json.
            results.append(
                {
                    "id": attack["id"],
                    "category": attack["category"],
                    "win_condition": attack["win_condition"],
                    "mitigation": mitigation_name,
                    "response": response,
                    "success": success,
                }
            )

            # Print progress as it runs, so you can watch it live.
            print(f"{attack['id']:22s} {mitigation_name:12s} success={success}")

    # Write all 27 results out as one JSON array.
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nWrote {len(results)} results to {RESULTS_PATH}")


if __name__ == "__main__":
    run()
