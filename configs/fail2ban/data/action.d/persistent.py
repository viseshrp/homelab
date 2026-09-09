"""Preserve external bans during shutdown; explicit unbans still execute."""
from fail2ban.server.action import CommandAction

class Action(CommandAction):
    def __init__(self, jail, name, command, skip_restored='false', startup=''):
        super().__init__(jail, name)
        self._configure(command, skip_restored, startup)

    def _configure(self, command, skip_restored='false', startup=''):
        self.timeout = 120
        self.actionstart_on_demand = False
        self.actionstart = command + ' ' + startup if startup else ''
        self.actionstop = ''
        self.actioncheck = ''
        self.actionflush = 'true'
        guard = '[ "<restored>" = "1" ] || ' if str(skip_restored).lower() == 'true' else ''
        self.actionban = guard + command + ' ban <ip>'
        self.actionunban = command + ' unban <ip>'

    def reload(self, command, skip_restored='false', startup=''):
        self._configure(command, skip_restored, startup)
        return super().reload()

    def flush(self):
        # Fail2ban 1.1.0 sets actions.active=False before its shutdown flush.
        # Return False while running so explicit unban-all uses individual unbans.
        if self._jail.actions.active:
            return False
        return super().flush()
