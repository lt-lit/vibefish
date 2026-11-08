package vibefish;

import java.io.File;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.tuple.Pair;

import forge.StaticData;
import forge.card.CardDb;
import forge.card.CardRules;
import forge.deck.CardPool;
import forge.deck.Deck;
import forge.deck.DeckFormat;
import forge.deck.io.DeckSerializer;
import forge.item.PaperCard;
import forge.util.FileSection;
import forge.util.FileUtil;

/**
 * Validates .dck files against the pinned Forge: unknown card names, cards Forge marks unsupported,
 * cards the AI is told never to play (AI:RemoveDeck:All) or to keep out of random decks
 * (AI:RemoveDeck:Random), and Forge's own Commander deck-conformance check.
 */
final class DeckCheck {
    private DeckCheck() {}

    static int run(String[] args) throws Exception {
        String deckDir = null;
        String outFile = null;
        List<String> files = new ArrayList<>();
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--deck-dir": deckDir = args[++i]; break;
                case "--out": outFile = args[++i]; break;
                default: files.add(args[i]);
            }
        }
        if (files.isEmpty()) {
            Sim.usage();
            return 2;
        }
        Sim.boot();
        CardDb common = StaticData.instance().getCommonCards();
        CardDb variants = StaticData.instance().getVariantCards();

        List<Map<String, Object>> report = new ArrayList<>();
        int problems = 0;
        for (String spec : files) {
            File f = Sim.resolve(spec, deckDir);
            Map<String, Object> r = Sim.obj("file", f.getName(), "path", f.getPath());
            report.add(r);
            if (!f.isFile()) {
                r.put("error", "file not found");
                problems++;
                continue;
            }
            Deck deck = DeckSerializer.fromFile(f);
            if (deck == null) {
                r.put("error", "Forge could not parse this deck file");
                problems++;
                continue;
            }
            // What the file asked for, before Forge silently drops names it does not know.
            Map<String, List<String>> sections = FileSection.parseSections(FileUtil.readFile(f));
            int requested = 0;
            List<String> unknown = new ArrayList<>();
            for (Map.Entry<String, List<String>> s : sections.entrySet()) {
                String key = s.getKey().toLowerCase();
                if (!key.equals("main") && !key.equals("commander")) {
                    continue;
                }
                for (Pair<String, Integer> req : CardPool.processCardList(s.getValue())) {
                    requested += req.getRight();
                    String name = CardDb.CardRequest.fromString(req.getLeft()).cardName;
                    if (common.getCard(name) == null && variants.getCard(name) == null) {
                        unknown.add(name);
                    }
                }
            }
            List<String> commanders = new ArrayList<>();
            List<String> unsupported = new ArrayList<>();
            List<String> aiNever = new ArrayList<>();
            List<String> aiRandom = new ArrayList<>();
            List<PaperCard> all = new ArrayList<>(deck.getCommanders());
            for (PaperCard pc : deck.getCommanders()) {
                commanders.add(pc.getName());
            }
            for (Map.Entry<PaperCard, Integer> e : deck.getMain()) {
                all.add(e.getKey());
            }
            for (PaperCard pc : all) {
                CardRules rules = pc.getRules();
                if (rules == null) {
                    continue;
                }
                if (rules.isUnsupported()) {
                    unsupported.add(pc.getName());
                }
                if (rules.getAiHints() != null) {
                    if (rules.getAiHints().getRemAIDecks()) {
                        aiNever.add(pc.getName());
                    } else if (rules.getAiHints().getRemRandomDecks()) {
                        aiRandom.add(pc.getName());
                    }
                }
            }
            String conformance = DeckFormat.Commander.getDeckConformanceProblem(deck);
            r.put("name", deck.getName());
            r.put("commanders", commanders);
            r.put("requested_count", requested);
            r.put("loaded_count", deck.getMain().countAll() + deck.getCommanders().size());
            r.put("unknown", unknown);
            r.put("unsupported", unsupported);
            r.put("ai_never", aiNever);
            r.put("ai_random", aiRandom);
            r.put("conformance", conformance);
            boolean ok = unknown.isEmpty() && conformance == null;
            r.put("ok", ok);
            if (!ok) {
                problems++;
            }
            System.err.printf("[check] %s: %s | %d cards | unknown %d | unsupported %d | ai-never %d | ai-random %d | %s%n",
                    f.getName(), String.join(" + ", commanders), requested, unknown.size(), unsupported.size(),
                    aiNever.size(), aiRandom.size(), conformance == null ? "conforms" : conformance);
        }
        String json = Sim.GSON_PRETTY.toJson(report);
        if (outFile != null) {
            Files.writeString(Sim.resolve(outFile, null).toPath(), json);
        } else {
            System.out.println(json);
        }
        return problems == 0 ? 0 : 1;
    }
}
