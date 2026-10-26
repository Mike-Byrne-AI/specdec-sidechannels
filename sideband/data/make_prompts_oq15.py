"""Generate the OQ-15 Stage-C populations: deterministic, committed alongside
their outputs so the audit's inputs are reviewable evidence (D-4 spirit; the
K-3 verdict-set precedent, commit 2db51aa).

Two files, authored and committed WITH the OQ-15 arc registration and BEFORE
any Stage-I result exists (the population-selection surface closes at that
commit):
  prompts_oq15_verdict.jsonl — 210 prompts = 3 families x 70 unique topics
  prompts_oq15_val.jsonl     —  30 prompts = 3 families x 10 unique topics

Same recipe as the committed sets: one prompt per unique topic (prompt-cluster
independence for the bootstrap), two templates per family alternating across
topics, families interleaved so any prefix stays balanced. No RNG.

MECHANICAL REFUSALS (the K-3 precedent, extended): the generator refuses to
run if any new topic collides (case-insensitive exact match) with another new
topic or with any topic in data/prompts.jsonl or data/prompts_k3_verdict.jsonl,
and refuses to overwrite existing outputs.

Rerun: python data/make_prompts_oq15.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent

INSTRUCT_VERDICT = [
    "cranes lift heavy loads without tipping", "icebreakers clear frozen shipping lanes",
    "woodpeckers hammer without getting concussions", "cacti survive years without rain",
    "scuba divers avoid the bends", "water striders walk on the surface of a pond",
    "suspension bridges damp their swaying", "ferries dock precisely in strong currents",
    "bees keep their hive cool in summer", "chimneys draw smoke upward",
    "grain silos keep their contents dry", "lizards regrow their tails",
    "maple trees are tapped for syrup", "foghorns warn ships in low visibility",
    "sled dogs run for hours without overheating", "thermos bottles keep drinks hot",
    "periscopes see over obstacles", "stalactites grow from cave ceilings",
    "starling flocks turn in unison", "pressure washers strip paint",
    "pickling preserves vegetables for months", "harbor buoys mark safe channels",
    "seismographs record distant earthquakes", "sundials tell time",
    "potters glaze their ceramics", "dry ice skips the liquid phase",
    "carbon dating estimates an object's age", "wetsuits keep swimmers warm",
    "antifreeze protects a car engine", "ventriloquists throw their voices",
    "barometers forecast changing weather", "tugboats steer enormous ships",
    "deep-sea fish glow in the dark", "rust eats away at iron",
    "helium balloons eventually sink", "sonar maps the seafloor",
    "controlled burns prevent wildfires", "quicksand traps a walker",
    "northern lights appear near the poles", "steam irons smooth wrinkled shirts",
    "storm shutters protect coastal homes", "double-pane windows insulate a house",
    "leaf-cutter ants farm their own food", "geckos climb smooth glass",
    "hourglasses measure time with sand", "combination locks open to one sequence",
    "olive presses extract oil", "salt is harvested from evaporation ponds",
    "wine corks seal a bottle for decades", "dolphins sleep with half their brain",
    "earthworms aerate garden soil", "hummingbirds hover in place",
    "frost patterns form on windows", "railroads bank their curves",
    "surge protectors shield electronics", "stage spotlights follow a performer",
    "carbonated drinks go flat", "yo-yos return to the hand",
    "levees hold back floodwaters", "desalination plants make seawater drinkable",
    "prairie dog towns connect underground", "power grids balance supply in real time",
    "gymnasts spin faster by tucking in", "blast furnaces smelt iron ore",
    "silkworms spin their cocoons", "bogs preserve ancient artifacts",
    "wells reach the water table", "revolving doors save building heat",
    "fireworks make their colors", "prisms split white light",
]

INSTRUCT_VAL = [
    "toll plazas count axles", "weather balloons reach the stratosphere",
    "moths navigate by the moon", "player pianos read punched rolls",
    "chalk cliffs erode into arches", "campfires are safely extinguished",
    "semaphore flags carried messages", "drought-resistant crops are bred",
    "metronomes keep a steady beat", "storm drains prevent street flooding",
]

STORY_VERDICT = [
    "a cooper whose barrels keep whatever season they were sealed in",
    "a thatcher who roofs houses with last night's dreams",
    "a wheelwright asked to build a wheel that rolls uphill",
    "a farrier shoeing a horse made of weather",
    "a tinker who repairs broken promises",
    "a brewer whose ale tastes of the drinker's childhood",
    "a miller who grinds grain into quiet",
    "a falconer whose hawk brings back lost words",
    "an apothecary whose tinctures cure the wrong ailments",
    "a sailmaker sewing a sail for a ship that sails on grass",
    "a netmender whose nets catch only what the sea regrets",
    "an engraver who etches doors onto cliff faces",
    "a typesetter whose spilled type rearranges into warnings",
    "a bookmobile driver whose last stop never appears twice",
    "an ice-cream vendor whose flavors are extinct summers",
    "a crossing guard who halts traffic for invisible parades",
    "a harbor master logging ships that departed centuries ago",
    "a building superintendent who sweeps a hallway that lengthens",
    "a sign painter whose signs point to what the town has lost",
    "a taxidermist whose birds molt every autumn",
    "a clocktower keeper who winds the town's luck",
    "a planetarium narrator who notices a new star in the projection",
    "a tea blender whose blends brew the weather of far coasts",
    "a perfumer bottling the smell of thunderstorms that never arrived",
    "a balloonist who maps the migration of clouds",
    "a street sweeper who sweeps up dropped names",
    "a zamboni driver smoothing ice that remembers every fall",
    "a gondolier who poles through flooded libraries",
    "a log driver steering timber down a river of stars",
    "a fire tower watcher who spots smoke from cold campfires long out",
    "a fountain cleaner who fishes wishes from the drain",
    "an organ grinder whose monkey conducts the pigeons",
    "a mime trapped in a box that turns out to be real",
    "a ringmaster whose circus performs only for one child",
    "a fortune cookie writer whose fortunes start rhyming with the news",
    "an obituary writer assigned an obituary with no name",
    "a proofreader who finds the same typo spreading between books",
    "an auctioneer selling the contents of an unopened room",
    "a pawnbroker who accepts regrets as collateral",
    "an antiques dealer whose mirrors hold their previous owners' mornings",
    "a junk collector assembling a machine from what the city discards",
    "a jeweler who sets stones that dim when lies are told",
    "an upholsterer restuffing a chair that sighs",
    "a broom maker whose brooms refuse to sweep on Sundays",
    "a basket weaver weaving baskets that hold water",
    "a dyer whose vats color cloth with tomorrow's sunset",
    "a saddler stitching a saddle for the north wind",
    "a stable hand who grooms the mayor's invisible horse",
    "a carousel operator whose painted horses tire at dusk",
    "a pinsetter in a bowling alley beneath the opera house",
    "a caddie who carries clubs for a golfer no one else sees",
    "a stenographer transcribing a trial held in her sleep",
    "a rag-and-bone man collecting the town's discarded Tuesdays",
    "a jam maker preserving fruit from a tree no one planted",
    "a bellhop carrying luggage that grows heavier with secrets",
    "a snowplow driver whose plow turns up seashells each storm",
    "a sommelier who pours a vintage from a year that never happened",
    "a spice merchant whose cinnamon makes customers homesick for places unseen",
    "a frame maker whose empty frames fill overnight",
    "a gem cutter who splits a stone and finds a tiny sky",
    "a mattress maker whose mattresses trade dreams between sleepers",
    "a piano teacher whose student plays a piece not yet composed",
    "a fencing master dueling his own shadow for the title",
    "an origami teacher who folds a map of a foldable city",
    "a radio repairman who fixes a set that receives the sea",
    "a night ferry deckhand counting passengers who board dry from the water",
    "a lace maker whose patterns knot the fates of brides",
    "a well digger who taps a vein of warm rain",
    "a scoreboard operator at a stadium where the game never ends",
    "a toymaker whose wind-up toys wind themselves at dawn",
]

STORY_VAL = [
    "a dead-letter clerk who answers the unanswerable mail",
    "a canal lockkeeper who lets the autumn through a day early",
    "a birdhouse builder whose tenants pay rent in feathers",
    "a wig maker whose wigs whisper their former owners' songs",
    "a puddle measurer employed by a city of reflections",
    "a music box repairman who finds an unfamiliar tune inside",
    "a lightship cook anchored above a sunken carnival",
    "a hedge trimmer shaping a maze that rearranges at night",
    "a stamp collector whose rarest stamp changes its picture",
    "a snow-globe maker whose globes hold rooms from demolished houses",
]

SUMMARIZE_VERDICT = [
    "the history of the windmill", "the construction of the Hoover Dam",
    "the decipherment of cuneiform", "the origins of daylight saving time",
    "the history of the encyclopedia", "the great molasses flood of Boston",
    "the history of the parking meter", "the history of the traffic light",
    "the domestication of the cat", "the history of the phonograph",
    "the history of the banjo", "the year without a summer of 1816",
    "the history of the roller skate", "the origins of the public museum",
    "the history of the cash register", "the history of the lifeboat",
    "the great horse manure crisis of 1894", "the history of the pencil",
    "the origins of the jigsaw puzzle", "the history of the harpsichord",
    "the construction of the Channel Tunnel", "the history of the paperclip",
    "the history of the raincoat", "the history of the swimming pool",
    "the origins of the farmers market", "the history of the doorbell",
    "the exploration of the Grand Canyon", "the history of the ski lift",
    "the history of the thermometer", "the amber trade routes of the Baltic",
    "the history of the drive-in cinema", "the rise and fall of the clipper ships",
    "the history of the weather vane", "the discovery of Tutankhamun's tomb",
    "the history of the kaleidoscope", "the origins of the harvest festival",
    "the history of the smokehouse", "the great train robbery of 1963",
    "the history of crop rotation", "the history of the lightning rod",
    "the origins of the coast guard", "the history of the stagecoach",
    "the history of the button", "the history of the top hat",
    "the discovery of the Antikythera mechanism", "the history of the mosaic",
    "the origins of the theater mask", "the collapse of the Mayan cities",
    "the history of the plow", "the history of the barbershop",
    "the origins of the siesta", "the history of the mail-order catalog",
    "the exploration of the Gobi Desert", "the history of the tide table",
    "the history of the harbor breakwater", "the mystery of the Mary Celeste",
    "the history of the citrus trade", "the history of the neon sign",
    "the origins of the spelling bee", "the history of the rocking chair",
    "the great flood of Johnstown", "the aqueducts of ancient Rome",
    "the history of the shadow play", "the history of the milestone",
    "the origins of the rooftop garden", "the history of the paddle steamer",
    "the history of the phrase book", "the history of the hand fan",
    "the origins of the time capsule", "the history of the pogo stick",
]

SUMMARIZE_VAL = [
    "the history of the picket fence", "the origins of the school lunch",
    "the history of dominoes", "the exploration of Mammoth Cave",
    "the history of the lunchbox", "the great fire of Chicago",
    "the history of the megaphone", "the origins of the town square",
    "the history of the gingerbread house", "the history of marbles",
]

TEMPLATES = {
    "instruct": ["Explain how {t}.", "Describe to a curious teenager how {t}."],
    "story": ["Write a short story about {t}.", "Tell a brief folktale about {t}."],
    "summarize": ["Summarize {t}.", "Give a concise overview of {t}."],
}

SETS = {
    "prompts_oq15_verdict.jsonl": {
        "instruct": INSTRUCT_VERDICT, "story": STORY_VERDICT, "summarize": SUMMARIZE_VERDICT,
    },
    "prompts_oq15_val.jsonl": {
        "instruct": INSTRUCT_VAL, "story": STORY_VAL, "summarize": SUMMARIZE_VAL,
    },
}


def committed_topics() -> set[str]:
    topics: set[str] = set()
    for name in ("prompts.jsonl", "prompts_k3_verdict.jsonl"):
        for line in (DATA / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                topics.add(json.loads(line)["topic"].lower())
    return topics


def build(fam_topics: dict[str, list[str]]) -> list[dict]:
    per_family = {}
    for fam, topics in fam_topics.items():
        tpls = TEMPLATES[fam]
        per_family[fam] = [
            {"prompt": tpls[i % len(tpls)].format(t=t), "family": fam, "topic": t}
            for i, t in enumerate(topics)
        ]
    out = []
    for i in range(max(len(v) for v in per_family.values())):
        for fam in ("instruct", "story", "summarize"):
            if i < len(per_family[fam]):
                out.append(per_family[fam][i])
    return out


if __name__ == "__main__":
    old = committed_topics()
    new_all: list[str] = []
    for fam_topics in SETS.values():
        for topics in fam_topics.values():
            new_all.extend(t.lower() for t in topics)
    if len(set(new_all)) != len(new_all):
        dupes = sorted({t for t in new_all if new_all.count(t) > 1})
        raise SystemExit(f"REFUSED: duplicate new topics: {dupes}")
    clashes = sorted(set(new_all) & old)
    if clashes:
        raise SystemExit(f"REFUSED: topics collide with committed sets: {clashes}")
    for name, fam_topics in SETS.items():
        path = DATA / name
        if path.exists():
            raise SystemExit(f"REFUSED: {path} exists (delete deliberately to regenerate)")
        prompts = build(fam_topics)
        want = sum(len(v) for v in fam_topics.values())
        assert len(prompts) == want, (len(prompts), want)
        path.write_text("\n".join(json.dumps(p) for p in prompts) + "\n", encoding="utf-8")
        fams = [p["family"] for p in prompts]
        print(f"wrote {len(prompts)} prompts to {path} "
              f"({', '.join(f'{f}: {fams.count(f)}' for f in TEMPLATES)})")
