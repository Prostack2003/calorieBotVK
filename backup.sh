#!/bin/bash
BACKUP_DIR="/home/backups/calorieBot"
mkdir -p $BACKUP_DIR
cp /home/container/calorieBot/kbju_bot.db $BACKUP_DIR/kbju_bot.db.$(date +%Y%m%d_%H%M%S)
# Хранить только последние 7 бэкапов
find $BACKUP_DIR -name "kbju_bot.db.*" -mtime +7 -delete