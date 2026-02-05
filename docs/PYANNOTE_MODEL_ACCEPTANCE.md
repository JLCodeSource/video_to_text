# Hugging Face Model Terms Acceptance

Before using the speaker diarization features in vtt-transcribe, the following Hugging Face models require you to accept the model license/terms on their model pages:

- pyannote/speaker-diarization-3.1 — Required (main diarization model)
- pyannote/segmentation-3.0 — Required (speaker segmentation)
- pyannote/speaker-diarization-community-1 — Required (community model)

Additionally, the speaker embedding model below is typically auto-downloaded and does not require manual acceptance in most cases:

- pyannote/wespeaker-voxceleb-resnet34-LM — Speaker embedding model (auto-downloaded)

## How to accept terms

1. Sign into your Hugging Face account at https://huggingface.co/
2. Visit each of the model pages listed above (examples):
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
   - https://huggingface.co/pyannote/speaker-diarization-community-1
3. Click "Accept" on the model page if prompted to accept license or terms.

Without accepting the required model terms, diarization runs that use these models will fail with authentication or access errors. Once accepted, the models will be available to download into your Hugging Face cache when running diarization for the first time.