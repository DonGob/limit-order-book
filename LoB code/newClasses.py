from dataclasses import dataclass, field
from itertools import count, filterfalse
from typing import ClassVar
import numpy as np
from pprintpp import pprint
import enum
import random
from bisect import bisect
import math
from enum import Enum

depth = 14

class OrderBookType(enum.Enum):
    ASK = 0
    BUY = 0
    BID = -1
    SELL = -1
 
@dataclass
class Order:    #werkt
    id: int = field(default_factory=int)
    volume: int = field(default_factory=int)
    price: float = field(default_factory=float)
 
    def sub_volume(self, vol):  #werkt
        self.volume = self.volume - vol
 
@dataclass
class Queue:
    line: list[Order] = field(default_factory=list)
    price: float = field(default_factory=float)
    total_volume: int = field(default_factory=int)

    def execute_orders(self, vol: int): #werkt
        while vol > 0:
            head_order_volume = self.line[0].volume
            if vol >= head_order_volume:
                self.delete_order()
                vol -= head_order_volume
            else:
                self.sub_volume(vol)
                vol = 0
            if not self.line:
                break

    def add_volume(self, new_volume):   #werkt
        self.total_volume += new_volume

    def sub_volume(self, volume, idx=0):    #werkt
        self.total_volume = self.total_volume - volume
        self.line[idx].sub_volume(volume)
 
    def add_order(self, new_order: Order): #werkt
        self.line.append(new_order)
        self.add_volume(new_order.volume)
 
    def delete_order(self, idx = 0):    #werkt
        self.sub_volume(volume=self.line[idx].volume, idx=idx)
        del self.line[idx]

    def cancel_order(self): #werkt
        self.delete_order(idx=(random.randint(0,len(self.line) - 1)))
        
@dataclass
class OrderBookSide:
    type: Enum = field(default_factory=Enum)
    price_levels: list = field(default_factory=list)
    prices: list = field(default_factory=list)  #sorted from small to big
    
    @property
    def head_queue(self):
        return self.price_levels[self.type.value]

    def get_orderbook_side_volume(self):    #werkt
        volume = []
        for i in self.price_levels:
            volume.append(i.total_volume)
        return volume

    def add_order_to_queue(self, new_order: Order): #werkt
        idx = self.check_price_level_idx(new_order.price)
        self.price_levels[idx].add_order(new_order)

    def add_price_level(self, price: float, idx: int):  #werkt
        a = Queue(total_volume=0, price=price) 
        self.price_levels.insert(idx, a)
        self.prices.insert(idx, price)
        
    def del_price_level(self, idx = 0): #werkt
        del self.price_levels[idx]
        del self.prices[idx]

    def check_price_level_idx(self, price: float):  #werkt
        if price in self.prices:
            idx = self.prices.index(price)
            return idx
        else:
            idx = bisect(self.prices, price)
            self.add_price_level(price, idx)
            return idx

    def cancel_order(self, cancel_price: int):  #werkt
        if cancel_price in self.prices:
            idx = self.prices.index(cancel_price)
            self.price_levels[idx].cancel_order()
            if not self.price_levels[idx].line:     #delete pricelevel if last order was deleted
                self.del_price_level(idx)

    def execute_market_order(self, incoming_vol: int): #werkt 
        vol = min(incoming_vol, np.sum(self.get_orderbook_side_volume())) #vol can't exceed total side volume
        while vol > 0:
            execution_vol = min(self.head_queue.total_volume, vol)
            self.head_queue.execute_orders(execution_vol)
            vol -= execution_vol
            if not self.head_queue.line:
                self.del_price_level(idx = self.type.value)
  
    def get_volume_per_tick_side(self, begin_price): #werkt
        volumes_per_tick = np.empty(depth)
        for i in range(0,len(volumes_per_tick)):
            ticks = i +2*i*self.type.value       #adjusted for type
            if begin_price + ticks in self.prices:
                idx = self.prices.index( begin_price + ticks)
                volumes_per_tick[i] = self.get_orderbook_side_volume()[idx]
            else:
                volumes_per_tick[i] = 0
        return np.array(volumes_per_tick, dtype=int)
        
    def initialize_side(self, tick_beginpoint: int): #werkt 
        for i in range (0,depth):
            ticks = i + 2*i*self.type.value       #adjusted for type
            self.add_order_to_queue(Order(id=i,volume=500,price=tick_beginpoint + ticks))

@dataclass
class OrderBook:
    bids = OrderBookSide(OrderBookType.BID)
    asks = OrderBookSide(OrderBookType.ASK)
    price: float = field(default_factory=float)
    ticks_beginpoint_bid: int = field(default_factory=int)
    ticks_beginpoint_ask: int = field(default_factory=int)

    def get_volume_per_tick(self, type: Enum):
        self.update_tick_beginpoints()
        if type == OrderBookType.BID:
            return self.bids.get_volume_per_tick_side(self.ticks_beginpoint_bid)
        elif type == OrderBookType.ASK:
            return self.asks.get_volume_per_tick_side(self.ticks_beginpoint_ask)

    def update_tick_beginpoints(self):
        self.ticks_beginpoint_bid = math.ceil(self.price - 1)
        self.ticks_beginpoint_ask = math.floor(self.price + 1)

    def initialize_orderbook(self):     #goed
        self.update_tick_beginpoints()
        self.bids.initialize_side(self.ticks_beginpoint_bid)
        self.asks.initialize_side(self.ticks_beginpoint_ask)

    def update_price(self): #goed
        if self.bids.price_levels and self.asks.price_levels:
            self.price = (self.bids.head_queue.price + self.asks.head_queue.price)/2

    def add_order(self, new_order: Order, order_type: Enum, order_idx: int):    #goed
        new_order.price = self.determine_order_price(order_type, order_idx)
        if order_type == OrderBookType.BID:
            self.bids.add_order_to_queue(new_order)
        elif order_type == OrderBookType.ASK:
            self.asks.add_order_to_queue(new_order)
        
        self.update_price()

    def determine_order_price(self, order_type: Enum, order_idx: int):    #goed
        self.update_tick_beginpoints()
        if order_type == OrderBookType.BID:
            return self.ticks_beginpoint_bid - order_idx #determine the order price dependant on the orderbook price and distribution idx
        elif order_type == OrderBookType.ASK:
            return self.ticks_beginpoint_ask + order_idx #idem dito

    def fill_market_order(self, vol: int, order_type: Enum):    #goed
        if order_type == OrderBookType.BUY:
            self.asks.execute_market_order(vol)
        elif order_type == OrderBookType.SELL:
            self.bids.execute_market_order(vol)
        self.update_price()

    def cancel_order(self, idx: int, order_type: Enum): #goed
        cancel_price = self.determine_order_price(order_type, idx)
        if order_type == OrderBookType.BID:
            self.bids.cancel_order(cancel_price)
        if order_type == OrderBookType.ASK:
            self.asks.cancel_order(cancel_price)

            