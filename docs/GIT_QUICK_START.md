# Git & GitHub Quick Start Guide

A friendly, beginner-oriented guide to working with this repository.

## 🎯 The Basics

### What is Git?
- **Git** = Version control system (tracks changes to your code)
- **GitHub** = Website that hosts Git repositories
- **Repository (repo)** = A project's folder with all its code and history
- **Commit** = A saved snapshot of your code at a point in time
- **Branch** = A separate line of development
- **Merge** = Combining changes from one branch into another
- **Pull Request (PR)** = Asking to merge your changes into the main code

## 🚀 Quick Start: Your First Contribution

### Step 1: Get the Code

```bash
# Clone the repository to your computer
git clone https://github.com/blairmichaelg/secbrain.git
cd secbrain
```

### Step 2: Create a Branch

```bash
# Always create a new branch for your work
git checkout -b my-feature-name

# Example:
git checkout -b fix-typo-in-readme
```

### Step 3: Make Your Changes

Edit files using your favorite editor, then check what changed:

```bash
git status    # Shows which files changed
git diff      # Shows exact changes
```

### Step 4: Save Your Changes

```bash
# Stage your changes (prepare them for commit)
git add .

# Commit your changes (save them with a message)
git commit -m "Fix typo in README"
```

### Step 5: Push to GitHub

```bash
# First time pushing this branch:
git push -u origin my-feature-name

# After that, just:
git push
```

### Step 6: Create a Pull Request

1. Go to https://github.com/blairmichaelg/secbrain
2. Click "Compare & pull request" (yellow banner)
3. Add a description of what you changed
4. Click "Create pull request"

## 📝 Essential Commands

### Checking Status

```bash
git status            # What's changed?
git log --oneline     # Show recent commits
git branch            # List all branches
```

### Making Changes

```bash
git add filename.py   # Stage a specific file
git add .             # Stage all changes
git commit -m "msg"   # Commit with message
```

### Branching

```bash
git checkout -b new-branch  # Create new branch
git checkout main           # Switch to main
git branch -d old-branch    # Delete a branch
```

### Staying Updated

```bash
git pull origin main  # Get latest changes from main
```

## 🔧 Common Scenarios

### Scenario: "I want to work on something new"

```bash
git checkout main
git pull origin main
git checkout -b my-new-feature
# Make your changes...
git add .
git commit -m "Add new feature"
git push -u origin my-new-feature
```

### Scenario: "I made a mistake in my last commit"

```bash
# Add more changes to the last commit
git add .
git commit --amend -m "Updated commit message"

# Or, undo the last commit but keep the changes
git reset --soft HEAD~1
```

### Scenario: "My branch is out of date with main"

```bash
git checkout main
git pull origin main
git checkout my-feature
git merge main
# Fix any conflicts if they appear
git push
```

### Scenario: "I have uncommitted changes but need to switch branches"

```bash
# Option 1: Commit them
git add .
git commit -m "WIP: work in progress"

# Option 2: Stash them temporarily
git stash
git checkout other-branch
# Later, when you come back:
git checkout my-branch
git stash pop
```

## 🚨 Oh No! I Messed Up!

### "I committed to the wrong branch"

```bash
# Create a new branch from here
git branch correct-branch

# Go back to original branch and reset it
git checkout wrong-branch
git reset --hard origin/wrong-branch

# Continue on correct branch
git checkout correct-branch
```

### "I want to discard all my changes"

```bash
# Discard changes to a specific file
git checkout -- filename.py

# Discard ALL changes (be careful!)
git reset --hard HEAD
```

### "I want to undo my last commit completely"

```bash
# Keep the changes but undo the commit
git reset --soft HEAD~1

# Undo the commit AND discard the changes (careful!)
git reset --hard HEAD~1
```

## 🎓 Understanding Merge Conflicts

### What's a conflict?

When two people change the same line of code, Git can't automatically decide which version to keep.

### How to fix it:

1. **Git marks the conflict in your file:**
```python
<<<<<<< HEAD
your version
=======
their version
>>>>>>> main
```

2. **Edit the file to keep what you want:**
```python
the correct version
```

3. **Tell Git you fixed it:**
```bash
git add filename.py
git commit -m "Resolve merge conflict"
git push
```

## 🎪 GitHub Actions (CI/CD)

### What happens when you push code?

GitHub automatically:
1. ✅ Checks code style (linting)
2. ✅ Runs type checker (currently non-blocking)
3. ✅ Runs tests
4. ✅ Generates coverage report

### Where to see results?

- In your PR, scroll down to the "Checks" section
- Click "Details" on any check to see logs
- ❌ Red X = Something failed
- ✅ Green checkmark = All good!

### What if CI fails?

1. Click "Details" to see what failed
2. Fix the issue in your code
3. Commit and push the fix
4. CI runs automatically again

## 💡 Best Practices

### Commit Messages

✅ **Good:**
```
Fix type error in exploit_agent.py
Add user authentication
Update README with installation instructions
```

❌ **Bad:**
```
fix
updates
asdfasdf
work
```

### When to Commit

- **Commit often** - After each logical change
- **Don't commit broken code** - Test before committing
- **One thing per commit** - Don't mix multiple unrelated changes

### Branch Names

✅ **Good:**
```
feature/add-login
bugfix/fix-crash-on-startup
docs/update-readme
```

❌ **Bad:**
```
mybranch
test
asdf
```

## 🆘 Getting Help

### Read Error Messages

They're usually helpful! For example:
```
error: Your local changes would be overwritten by checkout
```
This means: "You have unsaved changes. Commit or stash them first."

### Common Commands for Help

```bash
git help <command>    # Detailed help
git status            # See current state
git log               # See commit history
```

### Ask for Help

- Open an issue on GitHub
- Ask in your Pull Request
- Check the full [CONTRIBUTING.md](../CONTRIBUTING.md) guide

## 📚 Workflow Summary

```
1. git checkout main
2. git pull origin main
3. git checkout -b my-feature
4. Make changes
5. git add .
6. git commit -m "message"
7. git push -u origin my-feature
8. Create PR on GitHub
9. Address feedback (repeat steps 4-7)
10. Merge on GitHub
```

## 🎉 You're Ready!

Remember:
- **Don't panic** - Git can usually undo mistakes
- **Commit often** - Small commits are easier to manage
- **Ask questions** - No question is too basic
- **Practice makes perfect** - You'll get better with each PR

---

**Next:** Read the full [Contributing Guide](../CONTRIBUTING.md) for more advanced topics!
