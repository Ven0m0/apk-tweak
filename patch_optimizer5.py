import re

with open("rvp/optimizer.py") as f:
  content = f.read()

# For debloat
content = re.sub(
  r"rel_dir = root\[decompiled_dir_len:\]",
  r'rel_dir = root[decompiled_dir_len:].replace(os.sep, "/")',
  content,
)

# For minify
content = re.sub(
  r'minify_patterns = ctx\.options\.get\(\n    "minify_patterns",\n    \[\n      "res/drawable-xxxhdpi/\*",  # Extra high DPI \(often unnecessary\)\n      "res/raw/\*\.mp3",  # Large audio files\n      "res/raw/\*\.wav",\n      "assets/unused/\*",  # Unused assets\n    \],\n  \)',
  r'minify_patterns = ctx.options.get(\n    "minify_patterns",\n    [\n      "res/drawable-xxxhdpi/*",  # Extra high DPI (often unnecessary)\n      "res/raw/*.mp3",  # Large audio files\n      "res/raw/*.wav",\n      "assets/unused/*",  # Unused assets\n    ],\n  )\n\n  if not minify_patterns:\n    ctx.log("optimizer: No minify patterns specified, skipping")\n    return',
  content,
)

with open("rvp/optimizer.py", "w") as f:
  f.write(content)
