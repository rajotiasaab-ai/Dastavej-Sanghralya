"""Generates a professional Windows application icon for DOCX Database."""

from pathlib import Path
from PIL import Image, ImageDraw

def create_app_icon():
    assets_dir = Path(__file__).resolve().parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []

    for width, height in sizes:
        # Transparent background
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        scale = width / 256.0

        # Rounded rectangle background (Word Blue / Royal Blue)
        # Gradient effect simulated with rounded rect
        bg_color = (24, 90, 189, 255) # #185abd Word Blue
        corner_r = int(48 * scale)
        draw.rounded_rectangle([int(16 * scale), int(16 * scale), int(240 * scale), int(240 * scale)], radius=corner_r, fill=bg_color)

        # Document page shape (white folded sheet)
        doc_left = int(60 * scale)
        doc_top = int(45 * scale)
        doc_right = int(196 * scale)
        doc_bottom = int(211 * scale)
        draw.rounded_rectangle([doc_left, doc_top, doc_right, doc_bottom], radius=int(12 * scale), fill=(255, 255, 255, 255))

        # Horizontal document text lines (slate blue)
        line_color = (180, 200, 230, 255)
        for y_offset in [80, 105, 130, 155]:
            draw.rounded_rectangle(
                [int(80 * scale), int(y_offset * scale), int(176 * scale), int((y_offset + 10) * scale)],
                radius=int(4 * scale),
                fill=line_color
            )

        # Bold "W" or Search badge at bottom-right
        # Dark circular search badge
        badge_center_x = int(185 * scale)
        badge_center_y = int(185 * scale)
        badge_r = int(42 * scale)
        draw.ellipse(
            [badge_center_x - badge_r, badge_center_y - badge_r, badge_center_x + badge_r, badge_center_y + badge_r],
            fill=(26, 115, 232, 255),
            outline=(255, 255, 255, 255),
            width=max(1, int(5 * scale))
        )

        # Magnifying glass inside badge
        lens_r = int(16 * scale)
        lens_x = badge_center_x - int(6 * scale)
        lens_y = badge_center_y - int(6 * scale)
        draw.ellipse(
            [lens_x - lens_r, lens_y - lens_r, lens_x + lens_r, lens_y + lens_r],
            outline=(255, 255, 255, 255),
            width=max(1, int(5 * scale))
        )
        # Handle
        draw.line(
            [lens_x + int(11 * scale), lens_y + int(11 * scale), badge_center_x + int(22 * scale), badge_center_y + int(22 * scale)],
            fill=(255, 255, 255, 255),
            width=max(1, int(6 * scale))
        )

        images.append(img)

    # Save PNG & ICO
    png_path = assets_dir / "app_icon.png"
    ico_path = assets_dir / "app_icon.ico"
    images[0].save(png_path)
    images[0].save(ico_path, format="ICO", sizes=sizes)
    print(f"Generated icons at {ico_path} and {png_path}")

if __name__ == "__main__":
    create_app_icon()

