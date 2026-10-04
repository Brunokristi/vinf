from pathlib import Path

from crawler.config import Settings
from crawler.frontier import Frontier
from crawler.storage import Storage


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        seed_file=tmp_path / "seeds.txt",
        data_dir=tmp_path / "data",
    )


def test_frontier_round_robins_across_groups(tmp_path):
    settings = make_settings(tmp_path)
    settings.seed_file.write_text(
        "\n".join([
            "https://biblehub.com/genesis/1.htm",
            "https://biblehub.com/genesis/2.htm",
            "https://biblehub.com/commentaries/genesis/1-1.htm",
            "https://biblehub.com/topical/m/moses.htm",
            "https://biblehub.com/atlas/jerusalem.htm",
        ]),
        encoding="utf-8",
    )

    frontier = Frontier(Storage(settings), settings.seed_file)

    groups = [frontier.pop()[1] for _ in range(4)]
    assert groups == ["bible", "commentary", "topical", "atlas"]

    # The next round starts with Bible again because that queue still has work.
    url, group = frontier.pop()
    assert group == "bible"
    assert url == "https://biblehub.com/genesis/2.htm"


def test_new_seed_is_added_to_existing_state(tmp_path):
    settings = make_settings(tmp_path)
    storage = Storage(settings)
    storage.append_line(storage.seen_file, "https://biblehub.com/genesis/1.htm")
    storage.append_line(storage.visited_file, "https://biblehub.com/genesis/1.htm")
    settings.seed_file.write_text(
        "https://biblehub.com/atlas/jerusalem.htm\n",
        encoding="utf-8",
    )

    frontier = Frontier(storage, settings.seed_file)
    url, group = frontier.pop()

    assert group == "atlas"
    assert url == "https://biblehub.com/atlas/jerusalem.htm"
