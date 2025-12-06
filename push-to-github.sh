#!/bin/bash
# Script to push to GitHub repository

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== S3 Zipper App - GitHub Push Setup ===${NC}\n"

# Check if git is initialized
if [ ! -d .git ]; then
    echo -e "${YELLOW}Git repository not initialized. Initializing now...${NC}"
    git init
fi

# Get repository name from user
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter the repository name (default: s3-zipper-app): " REPO_NAME
REPO_NAME=${REPO_NAME:-s3-zipper-app}

# Check if origin already exists
if git remote get-url origin > /dev/null 2>&1; then
    echo -e "${YELLOW}Remote 'origin' already exists. Removing it...${NC}"
    git remote remove origin
fi

# Add remote
REMOTE_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
echo -e "${BLUE}Adding remote: ${REMOTE_URL}${NC}"
git remote add origin "$REMOTE_URL"

# Push to GitHub
echo -e "${BLUE}Pushing code to GitHub...${NC}"
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully pushed to GitHub!${NC}"
    echo -e "${GREEN}Repository URL: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}${NC}\n"
else
    echo -e "${YELLOW}Push failed. Please ensure:${NC}"
    echo "1. You have created the repository on GitHub"
    echo "2. You have SSH key or Personal Access Token configured"
    echo "3. Run: git push -u origin main"
    exit 1
fi

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Visit: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo "2. Update repository settings if needed"
echo "3. Share the repository link for review"
