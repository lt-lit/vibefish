<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Blood Rites (`blood-rites`, Clavileño, First of the Blessed): report

**1. The audit** (12 stock goldfish games, seeds 26001–26012). Stock already plays this deck fairly well. It won all 12, with a mean kill turn of 12.42 (median 12.5, range 10–14). It left 2.5 of 5.8 lands' worth of mana unspent each turn (43%). On 39% of turns it ended holding a card it could have paid for, and on 16% it cast nothing. Most of that unspent mana goes on answers it is right to hold against opponents that do nothing: Swords to Plowshares, Utter End, New Blood, Return to Dust and Patron of the Vein.

The real misses:
- **Commander late:** Clavileño came down on turn 3–4 in most games, but on turn 5 even with Sol Ring and Talisman out (game 7), and on turn 7 once.
- **Cards held:** Elenda (four turns), Glass-Cast Heart, Kindred Boon and Elenda's Hierophant were held with the mana for them. Kindred Boon was mostly short of white mana, not badly played.
- **Barely cast:** March of the Canonized.
- **Never cast because Forge's AI is flagged never to cast them:** Viscera Seer and Pact of the Serpent.
- **Abilities never used:** Yahenni, Vona, Rogue's Passage, Dusk Legion Sergeant, Etchings of the Chosen and Viscera Seer. The equipment was equipped 3 times in about 20 turns.
- **Trigger declined:** only Promise of Aclazotz's populate, 7 times in tuning.

Stock does several things well: it attacks every turn, uses Indulgent Aristocrat as a sacrifice outlet at the end of opponents' turns, and pumps Bloodtracker and Kindred Boon.

**2. The candidate:** `playbook/variants/blood-rites-demons.json`
1. Mana rocks first.
2. Clavileño as soon as possible.
3. Anthems and engine permanents in order of worth: Legion Lieutenant, Radiant Destiny, Etchings, Glass-Cast Heart, Sanctum Seeker, Mavren Fein, Kindred Boon, Cordial Vampire, Drana, Elenda, Exquisite Blood, Crossway Troublemakers, Timothar, Promise of Aclazotz.
4. Champion of Dusk only with 3 or more Vampires, a library of at least 30 and life of at least 15 (it draws, and costs life, per Vampire).
5. The rest of the bodies, dearest first. Viscera Seer is included as a 1-mana Vampire.
6. March of the Canonized with X at maximum, X of 3 or more.
7. Viscera Seer's scry ability is held, so Forge cannot feed it creatures.
8. Glass-Cast Heart makes a 1/1 lifelink Vampire after combat with spare mana, while life is 10 or more.
9. Equip Blade of the Bloodchief and Heirloom Blade before combat, where Forge's own logic picks a carrier.
- **Triggers:** always accept Bloodghast, Heirloom Blade, Bloodline Necromancer and Timothar. Accept Crossway Troublemakers' card while life is 15+, library 30+ and hand 5 or fewer. Accept Promise of Aclazotz once there is a token and 4 creatures.
- **Attack:** go-wide at the highest life, as in the brief.
- **Tuning:** the version without rule 9 and the Promise trigger was 0.92 turns faster than stock on the audit seeds. Those two additions came out neutral (−0.08) and were kept.

**3. Validation** (seeds 26101–26140, 40 games each arm). The rules were not changed after the validation games were seen.

| arm | finished | mean kill turn | median |
|---|---|---|---|
| stock | 40/40 | 12.07 | 12 |
| playbook | 40/40 | 10.97 | 11 |

The playbook is 1.10 turns faster on the 40 paired seeds (95% +0.75 to +1.45). It was faster in 30 games, the same in 8 and slower in 2. Unspent mana fell from 44% to 36%, and turns casting nothing from 21% to 13%. Pair file: `<scratch>/batch/blood-rites/blood-rites-pair.json`.

**4. What fired** (validation, `playbook_stats`):
- Cast rules: rule 1 51, rule 2 40, rule 3 112, rule 4 10, rule 5 219, rule 6 6, rule 8 18, rule 9 10.
- Rule 9 (equip) was turned down by Forge's logic 38 times.
- Rule 7 (the hold) never had to stop anything: Forge never tried to use Seer's scry.
- Triggers: Bloodghast 7, Bloodline Necromancer 3, Timothar 1, Crossway 5, Promise 6. The Heirloom Blade trigger never fired.

**5. What the rule format cannot express:**
- Choosing which creature to sacrifice. The best line is to sacrifice the Vampire Clavileño made a Demon (a card plus a 4/3 flier) through Indulgent Aristocrat, Viscera Seer, Yahenni, Bartolomé or Village Rites.
- Naming the equip target by what it is (the evasive or attacking creature) rather than by a fixed card name.
- Pact of the Serpent needs a player as its target (ourselves) and a creature type, so it was left uncast.
- Clavileño's trigger target is Forge's choice.

**6. Recommendation:** send it to 200 tables. The engine gain held on unseen seeds (+1.1 turns, interval clear of zero). It is a modest gain, though: stock already runs the deck's attack plan, and the table result will depend on the answers, which these rules do not touch.

**7. The deck's answers** (all left to Forge; only Pact of the Serpent among the deck's cards is flagged never-cast, and it is card draw, not an answer):
- Swords to Plowshares: exile target creature.
- Utter End: exile target nonland permanent.
- Return to Dust: exile one or two artifacts or enchantments.
- New Blood: steal target creature, by tapping a Vampire.
- Damn: destroy target creature, or overloaded, a wipe of all creatures.
- Austere Command: choose two modes of a wipe (artifacts, enchantments, creatures with mana value 3 or less, or 4 or more).
- Olivia's Wrath: non-Vampires get −X/−X (one-sided).
- Patron of the Vein: destroy target opponent's creature when it enters.
- Butcher of Malakir: each opponent sacrifices a creature whenever one of ours dies.
- Vona, Butcher of Magan: tap and pay 7 life to destroy a nonland permanent.
- Sorin, Lord of Innistrad (−6): destroy up to three creatures or planeswalkers and take them.
- Bojuka Bog: graveyard hate.
- There are no counterspells or fogs.

**8. How it should play:** A person plays Clavileño on turn 3 and attacks with Vampires every turn, so each attack makes a Demon. They sacrifice that Demon at the right moment for a card and a 4/3 flier, while Blood Artist, Cruel Celebrant and Falkenrath Noble drain on every death and lifelink keeps them out of reach. Removal is saved for the real threats. The candidate gets the commander, anthems and engine down on time, but it cannot steer the sacrifices: which creature dies, and when, is still Forge's, and that is the heart of an aristocrats deck. Its answers are also still stock's.
