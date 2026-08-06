# Child boy 3D model (landing)

Place downloaded CGTrader files here:

| File | Required |
|------|----------|
| `young boy character riigged.gltf` | yes |
| `textures.zip` | yes |
| `.blend` / `.fbx` | optional (for Blender edits only) |

Then from `language-tutor/`:

```bash
node scripts/prepare-child-boy-model.mjs
```

Output: `webapp/public/models/child-boy.glb`

Without source files the script uses a TalkingHead fallback until you add the real model.
