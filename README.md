<a href="https://www.buymeacoffee.com/IntExCZ" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

# CHMI-Alerts
CHMI alert(s) live integration for Home Assistant

# Description
Integrates the most important alert (alert with highest severity) into HA as entity with describing attributes.

# How it works
The Python script downloads full XML alert list from CHMI and parses it (according to given CISORP) into JSON for HA CLI sensor.

# Installation
1. Copy content from repository directory **python_scripts** to **/config/python_scripts** in your HA instance.
2. Create HA command_line sensor (https://www.home-assistant.io/integrations/sensor.command_line/) - example in **configuration_example.yaml**.
3. Edit the command line in sensor configuration (*command: "python3 /config/python_scripts/chmi_alert.py 5309"*) and change the *5309* (CISORP) parameter according to your location - find your location on: https://apl.czso.cz/iSMS/cisdet.jsp?kodcis=65
4. Add a card with sensor to your dashboard - example in **card_example.yaml**.
5. Restart HA and the new configured entity would show up (you can change the update interval by *scan_interval:* parameter).

# Future implementations
Add "secondaryAlert" attribute(s) with information about alert with lower severity.
