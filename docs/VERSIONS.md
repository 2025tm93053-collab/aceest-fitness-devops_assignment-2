# Version history and release strategy

## Milestones

| Tag | Git commits | What the application can do | Tests |
|---|---|---|---|
| `v1.0.0` | core app + tests | Client create/edit/delete/search, programme catalogue (FL 3/5 day, MG PPL, Beginner), calorie estimate, membership status, dashboard, `/health`, `/version` | 31 |
| `v2.0.0` | tracking + tests | Weekly adherence, workouts with exercises (sets/reps/weight), body metrics (weight/waist/body fat), BMI, inline SVG charts | 51 |
| `v3.0.0` | auth/reports + tests | Login, Admin/Trainer roles, CSRF, hashed passwords, CSV export, PDF report, programme generator, `SHADOW_MODE` | 77 |

These follow the Tkinter evolution: v1.x/2.0.x -> v1.0.0 core; 2.2.x -> v2.0.0 tracking/metrics; 3.x -> v3.0.0 login/roles/reports.

## Honest provenance

The Flask application was written and validated as one codebase first. The v1.0.0 and v2.0.0
snapshots were then produced by `tools/build_version_history.py`, which **removes** later features
from the finished tree. Each snapshot was tested and linted on its own (31 / 51 / 77 passing tests)
**before** it was committed, and every commit carries the real date it was made, not an earlier one.
Anyone can regenerate the snapshots:

```powershell
python tools\build_version_history.py <path-to-v3.0.0-checkout> <empty-output-folder>
```

Commits made after `v3.0.0` (Docker, Jenkins, SonarQube, docs) are infrastructure work and do not
change application behaviour, so they carry no new application tag.

## Tag -> Docker image mapping

`Jenkinsfile` derives the version with `git describe --tags --always` and removes the leading `v`:

| Git state | Image tag |
|---|---|
| exactly on tag `v3.0.0` | `<user>/aceest-fitness:3.0.0` (+ `latest` on main) |
| 4 commits after `v3.0.0` | `<user>/aceest-fitness:3.0.0-4-g1a2b3c4` |

The version is baked in (`APP_VERSION`) and visible at `GET /version`, in the page footer and in the
Jenkins build name, so a running pod can always be traced back to a commit.

## Day-to-day workflow

```powershell
git checkout -b feature/short-name        # branch per change
# ...edit, run tests...
git commit -m "feat: ..."                 # feat / fix / test / ci / docs / chore prefixes
git checkout main; git merge --no-ff feature/short-name
git tag -a v3.1.0 -m "v3.1.0 <what changed>"   # only for real application changes
git push origin main --tags
```
