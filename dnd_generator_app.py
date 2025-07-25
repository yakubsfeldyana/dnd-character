import os
import random
import streamlit as st
from openai import OpenAI


import streamlit as st


st.markdown("""
<style>
/* Hide the hamburger menu (which contains the GitHub link) */
#MainMenu {visibility: hidden;}
/* Hide the footer "Made with Streamlit" */
footer {visibility: hidden;}
/* (Optional) hide the header */
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Config & OpenAI
# -----------------------------
st.set_page_config("🧙 D&D Generator", layout="centered")

# Load API key from Streamlit secrets or environment variable
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
AI_ENABLED = bool(OPENAI_API_KEY)

client = OpenAI(api_key=OPENAI_API_KEY) if AI_ENABLED else None

# ----------------- Streamlit session state -----------------
if "sheet" not in st.session_state:
    st.session_state.sheet = {}        # full character sheet lives here
if "asi_spent" not in st.session_state:
    st.session_state.asi_spent = 0     # ASIs the user has already applied

# -----------------------------
# Constants & helpers
# -----------------------------
ABILITIES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
# ---------- Ability‑Score‑Improvement (ASI) tables ----------
ASI_LEVELS = {
    "default": [4, 8, 12, 16, 19],
    "Fighter": [4, 6, 8, 12, 14, 16, 19],
    "Rogue":   [4, 8, 10, 12, 16, 19],
}

def asi_slots_available(cls: str, lvl: int) -> int:
    """Return how many ASI opportunities `cls` has earned up to `lvl`."""
    tbl = ASI_LEVELS.get(cls, ASI_LEVELS["default"])
    return sum(1 for x in tbl if x <= lvl)

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
        # Enforce exactly 2 choices
        half_elf_extras = half_elf_extras[:2]
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
POINTBUY = "🎯 Interactive Point Buy"

# -----------------------------
# User inputs
# -----------------------------
level = st.slider("📈 Choose Character Level", 1, 20, 1)

# Show ASI availability for selected class and level
selected_class = st.selectbox("🛡️ Pick Class", classes)
asi_available = asi_slots_available(selected_class, level)
if asi_available > 0:
    st.info(f"📈 At level {level}, your {selected_class} will have **{asi_available}** Ability Score Improvement(s) available.")
else:
    st.info(f"📈 At level {level}, your {selected_class} has no ASIs yet (first ASI typically at level 4).")

genders = ["Male", "Female", "Non-binary"]
pronouns_map = {
    "Male": {"subj": "He", "obj": "him", "poss": "his"},
    "Female": {"subj": "She", "obj": "her", "poss": "her"},
    "Non-binary": {"subj": "They", "obj": "them", "poss": "their"},
}

race = st.selectbox("🧬 Pick Race", races)
char_class = selected_class  # Use the class we already selected above
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
        [a for a in ABILITIES if a != "Charisma"],  # Exclude Charisma since it already gets +2
        default=[],
        max_selections=2,  # Enforce maximum of 2 selections
        key="half_elf_extra_asis"
    )

stat_input_method = st.radio(
    "🎯 Set Ability Scores",
    [ROLL, MANUAL, SLIDERS, POINTBUY],
    help="🎲 Random rolls: chance-based.\n✍️ Manual: full control.\n🎚️ Sliders: visual adjustment.\n🎯 Interactive Point Buy: real-time point allocation with 27 points."
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
elif stat_input_method == POINTBUY:
    st.markdown("### 🤖 Interactive Point Buy System")
    st.write("**Point Buy Rules:** Start with 8 in each ability. You have 27 points to spend.")
    
    # Initialize point buy values in session state if not exists
    if 'pointbuy_values' not in st.session_state:
        st.session_state.pointbuy_values = {stat: 8 for stat in ABILITIES}
    
    point_cost = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
    reverse_cost = {v: k for k, v in point_cost.items()}  # For finding valid values
    total_points = 27
    
    # Create sliders for each ability
    col1, col2 = st.columns(2)
    abilities_left = ABILITIES[:3]
    abilities_right = ABILITIES[3:]
    
    with col1:
        for stat in abilities_left:
            st.session_state.pointbuy_values[stat] = st.slider(
                f"{stat}", 
                min_value=8, 
                max_value=15, 
                value=st.session_state.pointbuy_values[stat],
                key=f"pointbuy_{stat}",
                help=f"Cost: {point_cost[st.session_state.pointbuy_values[stat]]} points"
            )
    
    with col2:
        for stat in abilities_right:
            st.session_state.pointbuy_values[stat] = st.slider(
                f"{stat}", 
                min_value=8, 
                max_value=15, 
                value=st.session_state.pointbuy_values[stat],
                key=f"pointbuy_{stat}",
                help=f"Cost: {point_cost[st.session_state.pointbuy_values[stat]]} points"
            )
    
    # Calculate and display points
    spent_points = sum(point_cost[val] for val in st.session_state.pointbuy_values.values())
    remaining_points = total_points - spent_points
    
    # Display point status
    if remaining_points > 0:
        st.success(f"✅ **Points Spent:** {spent_points}/27 | **Remaining:** {remaining_points}")
    elif remaining_points == 0:
        st.success(f"✅ **Perfect!** All 27 points spent: {spent_points}/27")
    else:
        st.error(f"❌ **Over Budget!** You've spent {spent_points}/27 points (over by {abs(remaining_points)})")
    
    # Show cost breakdown
    with st.expander("📊 Point Cost Breakdown"):
        for stat in ABILITIES:
            cost = point_cost[st.session_state.pointbuy_values[stat]]
            st.write(f"**{stat}:** {st.session_state.pointbuy_values[stat]} (costs {cost} points)")
    
    # Class recommendations
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
    
    if char_class in class_priority:
        recommended = class_priority[char_class]
        st.info(f"💡 **{char_class} Recommendation:** Prioritize {' and '.join(recommended)}")
    
    # Auto-optimize button
    if st.button("🎯 Auto-Optimize for Class"):
        priorities = class_priority.get(char_class, [])
        new_values = {s: 8 for s in ABILITIES}
        allocated = 0
        
        # Set priority stats to 15
        for stat in priorities:
            if allocated + point_cost[15] <= total_points:
                new_values[stat] = 15
                allocated += point_cost[15]
        
        # Distribute remaining points to other stats
        remaining_abilities = [s for s in ABILITIES if s not in priorities]
        for stat in remaining_abilities:
            cost_to_10 = point_cost[10] - point_cost[new_values[stat]]
            if allocated + cost_to_10 <= total_points:
                new_values[stat] = 10
                allocated += cost_to_10
        
        st.session_state.pointbuy_values = new_values
        st.rerun()

# -----------------------------
# Create Character
# -----------------------------
if st.button("🎲 Create Character"):
    # Reset ASI tracking when creating new character
    st.session_state.asi_spent = 0
    
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
        # Use the interactive point buy values
        stats = st.session_state.pointbuy_values.copy()
        
        # Validate point buy is within budget
        point_cost = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
        spent_points = sum(point_cost[val] for val in stats.values())
        if spent_points > 27:
            st.error(f"❌ Point buy exceeds 27 points ({spent_points}). Please adjust your scores.")
            st.stop()
        elif spent_points < 27:
            remaining = 27 - spent_points
            st.warning(f"⚠️ You have {remaining} unspent points. Consider using them to improve your character.")
        else:
            st.success("✅ Point buy allocation is perfect!")

    # Legacy AI-optimized point buy (kept for compatibility)
    elif stat_input_method == "🤖 AI-Optimized Point Buy":  # This shouldn't be reachable now
        # Legacy AI-optimized point buy (kept for compatibility)
        # This case shouldn't be reachable now with the new radio button options
        stats = {s: 10 for s in ABILITIES}  # Fallback

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

    # Store character in session state
    st.session_state.sheet = {
        "name": name,
        "race": race,
        "class": char_class,
        "background": background,
        "alignment": alignment,
        "level": level,
        "base_stats": base_stats,
        "final_stats": final_stats.copy(),  # Make a copy to allow modifications
        "backstory": backstory,
        "apply_racial": apply_racial
    }

# ================= Character Sheet Display =================
char = st.session_state.sheet
if char:
    # -------- Character Header --------
    st.subheader(f"🧝 {char['name']}")
    st.write(f"**Level**: {char['level']} | **Race**: {char['race']} | **Class**: {char['class']} | **Background**: {char['background']} | **Alignment**: {char['alignment']}")

    # -------- Ability Scores --------
    st.markdown("### 💪 Ability Scores")
    label_base  = "Base ability scores (before lineage bonuses)"
    label_final = "Final ability scores (after lineage bonuses)"
    
    if char.get('apply_racial', True):
        st.write(f"**{label_base}:**")
        for stat, val in char['base_stats'].items():
            st.write(f"{stat}: {val}")

        st.write(f"**{label_final}:**")
        for stat, val in char['final_stats'].items():
            st.write(f"{stat}: {val}")
    else:
        for stat, val in char['base_stats'].items():
            st.write(f"{stat}: {val}")

    # ================= Level‑up ASI panel =================
    asi_cap  = asi_slots_available(char["class"], char["level"])
    unspent  = asi_cap - st.session_state.asi_spent
    final    = char["final_stats"]

    # Show ASI information
    st.markdown("### 📈 Ability Score Improvements (ASIs)")
    
    # Explain what ASIs are
    with st.expander("ℹ️ What are Ability Score Improvements?", expanded=False):
        st.write("""
        **Ability Score Improvements (ASIs)** are gained at certain levels and allow you to:
        
        • **+2 to one ability** (e.g., Strength 14 → 16)
        • **+1 to two different abilities** (e.g., Dexterity 12 → 13, Constitution 14 → 15)
        • **Take a feat instead** (optional rule, not implemented here)
        
        **Important Rules:**
        • No ability score can exceed 20
        • You must use the full ASI (can't save partial points)
        • ASIs are permanent improvements to your character
        """)
    
    # Display ASI progression for this class
    asi_levels = ASI_LEVELS.get(char["class"], ASI_LEVELS["default"])
    asi_info = []
    for level_threshold in sorted(asi_levels):
        if level_threshold <= char["level"]:
            asi_info.append(f"**Level {level_threshold}** ✅")
        else:
            asi_info.append(f"Level {level_threshold} ⏳")
    
    st.write(f"**ASI Schedule for {char['class']}:** {' | '.join(asi_info)}")
    
    # Current ASI status
    if asi_cap == 0:
        st.info("🕐 **No ASIs available yet.** Your first ASI will come at level 4.")
    else:
        if unspent > 0:
            st.success(f"🎯 **You have {unspent} unspent ASI(s)** out of {asi_cap} total available at level {char['level']}.")
        else:
            st.info(f"✅ **All {asi_cap} ASI(s) have been allocated** for level {char['level']}.")

    if unspent > 0:
        st.markdown("#### 🎯 Allocate Your ASI")
        
        # Show current ability scores for reference
        st.write("**Current Ability Scores:**")
        score_display = " | ".join([f"{stat[:3]}: {final[stat]}" for stat in ABILITIES])
        st.code(score_display)
        
        # Strategy guidance
        st.markdown("**💡 ASI Strategy Tips:**")
        class_recommendations = {
            "Barbarian": "Prioritize **Strength** (damage) and **Constitution** (survivability).",
            "Bard": "Focus on **Charisma** (spellcasting) and **Dexterity** (AC/initiative).",
            "Cleric": "Boost **Wisdom** (spellcasting) and **Constitution** (concentration).",
            "Druid": "Improve **Wisdom** (spells) and **Constitution** (Wild Shape HP).",
            "Fighter": "Enhance **Strength/Dexterity** (attacks) and **Constitution** (survivability).",
            "Monk": "Focus on **Dexterity** (AC/attacks) and **Wisdom** (AC/saves).",
            "Paladin": "Boost **Strength** (attacks) and **Charisma** (spells/aura).",
            "Ranger": "Prioritize **Dexterity** (attacks) and **Wisdom** (spells).",
            "Rogue": "Max **Dexterity** first (attacks/AC), then **Constitution**.",
            "Sorcerer": "Focus on **Charisma** (spells) and **Constitution** (concentration).",
            "Warlock": "Boost **Charisma** (spells) and **Constitution** (survivability).",
            "Wizard": "Prioritize **Intelligence** (spells) and **Constitution** (concentration).",
            "Artificer": "Focus on **Intelligence** (spells) and **Constitution** (survivability).",
            "Blood Hunter": "Balance **Strength/Dexterity** and **Constitution** (for blood curses)."
        }
        
        if char["class"] in class_recommendations:
            st.info(f"**{char['class']} Recommendation:** {class_recommendations[char['class']]}")

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox(
                "🎯 Primary ability to improve", 
                ABILITIES, 
                key="asi_stat1",
                help="Choose the ability score you want to improve"
            )
            improvement_val = st.selectbox(
                "📊 Improvement amount", 
                [1, 2], 
                key="asi_val1",
                help="Choose +1 or +2. If you choose +2, you cannot improve a second ability."
            )
        
        with col2:
            second_options = ["—"] + [stat for stat in ABILITIES if stat != st.session_state.get("asi_stat1", "")]
            st.selectbox(
                "🎯 Second ability (+1 only)", 
                second_options, 
                key="asi_stat2",
                help="Optional: Choose a second ability to get +1 (only if primary gets +1)"
            )
            
            # Show preview of changes
            s1 = st.session_state.get("asi_stat1", ABILITIES[0])
            v1 = st.session_state.get("asi_val1", 1)
            s2 = st.session_state.get("asi_stat2", "—")
            
            st.write("**Preview of changes:**")
            if s2 != "—" and v1 == 1:
                st.write(f"• {s1}: {final[s1]} → {final[s1] + v1}")
                st.write(f"• {s2}: {final[s2]} → {final[s2] + 1}")
            elif v1 == 2:
                st.write(f"• {s1}: {final[s1]} → {final[s1] + v1}")
            else:
                st.write(f"• {s1}: {final[s1]} → {final[s1] + v1}")

        def apply_asi():
            s1 = st.session_state.asi_stat1
            v1 = st.session_state.asi_val1
            s2 = st.session_state.asi_stat2
            
            # Validation checks with helpful error messages
            if final[s1] + v1 > 20:
                st.error(f"❌ **Cannot improve {s1}:** Would exceed maximum of 20 (currently {final[s1]}).")
                return
            if s2 != "—" and v1 == 2:
                st.error("❌ **Invalid combination:** If you add +2 to one ability, you cannot improve a second ability.")
                return
            if s2 != "—" and final[s2] + 1 > 20:
                st.error(f"❌ **Cannot improve {s2}:** Would exceed maximum of 20 (currently {final[s2]}).")
                return
            if s2 != "—" and s1 == s2:
                st.error("❌ **Cannot apply bonuses to the same ability twice in one ASI.**")
                return
                
            # Apply the improvements
            old_s1 = final[s1]
            final[s1] += v1
            improvement_text = f"**{s1}:** {old_s1} → {final[s1]}"
            
            if s2 != "—":
                old_s2 = final[s2]
                final[s2] += 1
                improvement_text += f" | **{s2}:** {old_s2} → {final[s2]}"
            
            st.session_state.asi_spent += 1
            remaining_asis = unspent - 1
            
            success_msg = f"✅ **ASI Applied!** {improvement_text}"
            if remaining_asis > 0:
                success_msg += f"\n\n🎯 You have **{remaining_asis} more ASI(s)** to allocate."
            else:
                success_msg += f"\n\n🎉 **All ASIs allocated!** Your character is complete for level {char['level']}."
                
            st.success(success_msg)

        st.button("🚀 Apply ASI", on_click=apply_asi, type="primary")
        
        # Warning about permanence
        st.caption("⚠️ **Note:** ASI improvements are permanent and cannot be undone. Choose carefully!")
        
    elif asi_cap > 0:
        st.info("✅ **All ASIs have been allocated** for your current level.")
    else:
        st.info("🕐 **No ASIs available yet.** Your first ASI will typically come at level 4.")

    # -------- Backstory in Expander --------
    with st.expander("📜 Backstory", expanded=True):
        st.write(char['backstory'])

    # -------- Download --------
    txt = f"""D&D Character Sheet (PHB Only)
--------------------
Name: {char['name']}
Race: {char['race']}
Class: {char['class']}
Background: {char['background']}
Alignment: {char['alignment']}
Level: {char['level']}

Ability Scores (base – before lineage bonuses):
"""
    for stat, score in char['base_stats'].items():
        txt += f"    {stat}: {score}\n"

    if char.get('apply_racial', True):
        txt += "\nAbility Scores (final – after lineage bonuses):\n"
        for stat, score in char['final_stats'].items():
            txt += f"    {stat}: {score}\n"

    txt += f"\nBackstory:\n{char['backstory']}\n"
    txt += "\nNote: This character was created using only options from the official Player's Handbook (PHB).\n"

    st.download_button(
        label="📄 Download Character Sheet (.txt)",
        data=txt,
        file_name=f"{char['name'].replace(' ', '_')}_sheet.txt",
        mime="text/plain"
    )