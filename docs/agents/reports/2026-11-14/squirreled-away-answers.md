<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Squirreled Away (`squirreled-away`): answers candidate

The candidate is `playbook/variants/squirreled-away-answers.json` (version 3, of `acorns`). Its attack block is the same as the base's.

**1. The answer cards in the exam (200 tables)**

Counts are seen / cast / in hand at a loss.

| Card | Stock | acorns |
|---|---|---|
| Decree of Pain | 49/0/28 | 48/0/35 |
| Maelstrom Pulse | 43/0/30 | 45/0/30 |
| Casualties of War | 45/39/5 | 48/17/24 |
| Swarmyard Massacre | 46/45/2 | 45/28/18 |
| Skyfisher Spider | 50/45/6 | 60/22/23 |
| Binding the Old Gods | 56/27/19 | 51/9/23 |
| Plaguecrafter | 44/32/8 | 47/26/11 |
| Putrefy, Saw in Half, Tear Asunder, Windgrace's Judgment, Haywire Mite | cast in 84–100% | cast in 84–100% |

- **Decree of Pain:** while it sat in hand with enough lands to cast it, the biggest opposing board was 9 creatures against our 5, at 16 life (medians).
- **Skyfisher Spider:** its destroy trigger went off on only 13 of stock's 47 casts and 12 of acorns' 23.

**2. Rules added** (numbers are the new file's)
- **Rules 3–4, Decree of Pain:**
  - when an opponent could kill us next turn and has more power than we do (`threat >= life`, `opp_power > power`);
  - or when an opponent has 8+ creatures, more than ours, and more power.
- **Rule 5, Swarmyard Massacre** at `opp_creatures >= 3`. It is nearly one-sided in this deck. I took it out of the engine list.
- **Rule 6, Casualties of War** whenever an opponent has a creature, unless our Garruk is out. Forge picks the modes as the spell is cast, and its planeswalker mode must not find Garruk.
- **Rules 7–8:** Binding the Old Gods, and Skyfisher Spider when we have a token to sacrifice, go ahead of the engine when `opp_power > power`.
- **Trigger rule 3:** accept Skyfisher's "sacrifice another creature" when `tokens >= 1`.
- **Rule 19, Plaguecrafter** with a token to give up.
- **Rule 20, Cache Grab** in main phase 2, before the mana sinks.
- **Tried and changed:** rule 7 first let Skyfisher Spider go with any creature. Forge then declined its trigger twice, because the only creatures it could sacrifice were Hazel or nontoken creatures. That is why the token condition is there now.

**3. Local tables (16, seeds 20263130/1)**

Counts are seen / cast / in hand at a loss.
- Binding the Old Gods 6/5/0: chapter I always destroyed an opposing commander or key creature.
- Casualties of War 3/3: four targets each time, all of them opponents'.
- Swarmyard Massacre 3/3. Skyfisher Spider 2/2, both before the token condition was added.
- Rootcast Apprenticeship 5/3: modes went sensibly onto Hazel and our tokens.
- Poison-Tip Archer 4/3, Plaguecrafter 4/3, Cache Grab 4/3, Beledros Witherbloom 2/2, Arasta 4/3, Hazel's Brewmaster 7/6, Woe Strider 1/1, Insatiable Frugivore 3/2.
- End-Raze Forerunners 2/0: short of 8 mana both times.
- Decree of Pain was never drawn, and Maelstrom Pulse was drawn 6 times and cast 0.
- Untested: rules 3–4 never fired, trigger rule 3 never fired, and rule 8's token condition has not been played.
- Nothing backfired. The seat won 4 of 16, far too few games to mean anything.

**4. Out of reach of the rule format**
- **Maelstrom Pulse:** it is scripted as a Pump spell, so Forge's AI never casts it (0 of 96 games where it was drawn). A rule can only cast a targeted spell through Forge's own logic.
- **Decree of Pain's cycling:** it is an ability from hand.
- **Instant-speed removal on other players' turns.**
- **Choosing what Skyfisher Spider sacrifices.**

**5. Recommendation:** send it to 200 tables, against acorns on the same tables.

**"Cast less" cards, and what I did**
- **Skyfisher Spider:** added to the engine list, plus rule 8 and trigger rule 3.
- **Casualties of War:** rule 6.
- **Poison-Tip Archer:** added to the engine list after Beastmaster Ascension. It is a drain payoff.
- **Rootcast Apprenticeship:** added to the engine list. Forge chose sensible modes when a rule cast it.
- **Swarmyard Massacre:** rule 5.
- **Binding the Old Gods:** rule 7, and in the engine list.
- **Arasta and Hazel's Brewmaster:** moved up, behind the drain and card-draw pieces.
- **Woe Strider and Insatiable Frugivore:** left near the end. They are low-value bodies. The base's Woe Strider scry holds are kept.
- **End-Raze Forerunners:** kept the hold, but lowered it from 4 ready attackers to 3.
- **Plaguecrafter:** rule 19.
- **Beledros Witherbloom:** first in the engine list. The list takes the first castable card, so cheap cards used to use up the mana before it.
- **Cache Grab:** rule 20.

**Base rules moved or changed**
- **End-Raze play and hold:** threshold changed from `attackers >= 4` to 3.
- **Engine list:**
  - Swarmyard removed.
  - Beledros and Garruk moved to the front.
  - Skyfisher, Poison-Tip and Binding inserted, and Rootcast added.
  - Brewmaster and Arasta moved up.
  - Everything else keeps its relative order.
- **Every other base rule** is unchanged and in its order, now shifted down by the inserted rules.

Scratch files are in `<scratch>/batch/answers-squirreled-away/` (`results/t1`, `results/t2`, `t1-playtest.json`, `t2-playtest.json`, `scan.py`, `casts.py`).
