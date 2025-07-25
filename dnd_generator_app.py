import os
import random
import streamlit as st
from openai import OpenAI

# -----------------------------
# Config & OpenAI
# -----------------------------
st.set_page_config("🧙 D&D Generator", layout="centered")

# Load API key from Streamlit secrets or environment variable
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
AI_ENABLED = bool(OPENAI_API_KEY)

client = OpenAI(api_key=OPENAI_API_KEY) if AI_ENABLED else None

# -----------------------------
# Constants & helpers
# -----------------------------
ABILITIES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]

# PHB-style racial ASIs (simplified, no subraces)
RACE_ASI = {
    "Dragonborn": {"Strength": 2, "Charisma": 1},
    "Dwarf": {"Constitution": 2},
    "Elf": {"Dexterity": 2},
    "Gnome": {"Intelligence": 2},
    "Half-Elf": {"Charisma": 2},  # +1 to two other abilities handled separately
    "Half-Orc": {"Strength": 2, "Constitution": 1},
    "Halfling": {"Dexterity": 2},
    "Human": "ALL_PLUS_ONE",       # +1 to every ability
    "Tiefling": {"Charisma": 2, "Intelligence": 1},
}

def apply_racial_asi(stats, race, half_elf_extras=None):
    """Return a *new* dict with PHB racial ASIs applied."""
    out = stats.copy()
    bonus = RACE_ASI.get(race)

    if bonus is None:
        return out

    if bonus == "ALL_PLUS_ONE":
        for a in ABILITIES:
            out[a] += 1
        return out

    # fixed bonuses first
    for k, v in bonus.items():
        out[k] = out.get(k, 0) + v

    # Half-Elf: +2 CHA already in mapping, add +1 to two others
    if race == "Half-Elf":
        if not half_elf_extras or len(half_elf_extras) != 2:
            half_elf_extras = ["Dexterity", "Constitution"]  # sensible default
        for a in half_elf_extras:
            out[a] = out.get(a, 0) + 1

    return out

def generate_name():
    first_names = ["Arin", "Belra", "Cedric", "Dora", "Elryn", "Faelar", "Gorin", "Hilda", "Isen", "Jora"]
    last_names = ["Stoneheart", "Ravenshadow", "Ironfist", "Moonwhisper", "Stormblade", "Duskbane", "Lightbringer"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def roll_stat():
    rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)
    return sum(rolls[:3])

def generate_race_name_ai(race, char_class, gender):
    # Fallback if no key
    if not AI_ENABLED:
        return generate_name()

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
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_tokens=20,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"(AI Name Error: {e})"

def generate_backstory(name, race, char_class, background, alignment, pronoun):
    # Fallback if no key
    if not AI_ENABLED:
        return (
            f"{name} is a {alignment.lower()} {race} {char_class} who grew up as a "
            f"{background.lower()}. {pronoun['subj']} seeks adventure to prove "
            f"{pronoun['poss']} worth to the world."
        )

    prompt = (
        f"Write a short D&D backstory for this character:\n"
        f"Name: {name}\nRace: {race}\nClass: {char_class}\n"
        f"Background: {background}\nAlignment: {alignment}\n"
        f"Pronouns: {pronoun['subj']}/{pronoun['obj']}/{pronoun['poss']}"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"(Backstory Error: {e})"


# -----------------------------
# UI – static data
# -----------------------------
st.title("🧙 D&D Character Generator")

if not AI_ENABLED:
    st.info("⚠️ No OPENAI_API_KEY found. AI name & backstory will use simple fallbacks.")

races = ["Dragonborn", "Dwarf", "Elf", "Gnome", "Half-Elf", "Half-Orc", "Halfling", "Human", "Tiefling"]
classes = ["Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue",
           "Sorcerer", "Warlock", "Wizard", "Artificer", "Blood Hunter"]
backgrounds = ["Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero",
               "Guild Artisan", "Hermit", "Noble", "Outlander", "Sage",
               "Sailor", "Soldier", "Urchin"]
alignments = ["Lawful Good", "Neutral Good", "Chaotic Good",
              "Lawful Neutral", "True Neutral", "Chaotic Neutral",
              "Lawful Evil", "Neutral Evil", "Chaotic Evil"]

# Radio labels (constants so string compares never break)
ROLL     = "🎲 Roll randomly"
MANUAL   = "✍️ Enter manually"
SLIDERS  = "🎚️ Customize with sliders"
POINTBUY = "🤖 AI-Optimized Point Buy"

# -----------------------------
# User inputs
# -----------------------------
level = st.slider("📈 Choose Character Level", 1, 20, 1)

genders = ["Male", "Female", "Non-binary"]
pronouns_map = {
    "Male": {"subj": "He", "obj": "him", "poss": "his"},
    "Female": {"subj": "She", "obj": "her", "poss": "her"},
    "Non-binary": {"subj": "They", "obj": "them", "poss": "their"},
}

race = st.selectbox("🧬 Pick Race", races)
char_class = st.selectbox("🛡️ Pick Class", classes)
background = st.selectbox("📜 Pick Background", backgrounds)
alignment = st.selectbox("⚖️ Pick Alignment", alignments)
gender = st.radio("🧑‍🤝‍🧑 Pick Gender", genders)
pronoun = pronouns_map[gender]

# ---- Racial ASIs toggle ----
apply_racial = st.checkbox(
    "Apply PHB racial bonuses",
    value=True,
    help="Adds the PHB default racial bonuses to your final ability scores."
)

half_elf_extras = []
if apply_racial and race == "Half-Elf":
    st.caption("Half-Elf gets +2 CHA and +1 to two other abilities of your choice.")
    half_elf_extras = st.multiselect(
        "Pick two abilities for your Half-Elf +1 bonuses",
        ABILITIES,
        default=[],
        key="half_elf_extra_asis"
    )
    if len(half_elf_extras) > 2:
        st.warning("Pick only two. Extra ones will be ignored.")

stat_input_method = st.radio(
    "🎯 Set Ability Scores",
    [ROLL, MANUAL, SLIDERS, POINTBUY],
    help="🎲 Random rolls: chance-based.\n✍️ Manual: full control.\n🎚️ Sliders: visual adjustment.\n🤖 AI-Optimized: smart stat assignment based on class."
)

name_option = st.radio("🔮 Choose Name", ["Random from list", "AI-generated", "Enter manually"])

manual_name = ""
if name_option == "Enter manually":
    manual_name = st.text_input("Enter character name", placeholder="Your character's name")

# Render manual/sliders widgets NOW so they are visible pre-button
manual_or_slider_values = {}
if stat_input_method == MANUAL:
    st.markdown("### ✍️ Enter your ability scores")
    for stat in ABILITIES:
        manual_or_slider_values[stat] = st.number_input(
            f"Enter {stat}", min_value=1, max_value=20, value=10, key=f"manual_{stat}"
        )
elif stat_input_method == SLIDERS:
    st.markdown("### 🎚️ Adjust your ability scores")
    for stat in ABILITIES:
        manual_or_slider_values[stat] = st.slider(
            f"{stat}", min_value=1, max_value=20, value=10, key=f"slider_{stat}"
        )

# -----------------------------
# Create Character
# -----------------------------
if st.button("🎲 Create Character"):
    # -------- Ability scores (base) --------
    stats = {}

    if stat_input_method == ROLL:
        for stat in ABILITIES:
            stats[stat] = roll_stat()

    elif stat_input_method == MANUAL:
        stats = manual_or_slider_values.copy()

    elif stat_input_method == SLIDERS:
        stats = manual_or_slider_values.copy()

    elif stat_input_method == POINTBUY:
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

        point_cost   = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
        total_points = 27

        stats      = {s: 8 for s in ABILITIES}
        priorities = class_priority.get(char_class, [])
        allocated  = 0

        # Raise top 2 stats to 15
        for s in priorities:
            if allocated + point_cost[15] <= total_points:
                stats[s] = 15
                allocated += point_cost[15]

        # Try to raise the rest to 10
        for s in ABILITIES:
            if s in priorities:
                continue
            if allocated + point_cost[10] <= total_points:
                stats[s] = 10
                allocated += point_cost[10]

        # If overspent, drop back to 8
        for s in ABILITIES:
            if allocated > total_points and stats[s] > 8:
                allocated -= (point_cost[stats[s]] - point_cost[8])
                stats[s] = 8

        # Show point-buy remaining
        spent = sum(point_cost.get(val, 0) for val in stats.values())
        remaining = total_points - spent
        (st.success if remaining >= 0 else st.error)(
            f"🧮 Point-Buy spent: **{spent} / 27** — Remaining: **{remaining}**"
        )

    # Save pre-ASI numbers
    base_stats = stats.copy()

    # Apply racial ASIs
    final_stats = apply_racial_asi(base_stats, race, half_elf_extras) if apply_racial else base_stats

    # -------- Name --------
    if name_option == "Random from list":
        name = generate_name()
    elif name_option == "AI-generated":
        with st.spinner("Summoning name..."):
            name = generate_race_name_ai(race, char_class, gender)
    else:
        name = manual_name if manual_name else "Unnamed Character"

    # -------- Backstory --------
    with st.spinner("Writing backstory..."):
        backstory = generate_backstory(name, race, char_class, background, alignment, pronoun)

    # -------- Output --------
    label_base  = "Base ability scores (before lineage bonuses)"
    label_final = "Final ability scores (after lineage bonuses)"

    st.subheader(f"🧝 {name}")
    st.write(f"**Level**: {level} | **Race**: {race} | **Class**: {char_class} | **Background**: {background} | **Alignment**: {alignment}")

    st.markdown("### 💪 Ability Scores")
    if apply_racial:
        st.write(f"**{label_base}:**")
        for stat, val in base_stats.items():
            st.write(f"{stat}: {val}")

        st.write(f"**{label_final}:**")
        for stat, val in final_stats.items():
            st.write(f"{stat}: {val}")
    else:
        for stat, val in base_stats.items():
            st.write(f"{stat}: {val}")

    st.markdown("### 📜 Backstory")
    st.write(backstory)

    # -------- Download --------
    txt = f"""D&D Character Sheet (PHB Only)
--------------------
Name: {name}
Race: {race}
Class: {char_class}
Background: {background}
Alignment: {alignment}
Level: {level}
Ability Scores (base – before lineage bonuses):
"""
    for stat, score in base_stats.items():
        txt += f"    {stat}: {score}\n"

    if apply_racial:
        txt += "\nAbility Scores (final – after lineage bonuses):\n"
        for stat, score in final_stats.items():
            txt += f"    {stat}: {score}\n"

    txt += f"\nBackstory:\n{backstory}\n"
    txt += "\nNote: This character was created using only options from the official Player’s Handbook (PHB).\n"

    st.download_button(
        label="📄 Download Character Sheet (.txt)",
        data=txt,
        file_name=f"{name.replace(' ', '_')}_sheet.txt",
        mime="text/plain"
    )
