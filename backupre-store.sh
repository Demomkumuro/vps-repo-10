#!/bin/bash

# 🗂️ Backup and Restore Script for VPS
# 🔧 Usage: ./backupre-store.sh [backup|restore] [path]

ACTION=$1
PATH_TARGET=$2

echo "🚀 VPS Backup & Restore Tool"
echo "=========================="

if [ "$ACTION" == "backup" ]; then
    echo "📦 Creating backup..."
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf $BACKUP_NAME $PATH_TARGET
    echo "✅ Backup completed: $BACKUP_NAME"
    ls -lh $BACKUP_NAME
elif [ "$ACTION" == "restore" ]; then
    echo "📋 Restoring from backup..."
    tar -xzf $PATH_TARGET
    echo "✅ Restore completed!"
else
    echo "💡 Usage: $0 [backup|restore] [path]"
    echo "📦 Example: $0 backup /home/user/data"
    echo "📋 Example: $0 restore backup_20241215_120000.tar.gz"
fi
