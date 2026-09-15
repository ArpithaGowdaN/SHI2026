# GitHub Setup Guide — FSOC PAT Tracker Team

This walks through every click and command, in order. Do Part 1 yourself
first (you're the repo owner), then send Part 2 to each teammate.

---

## PART 1 — You do this first (repo owner)

### Step 1: Push the skeleton folder structure to `main`

Open a terminal in your project folder (the one with `src/`, `docs/`,
`outputs/`, `datasets/` inside it) and run:

```bash
git add .
git commit -m "Add project skeleton: config, interfaces, module stubs"
git push origin main
```

If this is the very first push to a brand-new repo, use this instead:

```bash
git init
git add .
git commit -m "Initial project skeleton"
git branch -M main
git remote add origin https://github.com/<your-username>/fsoc-pat-tracker.git
git push -u origin main
```

(Replace `<your-username>` and the repo name with your actual GitHub repo URL.)

### Step 2: Add everyone as a collaborator

1. Go to your repo on github.com
2. Click **Settings** (top right of the repo, not your account settings)
3. Click **Collaborators** in the left sidebar
4. Click **Add people**
5. Type each teammate's GitHub username or email, one at a time
6. They'll get an email invite — they must click **Accept** before they can push

### Step 3: Add the CODEOWNERS file

Create a folder called `.github` in your project root (note the dot at the
start — it's a hidden folder), and put a file called `CODEOWNERS` inside it
(no file extension). I've drafted the content for you below — just replace
the `@placeholder-username` parts with your teammates' actual GitHub usernames.

Then:
```bash
git add .github/CODEOWNERS
git commit -m "Add CODEOWNERS for module ownership"
git push origin main
```

### Step 4: Turn on branch protection for `main`

1. Repo → **Settings** → **Branches** (left sidebar)
2. Click **Add branch protection rule** (or **Add rule**)
3. Under "Branch name pattern" type: `main`
4. Check the box: **Require a pull request before merging**
5. Check the box: **Require approvals** (leave it at 1)
6. Click **Create** (or **Save changes**)

This means nobody — including you — can push straight to `main` anymore.
Everyone works on their own branch and opens a Pull Request (PR) to merge in.

### Step 5: Set up the Projects board

1. Repo → click the **Projects** tab (top of the repo, next to Issues)
2. Click **New project**
3. Choose **Board** as the template
4. Name it something like "FSOC Tracker — Module Status"
5. Click **Create**
6. Add one card per module: `simulation.py`, `tracking.py`, `predictor.py`,
   `control.py`, `analytics.py`, `gui.py`, `app.py`, `reporting.py`,
   `benchmark.py`
7. Rename the default columns to: **To Do**, **In Progress**, **In Review**, **Done**
8. Drag each card into **To Do**, and assign the right person to each card
   (click the card → **Assignees** on the right → pick their name)

Now anyone can open the Projects tab and see who owns what and how far along
it is, without asking.

---

## PART 2 — Send this to each teammate

### Step 1: Clone the repo (first time only)

```bash
git clone https://github.com/<your-username>/fsoc-pat-tracker.git
cd fsoc-pat-tracker
```

### Step 2: Create your own branch

Pick a branch name based on your module. Examples:

```bash
git checkout -b feature/tracking-yourname       # EC teammate
git checkout -b feature/predictor-control-yourname   # Electrical B teammate
```

### Step 3: Work normally, commit as you go

```bash
git add src/tracking.py
git commit -m "Implement blob detection in tracking.py"
git push origin feature/tracking-yourname
```

(The branch name after `origin` must match what you created in Step 2.)

### Step 4: Open a Pull Request when ready

1. Go to the repo on github.com — GitHub usually shows a yellow banner
   "Compare & pull request" right after you push a new branch. Click it.
2. If you don't see the banner: click **Pull requests** tab → **New pull request**
   → set base: `main`, compare: your branch name
3. Add a short title (e.g. "Tracking module: blob detection + confidence score")
4. Click **Create pull request**
5. Because of the CODEOWNERS file, the right reviewer gets auto-requested
6. Once approved, click **Merge pull request**

---

## Suggested merge order

Because the files depend on each other through `interfaces.py`, try to merge
roughly in this order so nobody's PR breaks on a missing function:

1. `simulation.py` (Arpitha — mostly a port, should be quick)
2. `tracking.py` (EC)
3. `predictor.py` (Electrical B)
4. `control.py` (Electrical B)
5. `analytics.py` (Arpitha — the new geometry layer)
6. `gui.py` / `app.py` / `reporting.py` / `benchmark.py` (Arpitha — integration, last)

Mention this order in your README or pin it in the Projects board description
so nobody merges into a half-finished interface.
