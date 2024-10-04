from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Final, List, Tuple, Union
from playwright.async_api import (
    Cookie,
    Playwright,
    Page,
    BrowserContext,
    Browser,
    BrowserType,
    JSHandle,
)
from time import sleep

import requests

WAIT_TIME: Final[int] = 15


async def setup_browser_context_page(
    playwright: Playwright,
    account_user_name: str = "primetimetank_",
    headless: bool = True,
) -> Tuple[Browser, BrowserContext, Page]:
    # Set up the browser and go to Instagram profile page
    firefox: BrowserType = playwright.firefox
    browser: Browser = await firefox.launch(headless=headless)
    context: BrowserContext = await browser.new_context(storage_state="instagram.json")
    page: Page = await context.new_page()
    url = f"https://www.instagram.com/{account_user_name}"
    await page.goto(url)
    sleep(WAIT_TIME)
    return (browser, context, page)


async def get_cookies(context: BrowserContext) -> Tuple[str, Dict[str, str]]:
    cookies: List[Cookie] = await context.cookies()
    ds_user_id: str = ""
    ds_user_id_exists: bool = False

    # Find the X-IG-App-ID cookie -- essential for the request to succeed
    for cookie in cookies:
        if cookie["name"] == "ds_user_id":
            ds_user_id = cookie["value"]
            ds_user_id_exists = True
            break

    if not ds_user_id_exists:
        print("ds_user_id cookie not found (needed for request to succeed). Exiting...")
        exit(1)

    # Reformat the cookies for the request
    cookie_dict: Dict[str, str] = {
        cookie["name"]: cookie["value"] for cookie in cookies
    }

    return (ds_user_id, cookie_dict)


async def get_limits(page: Page) -> Tuple[int, int]:
    followers_amount_str: List[str] = await page.locator(
        "text=followers"
    ).all_inner_texts()

    following_amount_str: List[str] = await page.locator(
        "text=following"
    ).all_inner_texts()

    followers_amount: int = int(followers_amount_str[0].split(" ")[0].replace(",", ""))
    following_amount: int = int(following_amount_str[0].split(" ")[0].replace(",", ""))

    return (followers_amount, following_amount)


async def get_x_ig_app_id(page: Page) -> str:
    a_handle: JSHandle = await page.evaluate_handle("document.body")
    result_handle: JSHandle = await page.evaluate_handle(
        "body => body.innerHTML", a_handle
    )
    script_str: Any = await result_handle.json_value()
    await result_handle.dispose()

    X_IG_APP_ID: Final[str] = "X-IG-App-ID"

    if X_IG_APP_ID not in script_str:
        print(f"{X_IG_APP_ID} not found (needed for request to succeed). Exiting...")
        exit(1)

    starting_index: int = script_str.index(X_IG_APP_ID)
    end_index: int = script_str[starting_index : starting_index + 50].index("}")
    x_ig_app_id: str = str(
        int(
            script_str[starting_index : starting_index + end_index]
            .split(",")[0]
            .split(":")[1]
            .replace('"', "")
            .replace('"', "")
        )
    )
    # print(x_ig_app_id)

    return x_ig_app_id


def create_instragram_stats_dir_and_instagram_users_filename(
    stats_dir_name: str = "statistics",
    instagram_users_dir_name: str = "instagram_users",
    instagram_users_filename_prefix: str = "instagram_users",
) -> Tuple[Path, Path]:
    instagram_stats_dir: Path = Path(Path.cwd(), stats_dir_name)
    instagram_stats_dir.mkdir(exist_ok=True, parents=True)

    instagram_users_dir: Path = Path(instagram_stats_dir, instagram_users_dir_name)
    instagram_users_dir.mkdir(exist_ok=True, parents=True)

    instagram_users_filename: Path = Path(
        instagram_users_dir,
        f"{instagram_users_filename_prefix}_{datetime.now().strftime('%d_%b_%Y_at_%H_%M_%S')}.json",
    )

    return (instagram_stats_dir, instagram_users_filename)


def get_instagram_users(
    *,
    expected_user_limits: Dict[str, int],
    account_user_name: str,
    x_ig_app_id: str,
    ds_user_id: str,
    cookies: Dict[str, str],
    instagram_users_filename: Path,
) -> Dict[str, List[Dict]]:
    # Variables
    instagram_users: Dict[str, List[Dict]] = {"followers": [], "following": []}
    followers_amount, following_amount = (
        expected_user_limits["followers"],
        expected_user_limits["following"],
    )
    COUNT: Final[int] = 100

    # Loop for followers and following requests
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

        while all([user_count < expected_max_users, stuck_count < 5]):
            params: Dict[str, Union[str, int]] = {
                "count": COUNT,
                "max_id": max_id,
                "search_surface": "follow_list_page",
            }

            try:
                response: requests.Response = requests.get(
                    f"https://www.instagram.com/api/v1/friendships/{ds_user_id}/{key}/",
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )

                response_dict: Any = response.json()

                instagram_users[key] += response_dict["users"]
                user_count = len(instagram_users[key])

                with open(instagram_users_filename, "w", encoding="utf-8") as f:
                    json.dump(instagram_users, f, indent=4)

                print(
                    f"Updated instagram_users for {key} (current length: {user_count})"
                )

                # Prepare for next loop iteration
                max_id = response_dict["next_max_id"]
                stuck_count = 0

            except Exception as e:
                print(e)
                stuck_count += 1
                print(f"Got stuck: {stuck_count}")
            finally:
                sleep(5)

    return instagram_users


def calculate_stats(instagram_users: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
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

    instagram_stats: Dict[str, List[Dict]] = {
        "not_following_me_back": not_following_me_back,
        "im_not_following_back": im_not_following_back,
    }

    return instagram_stats


def save_stats(
    instagram_stats: Dict[str, List[Dict]], instagram_stats_dir: Path
) -> None:
    for key in instagram_stats.keys():
        with open(Path(instagram_stats_dir, f"{key}.txt"), "w", encoding="utf-8") as f:
            for instagram_user in instagram_stats[key]:
                user_name = instagram_user["username"]
                f.write(f"https://www.instagram.com/{user_name}\n")
