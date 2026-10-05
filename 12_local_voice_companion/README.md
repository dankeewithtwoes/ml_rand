# Локальный голосовой помощник

Цепочка записи и ответа: sounddevice → faster-whisper → выделение команды после wake word → Ollama → pyttsx3. WAV проверяется через модуль wave; повреждённые промежуточные файлы удаляются.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
ollama pull llama3.1
ollama serve
python companion.py --wake-word "компьютер" --record-seconds 5
python companion.py --text-input --no-tts
python stt_demo.py --audio sample.wav --model small --language ru
python stt_demo.py --record-seconds 4 --model small
python tts_demo.py --text "Привет" --output demo/hello.wav
python benchmark_latency.py --audio sample.wav --model small
```

```bash
python -m unittest test_audio_io.py -v
```

## Ограничения

Первый запуск Whisper может скачать веса; для работы без сети передайте путь к локальной модели. Нужны микрофон, аудиодрайвер, системный TTS и Ollama. На Linux для pyttsx3 требуется espeak-ng. Тесты подменяют аудиоустройства и STT-модель. Ранее проверялось создание WAV через Windows SAPI; полный цикл распознавания с загруженной Whisper-моделью в этом отчёте не подтверждён.
