from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Callable
from discord import Interaction, File, ButtonStyle, Embed as E
from discord.ui import View as V, Button as B, ChannelSelect, Modal as M, TextInput


@dataclass
class Field:
    name: str|None = None
    value: str|None = None
    inline: bool|None = None

@dataclass
class Footer:
    text: str|None = None
    icon_url: str|None = None

@dataclass
class Author:
    name: str|None = None
    url: str|None = None
    icon_url: str|None = None

@dataclass
class Embed:
    title: str|None = None
    description: str|None = None
    color: int|None = None
    fields: list[Field] = field(default_factory = list)
    footer: Footer|None = None
    image: str|None = None
    thumbnail: str|None = None
    author: Author|None = None

@dataclass
class Button:
    callback: Callable
    style: ButtonStyle = ButtonStyle.secondary
    label: str = "Button"
    disabled: bool = False
    custom_id: str|None = None
    row: int|None = None

@dataclass
class Select:
    callback: Callable
    select_type: Any
    placeholder: str|None = None
    custom_id: str|None = None
    row: int|None = None

@dataclass
class View:
    data: Any|None = None
    timeout: int|None = None
    buttons: list[Button] = field(default_factory = list)
    selects: list[Select] = field(default_factory = list)

@dataclass
class Message:
    data: Any|None = None
    content: str|None = None
    embeds: list[Embed] = field(default_factory = list)
    view: View|None = None
    files: list[File] = field(default_factory = list)


def render(message_schema: Message) -> dict:
    result = {}

    message = _activate(message_schema, message_schema.data)

    if message.content:
        result["content"] = message.content

    if message.embeds:
        result["embeds"] = [_embed_factory(embed) for embed in message.embeds]

    if message.view:
        result["view"] = _ViewFactory(message.view)

    if message.files:
        result["files"] = message.files

    return result

_IGNORE = {"callback", "data", "select_type"}
def _activate(obj, data):
    if is_dataclass(obj):
        values = {}

        for field in fields(obj):
            value = getattr(obj, field.name)

            if field.name in _IGNORE:
                values[field.name] = value

            else:
                values[field.name] = _activate(value, data)

        return type(obj)(**values)

    if isinstance(obj, list):
        return [_activate(item, data) for item in obj]

    if callable(obj):
        return obj(data)

    return obj


def _embed_factory(embed: Embed) -> E:
    result = E(title = embed.title, description = embed.description, color = embed.color)

    if embed.fields:
        for field in embed.fields:
            result.add_field(name = field.name,
                             value = field.value,
                             inline = field.inline)

    if embed.footer:
        result.set_footer(text = embed.footer.text,
                          icon_url = embed.footer.icon_url)

    if embed.image:
        result.set_image(url = embed.image)

    if embed.thumbnail:
        result.set_thumbnail(url = embed.thumbnail)

    if embed.author:
        result.set_author(name = embed.author.name,
                          url = embed.author.url,
                          icon_url = embed.author.icon_url)

    return result


class _ViewFactory(V):
    def __init__(self, view: View):
        super().__init__(timeout = view.timeout)
        self.data = view.data

        for button in view.buttons:
            self.add_item(_ButtonFactory(button, self.data))

        for select in view.selects:
            self.add_item(select.select_type(select, self.data))

class _ButtonFactory(B):
    def __init__(self, button: Button, data: Any):
        super().__init__(style = button.style, label = button.label, disabled = button.disabled, custom_id = button.custom_id, row = button.row)
        self.button = button
        self.data = data

    async def callback(self, interaction: Interaction):
        await self.button.callback(self, interaction)

class _ChannelSelectFactory(ChannelSelect):
    def __init__(self, select: Select, data: Any):
        ChannelSelect.__init__(self, placeholder = select.placeholder, custom_id = select.custom_id, row = select.row)
        self.select = select
        self.data = data

    async def callback(self, interaction: Interaction):
        await self.select.callback(self, interaction)

class SelectType:
    channel = _ChannelSelectFactory


class Modal(M): # доработать идею
    def __init__(self, items: list[TextInput], func: Callable, data: Any):
        self.func = func
        self.data = data

        for item in items:
            self.add_item(item)

    async def on_submit(self, interaction: Interaction):
        await self.func(interaction, self.data)