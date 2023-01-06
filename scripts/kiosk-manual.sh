#!/bin/bash
set -ex

xset s noblank
xset s off
xset -dpms

unclutter -idle 0.5 -root &

#sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' /home/viseshprasad/.config/chromium/Default/Preferences
#sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' /home/viseshprasad/.config/chromium/Default/Preferences

#/snap/bin/chromium --noerrdialogs --disable-infobars --kiosk http://192.168.68.77:61208/ http://192.168.68.76:61208/ http://192.168.68.53:61208/ http://192.168.68.78:61208/ http://192.168.68.88:8123/a0d7b954_glances/dashboard http://192.168.68.77/admin/index.php &
#/snap/bin/chromium
gnome-terminal --window -- gnome-terminal --tab --command="/opt/glances/venv/bin/glances -c 192.168.68.77:61209" --tab --command="/opt/glances/venv/bin/glances -c 192.168.68.93:61209" --tab --command="/opt/glances/venv/bin/glances -c 192.168.68.100:61209" --tab --command="/opt/glances/venv/bin/glances -c 192.168.68.78:61209" --tab --command="/opt/glances/venv/bin/glances -c 192.168.68.53:61209" --tab --command="/opt/glances/venv/bin/glances -c localhost:61209" --tab --command="/opt/glances/venv/bin/glances -c 192.168.68.91:61209"
while true; do
   xdotool keydown ctrl+Next; xdotool keyup ctrl+Next;
   sleep 15
done
