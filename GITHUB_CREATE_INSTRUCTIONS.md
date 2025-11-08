# GitHub Repository Creation Instructions

## Using GitHub MCP Server (Recommended)

If you have the GitHub MCP server configured in Cursor, you can use it to create the repository:

1. **Create Repository via MCP:**
   - Use the `mcp_github_create_repository` tool (or similar based on your MCP server)
   - Repository name: `styletts2-dataset-toolkit`
   - Description: "Complete Windows-optimized workflow for voice cloning with StyleTTS2"
   - Visibility: `public` (or `private` if preferred)
   - Initialize: `false` (we already have files)

2. **After Repository Creation:**
   ```powershell
   cd E:\styletts2-dataset-toolkit
   git remote add origin https://github.com/YOUR_USERNAME/styletts2-dataset-toolkit.git
   git branch -M main
   git push -u origin main
   ```

## Using GitHub CLI (Alternative)

If you have GitHub CLI installed:

```powershell
cd E:\styletts2-dataset-toolkit

# Create repository
gh repo create styletts2-dataset-toolkit --public --description "Complete Windows-optimized workflow for voice cloning with StyleTTS2" --source=. --remote=origin --push
```

## Manual Method

1. **Go to GitHub:** https://github.com/new

2. **Repository Settings:**
   - Repository name: `styletts2-dataset-toolkit`
   - Description: `Complete Windows-optimized workflow for voice cloning with StyleTTS2`
   - Visibility: Public (or Private)
   - **DO NOT** initialize with README, .gitignore, or license (we already have them)

3. **Click "Create repository"**

4. **Link and Push:**
   ```powershell
   cd E:\styletts2-dataset-toolkit
   
   # Make initial commit if not done
   git add .
   git commit -m "Initial commit: StyleTTS2 Dataset Toolkit v1.0"
   
   # Add remote (replace YOUR_USERNAME)
   git remote add origin https://github.com/YOUR_USERNAME/styletts2-dataset-toolkit.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

## Post-Creation Steps

1. **Add Repository Topics:**
   - voice-cloning
   - text-to-speech
   - styletts2
   - demucs
   - stem-separation
   - windows
   - machine-learning
   - gpu
   - pytorch
   - gradio

2. **Update README Links:**
   - Replace `yourusername` with your actual GitHub username in:
     - README.md
     - GITHUB_SETUP.md
     - docs/INSTALLATION.md

3. **Create Initial Release:**
   ```powershell
   git tag -a v1.0.0 -m "Release v1.0.0 - Initial public release"
   git push origin v1.0.0
   ```
   Then create a release on GitHub with release notes from GITHUB_SETUP.md

4. **Enable Features:**
   - ✅ Issues
   - ✅ Discussions
   - ✅ Projects
   - ✅ Releases

