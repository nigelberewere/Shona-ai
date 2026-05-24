import os
import re
import sys

# Reconfigure stdout to support UTF-8 on Windows terminal
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure directory exists
os.makedirs("data/raw/conversations", exist_ok=True)

def main():
    print("JOB 4: Building synthetic Shona conversation dataset...")

    # Load corpus
    with open('data/processed/all_clean.txt', encoding='utf-8') as f:
        corpus_lines = [l.strip() for l in f if l.strip()]

    # Lowercase full text for substring search verification
    full_corpus_text = "\n".join(corpus_lines).lower()

    # Step 1: Extract real questions from corpus
    questions = [l for l in corpus_lines if '?' in l and len(l) > 20]
    print(f"Found {len(questions)} real Shona questions in corpus.")
    
    print("\n--- Sample real questions from corpus ---")
    for q in questions[:10]:
        print(f"  {q}")

    # Step 2: Define candidate phrases and verify against corpus
    candidate_greetings = [
        "Mhoro, makadii?",
        "Makadii henyu?", 
        "Marara sei?",
        "Mangwanani.",
        "Masikati.",
        "Manheru.",
        "Zita rako ndiani?",
        "Unobva kupi?",
    ]

    candidate_responses = [
        "Tiripo, makadinwo?",
        "Ndiripo zvakanaka, ndatenda.",
        "Ndinofara, makadinwo?",
        "Tiripo henyu.",
        "Zita rangu ndi Tambaoga.",
        "Ndinobva kuHarare.",
        "Ndiripo henyu.",
    ]

    print("\nVerifying greetings against the real corpus...")
    verified_greetings = []
    for g in candidate_greetings:
        # Standardize search by striping ending punctuation for better matching
        clean_g = re.sub(r'[?.!,]', '', g).strip().lower()
        if clean_g in full_corpus_text:
            verified_greetings.append(g)
            print(f"  [VERIFIED] '{g}' exists in corpus.")
        else:
            print(f"  [FAILED]   '{g}' NOT found in corpus.")

    print("\nVerifying responses against the real corpus...")
    verified_responses = []
    for r in candidate_responses:
        clean_r = re.sub(r'[?.!,]', '', r).strip().lower()
        if clean_r in full_corpus_text:
            verified_responses.append(r)
            print(f"  [VERIFIED] '{r}' exists in corpus.")
        else:
            print(f"  [FAILED]   '{r}' NOT found in corpus.")

    # Create synthetic conversation exchanges using verified combinations
    conversations = []
    
    # 1. Standard verified greeting-response pairs
    greeting_pairs = [
        ("Mhoro, makadii?", "Tiripo, makadinwo?"),
        ("Makadii henyu?", "Ndiripo zvakanaka, ndatenda."),
        ("Marara sei?", "Tiripo henyu."),
        ("Mangwanani.", "Ndiripo henyu."),
        ("Masikati.", "Tiripo henyu."),
        ("Manheru.", "Tiripo henyu."),
        ("Zita rako ndiani?", "Zita rangu ndi Tambaoga."),
        ("Unobva kupi?", "Ndinobva kuHarare.")
    ]

    print("\nPairing verified conversation turns...")
    for q, a in greeting_pairs:
        # Verify both parts exist in the corpus first
        q_clean = re.sub(r'[?.!,]', '', q).strip().lower()
        a_clean = re.sub(r'[?.!,]', '', a).strip().lower()
        if q_clean in full_corpus_text and a_clean in full_corpus_text:
            conversations.append(f"{q} {a}")
            print(f"  Added: {q} {a}")

    # 2. Extract natural QA pairs from the corpus!
    natural_pairs_count = 0
    for i in range(len(corpus_lines) - 1):
        line = corpus_lines[i]
        next_line = corpus_lines[i+1]
        if '?' in line and not '?' in next_line and len(line) > 15 and len(next_line) > 15:
            if len(line) < 100 and len(next_line) < 100:
                conversations.append(f"{line} {next_line}")
                natural_pairs_count += 1
                if natural_pairs_count <= 15:
                    print(f"  [NATURAL QA] Added: {line} {next_line}")

    # Remove duplicates
    conversations = list(dict.fromkeys(conversations))

    print(f"\nTotal synthetic/natural conversation lines generated: {len(conversations)}")

    # Save to data/raw/conversations/shona_conversations.txt
    output_file = "data/raw/conversations/shona_conversations.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for convo in conversations:
            f.write(convo + "\n")
    print(f"Saved to {output_file}")

    # Print first 50 generated lines for review (avoid overwhelming console)
    print("\n--- FIRST 50 GENERATED DIALOGUE LINES FOR REVIEW ---")
    for idx, convo in enumerate(conversations[:50]):
        # Encode as UTF-8 safe print or replace characters
        print(f"{idx+1}: {convo}")

if __name__ == "__main__":
    main()
