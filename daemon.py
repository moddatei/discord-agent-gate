import sys
import asyncio
from datetime import datetime
from aiohttp import web
import discord
from discord.ui import Button, View, Modal, TextInput

import config

class CustomPromptModal(Modal, title="Send New Prompt / Feedback"):
    feedback = TextInput(
        label="Feedback or Custom Instruction",
        style=discord.TextStyle.paragraph,
        placeholder="e.g. Don't run that command, test src/index.ts instead",
        required=True,
        max_length=2000
    )

    def __init__(self, callback_fut, view_ref, orig_message):
        super().__init__()
        self.callback_fut = callback_fut
        self.view_ref = view_ref
        self.orig_message = orig_message

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.feedback.value
        await interaction.response.send_message(f"💬 **Feedback sent to agent:**\n> {reason}", ephemeral=False)
        
        # Disable buttons on original message
        for item in self.view_ref.children:
            item.disabled = True
        try:
            await self.orig_message.edit(view=self.view_ref)
        except Exception:
            pass

        if not self.callback_fut.done():
            self.callback_fut.set_result({"decision": "deny", "reason": reason, "custom_prompt": reason})


class ApprovalView(View):
    def __init__(self, loop, timeout=config.TIMEOUT_SECONDS):
        super().__init__(timeout=timeout)
        self.decision_fut = loop.create_future()
        self.message = None

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: Button):
        for item in self.children:
            item.disabled = True
        button.label = "Approved ✅"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("✅ **Action approved.** Resuming agent...", ephemeral=True)
        
        if not self.decision_fut.done():
            self.decision_fut.set_result({"decision": "allow", "reason": "Approved via Discord."})
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: Button):
        for item in self.children:
            item.disabled = True
        button.label = "Declined ❌"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("❌ **Action declined.** Agent will be notified.", ephemeral=True)

        if not self.decision_fut.done():
            self.decision_fut.set_result({"decision": "deny", "reason": "Declined remotely via Discord."})
        self.stop()

    @discord.ui.button(label="Send Feedback / Prompt", style=discord.ButtonStyle.secondary, emoji="💬")
    async def custom_feedback(self, interaction: discord.Interaction, button: Button):
        modal = CustomPromptModal(self.decision_fut, self, self.message)
        await interaction.response.send_modal(modal)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(content="⏱️ **Request expired / timed out.**", view=self)
            except Exception:
                pass
        if not self.decision_fut.done():
            self.decision_fut.set_result({"decision": "deny", "reason": "Approval request timed out on Discord."})


class DiscordBridgeDaemon:
    def __init__(self):
        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)
        self.ready_event = asyncio.Event()

        @self.client.event
        async def on_ready():
            print(f"✅ Discord Bot connected as: {self.client.user} (ID: {self.client.user.id})")
            self.ready_event.set()

    async def handle_health(self, request):
        return web.json_response({
            "status": "ok",
            "bot_connected": self.ready_event.is_set(),
            "channel_id": config.CHANNEL_ID
        })

    async def handle_ask(self, request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"decision": "deny", "reason": "Invalid JSON payload"}, status=400)

        agent_name = data.get("agent", "AI AGENT").upper()
        tool_name = data.get("tool", "Action")
        args_content = data.get("args", "")
        workspace = data.get("workspace", "")

        await self.ready_event.wait()
        channel = self.client.get_channel(config.CHANNEL_ID)
        if not channel:
            err_msg = f"Error: Discord channel with ID {config.CHANNEL_ID} not found. Ensure bot is invited to the server."
            print(err_msg, file=sys.stderr)
            return web.json_response({"decision": "deny", "reason": err_msg}, status=500)

        # Truncate content for Discord Embed limit
        if len(args_content) > 1500:
            args_content = args_content[:1500] + "\n... [truncated]"

        # Color based on agent type
        colors = {
            "ANTIGRAVITY": 0x4285F4,  # Google Blue
            "CLAUDE": 0xD97706,       # Anthropic Amber
            "CODEX": 0x10A37F,        # OpenAI Green
        }
        embed_color = colors.get(agent_name, 0x5865F2)

        embed = discord.Embed(
            title=f"🛡️ Confirmation: {agent_name}",
            color=embed_color,
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Discord Agent Gate", url="https://github.com/moddatei/discord-agent-gate")
        embed.add_field(name="Tool / Operation", value=f"`{tool_name}`", inline=True)
        if workspace:
            embed.add_field(name="Workspace", value=f"`{workspace}`", inline=True)
        
        embed.add_field(
            name="Command / Arguments",
            value=f"```yaml\n{args_content}\n```" if args_content else "*No arguments*",
            inline=False
        )
        embed.set_footer(text=f"Auto-expires in {config.TIMEOUT_SECONDS // 60} min • Made by github.com/moddatei")

        view = ApprovalView(asyncio.get_running_loop(), timeout=config.TIMEOUT_SECONDS)
        
        content = config.MENTION if config.MENTION else None
        msg = await channel.send(content=content, embed=embed, view=view)
        view.message = msg

        try:
            result = await asyncio.wait_for(view.decision_fut, timeout=config.TIMEOUT_SECONDS + 5)
        except asyncio.TimeoutError:
            result = {"decision": "deny", "reason": "Timeout reached waiting for Discord response."}

        return web.json_response(result)

    async def start(self):
        if not config.BOT_TOKEN or not config.CHANNEL_ID:
            print("❌ ERROR: DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID must be set in .env")
            print("Run 'python install.py' or edit .env directly.")
            sys.exit(1)

        app = web.Application()
        app.router.add_get("/health", self.handle_health)
        app.router.add_post("/ask", self.handle_ask)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", config.LOCAL_PORT)
        await site.start()
        print(f"🚀 IPC Server listening on http://127.0.0.1:{config.LOCAL_PORT}")
        print(f"⏳ Connecting to Discord Gateway...")

        await self.client.start(config.BOT_TOKEN)


def main():
    daemon = DiscordBridgeDaemon()
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        print("\n👋 Discord Bridge Daemon stopped.")

if __name__ == "__main__":
    main()
