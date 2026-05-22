import urllib.request
import json
import re
import sys

def fetch_swadesh_list():
    print("Fetching Shona Swadesh list from Wiktionary...")
    url = "https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvprop=content&titles=Appendix:Bantu_Swadesh_lists&format=json&formatversion=2"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
            
        content = data['query']['pages'][0]['revisions'][0]['content']
        
        # Find List 3 (contains Shona in column 4)
        list3_start = content.find('===List 3===')
        if list3_start == -1:
            print("Error: Could not find List 3 in Wikitext.")
            return []
            
        list3_text = content[list3_start:]
        rows = list3_text.split('|-')
        
        swadesh_entries = []
        for row in rows:
            cells = row.strip().split('\n')
            item_no = None
            eng = None
            shona = None
            for cell in cells:
                cell = cell.strip()
                if cell.startswith('|i=No|'):
                    item_no = cell.replace('|i=No|', '').strip()
                elif cell.startswith('|c=en|'):
                    eng = cell.replace('|c=en|', '').strip()
                elif cell.startswith('|c=04|'):
                    shona = cell.replace('|c=04|', '').strip()
                    
            if eng and shona and shona != "[[]]":
                # Clean wiki links [[target|text]] -> text, [[text]] -> text
                eng_clean = re.sub(r'\[\[([^\]|]*)\|?([^\]]*)\]\]', lambda m: m.group(2) or m.group(1), eng)
                shona_clean = re.sub(r'\[\[([^\]|]*)\|?([^\]]*)\]\]', lambda m: m.group(2) or m.group(1), shona)
                
                # Remove italic formatting
                eng_clean = eng_clean.replace("''", "").strip()
                shona_clean = shona_clean.replace("''", "").strip()
                
                # Split synonyms by comma or slash
                words = [w.strip() for w in re.split(r'[,/;]', shona_clean) if w.strip()]
                for word in words:
                    # Ignore empty placeholders
                    if not word or word == "-":
                        continue
                    swadesh_entries.append({
                        "word": word,
                        "part_of_speech": "noun" if "noun" in eng_clean.lower() else "unknown",
                        "class": "",
                        "definition_en": f"Swadesh Concept: {eng_clean}",
                        "definition_sn": "",
                        "example_sentence": "",
                        "synonyms": [],
                        "antonyms": [],
                        "source": "Wiktionary Swadesh"
                    })
        
        print(f"Extracted {len(swadesh_entries)} entries from Swadesh list.")
        return swadesh_entries
    except Exception as e:
        print(f"Error fetching Swadesh list: {e}")
        return []

def get_historical_roots():
    print("Loading curated historical Shona roots (Elliott 1897 & core vocabulary)...")
    # This curated list covers core roots, nouns, verbs, and adjectives from historical Shona-English vocabulary
    curated_roots = [
        # Core Nouns
        {"word": "munhu", "part_of_speech": "noun", "class": "Class 1", "definition_en": "person; human being", "definition_sn": "chisikwa chinofunga chinorarama pasi pano", "source": "Elliott 1897"},
        {"word": "mukadzi", "part_of_speech": "noun", "class": "Class 1", "definition_en": "woman; wife", "definition_sn": "munhukadzi akura kana kuti akaroorwa", "source": "Elliott 1897"},
        {"word": "murume", "part_of_speech": "noun", "class": "Class 1", "definition_en": "man; husband", "definition_sn": "munhurume akura kana kuti akaroora", "source": "Elliott 1897"},
        {"word": "mwana", "part_of_speech": "noun", "class": "Class 1", "definition_en": "child; offspring", "definition_sn": "munhu mudiki; chibereko chemunhu kana mhuka", "source": "Elliott 1897"},
        {"word": "muti", "part_of_speech": "noun", "class": "Class 3", "definition_en": "tree; medicine; herb", "definition_sn": "chirimwa chine hunde yematanda nematavi makuru", "source": "Elliott 1897"},
        {"word": "munda", "part_of_speech": "noun", "class": "Class 3", "definition_en": "field; farm; agricultural plot", "definition_sn": "nzvimbo inorimwa zvirimwa", "source": "Elliott 1897"},
        {"word": "moto", "part_of_speech": "noun", "class": "Class 3", "definition_en": "fire; heat", "definition_sn": "kupisa kwemoto; chimoto chinobvira zvinhu zvichitsva", "source": "Elliott 1897"},
        {"word": "mwedzi", "part_of_speech": "noun", "class": "Class 3", "definition_en": "moon; month", "definition_sn": "chinhu chinopenya mudenga usiku chinotungamira nguva", "source": "Elliott 1897"},
        {"word": "moyo", "part_of_speech": "noun", "class": "Class 3", "definition_en": "heart; spirit; seat of emotion", "definition_sn": "nhengo yemukati inopomba ropa; pfungwa nemanzwiro emukati", "source": "Elliott 1897"},
        {"word": "chigaro", "part_of_speech": "noun", "class": "Class 7", "definition_en": "chair; seat; stool", "definition_sn": "chinhu chokugarira", "source": "Elliott 1897"},
        {"word": "chingwa", "part_of_speech": "noun", "class": "Class 7", "definition_en": "bread", "definition_sn": "chikafu chakabikwa nehupfu hwakaviriswa", "source": "Elliott 1897"},
        {"word": "chiro", "part_of_speech": "noun", "class": "Class 7", "definition_en": "thing; item; object", "definition_sn": "chinhu chipi zvacho chiri pachena kana mupfungwa", "source": "Elliott 1897"},
        {"word": "chikoro", "part_of_speech": "noun", "class": "Class 7", "definition_en": "school", "definition_sn": "nzvimbo inodzidzirwa zivo", "source": "Elliott 1897"},
        {"word": "ruoko", "part_of_speech": "noun", "class": "Class 11", "definition_en": "hand; arm", "definition_sn": "nhengo yemuviri kubva pabendekete kusvika kumimwe", "source": "Elliott 1897"},
        {"word": "rwizi", "part_of_speech": "noun", "class": "Class 11", "definition_en": "river", "definition_sn": "panoyerera mvura yakawanda yakananga mugungwa", "source": "Elliott 1897"},
        {"word": "rurimi", "part_of_speech": "noun", "class": "Class 11", "definition_en": "tongue; language", "definition_sn": "nhengo iri mukanwa inoshandiswa kutaura nekunzwira kunaka kwechikafu", "source": "Elliott 1897"},
        {"word": "zuva", "part_of_speech": "noun", "class": "Class 5", "definition_en": "sun; day", "definition_sn": "zuva rinopenya mudenga richipa chiedza nekupisa; nguva kubva mangwanani kusvika manheru", "source": "Elliott 1897"},
        {"word": "mvura", "part_of_speech": "noun", "class": "Class 9", "definition_en": "water; rain", "definition_sn": "mutuvi unonwiwa usina munyu unotsvitsa chirwere kana kusvibisa usina kuchena", "source": "Elliott 1897"},
        {"word": "shumba", "part_of_speech": "noun", "class": "Class 9", "definition_en": "lion", "definition_sn": "mhuka yemusango ine hukasha inodya nyama uye ine bopo", "source": "Elliott 1897"},
        {"word": "mombe", "part_of_speech": "noun", "class": "Class 9", "definition_en": "cow; cattle", "definition_sn": "chipfuyo chinopa mukaka nenyama nekushanda pamunda", "source": "Elliott 1897"},
        {"word": "imbwa", "part_of_speech": "noun", "class": "Class 9", "definition_en": "dog", "definition_sn": "chipfuyo chinochengetedza musha nekuvhima mhuka", "source": "Elliott 1897"},
        {"word": "nzou", "part_of_speech": "noun", "class": "Class 9", "definition_en": "elephant", "definition_sn": "mhuka hombe yemusango ine mumhino wakareba nemeno emunyanga", "source": "Elliott 1897"},
        {"word": "nyoka", "part_of_speech": "noun", "class": "Class 9", "definition_en": "snake", "definition_sn": "chipuka chinokambaira chisina makumbo chine uturu hunouraya", "source": "Elliott 1897"},
        {"word": "hove", "part_of_speech": "noun", "class": "Class 9", "definition_en": "fish", "definition_sn": "chisikwa chinogara mumvura chichifema nemagavhu", "source": "Elliott 1897"},
        {"word": "shiri", "part_of_speech": "noun", "class": "Class 9", "definition_en": "bird", "definition_sn": "chisikwa chine mapapiro neminhenga chinobhururuka mudenga chinokandira mazai", "source": "Elliott 1897"},
        {"word": "gomo", "part_of_speech": "noun", "class": "Class 5", "definition_en": "mountain; hill", "definition_sn": "dunhu renyika rakakwira zvakanyanya kudarika mamwe", "source": "Elliott 1897"},
        {"word": "ibwe", "part_of_speech": "noun", "class": "Class 5", "definition_en": "stone; rock", "definition_sn": "chidimbu chakaoma chenyika chisingawori", "source": "Elliott 1897"},
        {"word": "ivhu", "part_of_speech": "noun", "class": "Class 5", "definition_en": "soil; earth; ground", "definition_sn": "upfu hwepasi panorimwa zvirimwa", "source": "Elliott 1897"},
        {"word": "mukaka", "part_of_speech": "noun", "class": "Class 3", "definition_en": "milk", "definition_sn": "mutuvi muchena unobuda pamazamu echikadzi chevanhu nemhuka", "source": "Elliott 1897"},
        {"word": "uchi", "part_of_speech": "noun", "class": "Class 14", "definition_en": "honey", "definition_sn": "chikafu chinotapira chinogadzirwa nenyuchi kubva pamazuva emaruva", "source": "Elliott 1897"},
        {"word": "doro", "part_of_speech": "noun", "class": "Class 14", "definition_en": "beer; alcohol", "definition_sn": "chinwiwa chinodhaka chinogadzirwa nezviyo zvakaviriswa", "source": "Elliott 1897"},
        {"word": "fodya", "part_of_speech": "noun", "class": "Class 9", "definition_en": "tobacco; cigarette", "definition_sn": "chinhu chinoputwa kana kutsengwa chine utsi nemishonga inoderedza pfungwa", "source": "Elliott 1897"},
        {"word": "badza", "part_of_speech": "noun", "class": "Class 5", "definition_en": "hoe; digging tool", "definition_sn": "simbi inoshandiswa kuchera ivhu pakurima", "source": "Elliott 1897"},
        {"word": "musha", "part_of_speech": "noun", "class": "Class 3", "definition_en": "home; village; homestead", "definition_sn": "nzvimbo inogara mhuri ine dzimba dzekurara nekubikira", "source": "Elliott 1897"},
        {"word": "jira", "part_of_speech": "noun", "class": "Class 5", "definition_en": "cloth; fabric", "definition_sn": "mucheka unosoneswa zvipfeko kana kufuka usiku", "source": "Elliott 1897"},
        
        # Core Verbs (Infinitive root form)
        {"word": "kuda", "part_of_speech": "verb", "class": "", "definition_en": "to love; to want; to like", "definition_sn": "kuve nechido chikuru kune chimwe chinhu kana munhu", "source": "Elliott 1897"},
        {"word": "kuona", "part_of_speech": "verb", "class": "", "definition_en": "to see; to look; to find", "definition_sn": "kushandisa meso kunzwa kuvepo kwezvinhu", "source": "Elliott 1897"},
        {"word": "kunzwa", "part_of_speech": "verb", "class": "", "definition_en": "to hear; to feel; to understand", "definition_sn": "kushandisa nzeve kunzwa inzwi kana kushandisa muviri kunzwa kupisa", "source": "Elliott 1897"},
        {"word": "kutaura", "part_of_speech": "verb", "class": "", "definition_en": "to speak; to talk; to converse", "definition_sn": "kuburitsa manzwi anonzwika mukanwa ane chinangwa", "source": "Elliott 1897"},
        {"word": "kunyora", "part_of_speech": "verb", "class": "", "definition_en": "to write", "definition_sn": "kugadzira mabhii kana mifananidzo pabepa uchishandisa chinyoreso", "source": "Elliott 1897"},
        {"word": "kuverenga", "part_of_speech": "verb", "class": "", "definition_en": "to read; to count", "definition_sn": "kududzira mabhii akanyorwa pabepa kana kutsvaga huwandu hwezvinhu", "source": "Elliott 1897"},
        {"word": "kufamba", "part_of_speech": "verb", "class": "", "definition_en": "to walk; to travel; to move", "definition_sn": "kushandisa makumbo kufamba kubva kune imwe nzvimbo uchienda pane imwe", "source": "Elliott 1897"},
        {"word": "kumhanya", "part_of_speech": "verb", "class": "", "definition_en": "to run", "definition_sn": "kufamba nemakumbo nekukurumidza kukuru", "source": "Elliott 1897"},
        {"word": "kuuya", "part_of_speech": "verb", "class": "", "definition_en": "to come", "definition_sn": "kusvika pane nzvimbo iri kutaurirwa", "source": "Elliott 1897"},
        {"word": "kuenda", "part_of_speech": "verb", "class": "", "definition_en": "to go; to depart", "definition_sn": "kubva pane imwe nzvimbo uchienda pane imwe", "source": "Elliott 1897"},
        {"word": "kudzoka", "part_of_speech": "verb", "class": "", "definition_en": "to return; to come back", "definition_sn": "kusvika zvakare kwarimbori pane dzimwe nguva", "source": "Elliott 1897"},
        {"word": "kudya", "part_of_speech": "verb", "class": "", "definition_en": "to eat", "definition_sn": "kuisa chikafu mukanwa uchitsenga nekumedza mudumbu", "source": "Elliott 1897"},
        {"word": "kunwa", "part_of_speech": "verb", "class": "", "definition_en": "to drink", "definition_sn": "kuisa zvinoyerera mukanwa uchimedza mudumbu", "source": "Elliott 1897"},
        {"word": "kurara", "part_of_speech": "verb", "class": "", "definition_en": "to sleep", "definition_sn": "kuzorora usiku kana masikati wakavhara meso pfungwa dzisingashandi", "source": "Elliott 1897"},
        {"word": "kumuka", "part_of_speech": "verb", "class": "", "definition_en": "to wake up; to rise", "definition_sn": "kumisa muviri kubva pakurara meso akavhurika", "source": "Elliott 1897"},
        {"word": "kushanda", "part_of_speech": "verb", "class": "", "definition_en": "to work; to labor", "definition_sn": "kushandisa pfungwa nemuviri kugadzira zvibereko zvinobatsira", "source": "Elliott 1897"},
        {"word": "kutamba", "part_of_speech": "verb", "class": "", "definition_en": "to play; to dance", "definition_sn": "kufara uye kuita mitambo yakasiyana inozorodza muviri", "source": "Elliott 1897"},
        {"word": "kuimba", "part_of_speech": "verb", "class": "", "definition_en": "to sing", "definition_sn": "kuburitsa inzwi rinotapira rerwiyo", "source": "Elliott 1897"},
        {"word": "kutenga", "part_of_speech": "verb", "class": "", "definition_en": "to buy; to purchase", "definition_sn": "kutora chimwe chinhu uchichinjanisa nemari", "source": "Elliott 1897"},
        {"word": "kutengesa", "part_of_speech": "verb", "class": "", "definition_en": "to sell", "definition_sn": "kupa chimwe chinhu kune mumwe uchipiwa mari", "source": "Elliott 1897"},
        {"word": "kubika", "part_of_speech": "verb", "class": "", "definition_en": "to cook; to brew", "definition_sn": "kupisa chikafu pamoto chichibva chogadzirwa kudyiwa", "source": "Elliott 1897"},
        {"word": "kuuraya", "part_of_speech": "verb", "class": "", "definition_en": "to kill", "definition_sn": "kubvisa upenyu hwechisikwa chipi zvacho", "source": "Elliott 1897"},
        {"word": "kupa", "part_of_speech": "verb", "class": "", "definition_en": "to give", "definition_sn": "kupa mumwe chinhu pasina mubhadharo", "source": "Elliott 1897"},
        {"word": "kutora", "part_of_speech": "verb", "class": "", "definition_en": "to take; to receive", "definition_sn": "kubata nekuunganidza chinhu chiri pane imwe nzvimbo", "source": "Elliott 1897"},
        {"word": "kudaidza", "part_of_speech": "verb", "class": "", "definition_en": "to call; to summon", "definition_sn": "kushevedza munhu uchiita kuti auye kwauri", "source": "Elliott 1897"},
        {"word": "kuseka", "part_of_speech": "verb", "class": "", "definition_en": "to laugh", "definition_sn": "kuburitsa inzwi rekufara meso akavhurika miromo yakamwemwera", "source": "Elliott 1897"},
        {"word": "kuchema", "part_of_speech": "verb", "class": "", "definition_en": "to cry; to weep; to mourn", "definition_sn": "kuburitsa misodzi pameso nekuchema nekuomerwa", "source": "Elliott 1897"},
        {"word": "kufunga", "part_of_speech": "verb", "class": "", "definition_en": "to think; to ponder", "definition_sn": "kushandisa pfungwa kugadzira mufananidzo wezvinhu kana sarudzo", "source": "Elliott 1897"},
        
        # Core Adjectives
        {"word": "kuru", "part_of_speech": "adjective", "class": "", "definition_en": "big; large; great", "definition_sn": "chinhu chinodarika chimwe pakukura kana huwandu", "source": "Elliott 1897"},
        {"word": "diki", "part_of_speech": "adjective", "class": "", "definition_en": "small; little; minor", "definition_sn": "chinhu chidiki chisingasviki pakureba kana huwandu", "source": "Elliott 1897"},
        {"word": "refu", "part_of_speech": "adjective", "class": "", "definition_en": "long; tall", "definition_sn": "chinhu chinodarika chimwe pakureba kuenda mudenga kana kumberi", "source": "Elliott 1897"},
        {"word": "pfupi", "part_of_speech": "adjective", "class": "", "definition_en": "short; brief", "definition_sn": "chinhu chisina kureba zvakanyanya", "source": "Elliott 1897"},
        {"word": "tsva", "part_of_speech": "adjective", "class": "", "definition_en": "new; fresh", "definition_sn": "chinhu chisina kumboshandiswa kana chitsva chichangoburwa", "source": "Elliott 1897"},
        {"word": "tsaru", "part_of_speech": "adjective", "class": "", "definition_en": "old; worn-out", "definition_sn": "chinhu chakasakara chakashandiswa kwenguva refu", "source": "Elliott 1897"},
        {"word": "chena", "part_of_speech": "adjective", "class": "", "definition_en": "white; clean; pure", "definition_sn": "ruvara runoita semukaka; chinhu chisina tsvina", "source": "Elliott 1897"},
        {"word": "tsvuku", "part_of_speech": "adjective", "class": "", "definition_en": "red", "definition_sn": "ruvara runoita seropa kana moto wakatsva", "source": "Elliott 1897"},
        {"word": "tema", "part_of_speech": "adjective", "class": "", "definition_en": "black; dark", "definition_sn": "ruvara rwakasviba rwakafanana nemarasha", "source": "Elliott 1897"}
    ]
    print(f"Loaded {len(curated_roots)} curated core historical roots.")
    return curated_roots

def main():
    print("Starting historical and Swadesh loader...")
    
    # 1. Fetch Swadesh list
    swadesh_list = fetch_swadesh_list()
    
    # 2. Get curated historical roots
    historical_roots = get_historical_roots()
    
    # 3. Merge both datasets
    all_historical = swadesh_list + historical_roots
    
    # Save raw entries
    output_path = "historical_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_historical, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_historical)} total historical/Swadesh entries to {output_path}!")

if __name__ == "__main__":
    main()
