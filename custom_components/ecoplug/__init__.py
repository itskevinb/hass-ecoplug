"""EcoPlug protocol integration for Home Assistant.

Supports WiOn, Workchoice, Woods, KAB, and other rebrands of the original
EcoPlug ESP8266-based Wi-Fi outlet. Discovery is local UDP broadcast on the
LAN; control is local UDP commands. No cloud, no app required after the
initial Wi-Fi onboarding.
"""

DOMAIN = "ecoplug"
