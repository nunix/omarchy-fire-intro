# omarchy-fire-intro

A boot-intro video for [Omarchy](https://omarchy.org/): a "Hackers"-style
burning OMARCHY wordmark, generated procedurally (no stock footage).

Install:

```
omarchy-intro-install https://github.com/nunix/omarchy-fire-intro.git
```

This clones the repo to `~/.config/omarchy/intros/fire/` and sets it as the
active boot-intro. Switch back to it later with:

```
intro=$(omarchy-intro-switcher); [[ -n $intro ]] && omarchy-intro-set "$intro"
```

or `omarchy-intro-set fire` directly.

## Regenerating intro.mp4

```
uv run --with numpy --with pillow make-intro.py
```

Requires `ffmpeg` and the `JetBrainsMonoNerdFont-Bold` font.

## Pairs well with

Visually, this fits a dark, high-contrast theme with warm accent colors —
e.g. [Infernium Dark](https://omarchythemes.com/themes/infernium-dark). This
is just a suggestion for your own theme; Omarchy boot-intros aren't tied to a
specific theme.
