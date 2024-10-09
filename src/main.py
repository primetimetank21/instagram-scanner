# Imports
from typing import Final, List, Dict
from src.helpers.utils import (
    calculate_stats,
    create_instragram_stats_dir_and_instagram_users_filename,
    get_cookies,
    get_instagram_users,
    get_limits,
    get_x_ig_app_id,
    save_stats,
    setup_browser_context_page,
)
from playwright.async_api import (
    async_playwright,
    Playwright,
)
import asyncio

# Constants
WAIT_TIME: Final[int] = 15


async def get_stats(
    playwright: Playwright,
    account_user_name: str = "primetimetank_",
    headless: bool = True,
) -> None:
    # Set up the browser and go to Instagram profile page
    browser, context, page = await setup_browser_context_page(
        playwright=playwright, account_user_name=account_user_name, headless=headless
    )

    # Get the essential cookies
    ds_user_id, cookie_dict = await get_cookies(context=context)

    # Get the number of followers and following -- these will serve as limits (i.e. how many users we expect to scrape)
    followers_amount, following_amount = await get_limits(page=page)

    # Get the X-IG-App-ID header -- essential for the request to succeed
    x_ig_app_id: str = await get_x_ig_app_id(page=page)

    # Create directories for the scraped and calculated data
    (
        instagram_stats_dir,
        instagram_users_filename,
    ) = create_instragram_stats_dir_and_instagram_users_filename()

    # Make the requests
    instagram_users: Dict[str, List[Dict]] = get_instagram_users(
        expected_user_limits={
            "followers": followers_amount,
            "following": following_amount,
        },
        account_user_name=account_user_name,
        x_ig_app_id=x_ig_app_id,
        ds_user_id=ds_user_id,
        cookies=cookie_dict,
        instagram_users_filename=instagram_users_filename,
    )

    # Close the context and browser
    await context.close()
    await browser.close()

    # Calculate statistics
    instagram_stats: Dict[str, List[Dict]] = calculate_stats(
        instagram_users=instagram_users, show_stats=True
    )

    # Save statistics
    save_stats(instagram_stats=instagram_stats, instagram_stats_dir=instagram_stats_dir)


async def async_main() -> None:
    async with async_playwright() as playwright:
        await get_stats(playwright)


def main() -> None:
    if __name__ == "__main__":
        asyncio.run(async_main())


main()
