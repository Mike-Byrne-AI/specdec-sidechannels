"""Generate the OQ-16 Stage-A VERDICT population: deterministic, committed
alongside its output so the audit's inputs are reviewable evidence (D-4
spirit; the K-3 / OQ-15 precedents).

One file, authored and committed WITH the STAGE-A FREEZE and BEFORE any
Stage-A GPU run exists (the population-selection surface closes at that
commit):
  prompts_oq16_verdict.jsonl — 210 prompts = 3 families x 70 unique topics

Why a fresh population: the reconstruction weights and the injection
adapters are trained on the four committed vanilla verdict runs
(prompts_k3_verdict + prompts_oq15_verdict, all 420 prompts); the verdict
must run on prompts none of them saw, and the seed-vs-seed spread of the
committed runs (CI half-width ~0.09 tokens/call at 42 prompts vs ~0.04 at
210) says 84 held-out prompts cannot resolve the +0.062 bar.

Same recipe as the committed sets: one prompt per unique topic (prompt-
cluster independence for the bootstrap), two templates per family
alternating across topics, families interleaved so any prefix stays
balanced. No RNG.

MECHANICAL REFUSALS (extended; the Stage-A critic's blocker on the first
draft — 83 of its 210 topics were paraphrases of committed topics at the
content-word level, several near-verbatim): refuses if any new topic
(i) collides case-insensitively with another new topic or a committed
topic, (ii) shares >= 2 content words (lower-cased, light plural
stemming, stop/frame words dropped — "history", "origins", "invention"
are the summarize frame, not content) with ANY topic in
data/prompts.jsonl, data/prompts_k3_verdict.jsonl,
data/prompts_oq15_verdict.jsonl or data/prompts_oq15_val.jsonl, or
(iii) is a summarize topic whose object contains or is contained in a
committed summarize object as a whole-word phrase; and refuses to
overwrite an existing output. Sharing ONE content word with a committed
topic is allowed (the families reuse a small vocabulary of crafts and
objects); the training and verdict populations are disjoint at the
prompt level and, by this rule, at the paraphrase level.

Rerun: python data/make_prompts_oq16.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent

INSTRUCT = [
    "wave energy buoys capture power from swells", "kilns fire clay into pottery",
    "glassblowers shape molten glass", "kingfishers dive without a splash",
    "avalanche beacons locate buried skiers", "weaver birds knot their nests",
    "zeppelins hold their shape aloft", "cheese caves ripen their wheels",
    "ship elevators hoist vessels between waterways", "squid flash patterns across their skin",
    "sprinkler systems know when to spray", "kayakers roll upright after capsizing",
    "kelp forests anchor to the seabed", "puffins carry a dozen fish crosswise",
    "bicycle gears make hills easier", "elevators are kept from falling",
    "antibiotics kill bacteria but not human cells", "kangaroo rats never drink water",
    "watermills power a sawmill", "spiders spin silk stronger than steel",
    "submarines dive and resurface", "lichens colonize bare rock",
    "arctic terns migrate pole to pole", "cold frames protect seedlings from frost",
    "bumper cars get their power from the ceiling", "fireflies produce their light",
    "air traffic controllers keep planes apart", "rain gauges measure a storm",
    "ptarmigans molt into winter plumage", "beekeepers harvest honey without harming the hive",
    "gondola cables span a valley", "searchlights sweep a harbor at night",
    "tortoises live for more than a century", "spring houses kept milk cool before refrigeration",
    "geothermal plants tap underground heat", "cuttlefish hypnotize their prey",
    "mountain goats climb sheer cliffs", "photovoltaic cells convert photons",
    "albatrosses glide for days without flapping", "croissants get their flaky layers",
    "thermal vents host life on the seafloor", "hearing aids amplify speech but not noise",
    "marathon runners avoid hitting the wall", "paternoster lifts run without stopping",
    "termites cool their mounds", "ice rinks stay frozen indoors",
    "manta rays leap out of the water", "canning keeps fruit safe for years",
    "bridges expand and contract with the weather", "sloths survive on so little food",
    "moving walkways speed up airport travel", "tea leaves are cured and dried",
    "walruses haul out onto ice floes", "roundabouts move cars without signals",
    "monarch butterflies migrate thousands of miles", "slow cookers tenderize tough cuts",
    "abalone shells get their shimmer", "anemometers gauge wind speed",
    "chameleons aim their tongues", "turnstiles count passengers",
    "clouds are seeded to make rain", "gray whales follow the coast to their lagoons",
    "earplugs block a jackhammer", "paragliders ride rising warm air",
    "torpedo rays stun their prey", "water clocks measured the hours in ancient cities",
    "kombucha cultures brew themselves", "porcupines defend themselves",
    "drawbridges open for passing ships", "snowplows clear a highway overnight",
]

STORY = [
    "a surveyor whose measurements come out in seasons",
    "a coppersmith who hammers out a pot that cooks memories",
    "a gatekeeper who admits travelers by the songs they know",
    "a clockmaker whose clocks run on borrowed minutes",
    "a beekeeper whose hive hums old lullabies",
    "a chandelier hanger whose crystals hum before a storm",
    "a shepherd whose flock grazes on clouds",
    "a locksmith who forges a key to yesterday",
    "a candle-maker whose candles burn away regrets",
    "a cider presser whose cider pours out the taste of the orchard's dreams",
    "a glovemaker whose gloves remember every hand they shook",
    "a firework maker whose rockets spell out wishes",
    "a lobsterman whose traps come up full of letters",
    "a baker whose loaves rise on good news",
    "an embroiderer whose needle stitches tomorrow's headlines",
    "a tile-setter whose floors rearrange themselves by mood",
    "an orchardist whose apples ripen only for the honest",
    "a saddler whose saddles let riders hear the horse's thoughts",
    "a scrivener whose contracts rewrite themselves at midnight",
    "a blacksmith who hammers a horseshoe for a comet",
    "a rope-maker whose ropes tie two distant towns together",
    "a coal merchant whose coal burns with last summer's sunlight",
    "a saltmaker whose salt tastes of the tide that made it",
    "an innkeeper whose rooms open onto other centuries",
    "a potter who throws a bowl that is always full",
    "a rainwater collector whose barrels fill with unshed tears",
    "a carpenter who builds a boat for a river that dried up",
    "a cartwright whose carts refuse to carry lies",
    "a perfumer whose scents recall places that never existed",
    "a toymaker whose puppets rehearse tomorrow",
    "a scribe whose ink dries into birds",
    "a ladder maker whose ladders reach one rung past the sky",
    "a piper who charms the frost off the fields",
    "a sentry at a gate that opens only onto the past",
    "a seamstress who mends a torn horizon",
    "a cheesemaker whose wheels age a year every night",
    "a chandler who sells the hours in wax",
    "a tinker who solders a cracked moon back together",
    "a vintner whose wine ages backwards",
    "a rag-picker who collects lost afternoons",
    "a printer whose press prints only what will come true",
    "a lantern-maker who traps a storm in a lantern",
    "a goatherd who trades a goat for a cloud",
    "a bridge-keeper who charges a toll of one secret",
    "a pharmacist whose pills taste of the patient's best day",
    "a shoeshine boy whose brushes buff out bad memories",
    "a town crier who announces tomorrow's news",
    "a miner who digs up a buried sunrise",
    "an acrobat who somersaults across a rainbow",
    "a dockhand who ties up a ship crewed by echoes",
    "a paper-lantern folder whose lanterns float away with regrets",
    "a fletcher whose arrows always return with a message",
    "a gravedigger who unearths the seed of a new town",
    "a spinner who spins thread from a spider's promise",
    "a goldsmith who beats a coin from a sunbeam",
    "a shipwright who launches a ship onto a field of wheat",
    "a stained-glass artist whose windows show next year's harvest",
    "a cook whose soup tastes of whoever is missed most",
    "a plasterer who smooths over a crack in the sky",
    "a courier who delivers a letter to the wrong century",
    "a marionette carver whose puppets refuse their strings",
    "a farmer who harvests echoes",
    "a barber whose scissors trim away bad luck",
    "a crow trainer whose crows return with other people's keys",
    "a coachman whose coach only stops for the lonely",
    "a brickmaker who fires bricks from river songs",
    "a schoolteacher whose chalk writes the future on the board",
    "a clam digger who unearths a bottle of last century's fog",
    "a woodcarver whose carved animals wander off at night",
    "a knife-grinder who sharpens the edge of the horizon",
]

SUMMARIZE = [
    "the history of the thumbtack", "the origins of the word search",
    "the history of the tricycle", "the invention of the zipper",
    "the history of the postcard", "the origins of the fire hydrant",
    "the history of the waffle iron", "the invention of the safety pin",
    "the history of the hammock", "the origins of the pinwheel",
    "the history of the parasol", "the history of the wristwatch",
    "the origins of the speed bump", "the history of the bagel",
    "the invention of the tea bag", "the history of the mailbox",
    "the history of the eraser", "the origins of the birthday candle",
    "the history of the barber pole", "the invention of the stapler",
    "the history of the rubber duck", "the history of the kite",
    "the origins of the weathervane", "the history of the kazoo",
    "the invention of the can opener", "the history of the bandage",
    "the history of the piggy bank", "the origins of the hopscotch grid",
    "the history of the door knocker", "the invention of the thermostat",
    "the history of the tote bag", "the history of the pocket knife",
    "the origins of the miniature golf course", "the history of the jukebox",
    "the invention of the egg carton", "the history of the sled",
    "the history of the whistle", "the origins of the vending machine",
    "the history of the beanbag", "the invention of the ballpoint pen",
    "the history of the flashlight", "the history of the bird feeder",
    "the origins of the bus stop", "the history of the lunch counter",
    "the invention of the lawn mower", "the history of the yo-yo",
    "the history of the trampoline", "the origins of the milk bottle",
    "the history of the wind chime", "the invention of the traffic cone",
    "the history of the swing set", "the history of the corkscrew",
    "the origins of the coat hanger", "the history of the bookmark",
    "the invention of the paper straw", "the history of the porch swing",
    "the history of the tin can", "the origins of the garbage truck",
    "the history of the sandcastle", "the invention of the escalator",
    "the history of the lawn flamingo", "the history of the comic strip",
    "the origins of the lemonade stand", "the history of the scarecrow",
    "the invention of the whiteboard", "the history of the skateboard",
    "the history of the map legend", "the origins of the water cooler",
    "the history of the hourglass", "the invention of the hairbrush",
]

TEMPLATES = {
    "instruct": ["Explain how {t}.", "Describe to a curious teenager how {t}."],
    "story": ["Write a short story about {t}.", "Tell a brief folktale about {t}."],
    "summarize": ["Summarize {t}.", "Give a concise overview of {t}."],
}

OUT = "prompts_oq16_verdict.jsonl"
COMMITTED = ("prompts.jsonl", "prompts_k3_verdict.jsonl",
             "prompts_oq15_verdict.jsonl", "prompts_oq15_val.jsonl")


def committed_topics() -> list[str]:
    topics: list[str] = []
    for name in COMMITTED:
        for line in (DATA / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                topics.append(json.loads(line)["topic"].lower())
    return topics


STOP = set("""the a an of to in on for and with without their its how who whose
that into from by at is are as up out off than over under more most each every
one two it be do does not no so all any some what when where why which this
then there here own made make makes only still never always through keep keeps
stay stays turn turns find finds get gets work works form forms use uses change
changes history origins origin invention exploration great fire""".split())


def content_words(topic: str) -> set[str]:
    out = set()
    for w in re.findall(r"[a-z0-9']+", topic.lower()):
        w = w.replace("'", "")
        if w in STOP or len(w) < 3:
            continue
        if len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 4 and w.endswith("es") and not w.endswith("ses"):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def summarize_object(topic: str) -> str | None:
    m = re.match(r"the (?:history|origins|invention|exploration|great fire) of (?:the )?(.+)",
                 topic.lower())
    return m.group(1).strip() if m else None


def overlaps(new: str, old: str) -> list[str]:
    """Why `new` is refused against committed `old` ([] = allowed)."""
    shared = sorted(content_words(new) & content_words(old))
    if len(shared) >= 2:
        return shared
    a, b = summarize_object(new), summarize_object(old)
    if a and b and (f" {a} " in f" {b} " or f" {b} " in f" {a} "):
        return [f"object:{a}~{b}"]
    return []


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
    fam_topics = {"instruct": INSTRUCT, "story": STORY, "summarize": SUMMARIZE}
    for fam, topics in fam_topics.items():
        if len(topics) != 70:
            raise SystemExit(f"REFUSED: {fam} has {len(topics)} topics, want 70")
    new_all = [t.lower() for topics in fam_topics.values() for t in topics]
    if len(set(new_all)) != len(new_all):
        dupes = sorted({t for t in new_all if new_all.count(t) > 1})
        raise SystemExit(f"REFUSED: duplicate new topics: {dupes}")
    old = committed_topics()
    clashes = sorted(set(new_all) & set(old))
    if clashes:
        raise SystemExit(f"REFUSED: topics collide with committed sets: {clashes}")
    para = [(n, o, why) for n in new_all for o in old if (why := overlaps(n, o))]
    if para:
        lines = "\n".join(f"  {n!r} ~ {o!r} {why}" for n, o, why in para[:40])
        raise SystemExit(f"REFUSED: {len(para)} paraphrase-level overlaps with "
                         f"committed topics:\n{lines}")
    path = DATA / OUT
    if path.exists():
        raise SystemExit(f"REFUSED: {path} exists (delete deliberately to regenerate)")
    prompts = build(fam_topics)
    assert len(prompts) == 210, len(prompts)
    path.write_text("\n".join(json.dumps(p) for p in prompts) + "\n", encoding="utf-8")
    fams = [p["family"] for p in prompts]
    print(f"wrote {len(prompts)} prompts to {path} "
          f"({', '.join(f'{f}: {fams.count(f)}' for f in TEMPLATES)})")
