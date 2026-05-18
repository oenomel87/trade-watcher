import io

from watcher_cli.terminal import ScreenRenderer


class FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_screen_renderer_uses_alternate_screen_and_rerenders_in_place():
    stream = FakeTTY()
    renderer = ScreenRenderer(stream)

    renderer.start()
    renderer.render("frame-1")
    renderer.render("frame-2")
    renderer.stop()

    output = stream.getvalue()

    assert "\033[?1049h" in output
    assert output.count("\033[H\033[J") == 2
    assert "\033[?1049l" in output
