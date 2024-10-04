from typing import Final, List, Dict, Union
from requests import Response
from playwright.async_api import (
    async_playwright,
    Cookie,
    Playwright,
    Page,
    BrowserContext,
    Browser,
    BrowserType,
)
from pathlib import Path
from time import sleep
from datetime import datetime
import asyncio
import requests
import json

WAIT_TIME: Final[int] = 15


async def get_stats(
    playwright: Playwright,
    account_user_name: str = "primetimetank_",
    headless: bool = True,
) -> None:
    firefox: BrowserType = playwright.firefox
    browser: Browser = await firefox.launch(headless=headless)
    context: BrowserContext = await browser.new_context(storage_state="instagram.json")
    page: Page = await context.new_page()
    url = f"https://www.instagram.com/{account_user_name}"
    await page.goto(url)
    sleep(WAIT_TIME)

    cookies: List[Cookie] = await context.cookies()
    ds_user_id: str = ""

    for cookie in cookies:
        # print(f"{cookie['name']:<20}:\t\t{cookie['value'][:25]}")
        if cookie["name"] == "ds_user_id":
            # print(cookie)
            # print(cookie["name"],":",cookie["value"])
            ds_user_id = cookie["value"]
            break

    # Reformat the cookies
    cookie_dict: Dict[str, str] = {
        cookie["name"]: cookie["value"] for cookie in cookies
    }

    followers_amount_str: List[str] = await page.locator(
        "text=followers"
    ).all_inner_texts()
    followers_amount: int = int(followers_amount_str[0].split(" ")[0].replace(",", ""))

    following_amount_str: List[str] = await page.locator(
        "text=following"
    ).all_inner_texts()
    following_amount: int = int(following_amount_str[0].split(" ")[0].replace(",", ""))

    a_handle = await page.evaluate_handle("document.body")
    result_handle = await page.evaluate_handle("body => body.innerHTML", a_handle)
    script_str = await result_handle.json_value()
    # print(await result_handle.json_value())
    await result_handle.dispose()

    x_ig_app_id: str = ""

    if "X-IG-App-ID" in script_str:
        starting_index: int = script_str.index("X-IG-App-ID")
        end_index: int = script_str[starting_index : starting_index + 50].index("}")
        x_ig_app_id = str(
            int(
                script_str[starting_index : starting_index + end_index]
                .split(",")[0]
                .split(":")[1]
                .replace('"', "")
                .replace('"', "")
            )
        )
        # print(x_ig_app_id)

    instagram_stats_dir = Path(Path.cwd(), "statistics")
    instagram_stats_dir.mkdir(exist_ok=True, parents=True)
    instagram_users_dir = Path(instagram_stats_dir, "instagram_users")
    instagram_users_dir.mkdir(exist_ok=True, parents=True)
    instagram_users_filename: Path = Path(
        instagram_users_dir,
        f"instagram_users_{datetime.now().strftime('%d_%b_%Y_at_%H_%M_%S')}.json",
    )

    instagram_users: Dict[str, List[Dict]] = {"followers": [], "following": []}
    COUNT: Final[int] = 100

    for key in instagram_users.keys():
        user_count: int = 0
        expected_max_users: int = -1
        stuck_count: int = 0
        max_id: str = ""

        if key == "followers":
            expected_max_users = followers_amount
        elif key == "following":
            expected_max_users = following_amount
        else:
            raise Exception("Error: Invalid key (should be 'followers' or 'following'")

        while all([user_count < expected_max_users, stuck_count < 5]):
            headers: Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "X-IG-App-ID": x_ig_app_id,
                "X-Requested-With": "XMLHttpRequest",
                "Alt-Used": "www.instagram.com",
                "Connection": "keep-alive",
                "Referer": f"https://www.instagram.com/{account_user_name}/{key}/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }

            params: Dict[str, Union[str, int]] = {
                "count": COUNT,
                "max_id": max_id,
                "search_surface": "follow_list_page",
            }

            try:
                response: Response = requests.get(
                    f"https://www.instagram.com/api/v1/friendships/{ds_user_id}/{key}/",
                    params=params,
                    cookies=cookie_dict,
                    headers=headers,
                )

                response_dict = response.json()

                instagram_users[key] += response_dict["users"]
                user_count = len(instagram_users[key])

                with open(instagram_users_filename, "w", encoding="utf-8") as f:
                    json.dump(instagram_users, f, indent=4)

                print(
                    f"Updated instagram_users for {key} (current length: {user_count})"
                )

                # prepare for next loop iteration
                max_id = response_dict["next_max_id"]
                stuck_count = 0

            except Exception as e:
                print(e)
                stuck_count += 1
                print(f"Got stuck: {stuck_count}")
            finally:
                sleep(5)

    await context.close()
    await browser.close()

    not_following_me_back: List[dict] = []
    for instagram_user_im_following in instagram_users["following"]:
        user_name_im_following = instagram_user_im_following["username"]
        # print(user_name_im_following, end=" ")
        is_following_me_back: bool = False
        for instagram_follower in instagram_users["followers"]:
            if user_name_im_following == instagram_follower["username"]:
                is_following_me_back = True
                break
        if not is_following_me_back:
            not_following_me_back.append(instagram_user_im_following)

    im_not_following_back: List[dict] = []
    for instagram_user_following_me in instagram_users["followers"]:
        user_name_following_me = instagram_user_following_me["username"]
        im_following_back: bool = False
        for instagram_following in instagram_users["following"]:
            if user_name_following_me == instagram_following["username"]:
                im_following_back = True
                break
        if not im_following_back:
            im_not_following_back.append(instagram_user_following_me)

    with open(
        Path(instagram_stats_dir, "not_following_me_back.txt"), "w", encoding="utf-8"
    ) as f:
        for instagram_user in not_following_me_back:
            user_name = instagram_user["username"]
            f.write(f"https://www.instagram.com/{user_name}\n")

    with open(
        Path(instagram_stats_dir, "im_not_following_back.txt"), "w", encoding="utf-8"
    ) as f:
        for instagram_user in im_not_following_back:
            user_name = instagram_user["username"]
            f.write(f"https://www.instagram.com/{user_name}\n")


async def async_main() -> None:
    async with async_playwright() as playwright:
        await get_stats(playwright, headless=True)


def main() -> None:
    if __name__ == "__main__":
        asyncio.run(async_main())


main()
