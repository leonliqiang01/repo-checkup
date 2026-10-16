"""README exists and is more than a stub."""

from repo_checkup.core import Check, Context, Result

NAMES = ("README.md", "README.markdown", "README.rst", "README.txt", "README")
MIN_CONTENT_CHARS = 50
# A line made only of these characters is a reStructuredText heading underline.
UNDERLINE_CHARS = set("=-~^*+#`'\"")


def _is_heading(line: str) -> bool:
    return line.startswith("#") or set(line) <= UNDERLINE_CHARS


class Readme(Check):
    id = "readme"
    title = "README"
    order = 10

    def run(self, ctx: Context) -> Result:
        path = ctx.find_file(*NAMES)
        if path is None:
            return Result.fail(
                "No README found",
                "Add a README.md that explains what the project does and how to use it",
            )
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            return Result.fail(
                f"{path.name} is empty",
                "Describe what the project does, how to install it and how to use it",
            )
        content = [s for line in text.splitlines() if (s := line.strip()) and not _is_heading(s)]
        chars = sum(len(line) for line in content)
        if chars < MIN_CONTENT_CHARS:
            return Result.warn(
                f"{path.name} looks like a stub ({chars} characters besides headings)",
                "Add a short description, a usage example and how to develop the project",
            )
        return Result.ok(f"{path.name} has {len(content)} lines of content")
