import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from kurumi_podcast import audio
from kurumi_podcast.core import load_json, save_json
from kurumi_podcast.voices import (FONTS, confirm_review, review_video, score_segments, select_entries,
                                   separate_vocals, shared_intervals)

HAS_TORCH = importlib.util.find_spec("torch") is not None
HAS_FFMPEG = shutil.which("ffmpeg") is not None


def direction(seed, base=None, closeness=0.):
    v = np.random.default_rng(seed).normal(size=192)
    if base is not None:
        v = closeness * base + (1 - closeness) * v / np.linalg.norm(v)
    return v / np.linalg.norm(v)


class ScoringTests(unittest.TestCase):
    def test_margin_uses_the_closest_other_voice(self):
        kurumi = direction(1)
        yasuko = direction(2, kurumi, .55)  # A voice the embedding hears as close to the target.
        mochiko = direction(3)
        lines = ([{"embedding": direction(10 + i, kurumi, .8)} for i in range(6)] +
                 [{"embedding": direction(20 + i, yasuko, .8)} for i in range(3)] +
                 [{"embedding": direction(30 + i, mochiko, .8)} for i in range(3)])
        score_segments(lines, [kurumi], {"mochiko": [mochiko]})
        fooled = sum(s["tier"] == "high" for s in lines[6:9])
        score_segments(lines, [kurumi], {"mochiko": [mochiko], "yasuko": [yasuko]}, high=(.6, 0.))
        self.assertGreater(fooled, 0)
        self.assertTrue(all(s["tier"] != "high" for s in lines[6:]))
        self.assertTrue(all(s["tier"] == "high" for s in lines[:6]))
        self.assertEqual({s["nearest_other"] for s in lines[6:9]}, {"yasuko"})

    def test_mixed_halves_never_reach_high(self):
        target = direction(1)
        lines = [{"embedding": target, "halves": .1}]
        score_segments(lines, [target], {"other": [direction(2)]})
        self.assertTrue(lines[0]["mixed"])
        self.assertNotEqual(lines[0]["tier"], "high")


@unittest.skipUnless(HAS_TORCH, "torch is needed for fingerprint matching")
class SharedAudioTests(unittest.TestCase):
    def test_song_shared_at_different_offsets_is_found_in_both(self):
        import torch
        rng = np.random.default_rng(0)

        def frames(n):
            return torch.nn.functional.normalize(torch.tensor(rng.normal(size=(n, 48)), dtype=torch.float32), dim=1)

        song = frames(900)  # 90 s at 0.1 s per frame.
        a = torch.cat([frames(1000), song, frames(1500)])
        b = torch.cat([frames(700), song, frames(1800)])
        found_a, found_b = shared_intervals(a, b)
        self.assertEqual(len(found_a), 1)
        self.assertAlmostEqual(found_a[0][0], 100 - 2, delta=2)
        self.assertAlmostEqual(found_a[0][1], 190 + 2, delta=2)
        self.assertAlmostEqual(found_b[0][0], 70 - 2, delta=2)
        self.assertEqual(shared_intervals(frames(2000), frames(2000)), ([], []))


class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.index = []
        cursor = 0.
        for number in range(1, 6):
            clip = self.root / "candidates" / f"3b_{number:07.2f}.wav"
            audio.write_pcm(clip, np.ones(2400) * 500, 24000)
            self.index.append({"no": number, "episode": "3b", "start": number, "end": number + 2,
                               "score": .7, "margin": .1, "text": f"台词{number}", "file": str(clip),
                               "video_start": cursor, "video_end": cursor + 2.5})
            cursor += 2.5
        save_json(self.root / "review.json", self.index)

    def test_picks_by_number_range_and_video_time(self):
        self.assertEqual(select_entries(self.index, ["2-3"]), {2, 3})
        self.assertEqual(select_entries(self.index, ["0:07.6-"]), {4, 5})
        self.assertEqual(select_entries(self.index, ["0:05~0:07"]), {3})
        self.assertEqual(select_entries(self.index, ["0:01"]), {1})
        with self.assertRaisesRegex(ValueError, "no entries"):
            select_entries(self.index, ["9"])

    def test_verdict_splits_confirmed_and_other_character(self):
        confirmed, anchors = self.root / "kurumi_confirmed", self.root / "anchors"
        result = confirm_review(self.root / "review.json", confirmed, ["0:10-"], "yasuko", anchors)
        self.assertEqual(result["rejected"], [5])
        self.assertEqual(len(list(confirmed.glob("*.wav"))), 4)
        self.assertEqual(len(list((anchors / "yasuko").glob("*.wav"))), 1)
        listing = (confirmed / "kurumi_confirmed.lst").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(listing), 4)
        confirm_review(self.root / "review.json", confirmed, ["0:10-"], "yasuko", anchors)
        self.assertEqual(len((confirmed / "kurumi_confirmed.lst").read_text(encoding="utf-8").splitlines()), 4)
        self.assertIn("yasuko", (anchors / "yasuko" / "README.txt").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "reject-as"):
            confirm_review(self.root / "review.json", confirmed, ["1"])


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is needed for media tests")
class MediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_separation_renames_stem_and_reports_removed_energy(self):
        source = self.root / "clip one.wav"
        t = np.arange(24000) / 24000
        audio.write_pcm(source, 6000 * np.sin(2 * np.pi * 220 * t), 24000)
        fake = self.root / "fake_separator.py"
        fake.write_text(
            "import shutil, sys\nfrom pathlib import Path\nargs = sys.argv[1:]\n"
            "out = Path(args[args.index('--output_dir') + 1])\n"
            "for src in [a for a in args if a.endswith('.wav')]:\n"
            "    shutil.copy(src, out / (Path(src).stem + '_(Vocals)_fake.wav'))\n", encoding="utf-8")
        rows = separate_vocals([source], self.root / "out", [sys.executable, str(fake)])
        self.assertTrue(Path(rows[0]["vocals"]).name == "clip one.wav")
        self.assertLess(rows[0]["removed_db"], -40)  # Nothing removed from an already clean clip.
        self.assertTrue((self.root / "out" / "separation.json").is_file())

    @unittest.skipUnless(any(Path(f).is_file() for f in FONTS), "a CJK font is needed for labels")
    def test_review_video_labels_clips_and_indexes_video_time(self):
        video = self.root / "episode.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=24",
                        "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000", "-t", "12",
                        "-c:v", "libx264", "-c:a", "aac", "-shortest", str(video)], check=True)
        save_json(self.root / "candidates.json", {"segments": [
            {"episode": "2b", "start": 1., "end": 3.5, "score": .8, "margin": .2, "tier": "high",
             "text": "テスト 100% の台詞"},
            {"episode": "2b", "start": 6., "end": 9., "score": .7, "margin": .1, "tier": "high", "text": "二つ目"},
            {"episode": "2b", "start": 10., "end": 11., "score": .4, "margin": 0, "tier": "other", "text": "x"}]})
        index = review_video(self.root / "candidates.json", {"2b": video}, self.root / "review.mp4")
        self.assertEqual([e["no"] for e in index], [1, 2])
        self.assertAlmostEqual(index[0]["video_end"], 3.1, delta=.2)
        self.assertEqual(index[1]["video_start"], index[0]["video_end"])
        self.assertAlmostEqual(audio.duration_any(self.root / "review.mp4"), index[1]["video_end"], delta=.3)
        self.assertEqual(load_json(self.root / "review.json"), index)


if __name__ == "__main__":
    unittest.main()
