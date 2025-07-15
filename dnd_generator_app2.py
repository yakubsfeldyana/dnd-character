import streamlit as st
from openai import OpenAI
import random
import json

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Static fallback name generator
def generate_name():
    first_names = ["Arin", "Belra", "Cedric", "Dora", "Elryn", "Faelar", "Gorin", "Hilda", "Isen", "Jora"]
    last_names = ["Stoneheart", "Ravenshadow", "Ironfist", "Moonwhisper", "Stormblade", "Duskbane", "Lightbringer"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# AI name generation by race/class
def generate_race_name_ai(race, char_class, gender):
    race_styles = {
        "Elf": "elegant, melodic Elvish names (e.g., Elrandor, Lirael)",
        "Dwarf": "strong, gritty Dwarven names (e.g., Brundir, Thrain)",
        "Halfling": "friendly, simple Halfling names (e.g., Milo, Petunia Greenbottle)",
        "Tiefling": "mysterious, dark Tiefling names (e.g., Azazel, Nyx)",
        "Dragonborn": "powerful, draconic names (e.g., Vytharax, Zyrmorn)",
        "Human": "classic medieval fantasy names (e.g., Cedric, Alina)"
    }
    style = race_styles.get(race, "fantasy-themed names")
    prompt = (
        f"Generate a unique first and last name for a {gender.lower()} "
        f"{race} {char_class} in Dungeons & Dragons. "
        f"Use {style}. Only return the name."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_tokens=20,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(AI Name Error: {e})"

# AI backstory
def generate_backstory(name, race, char_class, background, alignment, pronoun):
    prompt = (
        f"Write a short Dungeons & Dragons character backstory.\n"
        f"Name: {name}\n"
        f"Race: {race}\n"
        f"Class: {char_class}\n"
        f"Background: {background}\n"
        f"Alignment: {alignment}\n"
        f"Use these pronouns: {pronoun['subj']}/{pronoun['obj']}/{pronoun['poss']}\n"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(Error generating backstory: {e})"

# D&D stat roller
def roll_stat():
    rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)
    return sum(rolls[:3])

# Main UI
st.title("🧙 D&D Character Generator")
st.markdown(
    """
    <style>
    /* Main app background */
    [data-testid="stAppViewContainer"] > .main {
        background-color: #f5f0dc;  /* ancient scroll look*/
        color: white;
    }

    /* Optional: Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #1a102b;
    }

    /* Optional: Transparent top bar */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: rgba(0, 0, 0, 0);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Manual pickers FIRST
races = ["Dragonborn", "Dwarf", "Elf", "Gnome", "Half-Elf", "Half-Orc", "Halfling", "Human", "Tiefling"]
classes = ["Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"]
backgrounds = ["Noble", "Soldier", "Criminal", "Sage", "Entertainer", "Hermit", "Acolyte", "Folk Hero"]
alignments = ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"]

race = st.selectbox("🧬 Pick a Race", races)
char_class = st.selectbox("🛡️ Pick a Class", classes)
background = st.selectbox("📜 Pick a Background", backgrounds)
alignment = st.selectbox("⚖️ Pick an Alignment", alignments)
#added gender selection
gender = st.radio("🧑‍🤝‍🧑 Select Gender", ["Male", "Female", "Non-binary"], index=0)
#added pronouns
pronouns = {
    "Male": {"subj": "He", "obj": "him", "poss": "his"},
    "Female": {"subj": "She", "obj": "her", "poss": "her"},
    "Non-binary": {"subj": "They", "obj": "them", "poss": "their"},
}
selected_pronoun = pronouns[gender]


# Choose name generation method
st.markdown("### 🧙 Choose Character Name")
name_option = st.radio("How should the name be generated?", [
    "Random from list",
    "AI-generated (race-specific)",
    "Enter custom name"
], index=0)

if name_option == "Random from list":
    name = generate_name()
elif name_option == "AI-generated (race-specific)":
    if "ai_name" not in st.session_state or st.button("🔁 Regenerate Name"):
        with st.spinner("Summoning a race-specific name..."):
            st.session_state.ai_name = generate_race_name_ai(race, char_class, gender)
    name = st.session_state.ai_name
    st.success(f"✨ AI Name: {name}")

# Generate character button
if st.button("🎲 Create Character"):
    # Build character
    stats = {
        "Strength": roll_stat(),
        "Dexterity": roll_stat(),
        "Constitution": roll_stat(),
        "Intelligence": roll_stat(),
        "Wisdom": roll_stat(),
        "Charisma": roll_stat(),
    }
    character = {
        "Name": name,
        "Race": race,
        "Class": char_class,
        "Background": background,
        "Alignment": alignment,
        "Stats": stats
    }

    # Backstory
    with st.spinner("🪄 Writing your backstory..."):
        backstory = generate_backstory(name, race, char_class, background, alignment, selected_pronoun)
    character["Backstory"] = backstory

    # Show info
    st.subheader(f"🧝 Name: {character['Name']}")
    st.text(f"🏹 Race: {character['Race']}")
    st.text(f"⚔️ Class: {character['Class']}")
    st.text(f"📜 Background: {character['Background']}")
    st.text(f"🧭 Alignment: {character['Alignment']}")

    st.markdown("### 📝 Backstory")
    st.write(backstory)

    st.markdown("### 📊 Ability Scores")
    for stat, value in character["Stats"].items():
        st.text(f"{stat}: {value}")

    # Downloadable .txt
    txt = f"""
D&D Character Sheet
--------------------
Name: {character['Name']}
Race: {character['Race']}
Class: {character['Class']}
Background: {character['Background']}
Alignment: {character['Alignment']}

Ability Scores:
"""
    for stat, score in stats.items():
        txt += f"{stat}: {score}\n"
    txt += f"\nBackstory:\n{backstory}"

    st.download_button("📄 Download .txt", txt, f"{name.replace(' ', '_')}_sheet.txt", "text/plain")
