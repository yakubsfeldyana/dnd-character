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
        "Elf": "elegant, melodic Elvish names",
        "Dwarf": "gritty Dwarven names",
        "Human": "classic fantasy names",
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

races = ["Elf", "Dwarf", "Human", "Halfling", "Tiefling"]
classes = ["Wizard", "Fighter", "Rogue", "Cleric", "Bard"]
backgrounds = ["Sage", "Soldier", "Criminal", "Noble"]
alignments = ["Lawful Good", "Chaotic Good", "Neutral", "Lawful Evil", "Chaotic Evil"]
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
stat_input_method = st.radio("🎯 Set Ability Scores", ["Roll randomly", "Enter manually", "Customize with sliders"])

# Name method
name_option = st.radio("🔮 Choose Name", ["Random from list", "AI-generated", "Enter manually"])

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
else:
    for stat in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
        stats[stat] = st.slider(
            f"{stat}", min_value=1, max_value=20, value=10, key=f"slider_{stat}"
        )
    

# Button
if st.button("🎲 Create Character"):
    # --- Generate Name ---
    if name_option == "Random from list":
        name = generate_name()
    elif name_option == "AI-generated":
        with st.spinner("Summoning name..."):
            name = generate_race_name_ai(race, char_class, gender)
    else:
        name = st.text_input("Enter character name", "Your Name")
    
    # --- Generate Backstory ---
    with st.spinner("Writing backstory..."):
        backstory = generate_backstory(name, race, char_class, background, alignment, pronoun)

    # --- Output ---
    st.subheader(f"🧝 {name}")
    st.write(f"**Race**: {race} | **Class**: {char_class} | **Background**: {background} | **Alignment**: {alignment}")
    
    st.markdown("### 📜 Backstory")
    st.write(backstory)

    st.markdown("### 💪 Stats")
    for stat, val in stats.items():
        st.write(f"**{stat}**: {val}")
    
    # 📄 Prepare .txt file content
    txt = f"""D&D Character Sheet
--------------------
Name: {name}
Race: {race}
Class: {char_class}
Background: {background}
Alignment: {alignment}

Ability Scores:
"""

    for stat, score in stats.items():
        txt += f"    {stat}: {score}\n"

    txt += f"\nBackstory:\n{backstory}\n"

    # 📥 Download button
    st.download_button(
        label="📄 Download Character Sheet (.txt)",
        data=txt,
        file_name=f"{name.replace(' ', '_')}_sheet.txt",
        mime="text/plain"
    )
