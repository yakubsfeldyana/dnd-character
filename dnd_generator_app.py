import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

import random
import json


# Fantasy name parts
first_names = ["Arin", "Belra", "Cedric", "Dora", "Elryn", "Faelar", "Gorin", "Hilda", "Isen", "Jora"]
last_names = ["Stoneheart", "Ravenshadow", "Ironfist", "Moonwhisper", "Stormblade", "Duskbane", "Lightbringer"]

# D&D options
races = ["Dragonborn", "Dwarf", "Elf", "Gnome", "Half-Elf", "Half-Orc", "Halfling", "Human", "Tiefling", "Aarakocra", "Genasi", "Goliath", "Aasimar", "Bugbear", "Firbolg", "Goblin", "Hobgoblin", "Kenku", "Kobold", "Lizardfolk", "Orc", "Tabaxi", "Triton", "Yuan-Ti Pureblood", "Tortle", "Gith", "Changeling", "Kalashtar", "Shifter", "Warforged", "Centaur", "Loxodon", "Minotaur", "Simic Hybrid", "Vedalken", "Locathah", "Grung"]
classes = ["Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard", "Blood Hunter"]
backgrounds = ["Noble", "Soldier", "Criminal", "Sage", "Entertainer", "Hermit", "Acolyte", "Criminal", "Folk Hero", "Noble", "Sage", "Soldier", "Charlatan", "Entertainer", "Guild Artisan", "Hermit", "Outlander", "Sailor", "Anthropologist", "Archaeologist", "City Watch", "Clan Crafter", "Cloistered Scholar", "Courtier", "Faction Agent", "Far Traveler", "Inheritor", "Knight of the Order", "Mercenary Veteran", "Urban Bounty Hunter", "Uthgardt Tribe Member", "Waterdhavian Noble", "Acquisitions Incorporated", "Astral Drifter", "Celebrity Adventurer's Scion", "Failed Merchant", "Gambler", "Plaintiff", "Rival Intern", "Black Fist Double Agent", "Dragon Casualty", "Earthspur Miner", "Hillsfar Merchant", "Hillsfar Smuggler", "Mulmaster Aristocrat", "Phlan Insurgent", "Phlan Refugee", "Stojanow Prisoner", "Ticklebelly Nomad", "Trades Sheriff", "Caravan Specialist", "Earthspur Miner", "Harborfolk", "Phlan Refugee", "Giant Foundling", "Ruined", "Witchlight Hand"]
alignments = ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"]



# def generate_backstory(name, race, char_class, background, alignment):
#     templates = [
#         f"{name} was born into a {background.lower()} family of {race.lower()}s, but always dreamed of becoming a {char_class.lower()}.",
#         f"As a {race.lower()}, {name} grew up facing prejudice, shaping their strong sense of {alignment.lower()} justice.",
#         f"{name} discovered ancient powers while exploring the ruins near their hometown, pushing them toward the path of a {char_class.lower()}.",
#         f"Trained as a {background.lower()}, {name} left their {race.lower()} clan behind to follow their calling as a {char_class.lower()}.",
#         f"{name}'s life changed forever after a tragic event, forging their destiny as a {alignment.lower()} {char_class.lower()}."
#     ]
#     return random.choice(templates) 



def generate_backstory(name, race, char_class, background, alignment):
    prompt = (
        f"Write a short Dungeons & Dragons character backstory.\n"
        f"Name: {name}\n"
        f"Race: {race}\n"
        f"Class: {char_class}\n"
        f"Background: {background}\n"
        f"Alignment: {alignment}\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(Error generating backstory: {e})"




# Stat roller
def roll_stat():
    rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)
    return sum(rolls[:3])

# Name generator
def generate_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# Generate character with custom or random inputs
def generate_character(name, race, char_class, background, alignment):
    return {
        "Name": name,
        "Race": race,
        "Class": char_class,
        "Background": background,
        "Alignment": alignment,
        "Stats": {
            "Strength": roll_stat(),
            "Dexterity": roll_stat(),
            "Constitution": roll_stat(),
            "Intelligence": roll_stat(),
            "Wisdom": roll_stat(),
            "Charisma": roll_stat(),
        }
    }

# --- Streamlit UI ---
st.title("🧙 D&D Character Generator")

# Custom or random name
use_random_name = st.checkbox("Use random name", value=True)
if use_random_name:
    name = generate_name()
else:
    name = st.text_input("Enter character name", "Your Name")

# Manual pickers
race = st.selectbox("Pick a Race", races)
char_class = st.selectbox("Pick a Class", classes)
background = st.selectbox("Pick a Background", backgrounds)
alignment = st.selectbox("Pick an Alignment", alignments)

# Generate button
if st.button("🎲 Create Character"):
    character = generate_character(name, race, char_class, background, alignment)

    # Generate backstory early
    backstory = generate_backstory(name, race, char_class, background, alignment)
    character["Backstory"] = backstory

    # Show character info
    st.subheader(f"🧝 Name: {character['Name']}")
    st.text(f"🏹 Race: {character['Race']}")
    st.text(f"⚔️  Class: {character['Class']}")
    st.text(f"📜 Background: {character['Background']}")
    st.text(f"🧭 Alignment: {character['Alignment']}")

    st.markdown("### 📝 Backstory")
    st.write(backstory)

    st.markdown("### 📊 Ability Scores")
    for stat, score in character["Stats"].items():
        st.text(f"{stat}: {score}")


    # 🎉 Downloadable TXT
    txt_content = f"""
    D&D Character Sheet
    --------------------
    Name: {character['Name']}
    Race: {character['Race']}
    Class: {character['Class']}
    Background: {character['Background']}
    Alignment: {character['Alignment']}
    

    Ability Scores:
    """
    for stat, score in character["Stats"].items():
        txt_content += f"{stat}: {score}\n"
    # Add backstory after stats
    txt_content += f"\nBackstory:\n{backstory}"

    st.download_button(
        label="📄 Download Character Sheet (.txt)",
        data=txt_content,
        file_name=f"{character['Name'].replace(' ', '_')}_sheet.txt",
        mime="text/plain"
    )


    # 🎉 Downloadable JSON
    st.download_button(
        label="🧾 Download JSON File",
        data=json.dumps(character, indent=2),
        file_name=f"{character['Name'].replace(' ', '_')}_sheet.json",
        mime="application/json"
    )
