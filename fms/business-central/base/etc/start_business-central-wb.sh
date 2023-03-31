#!/usr/bin/env bash

# Start Wildfly with the given arguments.
echo "Running business-central workbench on JBoss Wildfly..."
exec ./standalone.sh -b $JBOSS_BIND_ADDRESS -c $KIE_SERVER_PROFILE.xml -Dorg.kie.demo=$KIE_DEMO -Dorg.kie.example=$KIE_DEMO -Djava.net.preferIPv4Stack=true -Djava.net.preferIPv4Addresses=true
exit $?
