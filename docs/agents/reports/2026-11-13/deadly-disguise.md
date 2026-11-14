<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Deadly Disguise (Kaust, Eyes of the Glade): report

**What I measured.** Under the candidate the deck kills 0.82 turns faster than stock on the validation seeds (95% +0.45 to +1.18). Most of that comes from mana use, Kaust arriving on time and the activated abilities. The deck's real plan is turning creatures face up, and the rules can't do that. They can't choose to cast a card face down either.

**1. Audit, stock AI.** 12 games from seed 30001: kill turn 12.58. On the 40 validation games stock killed in 11.95, with 38 of 40 finished.
- **Unspent mana:** 67% (validation 68%). 63–72% of turns ended holding a card the unspent mana would have paid for, and 20–25% of turns cast nothing.
- **Face down:** stock does cast face down (196 casts in 40 games) and turns cards face up (about 100 that I could see through face-up triggers).
- **Kaust:** often late. In validation it came down by its own turn 3 in only 11 of 40 games, the median was turn 5, and it was never cast in 5 games.
- **Cards it sat on:** Mirror Entity (22 turns with the mana for it), then removal (no targets in goldfish), Whisperwood Elemental, Mastery of the Unseen, Scourge of the Throne, Wild Growth and Hooded Hydra.
- **Abilities never used:** Panoptic Projektor (0 of 16 turns), Krosan Verge, Saryth and Whisperwood's sacrifice ability. Mastery of the Unseen was used 5 times in 23 turns.
- **Triggers declined:** Trail of Mystery, Lifecrafter's Bestiary and Imperial Hellkite.
- **Flagged never-cast:** Mirror Entity, Obscuring Aether, Boltbender and Wild Growth.

**2. Candidate: `playbook/variants/deadly-disguise-veil.json`**
1. Cast the ramp: Sol Ring, Signet, Three Visits, Nature's Lore, Wild Growth (flagged), Sakura-Tribe Elder.
2. Cast Kaust as soon as possible.
3. Cast the face-down engines: Obscuring Aether (flagged), Projektor, Trail of Mystery, Ugin's Mastery, Veiled Ascension, Bestiary, Scroll of Fate, Mastery of the Unseen, Ransom Note.
4. Tap Panoptic Projektor whenever a morph or disguise card is in hand.
5. Cast the creature payoffs: Duskana, Beast Whisperer, Seedborn Muse and the rest, Mirror Entity among them.
6. Cast every morph and disguise card. The rule casts the face-up spell when it is affordable and the face-down one otherwise.
7. Tap Scroll of Fate.
8. Use Krosan Verge.
9. Activate Mirror Entity with X equal to all the mana, X at least 3, in the first main phase, when there are 3 or more attackers.
10. Activate Mastery of the Unseen up to 4 times after combat while the library has 20 or more cards.
- **Triggers accepted:** Trail of Mystery (library ≥ 20), Bestiary (library ≥ 30), and Ugin's Mastery, Imperial Hellkite, Deathmist Raptor, Veiled Ascension, Yedora, Broodhatch, Temur War Shaman and Root Elemental.
- **Attack:** go_wide, the batch default.
- **Tuning:** on the audit seeds rules 1–10 gave +1.67 turns (stock 12.58, candidate 10.92). Adding the trigger rules changed no kill turn. Lowering Mirror Entity's minimum X from 4 to 3 changed nothing either. Both were kept.

**3. Validation, seeds 30101–30140.** The rules were final before any validation game was read.

| arm | finished | kill turn (mean) | median |
|---|---|---|---|
| stock | 38/40 | 11.95 | 12 |
| veil | 38/40 | 11.13 | 11 |

Paired over the 38 seeds both arms finished: +0.82 turns (95% +0.45 to +1.18). The candidate was faster in 23 games, the same in 11 and slower in 4. Unspent mana fell from 68% to 47%. Kaust came down by turn 3 in 23 of 40 games (median turn 3, never missing). The pair file is `<scratch>/batch/deadly-disguise/deadly-disguise-pair.json`. The restart killed the first playbook run after 10 games, so it was rerun cleanly from scratch; stock was not rerun.

**4. Rules that fired** (validation `playbook_stats`, rules 1–10 in order): 74 / 40 / 68 / 12 / 110 / 209 / 37 / 7 / 9 / 6, and 95 triggers accepted (32 / 25 / 38 by trigger rule). Every rule fired.

**5. What the rule format can't express**
- **Turning a creature face up.** In Forge this is a special action built as `ST$ SetState | Mode$ TurnFaceUp` in `CardFactoryUtil.abilityTurnFaceUp`. That is an AbilityStatic, so `isActivatedAbility()` is false. The face-down permanent also has no name an `activate` rule could match. It stays entirely Forge's.
- **Choosing to cast face down.** Forge's face-down cast is an ordinary Spell (`isCastFaceDown`), not an AlternativeCost. `playable()` takes the first ready spell, so a cheap morph goes face up and its turned-face-up trigger is lost. Under the candidate, face-down casts fell from 196 to 96 and the face-ups I could see from about 100 to 70; manifests rose from 66 to 128.
- **Kaust's ability.** It targets an attacking creature, so it can only be used in combat, outside the rules' main phases. It stays Forge's (used 55 times in 302 turns).
- **What's needed:** a `face_down: true` key on play rules, a `turn_up` rule with a cost and timing (for example during combat after blockers, or at the end of an opponent's turn), and activate rules that can run in combat.

**6. Recommendation.** Send it to the 200-table exam. The gain is modest but clear of noise: mana used, Kaust on time, Mirror Entity, Projektor and Mastery working. At real tables the face-up tricks against blockers and removal matter more, and those stay Forge's. This deck would gain most from the face-down and turn-up hooks above.

**7. The deck's answers, for the second pass**
- **Austere Command:** board wipe; choose two of artifacts, enchantments, creatures with mana value 3 or less, creatures with mana value 4 or more.
- **Dusk // Dawn:** Dusk destroys every creature with power 3 or more; Dawn, from the graveyard, returns our creatures with power 2 or less.
- **Fell the Mighty:** destroys every creature with power greater than a target creature's. Face-down 2/2s make it one-sided.
- **Showstopping Surprise:** turns our creature face up, then it deals damage equal to its power to every other creature.
- **Decimate:** one artifact, one creature, one enchantment and one land.
- **Chaos Warp:** any permanent shuffled away.
- **Path to Exile:** a creature.
- **Unexplained Absence:** one nonland permanent from each player, each replaced by a cloaked 2/2.
- **Hidden Dragonslayer (when turned face up):** an opponent's creature with power 4 or more.
- **Ainok Survivalist (when turned face up):** an opponent's artifact or enchantment.
- **Nantuko Vigilante (when turned face up):** an artifact or enchantment.
- **Boltbender (when turned face up):** redirects spells and abilities. Flagged never-cast.
- **Ransom Note:** can goad a creature.
- Apart from Boltbender, none of these is flagged never-cast. The deck has no counterspells or fogs.

**8. How a person plays it.** An owner plays Kaust on turn 3 and lays two or three face-down 2/2s. They flip them at the right moment: mid-combat for Kaust's card draw, Experiment Twelve's counters and Trail of Mystery's +2/+2. Cheap disguise creatures go down face down for value, Projektor makes them nearly free, and Mirror Entity or Duskana finishes the board. The candidate gets Kaust, the mana and the engines down, and uses Mirror Entity and the manifest sinks. It can't hold cards face down on purpose or choose when to flip. It casts Printlifter Ooze, Hidden Dragonslayer and the other two-mana creatures face up and leaves every flip and Kaust's combat use to Forge, so the deck's signature play is still stock.
