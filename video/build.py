#!/usr/bin/env python3
"""Renders every scene of both videos and joins them (ffmpeg concat, no re-encode).
usage: python video/build.py [explainer | demo | all]
Writes video/build/<scene>.mp4 and media/corewar_explainer.mp4, media/corewar_demo.mp4."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import style

def join(scenes, dst):
    lst = os.path.join(style.OUT, os.path.basename(dst) + ".txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.join(style.OUT, name)}.mp4'\n" for name, _, _ in scenes)
    tmp = dst[:-4] + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, dst)
    print("wrote", dst, f"({sum(d for _, _, d in scenes):.1f} s)", flush=True)

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    media = os.path.join(style.ROOT, "media"); os.makedirs(media, exist_ok=True)
    for key, mod, out in (("explainer", "explainer", "corewar_explainer.mp4"), ("demo", "demo", "corewar_demo.mp4")):
        if what not in ("all", key):
            continue
        m = __import__(mod)
        for name, fn, dur in m.SCENES:
            style.render(name, fn, dur); print("rendered", name, flush=True)
        join(m.SCENES, os.path.join(media, out))
