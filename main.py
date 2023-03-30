import asyncio
from playwright.async_api import async_playwright
from time import sleep

# pylint: disable=fixme,bare-except


def save_names(f_names, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for f_name in f_names:
            f.write(f_name)


# TODO:
# figure out how to get rid of "Verified" when writing to file
async def get_names(page, text, nth, limit, filename):
    await page.locator(f"text={text}").nth(nth).focus()
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")

    f_names = set()

    for i in range(limit):
        for _ in range(50):
            await page.keyboard.press("ArrowDown")

        if i % 10 == 0:
            tmp_name_list = await page.locator("role=link").all_inner_texts()
            f_names.update(tmp_name_list)
            if len(f_names) >= limit:
                break

        sleep(0.75)

    tmp_name_list = await page.locator("role=link").all_inner_texts()
    f_names.update(tmp_name_list)

    for name in ("", "primetimetank_", "explore", "Verified"):
        try:
            f_names.remove(name)
        except:
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
    sleep(10)

    followers_amount = await page.locator("text=followers").all_inner_texts()
    followers_amount = int(followers_amount[0].split(" ")[0].replace(",", ""))

    following_amount = await page.locator("text=following").all_inner_texts()
    following_amount = int(following_amount[0].split(" ")[0].replace(",", ""))

    await page.goto(f"{url}/followers")
    sleep(4)

    followers_names = await get_names(
        page=page,
        text="Followers",
        nth=-2,
        limit=followers_amount,
        filename="followers_links.txt",
    )
    print(f"Followers: {len(followers_names)}")

    await page.goto(f"{url}/following")
    sleep(4)
    following_names = await get_names(
        page=page,
        text="Following",
        nth=3,
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
