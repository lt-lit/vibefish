<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Ahoy Mateys (Admiral Brass, Unsinkable): candidate playbook report

**1. The audit (12 stock goldfish games, seeds 29001 to 29012)**
- **Kill turn:** 9.75 on average (median 10, range 7 to 12).
- **Mana:** 29% left unspent (1.5 of 5.4 lands a turn). 26% of turns ended holding a card the spare mana could pay for, and 14% of turns cast nothing.
- **Commander timing:** Brass came down on own turn 5.9 on average. In 4 of 12 games he waited one to three turns after he could have been cast.
- **Cards it sat on:** Feed the Swarm, Dire Fleet Daredevil, Hostage Taker, Merchant Raiders, Coercive Recruiter (all targetless in goldfish), King Narfi's Betrayal, Windfall, Black Market Connections.
- **Abilities never used:** Departed Deckhand, Broadside Bombardiers' boast, Bident of Thassa, Arm-Mounted Anchor's equip (11 turns), Spectral Sailor's draw, Port of Karfell, Rogue's Passage, Captivating Crew, Icon of Ancestry, Daring Saboteur, Desolate Lighthouse.
- **Triggers declined:** Bident of Thassa's draw on the first trace run. Forge takes Brass's combat return on its own.
- **Flagged never-cast:** Windfall, Faithless Looting, Rakdos Charm (all `AI:RemoveDeck:All`).

Stock already plays this deck fairly well. What it gets wrong is timing, not an engine left idle.

**2. The candidate: `playbook/variants/ahoy-mateys-crew.json`**
- **Rocks:** Sol Ring, the signets and Commander's Sphere first, so Brass arrives on time.
- **Wayfarer's Bauble:** activated up to turn 7, for ramp.
- **Admiral Brass:** cast the first turn he is castable.
- **Lords and engines next:** Herald's Horn first for the discount, then Beckett Brass, Skeleton Crew, Corsair Captain, Banner, Icon, Shared Animosity and Angrath's Marauders. After them every other Pirate and engine, dearest first.
- **Arm-Mounted Anchor:** equipped in the first main phase (stock never equipped it).
- **Timestream Navigator:** takes its extra turn.
- **Distant Melody:** waits for 4 or more Pirates and a library of 30 or more.
- **Windfall:** cast with 5 or fewer cards in hand and a library of 30 or more. The do-nothing opponents hold full hands, so it refills ours, and the discards feed Brass.
- **Faithless Looting:** library of 30 or more; fills the graveyard for Brass.
- **Spectral Sailor:** draws in the second main phase when 4 mana are spare (library 30 or more).
- **Port of Karfell:** used in the second main phase at 9 or more lands.
- **Triggers accepted:** Admiral Brass; Fathom Fleet Captain's paid token; Bident of Thassa and Daring Saboteur draws (library 20 or more); Herald's Horn, Breeches, Ramirez, Zara.
- **Attack:** the batch default go-wide at the highest life, with the split.
- **Tried and dropped:** activating Broadside Bombardiers' boast. Forge's logic always declined it, because the rule cannot pick the sacrifice or the target. Windfall at 2 or fewer cards was loosened to 5 or fewer.

**3. Validation (seeds 29101 to 29140)**

| Arm | Games won | Kill turn (mean / median) | Mana unspent | Brass's turn |
|---|---|---|---|---|
| Stock | 40/40 | 10.12 / 10 | 26% | 6.2 on average; never cast in 3 games |
| Candidate | 40/40 | 9.05 / 9 | 19% | 5.1 on average; cast in every game |

- **Paired difference:** the candidate is +1.07 turns faster (95% +0.74 to +1.41).
- **Per game:** faster in 28, the same in 9, slower in 3.
- The rules were final before any validation game was seen and were not changed afterwards.

**4. Which rules fired (validation `playbook_stats`)**
- **Cast rules:** rocks 59, Bauble 3, Brass 42, the lords/engines/Pirates list 316, Anchor equip 9, Distant Melody 3, Windfall 10, Faithless Looting 6, Spectral Sailor 2, Port of Karfell 1.
- **Never fired:** Timestream Navigator (the city's blessing was never reached at that point).
- **Triggers:** Bident 107, Fathom Fleet Captain 34, Daring Saboteur 23. The Brass rule and the Horn/Breeches/Ramirez/Zara rule were never asked: Forge treats those as targeted or mandatory and takes them itself.

**5. What the rule format cannot express**
- Bombardiers' boast: which artifact or creature to sacrifice (a Treasure) and aiming the damage at an opponent's face.
- Which Pirate Brass returns. Forge picks; the best is a lord or Port Razer.
- Treasures made into Equipment by Gemcutter Buccaneer: their equip abilities are on tokens, which an activate rule cannot name.
- The creature type chosen for Herald's Horn, Icon of Ancestry and Vanquisher's Banner is Forge's choice and was not checked to be Pirate.
- Black Market Connections' modes are Forge's.
- Hostage Taker, Captivating Crew and Coercive Recruiter need an opponent's permanent as the target.

**6. Recommendation: send it to 200 tables.** The gain is a reliable turn faster in goldfish, mostly from Brass on time and fuller use of the mana. It is a modest gain, and stock already runs the deck fairly well. Expect a small edge at the tables rather than a large one.

**7. The deck's answers, for the second pass**
- **Blasphemous Act:** 13 damage to every creature (wipe).
- **Blood Money:** destroys all creatures; Treasures for nontoken ones.
- **Evacuation:** instant, returns all creatures to their owners' hands.
- **Chaos Warp:** shuffles any target permanent into its owner's library.
- **Feed the Swarm:** destroys an opponent's creature or enchantment.
- **Lethal Scheme:** instant with convoke, destroys a creature or planeswalker.
- **Prismari Command:** 2 damage to any target, or destroys an artifact (two modes).
- **Rakdos Charm:** destroys an artifact, exiles a graveyard, or each creature deals 1 damage to its controller. Flagged `AI:RemoveDeck:All`, so stock never casts it.
- **Hostage Taker:** exiles a creature or artifact and lets us cast it.
- **Amphin Mutineer:** exiles a non-Salamander creature; its controller gets a 4/3.
- **Siren Stormtamer:** the deck's only counter; stops a spell or ability that targets us or our creatures.
- **Merchant Raiders:** taps a creature down and keeps it tapped.
- **Warkite Marauder:** turns one blocker into a 0/1 with no abilities.
- **Dire Fleet Ravager:** every player loses a third of their life.
- **No fogs.** Of the answers above, only Rakdos Charm is flagged never-cast.

**8. How an owner expects it to play**
Ramp into Brass on turn 4 or 5, then use the graveyard as a second hand. Looting, Windfall, Brass's own mill and Grim Captain's Locker fill it, and every combat brings back a hasty 4/4 Pirate. The lords (Beckett Brass, Corsair Captain, Skeleton Crew) and the damage-trigger Pirates (Ramirez, Breeches, Malcolm) turn a wide evasive board into cards, Treasure and stolen permanents. Beckett Brass and the threaten effects steal the table's best threats.

The candidate now gets Brass and the lords out on time and keeps the graveyard fed. It still leaves to Forge which Pirate comes back, the boast, the steal targets and every answer. Against real opponents, the stealing and removal half of the deck is still stock.
