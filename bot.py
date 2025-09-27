import asyncio
import os
import requests
from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

url = "https://www.free4talk.com/"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def scrape_and_search(search_name: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=45000)

        await page.evaluate("document.body.style.zoom = '1%'")
        await page.wait_for_selector("div.sc-dNLxif.viewed")

        rooms_data = await page.evaluate("""() => {
            const rooms = Array.from(document.querySelectorAll("div.sc-dNLxif.viewed"));
            return rooms.map(room => {
                const members = Array.from(room.querySelectorAll("button.ant-btn.sc-fAjcbJ"))
                                     .map(b => b.getAttribute("aria-label"));
                const status = room.querySelector("ul.ant-card-actions")?.innerText || "";
                const title = room.querySelector("div.notranslate")?.innerText || "";
                return {members, status, title};
            });
        }""")

        await browser.close()
        return rooms_data, search_name


async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /scrape <Name>")
        return

    search_name = context.args[0]
    await update.message.reply_text(f"Searching for exact match: '{search_name}'...")

    rooms, search_name = await scrape_and_search(search_name)

    matches = []
    for room in rooms:
        if any(member and member.strip() == search_name for member in room["members"]):
            matches.append(room)

    if matches:
        msg = f"Found {len(matches)} room(s) for '{search_name}':\n"
        for match in matches:
            msg += f"\nTitle: {match['title']}\nMembers: {', '.join([i for i in match['members'] if i])}\nStatus: {match['status']}\n"
    else:
        msg = f"No matches found for '{search_name}'."

    await update.message.reply_text(msg)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("scrape", scrape_command))

    print("Bot is running...")
    app.run_polling()
