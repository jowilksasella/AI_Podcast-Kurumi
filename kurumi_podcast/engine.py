from __future__ import annotations

import inspect
import os
import random
import sys
from pathlib import Path

from .core import resolve_path


def index_home(config):
    value = os.environ.get("INDEXTTS_HOME") or config.get("index_home")
    if not value:
        raise ValueError("set INDEXTTS_HOME or index_home to the existing IndexTTS 2.5 package")
    home = resolve_path(value, config["_base"])
    if not (home / "indextts" / "infer_v2_5.py").is_file():
        raise ValueError(f"IndexTTS 2.5 infer_v2_5.py was not found under {home}")
    return home


def import_engine(home):
    sys.path.insert(0, str(home))
    os.chdir(home)
    from indextts.infer_v2_5 import IndexTTS2
    return IndexTTS2


class IndexBackend:
    """Lazy local backend; never fabricates speech or silently changes the engine."""

    def __init__(self, config):
        self.config = config
        self.model = None
        self.home = index_home(config)

    def _load(self):
        if self.model is not None:
            return
        if self.config.get("offline", True):
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        cls = import_engine(self.home)
        import torch
        torch.set_num_threads(int(self.config.get("cpu_threads", 4)))
        model_dir = resolve_path(self.config.get("model_dir", "checkpoints"), self.home)
        device = self.config.get("device", "cuda:0")
        kwargs = dict(
            model_dir=str(model_dir), cfg_path=str(model_dir / "config.yaml"),
            device=device, use_bf16=bool(self.config.get("use_bf16", True)) and device != "cpu",
            use_cuda_kernel=False, use_deepspeed=False, use_accel=False,
            use_torch_compile=False, use_qwen_emo=False, vram_offload=True,
        )
        parameters = inspect.signature(cls.__init__).parameters
        if not any(p.kind == p.VAR_KEYWORD for p in parameters.values()):
            kwargs = {k: v for k, v in kwargs.items() if k in parameters}
        self.model = cls(**kwargs)

    def synthesize(self, text, target, voice, emotion, seed):
        self._load()
        import numpy as np
        import torch
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        self.model.infer(
            spk_audio_prompt=str(voice), text=text, lang="ZH", output_path=str(target),
            emo_audio_prompt=str(emotion) if emotion else None,
            emo_alpha=float(self.config.get("emo_alpha", .5)),
            use_random=False, duration_factor=float(self.config.get("duration_factor", 1.0)),
            interval_silence=110, max_text_tokens_per_segment=180,
            max_mel_tokens=1300, diffusion_steps=25, verbose=False,
        )
        if not Path(target).is_file():
            raise RuntimeError("the model returned without creating speech")

    def close(self):
        if self.model is not None:
            self.model = None
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

