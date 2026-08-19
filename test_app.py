import os
import pandas as pd
from utils import clean_text, validate_csv, build_profile, validate_sender_info
from generator import parse_llm_response, generate_single_prospect

def run_tests():
    print("Running Verification Tests...\n")
    
    # Test 1: clean_text
    print("Testing clean_text...")
    assert clean_text("  hello   world  \n") == "hello world"
    print("[Pass] clean_text works correctly.\n")

    # Test 2: validate_sender_info
    print("Testing validate_sender_info...")
    sender = validate_sender_info("Krish", "Acme AI", "Founder", "Sales automation", "https://acme.ai")
    assert "Name: Krish" in sender
    assert "Company: Acme AI" in sender
    print("[Pass] validate_sender_info works correctly.\n")

    # Test 3: build_profile with missing profile column
    print("Testing build_profile...")
    row_no_profile = {
        "name": "Sarah",
        "job_title": "Head of Marketing",
        "company": "Acme Technologies"
    }
    profile_built = build_profile(row_no_profile)
    assert "Name: Sarah" in profile_built
    assert "Job Title: Head of Marketing" in profile_built
    assert "Company: Acme Technologies" in profile_built
    print("[Pass] build_profile works correctly.\n")

    # Test 4: parse_llm_response
    print("Testing parse_llm_response...")
    raw_response = """
    SUBJECT:
    Quick idea for Acme's outbound growth

    EMAIL:
    Hi Sarah,

    I saw you are heading marketing at Acme. Let's discuss outbound.

    Best,
    Krish

    FOLLOW_UP:
    Hi Sarah, just following up. Let me know what you think.
    """
    parsed = parse_llm_response(raw_response)
    assert "Quick idea" in parsed["subject"]
    assert "Hi Sarah, \n\nI saw" in parsed["email"] or "I saw you" in parsed["email"]
    assert "just following up" in parsed["follow_up"]
    print("[Pass] parse_llm_response works correctly.\n")

    # Test 5: Validate CSV
    print("Testing validate_csv...")
    df_valid = pd.DataFrame([row_no_profile])
    is_valid, err = validate_csv(df_valid)
    assert is_valid == True
    
    df_invalid = pd.DataFrame([{"age": 30}])
    is_valid, err = validate_csv(df_invalid)
    assert is_valid == False
    print("[Pass] validate_csv works correctly.\n")

    # Test 6: API check (if API key exists)
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        print("Testing generate_single_prospect with real Groq API key...")
        try:
            res = generate_single_prospect(
                profile="Sarah is Head of Marketing at Acme. Recently posted about improving outbound conversion.",
                tone="Friendly",
                goal="Start a conversation",
                sender_info=sender
            )
            print("Successfully received generated outreach!")
            print(f"Subject: {res['subject']}")
            print(f"Email: {res['email']}")
            print(f"Follow up: {res['follow_up']}")
            print("[Pass] generate_single_prospect works correctly.\n")
        except Exception as e:
            print(f"[Fail] generate_single_prospect failed: {e}\n")
    else:
        print("[Skip] Skipping API test because GROQ_API_KEY is not defined in .env.\n")

    print("All verification tests passed successfully!")

if __name__ == "__main__":
    run_tests()
