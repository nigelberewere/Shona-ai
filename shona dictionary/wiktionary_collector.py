import urllib.request
import json
import urllib.parse
import re
import time

def get_category_members(category_name):
    print(f"Retrieving members for: {category_name}")
    encoded_cat = urllib.parse.quote(category_name)
    url = f"https://en.wiktionary.org/w/api.php?action=query&list=categorymembers&cmtitle={encoded_cat}&cmlimit=max&format=json&formatversion=2"
    
    pages = []
    cmcontinue = None
    
    while True:
        query_url = url
        if cmcontinue:
            query_url += f"&cmcontinue={urllib.parse.quote(cmcontinue)}"
        
        try:
            req = urllib.request.Request(query_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                members = data.get("query", {}).get("categorymembers", [])
                for m in members:
                    if m['ns'] == 0:  # Main namespace only
                        pages.append(m['title'])
                
                cont = data.get("continue", {})
                cmcontinue = cont.get("cmcontinue")
                if not cmcontinue:
                    break
        except Exception as e:
            print(f"Error querying category {category_name}: {e}")
            break
            
    return list(set(pages))

def fetch_wikitext_batch(titles):
    titles_str = "|".join(urllib.parse.quote(t) for t in titles)
    url = f"https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvprop=content&titles={titles_str}&format=json&formatversion=2"
    
    pages_content = {}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            pages = data.get("query", {}).get("pages", [])
            for p in pages:
                title = p['title']
                revisions = p.get("revisions", [])
                if revisions:
                    pages_content[title] = revisions[0].get("content", "")
    except Exception as e:
        print(f"Error fetching batch: {e}")
    return pages_content

def clean_wikitext(text):
    # Remove wiki link brackets [[target|text]] -> text, [[text]] -> text
    text = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    # Remove templates {{temp|arg1|arg2}} -> try to keep something sensible or strip
    text = re.sub(r'\{\{[^\}]*\}\}', '', text)
    # Strip HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_shona_section(wikitext, title):
    # Shona section usually starts with ==Shona== and ends with another ==Language== or end of text
    # Let's search for ==Shona==
    shona_match = re.search(r'==\s*Shona\s*==', wikitext)
    if not shona_match:
        return None
    
    start_pos = shona_match.end()
    # The section ends at the next level-2 header
    next_section_match = re.search(r'(?:\n|^)==([^=]+)==\s*(?:\n|$)', wikitext[start_pos:])
    if next_section_match:
        shona_text = wikitext[start_pos:start_pos + next_section_match.start()]
    else:
        shona_text = wikitext[start_pos:]
        
    # Standard fields
    part_of_speech = "unknown"
    noun_class = ""
    definition_en = ""
    synonyms = []
    antonyms = []
    
    # 1. Part of speech
    # Look for common part of speech headers under Shona: ===Noun===, ===Verb===, ===Adjective===, ===Adverb===, etc.
    pos_match = re.search(r'===\s*(Noun|Verb|Adjective|Adverb|Pronoun|Interjection|Conjunction|Preposition)\s*===', shona_text, re.IGNORECASE)
    if pos_match:
        part_of_speech = pos_match.group(1).lower()
        pos_pos = pos_match.end()
        # Find ending of this POS block
        next_pos_match = re.search(r'===[^=]+===', shona_text[pos_pos:])
        if next_pos_match:
            pos_block = shona_text[pos_pos:pos_pos + next_pos_match.start()]
        else:
            pos_block = shona_text[pos_pos:]
    else:
        pos_block = shona_text
        
    # 2. Bantu Noun Class (if it is a noun, look for {{sn-noun|head|class}})
    if part_of_speech == "noun":
        noun_template = re.search(r'\{\{sn-noun\s*\|[^|}]*\|([^|}]*)\}\}', pos_block)
        if noun_template:
            noun_class = noun_template.group(1).strip()
            # If numeric or prefix, normalize to Bantu noun class
            if noun_class.isdigit():
                noun_class = f"Class {noun_class}"
            else:
                noun_class = f"mu-/mi- (Class 3/4)" if "3" in noun_class else noun_class
    
    # 3. Definition (lines starting with # in the POS block)
    def_lines = []
    for line in pos_block.split('\n'):
        line = line.strip()
        if line.startswith('#') and not line.startswith('#*') and not line.startswith('#:'):
            cleaned = clean_wikitext(line[1:])
            if cleaned:
                def_lines.append(cleaned)
                
    if def_lines:
        definition_en = "; ".join(def_lines)
    else:
        # Fallback to general clean text
        definition_en = clean_wikitext(pos_block)
        
    # Remove common artifacts from definition
    definition_en = re.sub(r'^\s*[:;,\s]+', '', definition_en).strip()
    
    # 4. Synonyms
    syn_match = re.search(r'====\s*Synonyms\s*====\s*([\s\S]*?)(?:====|\n\n|$)', shona_text)
    if syn_match:
        for item in re.findall(r'\*\s*([^\n]*)', syn_match.group(1)):
            cleaned_syn = clean_wikitext(item)
            if cleaned_syn:
                synonyms.append(cleaned_syn)
                
    # 5. Antonyms
    ant_match = re.search(r'====\s*Antonyms\s*====\s*([\s\S]*?)(?:====|\n\n|$)', shona_text)
    if ant_match:
        for item in re.findall(r'\*\s*([^\n]*)', ant_match.group(1)):
            cleaned_ant = clean_wikitext(item)
            if cleaned_ant:
                antonyms.append(cleaned_ant)

    return {
        "word": title,
        "part_of_speech": part_of_speech,
        "class": noun_class,
        "definition_en": definition_en,
        "definition_sn": "",
        "example_sentence": "",
        "synonyms": synonyms,
        "antonyms": antonyms,
        "source": "Wiktionary"
    }

def main():
    print("Starting Wiktionary Shona lemmas collector...")
    categories = [
        "Category:Shona_lemmas",
        "Category:Shona adjectives",
        "Category:Shona adverbs",
        "Category:Shona interjections",
        "Category:Shona nouns",
        "Category:Shona pronouns",
        "Category:Shona verbs"
    ]
    
    all_lemmas = []
    for cat in categories:
        members = get_category_members(cat)
        all_lemmas.extend(members)
        
    all_lemmas = sorted(list(set(all_lemmas)))
    print(f"Total unique lemma titles to fetch: {len(all_lemmas)}")
    
    parsed_entries = []
    
    # Batch query in groups of 50
    batch_size = 50
    for i in range(0, len(all_lemmas), batch_size):
        batch = all_lemmas[i:i+batch_size]
        print(f"Fetching batch {i // batch_size + 1}/{((len(all_lemmas) - 1) // batch_size) + 1} ({len(batch)} titles)...")
        
        wikitexts = fetch_wikitext_batch(batch)
        for title in batch:
            content = wikitexts.get(title)
            if content:
                entry = parse_shona_section(content, title)
                if entry and entry["definition_en"]:
                    parsed_entries.append(entry)
            else:
                print(f"No content returned for {title}")
                
        # Sleep for polite scraping
        time.sleep(1)
        
    print(f"Successfully collected and parsed {len(parsed_entries)} valid Shona entries from Wiktionary!")
    
    # Save raw parsed dataset
    output_path = "wiktionary_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_entries, f, ensure_ascii=False, indent=2)
    print(f"Saved raw Wiktionary dictionary to {output_path}")

if __name__ == "__main__":
    main()
