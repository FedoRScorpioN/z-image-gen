# Z-Image Generator

**Локальный генератор изображений на базе Z-Image-Turbo для Windows**

Оптимизирован для работы на GPU с 4GB видеопамяти (RTX 3050 и аналоги).

---

## Системные требования

| Компонент | Минимум |
|-----------|---------|
| ОС | Windows 10/11 (64-bit) |
| GPU | NVIDIA с CUDA support |
| VRAM | 4 GB минимум (рекомендуется 6+ GB) |
| RAM | 8 GB минимум |
| Диск | ~7 GB свободного места |
| Python | 3.10 или выше |

### Проверка системы

Перед установкой можно проверить совместимость:
```
check_system.bat
```

---

## Быстрая установка

### Шаг 1: Скачать

Нажми **Code** → **Download ZIP** на GitHub странице, затем распакуй архив.

Или через командную строку:
```cmd
curl -L -o z-image-gen.zip https://github.com/FedoRScorpioN/z-image-gen/archive/refs/heads/main.zip
```

### Шаг 2: Запустить установку

Дважды кликни на `install.bat` или запусти из командной строки:
```cmd
install.bat
```

Установка занимает 10-30 минут в зависимости от скорости интернета.

### Шаг 3: Генерировать изображения

```cmd
run.bat "beautiful sunset over mountains"
```

Изображение сохранится в папку **Downloads** (Загрузки).

---

## Что скачивается

| Компонент | Размер | Описание |
|-----------|--------|----------|
| sd-cli.exe | ~0.5 MB | Бинарник stable-diffusion.cpp |
| CUDA DLLs | ~500 MB | CUDA runtime библиотеки |
| Z-Image-Turbo Q4_0 | ~3.5 GB | Diffusion модель (квантованная) |
| VAE (ae.safetensors) | ~320 MB | Variational Autoencoder |
| Qwen3-4B-Instruct | ~2.4 GB | Текстовый энкодер |

**Итого: ~7 GB**

---

## Использование

### Базовая генерация
```cmd
run.bat "beautiful sunset over mountains"
```

### С указанием размера
```cmd
run.bat "cyberpunk city" --width 1024 --height 576
```

### С seed (для повторяемости)
```cmd
run.bat "cat in space" --seed 42
```

### Проверка установки
```cmd
run.bat --check
```

### Переустановка
```cmd
run.bat --install
```

---

## Примеры промптов

```
"beautiful sunset over mountains, golden hour, digital art"
"cyberpunk city at night, neon lights, rain, reflections"
"cute cat sitting on a windowsill, soft sunlight, photorealistic"
"fantasy forest with glowing mushrooms, magical atmosphere"
"portrait of a woman, cinematic lighting, bokeh background"
"underwater scene with colorful coral reef and tropical fish"
"steampunk mechanical dragon, brass and copper, intricate details"
"northern lights over snowy landscape, aurora borealis"
```

---

## Где сохраняются изображения?

По умолчанию: **Папка Downloads (Загрузки)**

Формат имени файла: `zimage_{seed}_{дата_время}.png`

Пример: `zimage_123456_20250115_143022.png`

---

## Решение проблем

### Ошибка: "cudart_12.dll not found" или "cudart64_12.dll not found"

**Причина:** Отсутствуют CUDA runtime библиотеки.

**Решение 1:** Скопировать существующий DLL:
```cmd
copy "%LOCALAPPDATA%\z-image-gen\bin\cudart64_12.dll" "%LOCALAPPDATA%\z-image-gen\bin\cudart_12.dll"
```

**Решение 2:** Скачать CUDA DLLs отдельно:
```cmd
cd %TEMP%
curl -L -o update_cuda.bat https://raw.githubusercontent.com/FedoRScorpioN/z-image-gen/main/update_cuda.bat
update_cuda.bat
```

**Решение 3:** Установить CUDA Toolkit 12.x с сайта NVIDIA:
https://developer.nvidia.com/cuda-downloads

---

### Ошибка: "sd-cli.exe not found"

**Причина:** Не скачался бинарник sd-cli.

**Решение:** Переустановить:
```cmd
run.bat --install
```

---

### Ошибка: "CUDA out of memory" или "Out of VRAM"

**Причина:** Недостаточно видеопамяти для текущего размера.

**Решение 1:** Уменьшить размер изображения:
```cmd
run.bat "prompt" --width 512 --height 288
```

**Решение 2:** Закрыть другие приложения, использующие GPU (браузеры, игры, другие нейросети).

**Решение 3:** Проверить температуру и вентиляторы GPU - перегрев может снижать производительность.

---

### Ошибка: "CUDA error" или "GPU not detected"

**Причина:** Устаревшие драйверы или проблемы с CUDA.

**Решение 1:** Обновить драйверы NVIDIA:
https://www.nvidia.com/Download/index.aspx

**Решение 2:** Проверить, что GPU поддерживает CUDA:
```cmd
nvidia-smi
```
Должна появиться информация о видеокарте.

**Решение 3:** Установить CUDA Toolkit 12.x:
https://developer.nvidia.com/cuda-downloads

---

### Ошибка: "Python not found"

**Причина:** Python не установлен или не добавлен в PATH.

**Решение:**
1. Скачать Python с https://www.python.org/downloads/
2. При установке отметить **"Add Python to PATH"**
3. Перегрузить командную строку

---

### Ошибка: "pip not found" или module errors

**Причина:** Не установлен модуль requests.

**Решение:**
```cmd
python -m pip install requests
```

---

### Ошибка: "Model file not found"

**Причина:** Модели не скачались или повреждены.

**Решение:** Переустановить модели:
```cmd
run.bat --install
```

---

### Медленная генерация

**Причина:** Слишком большие модели или неправильные настройки.

**Решения:**
- Убедиться, что используется Q4_0 квантованная модель (она уже по умолчанию)
- Закрыть фоновые приложения
- Для RTX 3050 4GB нормальное время: 30-90 секунд на изображение 768x512

---

### Консоль закрывается сразу после запуска

**Причина:** Скрипт завершился с ошибкой.

**Решение:** Запустить из командной строки чтобы увидеть ошибку:
```cmd
cd путь\к\папке\z-image-gen
run.bat "test prompt"
```

---

### Изображение не сохраняется

**Причина:** Нет доступа к папке Downloads.

**Решение:** Указать другой путь:
```cmd
run.bat "prompt" --output "D:\my_images\test.png"
```

---

## Полная переустановка

Если ничего не помогает:

```cmd
:: Удалить старую установку
rmdir /s /q "%LOCALAPPDATA%\z-image-gen"

:: Запустить установку заново
install.bat
```

---

## Структура файлов

```
%LOCALAPPDATA%\z-image-gen\
├── bin\
│   ├── sd-cli.exe          # Бинарник stable-diffusion.cpp
│   ├── cudart64_12.dll     # CUDA runtime
│   ├── cublas64_12.dll     # CUDA BLAS
│   ├── cublasLt64_12.dll   # CUDA BLAS LT
│   └── stable-diffusion.dll
├── models\
│   ├── z_image_turbo-Q4_0.gguf      # Diffusion модель
│   ├── ae.safetensors               # VAE
│   └── Qwen3-4B-Instruct-2507-Q4_K_M.gguf  # Text encoder
└── generate.py            # Основной скрипт
```

---

## Технические детали

- **Модель:** Z-Image-Turbo (6B параметров)
- **Квантование:** Q4_0 для минимального использования VRAM
- **Инференс:** stable-diffusion.cpp (C++)
- **Оптимизации для 4GB VRAM:**
  - `--offload-to-cpu` - выгрузка слоёв в RAM
  - `--diffusion-fa` - flash attention
  - `--vae-tiling` - тайловая обработка VAE
  - `--clip-on-cpu` - CLIP на процессоре

---

## Благодарности

- [leejet/stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) - быстрый инференс на C++
- [Tongyi-MAI/Z-Image](https://github.com/Tongyi-MAI/Z-Image) - модель Z-Image
- [Qwen Team](https://github.com/QwenLM/Qwen3) - Qwen3 текстовый энкодер

---

## Лицензия

MIT License
