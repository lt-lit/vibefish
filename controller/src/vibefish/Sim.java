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

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import forge.GuiDesktop;
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
 *                      [--seed S] [--clock SEC] [--turn-cap T] [--profile NAME ...] [--start N]
 *                      [--forge-version TAG]
 *   vibefish.Sim check [--deck-dir DIR] [--out FILE] file.dck [file.dck ...]
 * </pre>
 *
 * Relative paths resolve against $VIBEFISH_CWD when set (the launcher cds into the Forge runtime).
 */
public final class Sim {
    public static final String VERSION = "0.1.0";
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
        System.err.println("                         [--clock SEC] [--turn-cap T] [--profile NAME ...] [--start N] [--forge-version TAG]");
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
        if (seedBase == null) {
            seedBase = new SecureRandom().nextInt(1_000_000_000) + 0L;
        }
        Path out = resolve(outDir, null).toPath();
        Files.createDirectories(out.resolve("games"));

        long t0 = System.currentTimeMillis();
        boot();
        System.err.printf("[vibefish] Forge %s loaded in %d ms%n", BuildInfo.getVersionString(), System.currentTimeMillis() - t0);

        GameRules rules = new GameRules(GameType.Commander);
        rules.setAppliedVariants(EnumSet.of(GameType.Commander));
        rules.setSimTimeout(clock);

        List<RegisteredPlayer> seats = new ArrayList<>();
        List<Map<String, Object>> deckInfos = new ArrayList<>();
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
            rp.setPlayer(GamePlayerUtil.createAiPlayer(id, i, profile));
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
            deckInfos.add(obj("seat", i, "id", id, "file", f.getName(), "name", deck.getName(),
                    "commanders", commanders, "profile", profile.isEmpty() ? "Default" : profile,
                    "main_count", deck.getMain().countAll(), "commander_cards", commanderCards, "cards", cards));
        }

        Map<String, Object> run = obj(
                "vibefish", VERSION,
                "forge_version", forgeVersion,
                "forge_build", BuildInfo.getVersionString(),
                "format", "Commander",
                "seed_base", seedBase,
                "clock_s", clock,
                "turn_cap", turnCap,
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
            MyRandom.setRandom(new Random(seed));
            Match match = new Match(rules, seats, "Vibefish");
            Game game = match.createGame();
            game.setNoGUIUser();

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
                        "forge_version", forgeVersion, "turn_cap", turnCap, "clock_s", clock));
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
                        "duration_ms", ms, "players", players);
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
