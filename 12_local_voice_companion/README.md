# 12 — Local Voice Desktop Companion

Рабочий локальный голосовой цикл: микрофон → `faster-whisper` → wake word →
Ollama → системный TTS. Аудио и текст не отправляются в облачные сервисы.

## Реализованные функции

- запись настоящего 16-bit PCM WAV с микрофона через `sounddevice`;
- локальное распознавание речи через `faster-whisper`;
- локальная LLM через OpenAI-совместимый endpoint Ollama;
- воспроизведение и сохранение речи через системный движок `pyttsx3`;
- точное выделение команды после wake word;
- явные ошибки при отсутствии библиотеки, модели, аудиодрайвера или Ollama.

Запись и синтез публикуют WAV атомарно и проверяют контейнер через модуль
`wave`. При сбое частичный файл удаляется: приложение никогда не записывает
текст в файл с расширением `.wav`.

## Установка и запуск

```bash
pip install -r requirements.txt

# Нужен запущенный локальный Ollama и модель:
ollama pull llama3.1
ollama serve

# Голосовой режим: каждые 5 секунд распознаётся новый фрагмент
python companion.py --wake-word "компьютер" --record-seconds 5

# Текстовый вход полезен для проверки LLM без микрофона
python companion.py --text-input --no-tts

# Отдельно STT: существующий файл или запись с микрофона
python stt_demo.py --audio sample.wav --model small --language ru
python stt_demo.py --record-seconds 4 --model small

# Настоящий WAV через локальный системный голос
python tts_demo.py --text "Привет" --output demo/hello.wav

# Измерить реальную STT → Ollama → TTS цепочку
python benchmark_latency.py --audio sample.wav --model small
```

Первый запуск `faster-whisper` с именем модели может скачать веса; чтобы
исключить сеть полностью, передайте в `--model`/`--stt-model` путь к заранее
загруженной локальной модели. На Linux для `pyttsx3` нужен установленный
`espeak-ng`; Windows использует SAPI, macOS — системный speech engine.

## Проверка

Юнит-тесты подменяют аппаратную границу, но проверяют реальные контракты:
PCM-запись, вызов Whisper, валидность WAV и удаление повреждённого TTS-файла.

```bash
python -m unittest test_audio_io.py -v
```

В текущей Windows-среде 8/8 тестов прошли; реальный SAPI/`pyttsx3` создал
валидный mono WAV (49 957 frames, 22 050 Hz), а PortAudio обнаружил 22
устройства. `faster-whisper` 1.2.1 импортируется, но inference tiny-модели не
заявлен как проверенный: первая загрузка весов остановилась из-за нехватки
page file в общей тестовой среде. Тесты STT проверяют контракт модели, пустой
transcript и ошибки, не выдавая mocked inference за измерение качества речи.

Если устройство или движок недоступны, CLI завершится с кодом 2 и сообщит
причину в stderr. Фальшивый transcript или «placeholder audio» не создаётся.
