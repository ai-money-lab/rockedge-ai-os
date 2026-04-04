#!/usr/bin/env python3
"""
ailyxtokyo IG Reel 自動投稿スクリプト
=====================================
Playwrightを使用してInstagramリールを正しいサイズ（1080x1920 / 9:16）で投稿する。

使い方:
  python scripts/ig_reel_post.py --image /path/to/image.jpg --caption "投稿テキスト"

環境変数:
  IG_USERNAME: Instagramのユーザー名（ailyxtokyo）
  IG_PASSWORD: Instagramのパスワード
"""

import argparse
import os
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright が未インストールです")
    print("  pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    Image = None

# ─────────────────────────────────────────
# IGリールの正しいサイズ設定
# ─────────────────────────────────────────
REEL_WIDTH = 1080
REEL_HEIGHT = 1920  # 9:16 アスペクト比


def resize_image_for_reel(image_path: str) -> str:
    """
    画像をIGリールサイズ（1080x1920 / 9:16）にリサイズする。
    - 顔が切れないよう、上部を優先して保持する
    - 元画像が正方形の場合、上下に余白を追加するのではなく
      幅に合わせてリサイズし、上部基準でクロップする
    """
    if Image is None:
        print("Warning: Pillow未インストール。画像リサイズをスキップします。")
        print("  pip install Pillow")
        return image_path

    img = Image.open(image_path)
    orig_w, orig_h = img.size
    target_ratio = REEL_WIDTH / REEL_HEIGHT  # 0.5625

    current_ratio = orig_w / orig_h

    if abs(current_ratio - target_ratio) < 0.01:
        # 既に9:16に近い場合、リサイズのみ
        img = img.resize((REEL_WIDTH, REEL_HEIGHT), Image.LANCZOS)
    elif current_ratio > target_ratio:
        # 横長すぎる（正方形含む）→ 幅を基準にクロップ
        # 顔が上部にあるため、上部を優先して保持
        new_h = int(orig_w / target_ratio)
        if new_h <= orig_h:
            # 上部基準でクロップ（顔を残す）
            img = img.crop((0, 0, orig_w, new_h))
        else:
            # 高さが足りない場合は、高さ基準で幅をクロップ（中央寄せ）
            new_w = int(orig_h * target_ratio)
            left = (orig_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, orig_h))
        img = img.resize((REEL_WIDTH, REEL_HEIGHT), Image.LANCZOS)
    else:
        # 縦長すぎる → 高さを基準に幅をクロップ（中央寄せ）
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, orig_h))
        img = img.resize((REEL_WIDTH, REEL_HEIGHT), Image.LANCZOS)

    # リサイズ済みファイルを保存
    out_path = Path(image_path)
    resized_path = out_path.parent / f"{out_path.stem}_reel_1080x1920{out_path.suffix}"
    img.save(str(resized_path), quality=95)
    print(f"  リサイズ完了: {orig_w}x{orig_h} → {REEL_WIDTH}x{REEL_HEIGHT}")
    print(f"  保存先: {resized_path}")
    return str(resized_path)


def post_ig_reel(image_path: str, caption: str, username: str, password: str, headless: bool = True):
    """
    Playwrightを使用してIGリールを投稿する。
    ビューポートを1080x1920（9:16）に設定して正しいサイズで投稿。
    """
    # 画像をリールサイズにリサイズ
    image_path = resize_image_for_reel(image_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": REEL_WIDTH, "height": REEL_HEIGHT},
            device_scale_factor=1,
            user_agent=(
                "Mozilla/5.0 (iPhone 14 Pro; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()

        try:
            # ── ログイン ──
            print("IG ログイン中...")
            page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
            time.sleep(2)

            # Cookie同意バナーがあれば閉じる
            try:
                page.click("text=Allow all cookies", timeout=3000)
            except Exception:
                pass
            try:
                page.click("text=すべてのCookieを許可する", timeout=3000)
            except Exception:
                pass

            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            time.sleep(3)

            # 「後で」ボタンがあれば閉じる
            for dismiss_text in ["後で", "Not Now", "Not now"]:
                try:
                    page.click(f"text={dismiss_text}", timeout=3000)
                    time.sleep(1)
                except Exception:
                    pass

            print("ログイン完了")

            # ── 新規投稿 ──
            print("投稿作成中...")
            # 新規投稿ボタン
            page.click('svg[aria-label="New post"], svg[aria-label="新規投稿"]', timeout=10000)
            time.sleep(2)

            # ファイルアップロード
            file_input = page.locator('input[type="file"]')
            file_input.set_input_files(image_path)
            time.sleep(3)

            # アスペクト比を9:16に変更
            try:
                # リサイズアイコンをクリック
                page.click('svg[aria-label="Select crop"], svg[aria-label="切り取りを選択"]', timeout=5000)
                time.sleep(1)
                # 9:16オプションを選択
                page.click('svg[aria-label="Portrait photo outline icon"], text=9:16', timeout=5000)
                time.sleep(1)
            except Exception:
                print("  アスペクト比の手動設定をスキップ（画像は既に9:16）")

            # 「次へ」をクリック
            for next_text in ["Next", "次へ"]:
                try:
                    page.click(f"text={next_text}", timeout=5000)
                    time.sleep(2)
                    break
                except Exception:
                    pass

            # フィルター画面 →「次へ」
            for next_text in ["Next", "次へ"]:
                try:
                    page.click(f"text={next_text}", timeout=5000)
                    time.sleep(2)
                    break
                except Exception:
                    pass

            # キャプション入力
            if caption:
                caption_area = page.locator('textarea[aria-label="Write a caption..."], textarea[aria-label="キャプションを入力…"]')
                caption_area.fill(caption)
                time.sleep(1)

            # 「リール」タブがあれば選択（動画の場合）
            try:
                page.click('text=Reel, text=リール', timeout=3000)
                time.sleep(1)
            except Exception:
                pass

            # 「シェア」をクリック
            for share_text in ["Share", "シェア"]:
                try:
                    page.click(f"text={share_text}", timeout=5000)
                    time.sleep(5)
                    break
                except Exception:
                    pass

            print(f"投稿完了! サイズ: {REEL_WIDTH}x{REEL_HEIGHT} (9:16)")

        except Exception as e:
            print(f"エラー: {e}")
            # デバッグ用スクリーンショット
            page.screenshot(path="ig_error_screenshot.png")
            print("エラースクリーンショットを保存しました: ig_error_screenshot.png")
            raise
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description="ailyxtokyo IG Reel 投稿 (1080x1920)")
    parser.add_argument("--image", required=True, help="投稿する画像のパス")
    parser.add_argument("--caption", default="", help="投稿のキャプション")
    parser.add_argument("--username", default=os.environ.get("IG_USERNAME", "ailyxtokyo"),
                        help="IGユーザー名 (default: IG_USERNAME env or ailyxtokyo)")
    parser.add_argument("--password", default=os.environ.get("IG_PASSWORD", ""),
                        help="IGパスワード (default: IG_PASSWORD env)")
    parser.add_argument("--no-headless", action="store_true", help="ブラウザを表示して実行")
    args = parser.parse_args()

    if not args.password:
        print("Error: IGパスワードが未設定です")
        print("  --password で指定するか、環境変数 IG_PASSWORD を設定してください")
        sys.exit(1)

    if not Path(args.image).exists():
        print(f"Error: 画像が見つかりません: {args.image}")
        sys.exit(1)

    print(f"=== ailyxtokyo IG Reel 投稿 ===")
    print(f"  画像: {args.image}")
    print(f"  サイズ: {REEL_WIDTH}x{REEL_HEIGHT} (9:16)")
    print(f"  ユーザー: {args.username}")
    print()

    post_ig_reel(
        image_path=args.image,
        caption=args.caption,
        username=args.username,
        password=args.password,
        headless=not args.no_headless,
    )


if __name__ == "__main__":
    main()
