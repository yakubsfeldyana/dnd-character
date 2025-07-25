import streamlit as st
from openai import OpenAI
import random

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# --- Utility Functions ---
def generate_name():
    first_names = ["Arin", "Belra", "Cedric", "Dora", "Elryn", "Faelar", "Gorin", "Hilda", "Isen", "Jora"]
    last_names = ["Stoneheart", "Ravenshadow", "Ironfist", "Moonwhisper", "Stormblade", "Duskbane", "Lightbringer"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def roll_stat():
    rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)
    return sum(rolls[:3])

def generate_race_name_ai(race, char_class, gender):
    race_styles = {
    "Dragonborn": "powerful, draconic names, often harsh and guttural",
    "Dwarf": "gritty, earthy Dwarven names that sound sturdy and traditional",
    "Elf": "elegant, melodic Elvish names with lyrical qualities",
    "Gnome": "quirky, playful names with a touch of cleverness or whimsy",
    "Half-Elf": "a blend of Elvish elegance and Human familiarity",
    "Half-Orc": "rough, strong-sounding names with Orcish grit and Human influence",
    "Halfling": "cheerful, simple names with a rural, friendly tone",
    "Human": "classic medieval fantasy names with cultural variety",
    "Tiefling": "mysterious, dark names, often with infernal or celestial flair"
    }
    style = race_styles.get(race, "fantasy names")
    prompt = (
        f"Generate a unique first and last name for a {gender.lower()} {race} {char_class} "
        f"in D&D. Use {style}. Only return the name."
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

def generate_backstory(name, race, char_class, background, alignment, pronoun):
    prompt = (
        f"Write a short D&D backstory for this character:\n"
        f"Name: {name}\nRace: {race}\nClass: {char_class}\n"
        f"Background: {background}\nAlignment: {alignment}\n"
        f"Pronouns: {pronoun['subj']}/{pronoun['obj']}/{pronoun['poss']}"
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
        return f"(Backstory Error: {e})"

# --- UI ---
st.set_page_config("🧙 D&D Generator", layout="centered")
st.title("🧙 D&D Character Generator")



races = ["Dragonborn", "Dwarf", "Elf", "Gnome", "Half-Elf", "Half-Orc", 
    "Halfling", "Human", "Tiefling"]
classes = ["Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard", "Artificer", "Blood Hunter"]
backgrounds = [ "Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero", 
    "Guild Artisan", "Hermit", "Noble", "Outlander", "Sage", 
    "Sailor", "Soldier", "Urchin"]
alignments = ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"]
#level = st.number_input("📈 Choose Character Level", min_value=1, max_value=20, value=1)
level = st.slider("📈 Choose Character Level", 1, 20, 1)
genders = ["Male", "Female", "Non-binary"]
pronouns_map = {
    "Male": {"subj": "He", "obj": "him", "poss": "his"},
    "Female": {"subj": "She", "obj": "her", "poss": "her"},
    "Non-binary": {"subj": "They", "obj": "them", "poss": "their"},
}

# --- User Inputs ---
race = st.selectbox("🧬 Pick Race", races)
char_class = st.selectbox("🛡️ Pick Class", classes)
background = st.selectbox("📜 Pick Background", backgrounds)
alignment = st.selectbox("⚖️ Pick Alignment", alignments)
gender = st.radio("🧑‍🤝‍🧑 Pick Gender", genders)
pronoun = pronouns_map[gender]

# Stat method
stat_input_method = st.radio(
    "🎯 Set Ability Scores",
    [
        "🎲 Roll randomly",
        "✍️ Enter manually",
        "🎚️ Customize with sliders",
        "🤖 AI-Optimized Point Buy"
    ],
    help="🎲 Random rolls: chance-based.\n✍️ Manual: full control.\n🎚️ Sliders: visual adjustment.\n🤖 AI-Optimized: smart stat assignment based on class."
)

# Name method
name_option = st.radio("🔮 Choose Name", ["Random from list", "AI-generated", "Enter manually"])

# Show manual name input if selected
manual_name = ""
if name_option == "Enter manually":
    manual_name = st.text_input("Enter character name", placeholder="Your character's name")

# --- Get Stats ---
stats = {}
if stat_input_method == "Roll randomly":
    for stat in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
        stats[stat] = roll_stat()
elif stat_input_method == "Enter manually":
    for stat in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
        stats[stat] = st.number_input(
            f"Enter {stat}", min_value=1, max_value=20, value=10, key=f"num_{stat}"
        )
elif stat_input_method == "Customize with sliders":
    for stat in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
        stats[stat] = st.slider(
            f"{stat}", min_value=1, max_value=20, value=10, key=f"slider_{stat}"
        )

elif stat_input_method == "AI-Optimized Point Buy":
    # Define priorities by class
    class_priority = {
        "Barbarian": ["Strength", "Constitution"],
        "Bard": ["Charisma", "Dexterity"],
        "Cleric": ["Wisdom", "Constitution"],
        "Druid": ["Wisdom", "Intelligence"],
        "Fighter": ["Strength", "Dexterity"],
        "Monk": ["Dexterity", "Wisdom"],
        "Paladin": ["Charisma", "Strength"],
        "Ranger": ["Dexterity", "Wisdom"],
        "Rogue": ["Dexterity", "Intelligence"],
        "Sorcerer": ["Charisma", "Constitution"],
        "Warlock": ["Charisma", "Wisdom"],
        "Wizard": ["Intelligence", "Dexterity"],
        "Artificer": ["Intelligence", "Constitution"],
        "Blood Hunter": ["Strength", "Intelligence"],
    }

    # Basic point buy rules
    point_cost = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
    total_points = 27
    all_stats = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    
    # Default to 8
    stats = {stat: 8 for stat in all_stats}
    
    # Get class priorities
    priorities = class_priority.get(char_class, [])
    
    # Assign points to top 2 stats
    allocated = 0
    for stat in priorities:
        stats[stat] = 15
        allocated += point_cost[15]

    # Fill in others with 10 if points allow
    for stat in all_stats:
        if stat in priorities:
            continue
        if allocated + point_cost[10] <= total_points:
            stats[stat] = 10
            allocated += point_cost[10]

    # Fine-tune: drop to 9 or 8 if points exceeded
    for stat in all_stats:
        if allocated > total_points:
            if stats[stat] > 8:
                allocated -= (point_cost[stats[stat]] - point_cost[8])
                stats[stat] = 8

    

# Button
if st.button("🎲 Create Character"):
    # --- Generate Name ---
    if name_option == "Random from list":
        name = generate_name()
    elif name_option == "AI-generated":
        with st.spinner("Summoning name..."):
            name = generate_race_name_ai(race, char_class, gender)
    else:
        name = manual_name if manual_name else "Unnamed Character"
    
    # --- Generate Backstory ---
    with st.spinner("Writing backstory..."):
        backstory = generate_backstory(name, race, char_class, background, alignment, pronoun)

    # --- Output ---
    st.subheader(f"🧝 {name}")
    st.write(f"**Level**: {level} | **Race**: {race} | **Class**: {char_class} | **Background**: {background} | **Alignment**: {alignment}")
    
    st.markdown("### 📜 Backstory")
    st.write(backstory)

    st.markdown("### 💪 Stats")
    for stat, val in stats.items():
        st.write(f"**{stat}**: {val}")
    
    # 📄 Prepare .txt file content
    txt = f"""D&D Character Sheet (PHB Only)
--------------------
Name: {name}
Race: {race}
Class: {char_class}
Background: {background}
Alignment: {alignment}
Level: {level}
Ability Scores:
"""

    for stat, score in stats.items():
        txt += f"    {stat}: {score}\n"

    txt += f"\nBackstory:\n{backstory}\n"
    txt += "\n\nNote: This character was created using only options from the official Player’s Handbook (PHB).\n"


    st.download_button(
    label="📄 Download Character Sheet (.txt)",
    data=txt,
    file_name=f"{name.replace(' ', '_')}_sheet.txt",
    mime="text/plain"
    )
