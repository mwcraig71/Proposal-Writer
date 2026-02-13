from PIL import Image, ImageDraw, ImageFont
import io
import json
import textwrap


FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

BRAND_RED = (207, 57, 16)
BRAND_DARK = (30, 41, 59)
WHITE = (255, 255, 255)
LIGHT_GRAY = (241, 245, 249)
MEDIUM_GRAY = (148, 163, 184)


def get_font(bold=False, size=14):
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines if lines else [""]


def render_challenge_solution(payload, scale=2):
    data = payload if isinstance(payload, dict) else json.loads(payload)
    pairs = data.get('pairs', [])
    title = data.get('title', 'CHALLENGE / SOLUTION')

    if not pairs:
        pairs = [{'challenge': '', 'solution': ''}]

    width = 700 * scale
    padding = 20 * scale
    col_width = (width - padding * 3) // 2
    title_font = get_font(bold=True, size=16 * scale)
    header_font = get_font(bold=True, size=11 * scale)
    body_font = get_font(size=10 * scale)

    temp_img = Image.new('RGB', (width, 100))
    temp_draw = ImageDraw.Draw(temp_img)

    row_heights = []
    rendered_pairs = []
    for pair in pairs:
        ch_lines = wrap_text(pair.get('challenge', ''), body_font, col_width - padding, temp_draw)
        sol_lines = wrap_text(pair.get('solution', ''), body_font, col_width - padding, temp_draw)
        line_h = temp_draw.textbbox((0, 0), "Ay", font=body_font)[3]
        ch_h = len(ch_lines) * (line_h + 4 * scale) + padding * 2 + 20 * scale
        sol_h = len(sol_lines) * (line_h + 4 * scale) + padding * 2 + 20 * scale
        row_h = max(ch_h, sol_h)
        row_heights.append(row_h)
        rendered_pairs.append((ch_lines, sol_lines))

    title_h = 50 * scale
    total_h = title_h + sum(row_heights) + padding * (len(pairs) + 1)

    img = Image.new('RGB', (width, total_h), WHITE)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, width, title_h], fill=BRAND_RED)
    tbbox = draw.textbbox((0, 0), title, font=title_font)
    tx = (width - (tbbox[2] - tbbox[0])) // 2
    ty = (title_h - (tbbox[3] - tbbox[1])) // 2
    draw.text((tx, ty), title, fill=WHITE, font=title_font)

    y = title_h + padding
    line_h = draw.textbbox((0, 0), "Ay", font=body_font)[3]

    for idx, (ch_lines, sol_lines) in enumerate(rendered_pairs):
        row_h = row_heights[idx]

        draw.rectangle([padding, y, padding + col_width, y + row_h], fill=LIGHT_GRAY)
        draw.rectangle([padding * 2 + col_width, y, padding * 2 + col_width * 2, y + row_h], fill=LIGHT_GRAY)

        draw.text((padding + 10 * scale, y + 8 * scale), "CHALLENGE", fill=BRAND_RED, font=header_font)
        draw.text((padding * 2 + col_width + 10 * scale, y + 8 * scale), "SOLUTION", fill=(16, 124, 65), font=header_font)

        text_y = y + 28 * scale
        for line in ch_lines:
            draw.text((padding + 10 * scale, text_y), line, fill=BRAND_DARK, font=body_font)
            text_y += line_h + 4 * scale

        text_y = y + 28 * scale
        for line in sol_lines:
            draw.text((padding * 2 + col_width + 10 * scale, text_y), line, fill=BRAND_DARK, font=body_font)
            text_y += line_h + 4 * scale

        y += row_h + padding

    return img


def render_badge(payload, scale=2):
    data = payload if isinstance(payload, dict) else json.loads(payload)
    badges = data.get('badges', [])

    if not badges:
        badges = [{'label': '', 'value': ''}]

    width = 700 * scale
    padding = 20 * scale
    badge_size = 80 * scale
    cols = min(len(badges), 4)
    rows_count = (len(badges) + cols - 1) // cols
    col_w = (width - padding * 2) // cols
    row_h = badge_size + 40 * scale

    total_h = padding * 2 + rows_count * row_h + 20 * scale

    img = Image.new('RGB', (width, total_h), WHITE)
    draw = ImageDraw.Draw(img)

    value_font = get_font(bold=True, size=20 * scale)
    label_font = get_font(size=9 * scale)

    for i, badge in enumerate(badges):
        col = i % cols
        row = i // cols
        cx = padding + col * col_w + col_w // 2
        cy = padding + row * row_h + badge_size // 2

        draw.ellipse([cx - badge_size // 2, cy - badge_size // 2,
                       cx + badge_size // 2, cy + badge_size // 2], fill=BRAND_RED)

        val = str(badge.get('value', ''))
        vbbox = draw.textbbox((0, 0), val, font=value_font)
        vw = vbbox[2] - vbbox[0]
        vh = vbbox[3] - vbbox[1]
        draw.text((cx - vw // 2, cy - vh // 2 - 2 * scale), val, fill=WHITE, font=value_font)

        label = badge.get('label', '')
        lbbox = draw.textbbox((0, 0), label, font=label_font)
        lw = lbbox[2] - lbbox[0]
        draw.text((cx - lw // 2, cy + badge_size // 2 + 6 * scale), label, fill=BRAND_DARK, font=label_font)

    return img


def render_key_staff(payload, scale=2):
    data = payload if isinstance(payload, dict) else json.loads(payload)
    staff = data.get('staff', [])
    title = data.get('title', 'KEY STAFF')

    if not staff:
        staff = [{'name': '', 'role': ''}]

    width = 700 * scale
    padding = 20 * scale
    title_font = get_font(bold=True, size=16 * scale)
    name_font = get_font(bold=True, size=12 * scale)
    role_font = get_font(size=10 * scale)

    title_h = 50 * scale
    row_h = 50 * scale
    cols = data.get('columns', 2)
    rows_count = (len(staff) + cols - 1) // cols
    total_h = title_h + rows_count * row_h + padding * 2

    img = Image.new('RGB', (width, total_h), WHITE)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, width, title_h], fill=BRAND_RED)
    tbbox = draw.textbbox((0, 0), title, font=title_font)
    tx = (width - (tbbox[2] - tbbox[0])) // 2
    ty = (title_h - (tbbox[3] - tbbox[1])) // 2
    draw.text((tx, ty), title, fill=WHITE, font=title_font)

    col_w = (width - padding * 2) // cols
    for i, person in enumerate(staff):
        col = i % cols
        row = i // cols
        x = padding + col * col_w + 10 * scale
        y = title_h + padding + row * row_h

        draw.text((x, y), person.get('name', ''), fill=BRAND_DARK, font=name_font)
        draw.text((x, y + 18 * scale), person.get('role', ''), fill=MEDIUM_GRAY, font=role_font)

    return img


def render_graphic_to_png(graphic_type, payload):
    data = payload if isinstance(payload, dict) else json.loads(payload)

    if graphic_type in ('challenge-solution', 'challenge_solution'):
        img = render_challenge_solution(data)
    elif graphic_type in ('competency-badge', 'badge'):
        img = render_badge(data)
    elif graphic_type in ('key-staff', 'key_staff'):
        img = render_key_staff(data)
    else:
        img = Image.new('RGB', (400, 100), WHITE)
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Unknown graphic type", fill=BRAND_DARK, font=get_font(size=14))

    buf = io.BytesIO()
    img.save(buf, format='PNG', dpi=(300, 300))
    buf.seek(0)
    return buf


def render_graphic_to_image(graphic_type, payload):
    data = payload if isinstance(payload, dict) else json.loads(payload)

    if graphic_type in ('challenge-solution', 'challenge_solution'):
        return render_challenge_solution(data)
    elif graphic_type in ('competency-badge', 'badge'):
        return render_badge(data)
    elif graphic_type in ('key-staff', 'key_staff'):
        return render_key_staff(data)
    else:
        img = Image.new('RGB', (400, 100), WHITE)
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Unknown graphic type", fill=BRAND_DARK, font=get_font(size=14))
        return img
