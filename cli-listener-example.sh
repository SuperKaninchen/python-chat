#!/bin/bash

# requires netcat
# requires expect package - but whoever is using tk could also use tcl :-)

{ listener="listener_"$(mkpasswd -s 0 -C 0 -d 0 -l 8);echo "$listener:LOG ON||nopassword"; sleep 2; } |nc chat.tdyn.de 5000
