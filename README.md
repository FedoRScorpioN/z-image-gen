# Z-Image Generator

**Локальный генератор изображений для Windows с 4GB VRAM**

## Требования

- **Windows 10/11**
- **NVIDIA GPU** с 4GB+ видеопамяти (RTX 3050 и выше)
- **Python 3.10+**
- **~6 GB** свободного места на диске

---

## Установка

### Шаг 1: Скачать
Нажми **Code** → **Download ZIP** и распакуй.

### Шаг 2: Установить
```
Дважды кликни install.bat
```

Скрипт скачает:
- sd-cli.exe (~540 MB) - бинарник stable-diffusion.cpp
- Diffusion модель (~3.7 GB)
- VAE (~300 MB)
- LLM энкодер (~2.5 GB)

### Шаг 3: Генерировать
```
run.bat "beautiful sunset over mountains"
```

---

## Использование

```cmd
:: Простая генерация
run.bat "beautiful sunset over mountains"

:: С размером
run.bat "cyberpunk city" --width 1024 --height 576

:: С seed для повторяемости
run.bat "cat in space" --seed 42

:: Проверить установку
run.bat --check

:: Переустановить
run.bat --install
```

---

## Примеры промптов

```
"beautiful sunset over mountains, digital art"
"cyberpunk city at night with neon lights"
"cute cat sitting on a windowsill"
"fantasy forest with glowing mushrooms"
"portrait of a woman, cinematic lighting"
```

---

## Где сохраняются картинки?

**Папка Downloads** (Загрузки)

---

## Решение проблем

### "sd-cli.exe not found"
Переустанови: `run.bat --install`

### "CUDA error"
Обнови драйверы NVIDIA: https://www.nvidia.com/Download/index.aspx

### "Out of memory"
Меньший размер: `--width 512 --height 288`

---

## Файлы

| Файл | Назначение |
|------|------------|
| `install.bat` | Установка |
| `run.bat` | Запуск |
| `generate.py` | Основной скрипт |

---

## Благодарности

- [leejet/stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp)
- [Tongyi-MAI/Z-Image](https://github.com/Tongyi-MAI/Z-Image)
