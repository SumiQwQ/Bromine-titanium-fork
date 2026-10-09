# Bromine (rebrand kit for the Titanium Android browser)

Helium is a gas, Titanium is a solid, Bromine is a liquid.

This kit turns a fork of [jqssun/android-titanium-browser](https://github.com/jqssun/android-titanium-browser)
into "Bromine": new name, new package ID, new launcher icon. It does **not** contain Chromium
or a built APK. You build through your fork's GitHub Actions, as Titanium's README describes.

## Use it

1. Fork Titanium, then unzip this kit so `bromine/` sits at the repo root.
2. Edit `bromine/bromine.conf` and set `BROMINE_PACKAGE` to an ID that is yours.
3. Preview: `bash bromine/scripts/rebrand.sh --dry-run`
4. Apply: `pip install pillow && bash bromine/scripts/rebrand.sh`, then review `git diff`.
5. Add the same step to `.github/workflows/build.yml`, before the step that runs the build:

       - run: pip install pillow && bash bromine/scripts/rebrand.sh

   If launcher icons only appear after patching (they live in the Chromium tree), also run
   `python3 bromine/scripts/make_icons.py apply <path-to-chromium-src>` after the patch step.
6. Follow Titanium's README for signing secrets (`keystore.jks`, `local.properties`).

Optional: copy `ci/rebrand-check.yml` to `.github/workflows/` for a dry-run check on PRs.

## What it does

- Replaces "Titanium" with the name in `bromine.conf` across tracked text files.
  "Titanium Extension" is left alone (separate app by the upstream author).
- Replaces the old package ID with yours.
- Re-renders every `app_icon*.png` / `ic_launcher*.png` at its existing size
  (round, adaptive foreground/background and monochrome variants included).
- Skips README, LICENSE, binaries, submodules and `third_party`. It is safe to re-run.

## Not verified / not done

- **Untested against the real repo.** I could not read Titanium's `patch.sh`, `build.sh` or
  `res/` layout, so I tested on a mock repo. Run `--dry-run` first and check the file list.
- **Package ID change:** installs won't upgrade from Titanium, and Titanium Extension may
  look for Titanium's package ID, so extension integration may not work yet.
- **Theme/colors:** not done. Needs Titanium's `res/` layout.
- **Helium's uBlock fork** ([imputnet/uBlock](https://github.com/imputnet/uBlock)): not bundled yet.
- **Helium onboarding page:** not wired in.
- **Branding:** Titanium was renamed to avoid confusion with desktop Helium. "Bromine" is
  clear of that, but is close to the discontinued "Bromite" browser.
- **Licence:** Titanium is GPL-2.0, so keep your fork GPL-2.0 and keep the credits to
  Titanium, Vanadium and GrapheneOS. Helium is GPL-3.0; don't copy its code in without
  checking compatibility.
