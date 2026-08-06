# Сюда 4 файла с CGTrader

Положите **все скачанные файлы** в эту папку `pack/`:

```
language-tutor/assets/child-boy/pack/
```

| Файл | Нужен |
|------|--------|
| `young boy character riigged.gltf` | ✅ |
| `textures.zip` | ✅ |
| `.blend` | опционально |
| `.fbx` | опционально |

## Сборка

```bash
cd language-tutor
node scripts/prepare-child-boy-model.mjs
```

Результат: `webapp/public/models/child-boy.glb` → лендинг, секция Kids.

## Локально

```bash
cd webapp
npm run dev
```

Откройте http://localhost:3000 → **Kids** → **Слушать демо**.
