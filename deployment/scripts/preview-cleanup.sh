#!/bin/bash

# Preview Cleanup Script
# Shows what files will be removed by the cleanup script WITHOUT actually removing them
# Run this to see what will be cleaned up before running the actual cleanup

set -e

# Configuration
APP_DIR="/opt/dayplanner"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if directory exists
if [ ! -d "$APP_DIR" ]; then
    log_error "Directory $APP_DIR does not exist"
    exit 1
fi

cd "$APP_DIR"

echo "🔍 CLEANUP PREVIEW - Files that will be removed:"
echo "=================================================="

# Count current files
total_files=$(find . -type f | wc -l)
total_size=$(du -sh . | cut -f1)

echo "📊 Current deployment:"
echo "   Files: $total_files"
echo "   Size: $total_size"
echo ""

# Preview files to be removed
files_to_remove=0

echo "📁 Development scripts that will be removed:"
find . -name "deploy_*.sh" -o -name "test_*.sh" -o -name "debug_*.sh" -o -name "cleanup_*.sh" -o -name "deploy-*.sh" -o -name "fix_*.sh" -o -name "apply_*.sh" -o -name "verify_*.py" -o -name "setup.sh" 2>/dev/null | while read file; do
    echo "   🗑️  $file"
    ((files_to_remove++))
done

echo ""
echo "📁 Development directories that will be removed:"
for dir in docs .github .vscode .idea tests __tests__ cypress e2e .devcontainer infrastructure .reports tools scripts; do
    if [ -d "$dir" ]; then
        echo "   🗑️  $dir/ ($(find "$dir" -type f | wc -l) files)"
    fi
done

echo ""
echo "📁 Development configuration files that will be removed:"
for file in .pre-commit-config.yaml .secrets.baseline .editorconfig .eslintrc* .prettierrc* tsconfig.json jest.config.js docker-compose.yml Makefile .gitignore .deployignore; do
    if [ -f "$file" ] || ls $file 1> /dev/null 2>&1; then
        echo "   🗑️  $file"
    fi
done

echo ""
echo "📁 Development data files that will be removed:"
for file in api_test_config.json AUTH_LOGIN.json openapi.json todo.txt times.tsv .env.example; do
    if [ -f "$file" ]; then
        echo "   🗑️  $file"
    fi
done

echo ""
echo "📁 Test report files that will be removed:"
find . -name "api_test_report_*.json" 2>/dev/null | while read file; do
    echo "   🗑️  $file"
done

echo ""
echo "📁 Temporary and backup files that will be removed:"
find . -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.backup" -o -name "*.log" 2>/dev/null | while read file; do
    echo "   🗑️  $file"
done

echo ""
echo "📁 OS generated files that will be removed:"
find . -name ".DS_Store" -o -name "Thumbs.db" -o -name "._*" 2>/dev/null | while read file; do
    echo "   🗑️  $file"
done

echo ""
echo "📁 Python cache files that will be removed:"
find . -name "__pycache__" -type d 2>/dev/null | while read dir; do
    echo "   🗑️  $dir/ ($(find "$dir" -name "*.pyc" | wc -l) .pyc files)"
done

echo ""
echo "✅ FILES THAT WILL BE KEPT (Essential for production):"
echo "=================================================="
echo "   📂 backend/ - FastAPI application"
echo "   📂 frontend/ - Next.js application"
echo "   📂 deployment/nginx/ - Nginx configuration"
echo "   📂 deployment/systemd/ - Service files"
echo "   📂 deployment/scripts/ - Essential deployment scripts"
echo "   📄 .env.production - Production environment"
echo "   📄 requirements.txt - Python dependencies"
echo "   📄 package.json - Node.js dependencies"
echo "   📄 alembic.ini - Database migrations"

echo ""
echo "🎯 ESTIMATED RESULTS AFTER CLEANUP:"
echo "=================================="

# Calculate estimated files to remove (rough estimate)
scripts_count=$(find . -name "deploy_*.sh" -o -name "test_*.sh" -o -name "debug_*.sh" -o -name "cleanup_*.sh" -o -name "deploy-*.sh" -o -name "fix_*.sh" -o -name "apply_*.sh" -o -name "verify_*.py" -o -name "setup.sh" 2>/dev/null | wc -l)
dev_files_count=$(find . -name "api_test_*.json" -o -name "AUTH_LOGIN.json" -o -name "openapi.json" -o -name "todo.txt" -o -name "times.tsv" -o -name ".env.example" 2>/dev/null | wc -l)
temp_files_count=$(find . -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.backup" -o -name "*.log" 2>/dev/null | wc -l)

# Count files in directories to be removed
dev_dirs_files=0
for dir in docs .github .vscode .idea tests __tests__ cypress e2e .devcontainer infrastructure .reports tools scripts; do
    if [ -d "$dir" ]; then
        dir_files=$(find "$dir" -type f 2>/dev/null | wc -l)
        dev_dirs_files=$((dev_dirs_files + dir_files))
    fi
done

estimated_removed=$((scripts_count + dev_files_count + temp_files_count + dev_dirs_files + 10)) # +10 for config files
estimated_remaining=$((total_files - estimated_removed))
estimated_reduction=$(echo "scale=0; ($estimated_removed * 100) / $total_files" | bc -l 2>/dev/null || echo "70")

echo "   📊 Estimated files to remove: ~$estimated_removed"
echo "   📊 Estimated files remaining: ~$estimated_remaining"
echo "   📊 Estimated reduction: ~${estimated_reduction}%"
echo "   💾 Expected size reduction: ~70% (similar to file reduction)"

echo ""
echo "🚀 TO PROCEED WITH CLEANUP:"
echo "=========================="
echo "   sudo /opt/dayplanner/deployment/scripts/cleanup-production.sh"
echo ""
echo "🛡️  SAFETY FEATURES:"
echo "   ✅ Automatic backup will be created before cleanup"
echo "   ✅ Services will be safely stopped and restarted"
echo "   ✅ All operations will be logged"
echo "   ✅ Rollback available if needed"

echo ""
echo "📋 CURRENT FILES IN ROOT DIRECTORY:"
echo "=================================="
ls -la | grep -v "^d" | awk '{print "   " $9 " (" $5 " bytes)"}'
