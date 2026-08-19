import os
import re
import time
from dotenv import load_dotenv
from groq import Groq
from typing import Dict, Any, Tuple, Optional, List
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# Load environment variables at module import
load_dotenv()

def get_groq_client() -> Optional[Groq]:
    """Initialize and return the Groq client if the API key is present."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None

def parse_llm_response(text: str) -> Dict[str, str]:
    """
    Parse the LLM response to extract SUBJECT, EMAIL, and FOLLOW_UP.
    Handles minor formatting variations and provides fallback values if parsing fails.
    """
    clean_text = text.strip()
    
    # Try finding headers using regex and slicing the text sequentially
    # We look for:
    # 1. Subject block
    # 2. Email block
    # 3. Follow-up block
    
    subject_pattern = r'(?i)\b(?:subject)\b\s*:?'
    email_pattern = r'(?i)\b(?:email\s*(?:body)?|outreach)\b\s*:?'
    follow_up_pattern = r'(?i)\b(?:follow[-_\s]*up|followup)\b\s*:?'
    
    # Collect all matches and their start/end spans
    positions = []
    
    sub_match = list(re.finditer(subject_pattern, clean_text))
    if sub_match:
        positions.append((sub_match[0].start(), sub_match[0].end(), "subject"))
        
    email_match = list(re.finditer(email_pattern, clean_text))
    if email_match:
        positions.append((email_match[0].start(), email_match[0].end(), "email"))
        
    follow_match = list(re.finditer(follow_up_pattern, clean_text))
    if follow_match:
        positions.append((follow_match[0].start(), follow_match[0].end(), "follow_up"))
        
    # Sort positions by start index
    positions.sort(key=lambda x: x[0])
    
    res = {"subject": "", "email": "", "follow_up": ""}
    
    # Extract sections based on the sorted boundaries
    for i in range(len(positions)):
        current_type = positions[i][2]
        start_content = positions[i][1]
        end_content = positions[i+1][0] if i + 1 < len(positions) else len(clean_text)
        
        section_text = clean_text[start_content:end_content].strip()
        
        # Remove any leading markdown code fences, headers, or leading colons/symbols
        section_text = re.sub(r'^[:\s\-\*=]+', '', section_text).strip()
        section_text = re.sub(r'```[a-zA-Z]*', '', section_text).strip()
        section_text = re.sub(r'```$', '', section_text).strip()
        
        res[current_type] = section_text
        
    # Validation / Fallbacks if any section is empty
    # If all extraction failed completely, let's try splitting on headers manually
    if not res["subject"] and not res["email"] and not res["follow_up"]:
        # Let's see if we can do line-based matching as a fallback
        lines = clean_text.split('\n')
        curr_section = None
        curr_lines = []
        for line in lines:
            line_strip = line.strip()
            line_upper = line_strip.upper()
            if "SUBJECT:" in line_upper:
                if curr_section:
                    res[curr_section] = "\n".join(curr_lines).strip()
                curr_section = "subject"
                curr_lines = [line_strip.replace("SUBJECT:", "").strip()]
            elif "EMAIL:" in line_upper:
                if curr_section:
                    res[curr_section] = "\n".join(curr_lines).strip()
                curr_section = "email"
                curr_lines = [line_strip.replace("EMAIL:", "").strip()]
            elif "FOLLOW_UP:" in line_upper or "FOLLOW-UP:" in line_upper or "FOLLOWUP:" in line_upper:
                if curr_section:
                    res[curr_section] = "\n".join(curr_lines).strip()
                curr_section = "follow_up"
                curr_lines = [line_strip.replace("FOLLOW_UP:", "").replace("FOLLOW-UP:", "").replace("FOLLOWUP:", "").strip()]
            else:
                if curr_section:
                    curr_lines.append(line)
        if curr_section:
            res[curr_section] = "\n".join(curr_lines).strip()

    # Final cleanup & fallback values
    if not res["subject"]:
        res["subject"] = "Quick note regarding your background"
    if not res["email"]:
        # If we failed to extract any email, put the full response as email
        res["email"] = clean_text
    if not res["follow_up"]:
        res["follow_up"] = "Hi,\n\nJust wanted to briefly follow up on my previous note. Let me know if you have a few minutes to connect this week."
        
    return res

def generate_single_prospect(
    profile: str,
    tone: str,
    goal: str,
    sender_info: str = "No sender information provided."
) -> Dict[str, str]:
    """
    Generate cold outreach subject, email, and follow-up using Groq API.
    Returns a dictionary containing "subject", "email", and "follow_up".
    """
    client = get_groq_client()
    if not client:
        raise ValueError("Groq API key is missing. Please configure it in your .env file.")
        
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Build the prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        profile=profile,
        tone=tone,
        goal=goal,
        sender_info=sender_info
    )
    
    # Call Groq API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3, # Low temperature for consistent adherence to formatting & guidelines
        max_tokens=1000
    )
    
    raw_response = response.choices[0].message.content
    parsed = parse_llm_response(raw_response)
    
    # Store raw response in parsed as well for absolute safety fallback
    parsed["raw_response"] = raw_response
    return parsed

def generate_batch(
    prospects: List[Dict[str, Any]],
    tone: str,
    goal: str,
    sender_info: str = "No sender information provided.",
    progress_callback = None
) -> List[Dict[str, Any]]:
    """
    Process batch generation row-by-row.
    Returns updated list of prospects with generated content.
    """
    results = []
    total = len(prospects)
    
    for idx, prospect in enumerate(prospects):
        name = prospect.get("name", "Prospect")
        if progress_callback:
            progress_callback(idx + 1, total, name)
            
        # Get profile text using utils (profile should have already been built)
        profile_text = prospect.get("built_profile", "")
        if not profile_text:
            profile_text = prospect.get("profile", "")
            
        if not profile_text.strip():
            # If empty, skip or log error
            prospect["generated_subject"] = ""
            prospect["generated_email"] = "Empty profile data."
            prospect["generated_follow_up"] = ""
            prospect["generation_status"] = "failed"
            results.append(prospect)
            continue
            
        try:
            # Generate outreach
            outreach = generate_single_prospect(
                profile=profile_text,
                tone=tone,
                goal=goal,
                sender_info=sender_info
            )
            
            prospect["generated_subject"] = outreach["subject"]
            prospect["generated_email"] = outreach["email"]
            prospect["generated_follow_up"] = outreach["follow_up"]
            prospect["generation_status"] = "success"
            
        except Exception as e:
            prospect["generated_subject"] = ""
            prospect["generated_email"] = f"Generation failed: {str(e)}"
            prospect["generated_follow_up"] = ""
            prospect["generation_status"] = "failed"
            
        # Optional delay to respect rate limits gently
        time.sleep(0.5)
        results.append(prospect)
        
    return results
