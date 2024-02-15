import asyncio
from typing import Set
from playwright.async_api import async_playwright
from time import sleep


# TODO: add logging instead of print statements


def save_names(f_names, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for f_name in f_names:
            f.write(f_name)


# maybe TODO:
# figure out how to get rid of "Verified" when writing to file
async def get_names(page, limit, filename) -> Set[str]:
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")

    f_names: Set[str] = set()
    same_length_count: int = 0
    f_names_old_length: int = 0

    for i in range(limit):
        for _ in range(20):
            await page.keyboard.press("ArrowDown")
            sleep(0.5)

        if i % 10 == 0:
            tmp_name_list = await page.locator("role=link").all_inner_texts()
            f_names.update(tmp_name_list)
            if len(f_names) >= limit:
                break

            if f_names_old_length == len(f_names):
                same_length_count += 1
                print(f"stuck count: {same_length_count}")
            else:
                same_length_count = 0
                f_names_old_length = len(f_names)
                print(f"current length: {len(f_names)}")

            if same_length_count >= 10:
                break

        sleep(2)

    tmp_name_list = await page.locator("role=link").all_inner_texts()
    f_names.update(tmp_name_list)

    for name in ("", "primetimetank_", "explore", "Verified"):
        try:
            f_names.remove(name)
        except Exception:
            continue

    with open(filename, "w", encoding="utf-8") as f:
        for f_name in f_names:
            f.write(f"https://www.instagram.com/{f_name}\n")

    f_names.clear()

    with open(filename, "r", encoding="utf-8") as f:
        for f_name in f.readlines():
            if f_name != "Verified":
                f_names.add(f_name)

    save_names(f_names=f_names, filename=filename)

    return f_names


async def run(playwright):
    firefox = playwright.firefox
    browser = await firefox.launch(headless=False)
    context = await browser.new_context(storage_state="instagram.json")
    page = await context.new_page()
    url = "https://www.instagram.com/primetimetank_"
    await page.goto(url)
    sleep(5)

    followers_amount = await page.locator("text=followers").all_inner_texts()
    followers_amount = int(followers_amount[0].split(" ")[0].replace(",", ""))

    following_amount = await page.locator("text=following").all_inner_texts()
    following_amount = int(following_amount[0].split(" ")[0].replace(",", ""))

    await page.goto(f"{url}/followers")
    sleep(5)

    followers_names = await get_names(
        page=page,
        limit=followers_amount,
        filename="followers_links.txt",
    )
    print(f"Followers: {len(followers_names)}")

    await page.goto(f"{url}/following")
    sleep(5)
    following_names = await get_names(
        page=page,
        limit=following_amount,
        filename="following_links.txt",
    )
    print(f"Following: {len(following_names)}")

    not_following_me_back = following_names.difference(followers_names)
    im_not_following_back = followers_names.difference(following_names)

    print(f"Not following me back: {len(not_following_me_back)}")
    save_names(f_names=not_following_me_back, filename="not_following_me_back.txt")

    print(f"I'm not following back: {len(im_not_following_back)}")
    save_names(f_names=im_not_following_back, filename="im_not_following_back.txt")

    await context.close()
    await browser.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


if __name__ == "__main__":
    asyncio.run(main())
