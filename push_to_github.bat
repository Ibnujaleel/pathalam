@echo off
title Git Branch and Push - Maveli AI
echo ========================================================
echo   CONFIGURING CLEAN GIT BRANCH & PUSHING TO PATHALAM
echo ========================================================
echo.

echo 1. Creating fresh clean orphan branch (purging old commit history)...
git checkout --orphan clean-release 2>nul || git checkout -b clean-release

echo 2. Staging clean project files...
git add .

echo 3. Creating clean root commit...
git commit -m "feat: complete Maveli AI installation software layer (Gemini AI, Malayalam STT, PySerial 30Hz bridge, Web Projector & Pygame HUD)"

echo 4. Renaming branch to 'maveli-ai-full'...
git branch -D maveli-ai-full 2>nul
git branch -m maveli-ai-full

echo 5. Setting remote origin...
git remote remove origin 2>nul
git remote add origin https://github.com/Ibnujaleel/pathalam.git

echo 6. Pushing clean branch 'maveli-ai-full' to GitHub...
git push -u origin maveli-ai-full --force

echo.
echo ========================================================
echo   SUCCESS! Clean branch pushed to:
echo   https://github.com/Ibnujaleel/pathalam/tree/maveli-ai-full
echo ========================================================
pause
