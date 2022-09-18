# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass, field
from typing import Union, List

import scrapy


@dataclass
class PartyItem:
    end_date: Union[str, None]
    type: str
    id: Union[str, None]
    name: Union[str, None]
    address: Union[str, None]
    aliases: Union[str, None]
    associates: List[str] = field(default_factory=list)


@dataclass
class EntryItem:
    filing_date: Union[str, None]
    description: Union[str, None]
    party: Union[str, None]
    monetary: Union[str, None]
    content: Union[str, None]


@dataclass
class DocketItem:
    url: str
    id: str
    start_date: Union[str, None]
    end_date: Union[str, None]
    title: str
    filing_date: str
    type: str
    status: str
    parties: List[PartyItem] = field(default_factory=list)
    entries: List[EntryItem] = field(default_factory=list)
