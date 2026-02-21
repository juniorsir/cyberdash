from textual.widgets import Static, Label, ProgressBar
from textual.containers import Horizontal

class ResourceBar(Static):
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.resource_name = name

    def compose(self):
        yield Label(f"[b]{self.resource_name}[/]", id="label")
        with Horizontal():
            yield ProgressBar(total=100, show_eta=False, show_percentage=False, id="bar")
            yield Label("0%", id="pct-label")

    def update_bar(self, value: float):
        try:
            bar = self.query_one("#bar", ProgressBar)
            # FIX: Animate the 'progress' attribute of the bar widget directly
            bar.animate("progress", value=float(value), duration=0.5)
            # Update the text label
            self.query_one("#pct-label").update(f"{int(value)}%")
        except:
            pass
