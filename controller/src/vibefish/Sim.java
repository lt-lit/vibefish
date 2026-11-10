package vibefish;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import forge.GuiDesktop;
import forge.ai.AiProfileUtil;
import forge.ai.LobbyPlayerAi;
import forge.deck.Deck;
import forge.deck.io.DeckSerializer;
import forge.game.Game;
import forge.game.GameEndReason;
import forge.game.GameOutcome;
import forge.game.GameRules;
import forge.game.GameType;
import forge.game.Match;
import forge.game.player.Player;
import forge.game.player.PlayerOutcome;
import forge.game.player.RegisteredPlayer;
import forge.gui.GuiBase;
import forge.item.PaperCard;
import forge.model.FModel;
import forge.player.GamePlayerUtil;
import forge.util.BuildInfo;
import forge.util.MyRandom;

/**
 * Vibefish sim harness. Runs Forge headless as a library and records every game as a JSONL event
 * stream plus a run.json summary.
 *
 * <pre>
 *   vibefish.Sim play  --out DIR --deck id=file.dck [--deck ...] [--deck-dir DIR] [--games N]
 *                      [--seed S] [--clock SEC] [--turn-cap T] [--profile NAME ...] [--rotate-profiles]
 *                      [--mc off|on|max|lite] [--start N] [--forge-version TAG]
 *   vibefish.Sim check [--deck-dir DIR] [--out FILE] file.dck [file.dck ...]
 * </pre>
 *
 * Relative paths resolve against $VIBEFISH_CWD when set (the launcher cds into the Forge runtime).
 */
public final class Sim {
    public static final String VERSION = "0.3.0";
    static final Gson GSON = new GsonBuilder().disableHtmlEscaping().serializeNulls().create();
    static final Gson GSON_PRETTY = new GsonBuilder().disableHtmlEscaping().serializeNulls().setPrettyPrinting().create();

    /** Exit code when a game hit the wall clock: the process stops so a stuck game thread cannot pollute later games. */
    public static final int EXIT_TIMEOUT = 3;

    private Sim() {}

    public static void main(String[] args) {
        int rc;
        try {
            if (args.length == 0) {
                usage();
                rc = 2;
            } else if ("play".equals(args[0])) {
                rc = play(Arrays.copyOfRange(args, 1, args.length));
            } else if ("check".equals(args[0])) {
                rc = DeckCheck.run(Arrays.copyOfRange(args, 1, args.length));
            } else {
                usage();
                rc = 2;
            }
        } catch (Exception e) {
            e.printStackTrace();
            rc = 1;
        }
        System.out.flush();
        System.err.flush();
        System.exit(rc);
    }

    static void usage() {
        System.err.println("usage: vibefish.Sim play --out DIR --deck id=file.dck ... [--deck-dir DIR] [--games N] [--seed S]");
        System.err.println("                         [--clock SEC] [--turn-cap T] [--profile NAME ...] [--rotate-profiles]");
        System.err.println("                         [--mc off|on|max|lite] [--start N] [--forge-version TAG] [--data id=deck.json ...]");
        System.err.println("  --data gives one seat its deck's AI data (playbook/precons/<id>.json, see runner/deckdata.py): KeyCards on");
        System.err.println("  the deck, card roles and combos added to Forge's AI lists for the game. Seats without --data are untouched.");
        System.err.println("  --playbook id=deck.json gives one seat its playbook (the file's playbook object): Vibefish takes the decisions");
        System.err.println("  it covers (attack policy, mulligan rule) through Forge's controller hooks; the rest stays Forge's AI.");
        System.err.println("  --profile is given once per seat in deck order; --rotate-profiles shifts the assignment by one seat");
        System.err.println("  every game, so each deck plays each profile equally (A/B runs). --mc switches Forge's Flat Monte");
        System.err.println("  Carlo AI on for the game (2.0.16+ builds); a profile with FLAT_MC_ENABLED=false keeps the heuristic AI.");
        System.err.println("       vibefish.Sim check [--deck-dir DIR] [--out FILE] file.dck ...");
    }

    /** Loads Forge's card database exactly as sim mode does. Takes ~10 s. */
    static void boot() {
        System.setProperty("java.awt.headless", "true");
        GuiBase.setInterface(new GuiDesktop());
        FModel.initialize(null, null);
    }

    static Path base() {
        String cwd = System.getenv("VIBEFISH_CWD");
        return Paths.get(cwd != null && !cwd.isEmpty() ? cwd : System.getProperty("user.dir"));
    }

    static File resolve(String path, String dir) {
        Path p = Paths.get(path);
        if (p.isAbsolute()) {
            return p.toFile();
        }
        if (dir != null) {
            Path d = Paths.get(dir);
            return (d.isAbsolute() ? d : base().resolve(d)).resolve(p).toFile();
        }
        return base().resolve(p).toFile();
    }

    static Map<String, Object> obj(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            m.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return m;
    }

    static int play(String[] args) throws Exception {
        List<String> deckArgs = new ArrayList<>();
        List<String> profiles = new ArrayList<>();
        String deckDir = null;
        String outDir = null;
        String forgeVersion = null;
        int games = 1;
        int start = 1;
        Long seedBase = null;
        int clock = 900;
        int turnCap = 120;
        String mcMode = "off";
        boolean rotateProfiles = false;
        Map<String, String> dataFiles = new LinkedHashMap<>();
        Map<String, String> playbookFiles = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i++) {
            String a = args[i];
            switch (a) {
                case "--deck": deckArgs.add(args[++i]); break;
                case "--profile": profiles.add(args[++i]); break;
                case "--deck-dir": deckDir = args[++i]; break;
                case "--out": outDir = args[++i]; break;
                case "--forge-version": forgeVersion = args[++i]; break;
                case "--games": games = Integer.parseInt(args[++i]); break;
                case "--start": start = Integer.parseInt(args[++i]); break;
                case "--seed": seedBase = Long.parseLong(args[++i]); break;
                case "--clock": clock = Integer.parseInt(args[++i]); break;
                case "--turn-cap": turnCap = Integer.parseInt(args[++i]); break;
                case "--mc": mcMode = args[++i].toLowerCase(); break;
                case "--rotate-profiles": rotateProfiles = true; break;
                case "--data": {
                    String spec = args[++i];
                    int eq = spec.indexOf('=');
                    if (eq <= 0) {
                        System.err.println("--data wants id=file.json");
                        return 2;
                    }
                    dataFiles.put(spec.substring(0, eq), spec.substring(eq + 1));
                    break;
                }
                case "--playbook": {
                    String spec = args[++i];
                    int eq = spec.indexOf('=');
                    if (eq <= 0) {
                        System.err.println("--playbook wants id=file.json");
                        return 2;
                    }
                    playbookFiles.put(spec.substring(0, eq), spec.substring(eq + 1));
                    break;
                }
                default:
                    System.err.println("unknown option " + a);
                    usage();
                    return 2;
            }
        }
        if (outDir == null || deckArgs.size() < 2) {
            usage();
            return 2;
        }
        if (!mcMode.matches("off|on|max|lite")) {
            System.err.println("--mc must be off, on, max or lite");
            return 2;
        }
        if (seedBase == null) {
            seedBase = new SecureRandom().nextInt(1_000_000_000) + 0L;
        }
        Path out = resolve(outDir, null).toPath();
        Files.createDirectories(out.resolve("games"));

        long t0 = System.currentTimeMillis();
        boot();
        System.err.printf("[vibefish] Forge %s loaded in %d ms%n", BuildInfo.getVersionString(), System.currentTimeMillis() - t0);

        while (profiles.size() < deckArgs.size()) {
            profiles.add("");
        }
        List<String> available = AiProfileUtil.getAvailableProfiles();
        for (String pr : profiles) {
            if (!pr.isEmpty() && !available.contains(pr)) {
                System.err.println("[vibefish] unknown AI profile " + pr + "; available: " + available);
                return 2;
            }
        }
        boolean mcAvailable = mcMode.equals("off") || hasMonteCarloSwitch();
        if (!mcAvailable) {
            System.err.println("[vibefish] this Forge build has no Flat Monte Carlo switch; --mc " + mcMode + " is ignored and the heuristic AI plays");
        }

        GameRules rules = new GameRules(GameType.Commander);
        rules.setAppliedVariants(EnumSet.of(GameType.Commander));
        rules.setSimTimeout(clock);

        List<RegisteredPlayer> seats = new ArrayList<>();
        List<Map<String, Object>> deckInfos = new ArrayList<>();
        List<String> roleLines = new ArrayList<>();
        List<String> comboLines = new ArrayList<>();
        List<String> pairLines = new ArrayList<>();
        for (int i = 0; i < deckArgs.size(); i++) {
            String spec = deckArgs.get(i);
            int eq = spec.indexOf('=');
            String id = eq > 0 ? spec.substring(0, eq) : slug(spec);
            String path = eq > 0 ? spec.substring(eq + 1) : spec;
            File f = resolve(path, deckDir);
            Deck deck = f.isFile() ? DeckSerializer.fromFile(f) : null;
            if (deck == null) {
                System.err.println("[vibefish] could not load deck " + f);
                return 2;
            }
            String profile = profiles.size() > i ? profiles.get(i) : "";
            RegisteredPlayer rp = RegisteredPlayer.forCommander(deck);
            Playbook playbook = null;
            Map<String, Object> playbookInfo = null;
            if (playbookFiles.containsKey(id)) {
                File pf = resolve(playbookFiles.get(id), null);
                try {
                    playbook = Playbook.fromDeckFile(JsonParser.parseString(Files.readString(pf.toPath())).getAsJsonObject());
                } catch (IllegalArgumentException e) {
                    System.err.println("[vibefish] " + pf + ": " + e.getMessage());
                    return 2;
                }
                if (playbook == null) {
                    System.err.println("[vibefish] " + pf + " has no playbook object");
                    return 2;
                }
                if (playbook.cast != null) {
                    // A misspelt card name would switch a rule off without a word; stop instead.
                    List<String> inDeck = new ArrayList<>();
                    for (Map.Entry<PaperCard, Integer> e : deck.getMain()) {
                        inDeck.add(e.getKey().getName());
                    }
                    for (PaperCard pc : deck.getCommanders()) {
                        inDeck.add(pc.getName());
                    }
                    List<String> unknown = new ArrayList<>();
                    for (String name : playbook.cast.namedCards()) {
                        if (name.endsWith(" Token")) {
                            continue;                   // a token a rule aims at or counts: Forge names them "<Name> Token"
                        }
                        if (!inDeck.contains(name) && !unknown.contains(name)) {
                            unknown.add(name);
                        }
                    }
                    if (!unknown.isEmpty()) {
                        System.err.println("[vibefish] " + pf + ": the cast rules name cards that are not in " + f.getName() + ": " + unknown);
                        return 2;
                    }
                }
                VibefishLobbyPlayer lp = new VibefishLobbyPlayer(id, null, playbook);
                lp.setAiProfile(profile.isEmpty() ? "Default" : profile);
                lp.setAvatarIndex(i);
                lp.setSleeveIndex(0);
                rp.setPlayer(lp);
                playbookInfo = obj("file", pf.getName(), "version", playbook.version, "attack", playbook.attack == null ? null
                        : obj("policy", playbook.attack.policy, "target", playbook.attack.target, "min_attackers", playbook.attack.minAttackers,
                              "safety_margin", playbook.attack.safetyMargin, "max_reserve", playbook.attack.maxReserve, "spread", playbook.attack.spread),
                        "mulligan", playbook.mulligan == null ? null
                        : obj("min_lands", playbook.mulligan.minLands, "max_lands", playbook.mulligan.maxLands, "max_mulligans", playbook.mulligan.maxMulligans),
                        "cast", playbook.cast == null ? null : playbook.cast.source);
                System.err.printf("[vibefish] playbook for %s: %s%n", id, playbook.describe());
            } else {
                rp.setPlayer(GamePlayerUtil.createAiPlayer(id, i, profile));
            }
            seats.add(rp);

            List<String> commanders = new ArrayList<>();
            for (PaperCard pc : deck.getCommanders()) {
                commanders.add(pc.getName());
            }
            List<Map<String, Object>> cards = new ArrayList<>();
            for (Map.Entry<PaperCard, Integer> e : deck.getMain()) {
                cards.add(cardInfo(e.getKey(), e.getValue()));
            }
            List<Map<String, Object>> commanderCards = new ArrayList<>();
            for (PaperCard pc : deck.getCommanders()) {
                commanderCards.add(cardInfo(pc, 1));
            }
            Map<String, Object> info = obj("seat", i, "id", id, "file", f.getName(), "name", deck.getName(),
                    "commanders", commanders, "profile", profile.isEmpty() ? "Default" : profile,
                    "main_count", deck.getMain().countAll(), "commander_cards", commanderCards, "cards", cards);
            if (playbookInfo != null) {
                info.put("playbook", playbookInfo);
            }
            if (dataFiles.containsKey(id)) {
                File df = resolve(dataFiles.get(id), null);
                JsonObject data = effectiveData(JsonParser.parseString(Files.readString(df.toPath())).getAsJsonObject());
                List<String> keyCards = strings(data.get("key_cards"));
                boolean keyed = applyKeyCards(deck, keyCards);
                int r0 = roleLines.size(), c0 = comboLines.size(), p0 = pairLines.size();
                dataLines(data, roleLines, comboLines, pairLines);
                info.put("data", obj("file", df.getName(), "key_cards", keyed ? keyCards : new ArrayList<String>(),
                        "key_cards_applied", keyed, "roles", roleLines.size() - r0, "combos", comboLines.size() - c0,
                        "pairs", pairLines.size() - p0, "deck_plan", data.has("deck_plan") ? data.get("deck_plan").getAsString() : "auto"));
                System.err.printf("[vibefish] data for %s: %d key cards%s, +%d role lines, +%d combos, +%d pairs%n", id, keyCards.size(),
                        keyed ? "" : " (this build has no Deck.addKeyCard; not applied)", roleLines.size() - r0, comboLines.size() - c0, pairLines.size() - p0);
            }
            deckInfos.add(info);
        }
        Map<String, Object> aiLists = null;
        if (!roleLines.isEmpty() || !comboLines.isEmpty() || !pairLines.isEmpty()) {
            boolean ok = configureAiLists(roleLines, comboLines, pairLines);
            aiLists = obj("applied", ok, "roles", roleLines.size(), "combos", comboLines.size(), "pairs", pairLines.size());
        }

        Map<String, Object> run = obj(
                "vibefish", VERSION,
                "forge_version", forgeVersion,
                "forge_build", BuildInfo.getVersionString(),
                "format", "Commander",
                "seed_base", seedBase,
                "clock_s", clock,
                "turn_cap", turnCap,
                "mc", mcMode,
                "mc_available", mcAvailable,
                "rotate_profiles", rotateProfiles,
                "ai_lists", aiLists,
                "games_requested", games,
                "started", Instant.now().toString(),
                "decks", deckInfos,
                "games", new ArrayList<Object>());
        @SuppressWarnings("unchecked")
        List<Object> gameList = (List<Object>) run.get("games");
        Path runJson = out.resolve("run.json");
        if (start > 1 && Files.isRegularFile(runJson)) {
            // Resuming after a timeout exit: keep the games already recorded, as JSON trees so numbers survive.
            JsonElement prev = JsonParser.parseString(Files.readString(runJson));
            if (prev.isJsonObject() && prev.getAsJsonObject().get("games") != null
                    && prev.getAsJsonObject().get("games").isJsonArray()) {
                for (JsonElement g : prev.getAsJsonObject().getAsJsonArray("games")) {
                    if (g.isJsonObject()) {
                        JsonObject go = g.getAsJsonObject();
                        if (go.get("index") != null && go.get("index").getAsInt() < start) {
                            gameList.add(go);
                        }
                    }
                }
            }
        }

        for (int g = start; g <= games; g++) {
            long seed = seedBase + g;
            String eventsName = String.format("games/game-%03d.events.jsonl", g);
            Path evPath = out.resolve(eventsName);
            // Profile per seat for this game: the list as given, shifted by one seat per game when rotating,
            // so that over any block of N games every deck has played every profile equally.
            List<String> gameProfiles = new ArrayList<>();
            for (int i = 0; i < seats.size(); i++) {
                String pr = profiles.get(rotateProfiles ? Math.floorMod(i - (g - 1), seats.size()) : i);
                gameProfiles.add(pr.isEmpty() ? "Default" : pr);
                if (seats.get(i).getPlayer() instanceof LobbyPlayerAi lp) {
                    lp.setAiProfile(pr);
                }
            }
            MyRandom.setRandom(new Random(seed));
            PlaybookController.resetStats();
            Match match = new Match(rules, seats, "Vibefish");
            Game game = match.createGame();
            game.setNoGUIUser();
            applyMonteCarlo(game, mcMode);

            Map<Integer, Integer> seatByPlayerId = new HashMap<>();
            for (Player p : game.getRegisteredPlayers()) {
                seatByPlayerId.put(p.getView().getId(), seats.indexOf(p.getRegisteredPlayer()));
            }

            String runReason;
            long ms;
            JsonGameLogger logger;
            try (Writer w = Files.newBufferedWriter(evPath, StandardCharsets.UTF_8)) {
                logger = new JsonGameLogger(game, w, GSON, seatByPlayerId, turnCap);
                logger.emit(obj("e", "meta", "game", g, "seed", seed, "vibefish", VERSION,
                        "forge_version", forgeVersion, "turn_cap", turnCap, "clock_s", clock, "mc", mcMode,
                        "profiles", gameProfiles));
                game.subscribeToEvents(logger);
                System.err.printf("[vibefish] game %d/%d seed %d ...%n", g, games, seed);
                long g0 = System.currentTimeMillis();
                runReason = runWithTimeout(() -> match.startGame(game), clock, game);
                ms = System.currentTimeMillis() - g0;

                GameOutcome oc = game.getOutcome();
                String endReason = logger.capReason() != null ? logger.capReason()
                        : runReason != null ? runReason
                        : oc == null ? "Unknown" : oc.getWinCondition().name();
                // A capped or timed-out game is a draw whatever Forge recorded: setGameOver(Draw) marks every
                // survivor as a winner.
                boolean forcedDraw = logger.capReason() != null || runReason != null;
                Integer winner = null;
                if (!forcedDraw && oc != null && !oc.isDraw() && oc.getWinningPlayer() != null) {
                    int w2 = seats.indexOf(oc.getWinningPlayer());
                    winner = w2 >= 0 ? w2 : null;
                }
                List<Map<String, Object>> players = new ArrayList<>();
                for (Player p : game.getRegisteredPlayers()) {
                    int seat = seats.indexOf(p.getRegisteredPlayer());
                    PlayerOutcome po = p.getOutcome();
                    players.add(obj(
                            "seat", seat,
                            "profile", gameProfiles.get(seat),
                            "won", !forcedDraw && po != null && po.hasWon(),
                            "lost", p.hasLost(),
                            "reason", p.hasLost() && po != null && po.lossState != null ? po.lossState.name() : (forcedDraw ? "Draw" : null),
                            "turn_lost", logger.turnLost(seat),
                            "life", p.getLife(),
                            "poison", p.getPoisonCounters(),
                            "mulligans", p.getStats().getMulliganCount(),
                            "turns_played", p.getTurn()));
                }
                int turns = oc != null ? oc.getLastTurnNumber() : logger.turn();
                Map<String, Object> end = obj("e", "game_end", "t", turns, "winner", winner, "reason", endReason,
                        "duration_ms", ms, "players", players, "events_logged", logger.eventCount(),
                        "logger_errors", logger.errorCount());
                logger.emit(end);

                Map<String, Object> summary = obj("index", g, "seed", seed, "events", eventsName,
                        "first_seat", logger.firstSeat(), "turns", turns, "winner", winner, "reason", endReason,
                        "duration_ms", ms, "profiles", gameProfiles, "players", players);
                String mcStats = monteCarloStats(mcMode);
                if (mcStats != null) {
                    summary.put("mc_stats", mcStats);
                }
                if (!playbookFiles.isEmpty()) {
                    summary.put("playbook_stats", PlaybookController.statsSnapshot());
                }
                gameList.add(summary);
                System.err.printf("[vibefish] game %d done: %s, turn %d, winner %s, %d s%n", g, endReason, turns,
                        winner == null ? "none" : deckInfos.get(winner).get("id"), ms / 1000);
            }
            run.put("updated", Instant.now().toString());
            Files.writeString(runJson, GSON_PRETTY.toJson(run));

            if ("Timeout".equals(runReason)) {
                System.err.printf("[vibefish] game %d hit the %d s clock; exiting so the stuck game thread cannot affect later games. Resume with --start %d%n",
                        g, clock, g + 1);
                return EXIT_TIMEOUT;
            }
        }
        System.err.printf("[vibefish] run complete: %d game(s) recorded in %s%n", gameList.size(), out);
        return 0;
    }

    /** Whether this Forge build has the Flat Monte Carlo switch on Game (2.0.16 snapshots and later). */
    /** The deck data file's `curated` block laid over its `generated` block, key by key (runner/deckdata.py). */
    static JsonObject effectiveData(JsonObject file) {
        JsonObject out = new JsonObject();
        for (String block : new String[] {"generated", "curated"}) {
            if (file.has(block) && file.get(block).isJsonObject()) {
                for (Map.Entry<String, JsonElement> e : file.getAsJsonObject(block).entrySet()) {
                    if (!"notes".equals(e.getKey())) {
                        out.add(e.getKey(), e.getValue());
                    }
                }
            }
        }
        return out;
    }

    static List<String> strings(JsonElement el) {
        List<String> out = new ArrayList<>();
        if (el != null && el.isJsonArray()) {
            for (JsonElement x : el.getAsJsonArray()) {
                if (x.isJsonPrimitive()) {
                    out.add(x.getAsString());
                }
            }
        }
        return out;
    }

    /** Lines for Forge's ai-card-roles.txt, ai-combos.txt and ai-commander-combos.txt from the data file's roles, combos and pairs. */
    static void dataLines(JsonObject data, List<String> roles, List<String> combos, List<String> pairs) {
        if (data.has("roles") && data.get("roles").isJsonObject()) {
            for (Map.Entry<String, JsonElement> e : data.getAsJsonObject("roles").entrySet()) {
                List<String> names = strings(e.getValue());
                if (!names.isEmpty()) {
                    roles.add(e.getKey() + " | " + String.join(" | ", names));
                }
            }
        }
        if (data.has("combos") && data.get("combos").isJsonArray()) {
            for (JsonElement el : data.getAsJsonArray("combos")) {
                JsonObject c = el.getAsJsonObject();
                List<String> slots = new ArrayList<>();
                if (c.has("slots")) {
                    for (JsonElement slot : c.getAsJsonArray("slots")) {
                        slots.add(String.join(" / ", strings(slot)));
                    }
                }
                if (slots.size() >= 2) {
                    combos.add((c.has("kind") ? c.get("kind").getAsString() : "win") + " | " + c.get("name").getAsString() + " | " + String.join(" | ", slots));
                }
            }
        }
        if (data.has("pairs") && data.get("pairs").isJsonArray()) {
            for (JsonElement el : data.getAsJsonArray("pairs")) {
                List<String> cards = strings(el.getAsJsonObject().get("cards"));
                if (cards.size() == 2) {
                    pairs.add("early_game | " + cards.get(0) + " | " + cards.get(1));
                }
            }
        }
    }

    /** Forge deck metadata KeyCards (tutor targets first, protected from discard); by reflection so 2.0.15 still compiles. */
    static boolean applyKeyCards(Deck deck, List<String> names) {
        try {
            java.lang.reflect.Method m = Deck.class.getMethod("addKeyCard", String.class);
            for (String n : names) {
                m.invoke(deck, n);
            }
            return true;
        } catch (ReflectiveOperationException | RuntimeException e) {
            return false;
        }
    }

    static List<String> readLines(String path) {
        try {
            return new ArrayList<>(Files.readAllLines(Paths.get(path), StandardCharsets.UTF_8));
        } catch (IOException | RuntimeException e) {
            return new ArrayList<>();
        }
    }

    static List<String> plus(List<String> a, List<String> b) {
        List<String> out = new ArrayList<>(a);
        out.addAll(b);
        return out;
    }

    /**
     * Hands Forge's AI its shipped list files plus the seats' data lines, the way FModel configures them at boot
     * (AiCardLists for card roles and Commander pairs, ComboCatalog for ai-combos), and forgets cached deck plans so
     * the new lines are read for this game. 2.0.16+ builds only; reflection keeps the harness compiling on 2.0.15.
     */
    static boolean configureAiLists(List<String> roles, List<String> combos, List<String> pairs) {
        try {
            Class<?> fc = Class.forName("forge.localinstance.properties.ForgeConstants");
            String rolesFile = (String) fc.getField("AI_CARD_ROLES_FILE").get(null);
            String bracketFile = (String) fc.getField("COMMANDER_BRACKET_COMBOS_FILE").get(null);
            String cmdFile = (String) fc.getField("AI_COMMANDER_COMBOS_FILE").get(null);
            String combosFile = (String) fc.getField("AI_COMBOS_FILE").get(null);
            Supplier<List<String>> rolesSup = () -> plus(readLines(rolesFile), roles);
            Supplier<List<String>> bracketSup = () -> readLines(bracketFile);
            Supplier<List<String>> cmdSup = () -> plus(readLines(cmdFile), pairs);
            Supplier<List<String>> combosSup = () -> plus(readLines(combosFile), combos);
            Class<?> lists = Class.forName("forge.ai.simulation.AiCardLists");
            lists.getMethod("configure", Supplier.class, Supplier[].class).invoke(null, rolesSup, (Object) new Supplier[] {bracketSup, cmdSup});
            Class<?> cat = Class.forName("forge.ai.simulation.ComboCatalog");
            cat.getMethod("configure", Supplier.class).invoke(null, combosSup);
            try {
                Class<?> dp = Class.forName("forge.ai.simulation.DeckPlan");
                java.lang.reflect.Field f = dp.getDeclaredField("KNOWN");
                f.setAccessible(true);
                ((Map<?, ?>) f.get(null)).clear();
            } catch (ReflectiveOperationException | RuntimeException ignore) {
                // older builds cache nothing here
            }
            System.err.printf("[vibefish] AI lists configured: +%d role lines, +%d combos, +%d pairs on top of Forge's own%n", roles.size(), combos.size(), pairs.size());
            return true;
        } catch (ReflectiveOperationException | RuntimeException e) {
            System.err.println("[vibefish] this Forge build cannot take AI list data (" + e.getClass().getSimpleName() + "); key cards only");
            return false;
        }
    }

    static boolean hasMonteCarloSwitch() {
        try {
            Game.class.getField("AI_FLAT_MONTE_CARLO");
            return true;
        } catch (NoSuchFieldException e) {
            return false;
        }
    }

    /**
     * Switches Forge's Flat Monte Carlo AI on for this game. Sim mode's own -mc flag does the same; the fields
     * are reached by reflection so the harness still compiles against 2.0.15, which has none of them. A seat
     * whose profile says FLAT_MC_ENABLED=false keeps the heuristic AI regardless.
     */
    static void applyMonteCarlo(Game game, String mode) {
        if ("off".equals(mode)) {
            return;
        }
        try {
            Game.class.getField("AI_FLAT_MONTE_CARLO").setBoolean(game, true);
            if ("max".equals(mode)) {
                Game.class.getField("AI_FLAT_MONTE_CARLO_MAX").setBoolean(game, true);
            } else if ("lite".equals(mode)) {
                Game.class.getField("AI_FLAT_MONTE_CARLO_LITE").setBoolean(game, true);
            }
        } catch (NoSuchFieldException | IllegalAccessException e) {
            // reported once up front by hasMonteCarloSwitch()
        }
    }

    /**
     * Forge's own Monte Carlo statistics for the game just played (decision counts, rollout time, cards that
     * could not be simulated), as the text FlatMonteCarloStats.summary() gives, then reset for the next game.
     * Null when Monte Carlo is off or the build has no such class (2.0.15).
     */
    static String monteCarloStats(String mode) {
        if ("off".equals(mode)) {
            return null;
        }
        try {
            Class<?> c = Class.forName("forge.ai.simulation.FlatMonteCarloStats");
            Object out = c.getMethod("summary").invoke(null);
            c.getMethod("reset").invoke(null);
            return out == null ? null : out.toString();
        } catch (ReflectiveOperationException | RuntimeException e) {
            return null;
        }
    }

    /** Runs the game on its own thread; after the clock expires the game is declared a draw. */
    static String runWithTimeout(Runnable task, int clockSeconds, Game game) {
        ExecutorService ex = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "vibefish-game");
            t.setDaemon(true);
            return t;
        });
        Future<?> f = ex.submit(task);
        try {
            f.get(clockSeconds, TimeUnit.SECONDS);
            return null;
        } catch (TimeoutException e) {
            f.cancel(true);
            if (!game.isGameOver()) {
                game.setGameOver(GameEndReason.Draw);
            }
            return "Timeout";
        } catch (ExecutionException e) {
            Throwable c = e.getCause() != null ? e.getCause() : e;
            System.err.println("[vibefish] game thread failed: " + c);
            c.printStackTrace();
            if (!game.isGameOver()) {
                game.setGameOver(GameEndReason.Draw);
            }
            return "Exception";
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return "Interrupted";
        } finally {
            ex.shutdownNow();
        }
    }

    static Map<String, Object> cardInfo(PaperCard pc, int count) {
        String type = null;
        Integer cmc = null;
        boolean land = false;
        if (pc.getRules() != null) {
            type = pc.getRules().getType() != null ? pc.getRules().getType().toString() : null;
            land = pc.getRules().getType() != null && pc.getRules().getType().isLand();
            cmc = pc.getRules().getManaCost() != null ? pc.getRules().getManaCost().getCMC() : null;
        }
        return obj("name", pc.getName(), "count", count, "type", type, "cmc", cmc, "land", land);
    }

    static String slug(String path) {
        String n = new File(path).getName();
        int dot = n.lastIndexOf('.');
        if (dot > 0) {
            n = n.substring(0, dot);
        }
        return n.toLowerCase().replaceAll("\\[[^\\]]*\\]", "").trim().replaceAll("[^a-z0-9]+", "-").replaceAll("(^-|-$)", "");
    }

    static void writeJson(Path p, Object o) throws IOException {
        Files.writeString(p, GSON_PRETTY.toJson(o));
    }
}
