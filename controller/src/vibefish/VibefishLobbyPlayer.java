package vibefish;

import java.util.Set;

import forge.ai.AIOption;
import forge.ai.LobbyPlayerAi;
import forge.game.Game;
import forge.game.player.Player;
import forge.game.player.PlayerController;

/** Forge's AI lobby player whose in-game player gets a {@link PlaybookController}; the AI profile and everything else are Forge's. */
public class VibefishLobbyPlayer extends LobbyPlayerAi {

    private final Playbook playbook;
    private final AIOption option;

    public VibefishLobbyPlayer(String name, Set<AIOption> options, Playbook playbook) {
        super(name, options);
        this.playbook = playbook;
        this.option = options != null && !options.isEmpty() ? options.iterator().next() : null;
    }

    private PlaybookController controllerFor(Player p) {
        PlaybookController c = new PlaybookController(p.getGame(), p, this, playbook);
        c.getAi().setUseSimulation(option);
        return c;
    }

    @Override
    public Player createIngamePlayer(Game game, int id) {
        Player p = new Player(getName(), game, id);
        p.setFirstController(controllerFor(p));
        return p;
    }

    @Override
    public PlayerController createMindSlaveController(Player master, Player slave) {
        return controllerFor(slave);
    }
}
