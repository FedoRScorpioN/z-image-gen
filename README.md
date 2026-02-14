# Z-Image Generator

**Автоматический генератор изображений для Windows с 4GB VRAM**

## Требования

- **Windows 10/11**
- **NVIDIA GPU** с 4GB+ видеопамяти (RTX 3050 и выше)
- **Python 3.10+** (установится автоматически если нет)
- **~5 GB** свободного места на диске

---

## Установка

### Шаг 1: Скачать

Нажми зелёную кнопку **Code** → **Download ZIP** и распакуй архив.

### Шаг 2: Проверить систему (опционально)

Дважды кликни **`check_system.bat`** чтобы проверить требования.

### Шаг 3: Установить

Дважды кликни **`install.bat`**

Скрипт автоматически:
- Проверит Python (установит если нет)
- Проверит NVIDIA драйвер
- Создаст виртуальное окружение
- Установит все зависимости
- Скачает модель (~3.7 GB)
- Создаст ярлык на рабочем столе

---

## Использование

### Быстрая генерация

Открой командную строку в папке и введи:

```cmd
run.bat "красивый закат над горами"
```

Или используй полный путь:

```cmd
"%LOCALAPPDATA%\z-image-gen\run.bat" "киберпанк город ночью"
```

### Интерактивный режим

```cmd
run.bat --interactive
```

Вводи промпты один за другим, картинки сохраняются в Downloads.

### Параметры

```cmd
run.bat "промпт" --width 1024 --height 576
run.bat "промпт" --seed 42
run.bat "промпт" -o C:\MyImages\output.png
```

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| `-w, --width` | 768 | Ширина |
| `-H, --height` | 512 | Высота |
| `-s, --steps` | 4 | Шаги генерации |
| `--seed` | случайный | Seed для повторяемости |
| `-o` | Downloads | Путь сохранения |
| `-i` | - | Интерактивный режим |

---

## Примеры промптов

```
"beautiful sunset over mountains, digital art"
"cyberpunk city at night with neon lights"
"cute cat sitting on a windowsill"
"fantasy forest with magical glowing mushrooms"
"portrait of a woman, cinematic lighting"
"space station orbiting Earth, detailed"
```

---

## Решение проблем

### "Python not found"
Установи Python с https://www.python.org/downloads/
Не забудь галочку **"Add Python to PATH"**

### "NVIDIA GPU not detected"
Установи драйверы: https://www.nvidia.com/Download/index.aspx

### "CUDA not available"
CUDA установится автоматически с PyTorch.
Если нет - установи CUDA Toolkit 12.x

### "Недостаточно видеопамяти"
- Убедись что модель Q4_0
- Закрой другие приложения с GPU
- Уменьши размер: `--width 512 --height 288`

### Медленная генерация
Первая генерация медленная (загрузка модели). Следующие быстрее.

---

## Файлы

| Файл | Назначение |
|------|------------|
| `install.bat` | Установка всего |
| `run.bat` | Запуск генерации |
| `check_system.bat` | Проверка системы |
| `uninstall.bat` | Удаление |

---

## Где сохраняются картинки?

По умолчанию: **Папка Downloads** (Загрузки)

Можно указать свой путь: `run.bat "prompt" -o C:\output.png`

---

## Удаление

Запусти `uninstall.bat` или удали папку:
```
%LOCALAPPDATA%\z-image-gen
```

---

## Лицензия

MIT License

---

## Благодарности

- [Tongyi-MAI/Z-Image](https://github.com/Tongyi-MAI/Z-Image) - модель Z-Image
- [leejet/stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) - C++ реализация
