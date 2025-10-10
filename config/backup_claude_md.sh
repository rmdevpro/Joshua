#!/bin/bash
# Backup CLAUDE.md with timestamp

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp /home/aristotle9/CLAUDE.md /mnt/projects/Joshua/config/CLAUDE.md.versions/CLAUDE.md.$TIMESTAMP

echo "✅ Backed up to: CLAUDE.md.$TIMESTAMP"
echo ""
echo "📋 Don't forget to:"
echo "1. Update CHANGELOG.md"
echo "2. Commit to git: git add config/CLAUDE.md.versions/"
echo "3. Push to remote: git push origin main"
