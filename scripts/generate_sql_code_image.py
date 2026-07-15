"""Render the actual MySQL analysis SQL as a readable code image for project docs."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_DIR / "sql" / "01_business_analysis_mysql.sql"
DESTINATION = PROJECT_DIR / "docs" / "images" / "mysql_business_analysis_sql.png"


def main() -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    sql = SOURCE.read_text(encoding="utf-8")
    # Use the Windows Chinese font directly so comments and Chinese business labels remain readable.
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", size=19)
    line_number_font = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", size=17)
    lines = sql.splitlines()
    probe = Image.new("RGB", (1, 1))
    probe_draw = ImageDraw.Draw(probe)
    text_width = max(probe_draw.textbbox((0, 0), line or " ", font=font)[2] for line in lines)
    line_height = 31
    image = Image.new("RGB", (text_width + 115, line_height * len(lines) + 38), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 82, image.height), fill="#e2e8f0")
    draw.line((82, 0, 82, image.height), fill="#cbd5e1", width=2)
    for number, line in enumerate(lines, start=1):
        y = 18 + (number - 1) * line_height
        draw.text((14, y), str(number), fill="#64748b", font=line_number_font)
        draw.text((98, y), line, fill="#0f172a", font=font)
    image.save(DESTINATION)
    print(DESTINATION)


if __name__ == "__main__":
    main()
