#!/usr/bin/env python3
"""
OpenTrader DOM - point d'entrée principal.

Lance l'application Qt, initialise le bus d'événements, les managers
(Order/Position/Risk), le flux de marché (mock ou réel) et la fenêtre
principale avec tous les docks par défaut.
"""
import sys
import signal

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from Core.EventBus import EventBus
from Core.Settings import Settings
from Core.MarketData import MarketDataFeed
from Core.OrderManager import OrderManager
from Core.PositionManager import PositionManager
from Core.RiskManager import RiskManager

from Brokers.SimBroker import SimBroker
from Bots.BotManager import BotManager
from Addons.AddonManager import AddonManager

from GUI.MainWindow import MainWindow
from GUI.Theme import DARK_THEME


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OpenTrader DOM")
    app.setStyleSheet(DARK_THEME)

    # Autoriser Ctrl+C dans le terminal pour fermer proprement l'app Qt
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # --- Coeur applicatif ---------------------------------------------
    bus = EventBus()
    settings = Settings()

    broker = SimBroker(bus)  # remplaçable par Rithmic/CQG/IB/Binance
    market_data = MarketDataFeed(bus, symbol=settings.get("default_symbol", "ESU6"))
    order_manager = OrderManager(bus, broker)
    position_manager = PositionManager(bus)
    risk_manager = RiskManager(bus, order_manager, settings)

    bot_manager = BotManager(bus, order_manager, position_manager)
    addon_manager = AddonManager(bus)

    # --- Interface graphique -------------------------------------------
    window = MainWindow(
        bus=bus,
        settings=settings,
        order_manager=order_manager,
        position_manager=position_manager,
        risk_manager=risk_manager,
        bot_manager=bot_manager,
        addon_manager=addon_manager,
    )
    window.resize(1600, 950)
    window.show()

    market_data.start()

    exit_code = app.exec()
    market_data.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
