#!/bin/bash
set -e

PORT=$(jq -r '.port // 8888' $OPTIONS_FILE)
TYPE=$(jq -r '.type // "ac"' $OPTIONS_FILE)
LOG_LEVEL=$(jq -r '.log_level | ascii_upcase // "WARNING"' $OPTIONS_FILE)
ESPHOME_PORT=$(jq -r '.esphome_port // 6053' $OPTIONS_FILE)
ESPHOME_WEB_PORT=$(jq -r '.esphome_web_port // 6052' $OPTIONS_FILE)
ESPHOME_NAME=$(jq -r '.esphome_name // ""' $OPTIONS_FILE)
APPS=$(jq -r '.app | length // 0' $OPTIONS_FILE)
LOCAL_IP=$(jq -r 'if (.local_ip) then (.local_ip) else "" end' $OPTIONS_FILE)

mkdir -p $CONFIG_DIR
if [ -z "$(find $CONFIG_DIR -maxdepth 1 -type f -name "config_*.json")" ]; then
  rm -f config_*.json
  for i in $(seq 0 $(($APPS-1))); do
    CODE=$(jq -r '.app['$i'].code' $OPTIONS_FILE)
    USERNAME=$(jq -r '.app['$i'].username' $OPTIONS_FILE)
    PASSWORD=$(jq -r '.app['$i'].password' $OPTIONS_FILE)
    python -m aircon discovery $CODE $USERNAME $PASSWORD
  done
  mv config_*.json $CONFIG_DIR/
fi
configs=
for i in $(find $CONFIG_DIR -maxdepth 1 -type f -name "config_*.json" -exec basename {} \;)
  do configs="$configs --config $CONFIG_DIR/$i --type $TYPE"
done
python -m aircon --log_level $LOG_LEVEL run --port $PORT --esphome_port $ESPHOME_PORT --esphome_web_port $ESPHOME_WEB_PORT --esphome_name "$ESPHOME_NAME" --local_ip "$LOCAL_IP" $configs
