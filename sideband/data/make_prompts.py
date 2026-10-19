"""Generate the Phase 0a prompt set: deterministic, committed alongside its
output so the audit's inputs are reviewable evidence (D-4 spirit).

210 prompts = 3 task families (instruct / story / summarize) x 70 UNIQUE
topics, one prompt per topic (templates alternate across topics for surface
variety). One topic per prompt keeps the prompt-cluster bootstrap's clusters
independent — the K-1 kill rule reads that CI, and topic-paired prompts
would correlate its clusters. Families interleave so any --n-prompts prefix
stays balanced. No RNG. Rerun: python data/make_prompts.py

Regime note: prompts are short (4–16 words), so the audit probes
short-prefix behavior; stated in WHY_THIS_DIES K-1.
"""

from __future__ import annotations

import json
from pathlib import Path

INSTRUCT_TOPICS = [
    "a refrigerator keeps food cold", "airplanes stay in the air", "vaccines train the immune system",
    "the tides follow the moon", "compilers turn code into programs", "yeast makes bread rise",
    "GPS receivers find their position", "earthquakes happen", "solar panels make electricity",
    "the internet routes a message", "antibiotic resistance evolves", "noise-cancelling headphones work",
    "a bicycle stays upright", "inflation changes prices", "coral reefs form",
    "batteries store energy", "the seasons change", "search engines rank pages",
    "glaciers carve valleys", "the human eye focuses", "encryption protects a message",
    "volcanoes erupt", "supply and demand set prices", "birds navigate during migration",
    "a camera captures an image", "lightning forms in storms", "kidneys filter blood",
    "wind turbines generate power", "memory works in the brain", "ships float despite their weight",
    "credit scores are calculated", "rainbows appear after rain", "espresso differs from drip coffee",
    "submarines control their depth", "honeybees communicate food locations",
    "soap removes grease", "muscles grow stronger with exercise", "radios tune to one station",
    "bridges carry heavy loads", "clouds hold their water", "microwave ovens heat food",
    "rivers meander over time", "elevators know where to stop", "plants sense the direction of light",
    "interest compounds over years", "touchscreens sense a finger", "caves form in limestone",
    "sourdough starters stay alive", "traffic jams form without accidents", "telescopes gather faint light",
    "sleep consolidates memories", "salmon return to their birth river", "concrete cures rather than dries",
    "juries reach a verdict", "smoke detectors sense a fire", "languages borrow words from each other",
    "maps flatten a round planet", "insulin regulates blood sugar", "sailboats sail against the wind",
    "auctions discover prices", "spiders build webs at night", "libraries organize their shelves",
    "thermostats hold a temperature", "deserts get cold at night", "passwords get cracked",
    "orchestras stay in tune", "potholes form in winter", "vaccination schedules are designed",
    "fireflies synchronize their flashing", "recycling plants sort mixed waste",
]

STORY_TOPICS = [
    "a lighthouse keeper who hears a knock at midnight", "a gardener who finds a seed that grows overnight",
    "two rival street musicians forced to share a corner", "a cartographer mapping a city that keeps changing",
    "a retired detective's last unsolved case", "a baker whose bread makes people remember lost things",
    "a night-shift radio host and a mysterious caller", "an apprentice clockmaker who breaks time",
    "a ferry captain on the river between two feuding towns", "a librarian who discovers an unreturned book from 1911",
    "a child who trades secrets with the neighborhood crows", "an astronaut tending a greenhouse alone",
    "a translator who finds a word with no equivalent", "an innkeeper snowed in with seven strangers",
    "a painter who can only paint places that no longer exist", "a fisherman who catches a message in a bottle",
    "a courier crossing a desert with a fragile package", "a violin that refuses to play sad songs",
    "a museum guard who notices a statue has moved", "a shepherd counting one sheep too many",
    "a tailor sewing a coat for someone they've never met", "a chess hustler who meets an unbeatable child",
    "a beekeeper whose bees start spelling words", "a subway conductor on the train's final run",
    "a botanist cataloguing a plant that blooms once a century", "a blacksmith forging a key without a lock",
    "a diver exploring a sunken village", "a postman delivering to a house that isn't on any map",
    "a weather forecaster who is suddenly always right", "an archivist who finds their own photograph in a 1920s file",
    "a tour guide inventing history that starts coming true", "a carpenter building a staircase to nowhere",
    "a doctor on a houseboat clinic during the floods", "a stargazer who names a star after a stranger",
    "a printer whose misprints predict tomorrow", "a lamplighter on the last night before electric lights",
    "a ropemaker asked to braid a rope that cannot break", "a customs officer who can smell lies",
    "a piano tuner summoned to a house with no piano", "a girl who inherits her grandmother's unfinished chess game",
    "a locksmith locked out of their own shop", "a train that stops at a station not on the timetable",
    "a market vendor who sells memories by the ounce", "an old sailor teaching knots to a knotless age",
    "a scarecrow promoted to night watchman", "a well that echoes back different words",
    "a seamstress who stitches storms into quilts", "a boy who befriends the fog",
    "a watchmaker's apprentice who hears seconds arguing", "a mailboat pilot delivering to islands that drift",
    "a bell ringer whose bell rings one minute early", "a cook on a research station at the end of winter",
    "a bridge troll filing for retirement", "a calligrapher hired to write a letter no one can read",
    "a park ranger who finds footprints leading up a cliff", "a puppeteer whose puppet starts improvising",
    "a glassblower shaping a window to another season", "a night nurse who hums to the hospital generators",
    "a stonemason repairing a wall that repairs itself", "a ticket taker at a cinema showing tomorrow's films",
    "a herbalist trading remedies for riddles", "a ferrywoman who accepts only stories as fare",
    "a kite maker grounded by a windless summer", "a census taker in a town of one",
    "a saltminer who finds a frozen bell", "an organist in a church with no congregation",
    "a chimney sweep who maps the city by its rooftops", "a bookbinder asked to bind a book of silence",
    "a lifeguard at a lake with two moons", "a gravedigger who plants apple trees",
]

SUMMARIZE_TOPICS = [
    "the causes of the French Revolution", "the plot of a classic heist story", "how the printing press changed Europe",
    "the water cycle", "the history of the Silk Road", "the rules of chess",
    "the fall of the Roman Empire", "the theory of plate tectonics", "the space race of the 1960s",
    "the industrial revolution's effects on cities", "the life cycle of a butterfly", "the history of vaccines",
    "the gold rush era in California", "the workings of a democracy", "the discovery of penicillin",
    "the age of sail and naval exploration", "the basics of photosynthesis", "the construction of the Panama Canal",
    "the history of the Olympic Games", "the causes of the First World War", "the invention of the telephone",
    "the settlement of the American West", "the principles of natural selection", "the building of the transcontinental railroad",
    "the history of jazz music", "the eruption of Mount Vesuvius in 79 AD", "the development of writing systems",
    "the voyages of Polynesian navigators", "the medieval guild system", "the history of timekeeping",
    "the Apollo 11 mission", "the domestication of the horse", "the history of tea trade",
    "the invention of photography", "the rise of ancient Athens", "the spread of the Black Death",
    "the origins of the Olympic marathon", "the history of the compass", "the Dutch tulip mania",
    "the story of the Rosetta Stone", "the age of the great cathedrals", "the whaling era of the 1800s",
    "the invention of the steam engine", "the history of paper money", "the exploration of the deep ocean",
    "the founding of the first universities", "the history of the bicycle", "the California aqueduct system",
    "the race to the South Pole", "the history of chocolate", "the transatlantic telegraph cable",
    "the rise and fall of the Hanseatic League", "the invention of the elevator", "the history of firefighting",
    "the Bronze Age collapse", "the history of the circus", "the origins of the weekend",
    "the Suez Canal's construction", "the history of glassmaking", "the great library of Alexandria",
    "the history of the sandwich", "the development of weather forecasting", "the Viking trade routes",
    "the invention of canning", "the history of the skyscraper", "the origins of paper folding",
    "the first transcontinental flights", "the history of the postage stamp", "the terracotta army's discovery",
    "the history of streetlights",
]

TEMPLATES = {
    "instruct": ["Explain how {t}.", "Describe to a curious teenager how {t}."],
    "story": ["Write a short story about {t}.", "Tell a brief folktale about {t}."],
    "summarize": ["Summarize {t}.", "Give a concise overview of {t}."],
}
TOPICS = {"instruct": INSTRUCT_TOPICS, "story": STORY_TOPICS, "summarize": SUMMARIZE_TOPICS}


def build() -> list[dict]:
    per_family = {}
    for fam, topics in TOPICS.items():
        tpls = TEMPLATES[fam]
        per_family[fam] = [
            {"prompt": tpls[i % len(tpls)].format(t=t), "family": fam, "topic": t}
            for i, t in enumerate(topics)
        ]
    out = []
    for i in range(max(len(v) for v in per_family.values())):
        for fam in ("instruct", "story", "summarize"):  # interleave families
            if i < len(per_family[fam]):
                out.append(per_family[fam][i])
    return out


if __name__ == "__main__":
    prompts = build()
    assert len({p["topic"] for p in prompts}) == len(prompts), "topics must be unique"
    path = Path(__file__).resolve().parent / "prompts.jsonl"
    path.write_text("\n".join(json.dumps(p) for p in prompts) + "\n")
    fams = [p["family"] for p in prompts]
    print(f"wrote {len(prompts)} prompts to {path} "
          f"({', '.join(f'{f}: {fams.count(f)}' for f in TEMPLATES)})")
